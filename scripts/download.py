#!/usr/bin/env python3
"""Guarded, cross-platform yt-dlp wrapper for qiaomu-download."""

from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager
import hashlib
import ipaddress
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, BinaryIO, Iterator
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlsplit, urlunsplit

VERSION = "1.1.1"
YT_DLP_RELEASE_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
YT_DLP_RELEASE_LATEST = "https://github.com/yt-dlp/yt-dlp/releases/latest"
MEDIA_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".opus", ".ogg", ".wav"}
VIDEO_OUTPUT_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov"}
AUDIO_OUTPUT_SUFFIXES = {".mp3"}
SUBTITLE_SUFFIXES = {".srt", ".vtt", ".ass", ".lrc", ".txt"}
FORMAT_FRAGMENT_RE = re.compile(r"\.f[^.]+\.[^.]+$")
BROWSER_APPLICATIONS = {
    "chrome": ("/Applications/Google Chrome.app", "~/Applications/Google Chrome.app"),
    "edge": ("/Applications/Microsoft Edge.app", "~/Applications/Microsoft Edge.app"),
    "firefox": ("/Applications/Firefox.app", "~/Applications/Firefox.app"),
    "safari": ("/Applications/Safari.app",),
}
QUALITY_FORMATS = {
    "best": "bv*+ba/b",
    "1080p": "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
    "720p": "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b",
    "480p": "bv*[height<=480]+ba/b[height<=480]/bv*+ba/b",
}
KNOWN_PLATFORMS = {
    "youtube.com": "YouTube", "youtu.be": "YouTube", "bilibili.com": "Bilibili",
    "b23.tv": "Bilibili", "x.com": "X", "twitter.com": "X", "vimeo.com": "Vimeo",
    "tiktok.com": "TikTok", "instagram.com": "Instagram", "facebook.com": "Facebook",
    "twitch.tv": "Twitch", "reddit.com": "Reddit",
}


class SkillError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


def require_tool(name: str) -> str:
    override = os.environ.get(f"QIAOMU_{name.upper().replace('-', '_')}_BIN")
    path = override or shutil.which(name)
    if not path or not Path(path).expanduser().is_file():
        raise SkillError("dependency", f"{name} not found; run doctor for installation guidance")
    return str(Path(path).expanduser())


def error_summary(completed: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part for part in (completed.stderr, completed.stdout) if part).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines[-8:])[:1600] or f"command exited with {completed.returncode}"


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM) if os.name == "posix" else process.terminate()
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL) if os.name == "posix" else process.kill()
            except ProcessLookupError:
                pass


def run_command(args: list[str], stage: str, timeout: int, *, stream: bool = False,
                pass_fds: tuple[int, ...] = ()) -> subprocess.CompletedProcess[str]:
    if stream and os.name == "posix":
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, start_new_session=True, pass_fds=pass_fds)
        if process.stdout is None:
            raise SkillError(stage, "could not capture command output")
        output: deque[str] = deque(maxlen=500)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    terminate_process_tree(process)
                    raise SkillError(stage, f"command timed out after {timeout}s")
                for key, _mask in selector.select(timeout=min(1.0, remaining)):
                    line = key.fileobj.readline()
                    if line:
                        output.append(line)
                        print(line.rstrip(), file=sys.stderr, flush=True)
            tail = process.stdout.read()
            if tail:
                output.append(tail)
                print(tail.rstrip(), file=sys.stderr, flush=True)
        except KeyboardInterrupt:
            terminate_process_tree(process)
            raise
        finally:
            selector.close()
            process.stdout.close()
        completed = subprocess.CompletedProcess(args, process.returncode, "".join(output), "")
    else:
        try:
            completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise SkillError(stage, f"command timed out after {timeout}s") from exc
    if completed.returncode != 0:
        raise SkillError(stage, error_summary(completed))
    return completed


def normalize_url(raw: str) -> str:
    value = raw.strip().strip("<>[](){}\"'")
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise SkillError("validate", "video URL must use HTTPS")
    try:
        custom_port = parsed.port
    except ValueError as exc:
        raise SkillError("validate", "video URL contains an invalid port") from exc
    if parsed.username or parsed.password or custom_port:
        raise SkillError("validate", "video URL must not contain credentials or a custom port")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host or host == "localhost" or host.endswith(".localhost"):
        raise SkillError("validate", "video URL must use a public host")
    try:
        address = ipaddress.ip_address(host.strip("[]"))
        if not address.is_global:
            raise SkillError("validate", "private, loopback, and link-local addresses are not allowed")
    except ValueError:
        pass
    if host == "weixin.qq.com" and parsed.path.startswith("/sph/"):
        raise SkillError("route", "WeChat Channels links must use qiaomu-wx-video; do not automate the WeChat UI")
    return urlunsplit(("https", host, parsed.path or "/", parsed.query, ""))


def platform_name(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    for suffix, name in KNOWN_PLATFORMS.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    return "yt-dlp generic extractor"


def detect_cookie_browser(mode: str) -> str | None:
    if mode == "none":
        return None
    if mode != "auto":
        return mode
    for browser in ("chrome", "edge", "firefox", "safari"):
        if any(Path(path).expanduser().exists() for path in BROWSER_APPLICATIONS[browser]):
            return browser
    return None


def cookie_args(browser: str | None) -> list[str]:
    return ["--cookies-from-browser", browser] if browser else []


def ffmpeg_args() -> list[str]:
    override = os.environ.get("QIAOMU_FFMPEG_BIN")
    return ["--ffmpeg-location", str(Path(override).expanduser())] if override else []


def executable_version(executable: str) -> str:
    result = run_command([executable, "--version"], "dependency", 30)
    return next((line.strip() for line in result.stdout.splitlines() if line.strip()), "unknown")


def version_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", value)) or (0,)


def latest_ytdlp_version(timeout: int) -> str:
    request = urllib.request.Request(YT_DLP_RELEASE_API, headers={
        "Accept": "application/vnd.github+json", "User-Agent": f"qiaomu-download/{VERSION}"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            latest = str(json.loads(response.read().decode("utf-8")).get("tag_name") or "").lstrip("v")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        redirect = urllib.request.Request(YT_DLP_RELEASE_LATEST,
                                          headers={"User-Agent": f"qiaomu-download/{VERSION}"})
        try:
            with urllib.request.urlopen(redirect, timeout=timeout) as response:
                latest = urllib.parse.unquote(response.geturl().rstrip("/").rsplit("/", 1)[-1]).lstrip("v")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise SkillError("update-check", f"cannot read the official yt-dlp release: {exc}") from exc
    if not re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}(?:\.\d+)?", latest):
        raise SkillError("update-check", "official yt-dlp release returned an unexpected version")
    return latest


def detect_ytdlp_manager(yt_dlp: str) -> tuple[str, list[str]]:
    brew = shutil.which("brew")
    resolved = str(Path(yt_dlp).resolve())
    if brew:
        probe = subprocess.run([brew, "--prefix", "yt-dlp"], check=False, capture_output=True, text=True, timeout=30)
        if probe.returncode == 0 and probe.stdout.strip() and resolved.startswith(str(Path(probe.stdout.strip()).resolve())):
            return "homebrew", [brew, "upgrade", "yt-dlp"]
    sibling_python = Path(yt_dlp).resolve().parent / "python"
    if sibling_python.is_file():
        probe = subprocess.run([str(sibling_python), "-c", "import yt_dlp"], check=False,
                               capture_output=True, text=True, timeout=30)
        if probe.returncode == 0:
            return "pip", [str(sibling_python), "-m", "pip", "install", "--upgrade", "yt-dlp"]
    for name, command in (("pipx", [shutil.which("pipx") or "", "upgrade", "yt-dlp"]),
                          ("uv", [shutil.which("uv") or "", "tool", "upgrade", "yt-dlp"])):
        if command[0]:
            probe = subprocess.run([command[0], "list"], check=False, capture_output=True, text=True, timeout=30)
            if "yt-dlp" in (probe.stdout + probe.stderr):
                return name, command
    return "self-update", [yt_dlp, "-U"]


def optional_tool_version(name: str) -> str | None:
    try:
        executable = require_tool(name)
    except SkillError:
        return None
    result = subprocess.run([executable, "-version"], check=False, capture_output=True, text=True, timeout=30)
    lines = (result.stdout or result.stderr).splitlines()
    return lines[0].strip() if lines else None


def doctor(upgrade: bool, timeout: int) -> dict[str, Any]:
    yt_dlp = require_tool("yt-dlp")
    installed = executable_version(yt_dlp)
    latest = latest_ytdlp_version(min(timeout, 60))
    manager, command = detect_ytdlp_manager(yt_dlp)
    outdated = version_key(installed) < version_key(latest)
    upgraded = False
    if upgrade and outdated:
        previous = installed
        env = dict(os.environ)
        if manager == "homebrew":
            env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout, env=env)
        if result.returncode != 0:
            raise SkillError("upgrade", error_summary(result))
        installed = executable_version(yt_dlp)
        if version_key(installed) <= version_key(previous):
            raise SkillError("upgrade", f"yt-dlp version did not advance ({previous} -> {installed})")
        outdated = version_key(installed) < version_key(latest)
        upgraded = True
    return {"ok": True, "command": "doctor", "yt_dlp": {
        "executable": str(Path(yt_dlp).resolve()), "installed_version": installed,
        "latest_stable_version": latest, "outdated": outdated, "manager": manager,
        "upgrade_requested": upgrade, "upgraded": upgraded},
        "ffmpeg_version": optional_tool_version("ffmpeg"), "ffprobe_version": optional_tool_version("ffprobe")}


def load_metadata_once(url: str, browser: str | None, timeout: int) -> dict[str, Any]:
    command = [require_tool("yt-dlp"), "--dump-single-json", "--skip-download", "--no-playlist",
               "--no-warnings", *cookie_args(browser), url]
    result = run_command(command, "metadata", timeout)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SkillError("metadata", "yt-dlp returned invalid JSON") from exc
    if not payload.get("id"):
        raise SkillError("metadata", "yt-dlp metadata is missing a media ID")
    return payload


def load_metadata(url: str, cookie_mode: str, timeout: int = 90) -> tuple[dict[str, Any], str | None, list[str]]:
    warnings: list[str] = []
    if cookie_mode != "auto":
        browser = detect_cookie_browser(cookie_mode)
        return load_metadata_once(url, browser, timeout), browser, warnings
    try:
        return load_metadata_once(url, None, timeout), None, warnings
    except SkillError as public_error:
        browser = detect_cookie_browser("auto")
        if not browser:
            raise
        warnings.append(f"public extraction failed; retried with local {browser} cookies: {public_error}")
        return load_metadata_once(url, browser, timeout), browser, warnings


def metadata_summary(payload: dict[str, Any], source_url: str) -> dict[str, Any]:
    return {"id": payload.get("id"), "title": payload.get("title"),
            "channel": payload.get("channel") or payload.get("uploader"), "duration_seconds": payload.get("duration"),
            "width": payload.get("width"), "height": payload.get("height"),
            "extractor": payload.get("extractor_key") or payload.get("extractor"),
            "platform": platform_name(source_url), "webpage_url": payload.get("webpage_url") or source_url}


def output_template(output_dir: Path) -> str:
    return str(output_dir / "%(title).160B [%(id)s].%(ext)s")


def prepare_output_dir(value: str | None) -> Path:
    output = Path(value or os.environ.get("QIAOMU_DOWNLOAD_OUTPUT") or Path.home() / "Downloads").expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def lock_path(output_dir: Path, media_id: str, operation: str) -> Path:
    root = Path(tempfile.gettempdir()) / "qiaomu-download-locks"
    root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(f"{output_dir.resolve()}|{media_id}|{operation}".encode()).hexdigest()
    return root / f"{digest}.lock"


@contextmanager
def download_lock(output_dir: Path, media_id: str, operation: str) -> Iterator[BinaryIO]:
    handle = lock_path(output_dir, media_id, operation).open("a+b")
    try:
        if os.name == "posix":
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SkillError("download", "this media is already downloading to the same directory") from exc
        handle.seek(0); handle.truncate(); handle.write(str(os.getpid()).encode()); handle.flush()
        yield handle
    finally:
        if os.name == "posix":
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        handle.close()


def matching_files(output_dir: Path, media_id: str, suffixes: set[str]) -> list[Path]:
    return sorted(path for path in output_dir.iterdir() if path.is_file() and f"[{media_id}]" in path.name
                  and path.suffix.lower() in suffixes and not path.name.endswith((".part", ".ytdl"))
                  and not FORMAT_FRAGMENT_RE.search(path.name))


def all_media_files(output_dir: Path, media_id: str) -> list[Path]:
    return sorted(path for path in output_dir.iterdir() if path.is_file() and f"[{media_id}]" in path.name
                  and path.suffix.lower() in MEDIA_SUFFIXES)


def cleanup_new_format_fragments(output_dir: Path, media_id: str, before: set[Path]) -> list[str]:
    removed = []
    for path in all_media_files(output_dir, media_id):
        if path.resolve() not in before and FORMAT_FRAGMENT_RE.search(path.name):
            path.unlink(); removed.append(str(path.resolve()))
    return removed


def probe_media(path: Path, expect: str) -> dict[str, Any]:
    command = [require_tool("ffprobe"), "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height",
               "-show_entries", "format=format_name,duration,size", "-of", "json", str(path)]
    result = run_command(command, "verify", 60)
    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    expected = "audio" if expect == "audio" else "video"
    if not any(stream.get("codec_type") == expected for stream in streams):
        raise SkillError("verify", f"{path.name} has no {expected} stream")
    duration = float((payload.get("format") or {}).get("duration") or 0)
    if duration <= 0 or path.stat().st_size <= 0:
        raise SkillError("verify", f"{path.name} has invalid duration or size")
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "container": (payload.get("format") or {}).get("format_name"), "video_codec": video.get("codec_name"),
            "audio_codec": audio.get("codec_name"), "width": video.get("width"), "height": video.get("height"),
            "duration_seconds": round(duration, 3)}


def download_media(url: str, output_dir: Path, quality: str, cookie_mode: str,
                   audio_only: bool, timeout: int) -> dict[str, Any]:
    yt_dlp = require_tool("yt-dlp")
    require_tool("ffmpeg"); require_tool("ffprobe")
    metadata, browser, warnings = load_metadata(url, cookie_mode, min(timeout, 120))
    media_id = str(metadata["id"])
    operation = "audio" if audio_only else "video"
    suffixes = AUDIO_OUTPUT_SUFFIXES if audio_only else VIDEO_OUTPUT_SUFFIXES
    with download_lock(output_dir, media_id, operation) as lock:
        before = {p.resolve() for p in matching_files(output_dir, media_id, suffixes)}
        before_artifacts = {p.resolve() for p in all_media_files(output_dir, media_id)}
        command = [yt_dlp, "--no-playlist", "--no-overwrites", "--newline",
                   *ffmpeg_args(), *cookie_args(browser)]
        command += (["-x", "--audio-format", "mp3", "--audio-quality", "0"] if audio_only else
                    ["-f", QUALITY_FORMATS[quality], "--merge-output-format", "mp4"])
        command += ["-o", output_template(output_dir), url]
        run_command(command, "download", timeout, stream=True, pass_fds=(lock.fileno(),))
        files = matching_files(output_dir, media_id, suffixes)
        if not files:
            raise SkillError("download", "yt-dlp finished but no final media file was found")
        verified = [probe_media(path, operation) for path in files]
        for item in verified:
            item["created"] = Path(item["path"]).resolve() not in before
        cleaned = cleanup_new_format_fragments(output_dir, media_id, before_artifacts)
    return {"ok": True, "command": operation, **metadata_summary(metadata, url), "quality": quality,
            "files": verified, "cleaned_intermediate_files": cleaned, "cookies_from_browser": browser,
            "warnings": warnings}


def download_subtitles(url: str, output_dir: Path, langs: str, cookie_mode: str, timeout: int) -> dict[str, Any]:
    metadata, browser, warnings = load_metadata(url, cookie_mode, min(timeout, 120))
    media_id = str(metadata["id"])
    with download_lock(output_dir, media_id, "subtitles") as lock:
        command = [require_tool("yt-dlp"), "--no-playlist", "--no-overwrites", *ffmpeg_args(),
                   "--write-subs", "--write-auto-subs",
                   "--sub-langs", langs, "--convert-subs", "srt", "--skip-download", *cookie_args(browser),
                   "-o", output_template(output_dir), url]
        run_command(command, "download", timeout, stream=True, pass_fds=(lock.fileno(),))
    files = matching_files(output_dir, media_id, SUBTITLE_SUFFIXES)
    if not files:
        raise SkillError("download", "no requested subtitles were available")
    return {"ok": True, "command": "subtitles", **metadata_summary(metadata, url),
            "files": [{"path": str(path.resolve()), "bytes": path.stat().st_size} for path in files],
            "cookies_from_browser": browser, "warnings": warnings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download and verify public or user-authorized online video with yt-dlp.")
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    dependency = commands.add_parser("doctor")
    dependency.add_argument("--upgrade", action="store_true")
    dependency.add_argument("--timeout", type=int, default=300)
    def add_url_args(item: argparse.ArgumentParser, include_dir: bool = False) -> None:
        item.add_argument("url")
        if include_dir:
            item.add_argument("--dir", dest="output_dir")
        item.add_argument("--cookies-from-browser", choices=("auto", "none", "chrome", "firefox", "safari", "edge"), default="auto")
        item.add_argument("--timeout", type=int, default=1200)
    info = commands.add_parser("info"); add_url_args(info)
    download = commands.add_parser("download"); add_url_args(download, True)
    download.add_argument("--quality", choices=tuple(QUALITY_FORMATS), default="best")
    audio = commands.add_parser("audio"); add_url_args(audio, True)
    subtitles = commands.add_parser("subtitles"); add_url_args(subtitles, True)
    subtitles.add_argument("--langs", default="en.*,zh.*,ja.*")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "doctor":
            result = doctor(args.upgrade, args.timeout)
        else:
            url = normalize_url(args.url)
            if args.command == "info":
                metadata, browser, warnings = load_metadata(url, args.cookies_from_browser, args.timeout)
                result = {"ok": True, "command": "info", **metadata_summary(metadata, url),
                          "cookies_from_browser": browser, "warnings": warnings}
            elif args.command == "download":
                result = download_media(url, prepare_output_dir(args.output_dir), args.quality,
                                        args.cookies_from_browser, False, args.timeout)
            elif args.command == "audio":
                result = download_media(url, prepare_output_dir(args.output_dir), "best",
                                        args.cookies_from_browser, True, args.timeout)
            else:
                result = download_subtitles(url, prepare_output_dir(args.output_dir), args.langs,
                                            args.cookies_from_browser, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except SkillError as exc:
        print(json.dumps({"ok": False, "stage": exc.stage, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "stage": "interrupted", "error": "operation interrupted"}, ensure_ascii=False, indent=2))
        raise SystemExit(130)


if __name__ == "__main__":
    main()
