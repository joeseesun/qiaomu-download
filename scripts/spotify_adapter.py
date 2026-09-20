#!/usr/bin/env python3
"""Spotify track adapter: public metadata, scored YouTube match, verified MP3."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import difflib
import hashlib
from html.parser import HTMLParser
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit, urlunsplit

STRATEGY_FILE = Path(__file__).with_name("spotify") / "release-lock.json"
TRACK_RE = re.compile(r"^/track/([A-Za-z0-9]{22})/?$")
BAD_VARIANTS = {"cover", "karaoke", "nightcore", "slowed", "sped up", "remix", "remaster", "live", "instrumental"}


class AdapterError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        key = data.get("property") or data.get("name")
        if tag == "meta" and key and data.get("content") and key not in self.values:
            self.values[key] = str(data["content"])


def strategy() -> dict[str, Any]:
    try:
        payload = json.loads(STRATEGY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError("dependency", "Spotify matching strategy file is missing or invalid") from exc
    if not payload.get("version") or not payload.get("source"):
        raise AdapterError("dependency", "Spotify matching strategy file is incomplete")
    return payload


def normalize_track_url(raw: str) -> tuple[str, str]:
    parsed = urlsplit(raw.strip().strip("<>[](){}\"'"))
    host = (parsed.hostname or "").rstrip(".").lower()
    try:
        port = parsed.port
    except ValueError as exc:
        raise AdapterError("validate", "Spotify URL contains an invalid port") from exc
    if parsed.scheme.lower() != "https" or host != "open.spotify.com" or parsed.username or parsed.password or port:
        raise AdapterError("validate", "Spotify downloads require a public https://open.spotify.com/track/... URL")
    match = TRACK_RE.fullmatch(parsed.path)
    if not match:
        raise AdapterError("unsupported", "automatic Spotify download supports one track URL; collections need bounded batch selection")
    return urlunsplit(("https", host, parsed.path.rstrip("/"), "", "")), match.group(1)


def tool(name: str) -> str:
    found = os.environ.get(f"QIAOMU_{name.upper().replace('-', '_')}_BIN") or shutil.which(name)
    if not found or not Path(found).expanduser().is_file():
        raise AdapterError("dependency", f"{name} not found")
    return str(Path(found).expanduser())


def error_text(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in (result.stderr + "\n" + result.stdout).splitlines() if line.strip()]
    return " | ".join(lines[-8:])[:1600] or f"command exited with {result.returncode}"


def fetch_metadata(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 qiaomu-download/1.3.0", "Accept-Language": "en-US,en;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            page = response.read(2_000_000).decode("utf-8", "replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise AdapterError("metadata", f"could not read public Spotify metadata: {exc}") from exc
    parser = MetaParser(); parser.feed(page); meta = parser.values
    parts = [part.strip() for part in meta.get("og:description", "").split(" · ") if part.strip()]
    title, artist = meta.get("og:title", "").strip(), parts[0] if parts else ""
    try:
        duration = int(meta.get("music:duration", "0"))
    except ValueError:
        duration = 0
    if not title or not artist or duration <= 0:
        raise AdapterError("metadata", "Spotify page did not expose complete public track metadata")
    return {"title": title, "artist": artist, "album": parts[1] if len(parts) > 1 else "",
            "year": next((p for p in reversed(parts) if re.fullmatch(r"\d{4}", p)), ""),
            "duration": duration, "cover_url": meta.get("og:image")}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).split())


def ratio(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalized(left), normalized(right)).ratio() * 100


def score(track: dict[str, Any], item: dict[str, Any]) -> tuple[float, dict[str, float]]:
    title = str(item.get("title") or ""); channel = str(item.get("channel") or item.get("uploader") or "")
    title_score = max(ratio(track["title"], title), ratio(f"{track['artist']} {track['title']}", title))
    artist_score = max(ratio(track["artist"], channel), ratio(track["artist"], title))
    delta = abs(float(item.get("duration") or 0) - float(track["duration"]))
    duration_score = max(0.0, 100.0 - delta * 12.5)
    verified = 7.0 if item.get("channel_is_verified") is True else 0.0
    penalty = sum(14.0 for word in BAD_VARIANTS if word in normalized(title) and word not in normalized(track["title"]))
    if not any(ord(char) > 127 for char in track["title"] + track["artist"]) and any(ord(char) > 127 for char in title):
        penalty += 20.0
    total = max(0.0, title_score * .48 + artist_score * .27 + duration_score * .25 + verified - penalty)
    return round(total, 2), {"title": round(title_score, 2), "artist": round(artist_score, 2),
                              "duration": round(duration_score, 2), "verified_bonus": verified,
                              "variant_penalty": penalty}


def resolve_source(track: dict[str, Any], timeout: int) -> tuple[dict[str, Any], float, dict[str, float]]:
    # Plain normalized terms are more reliable for punctuation-heavy artist names;
    # adding "official audio" can cause YouTube to discard obscure exact matches.
    query = f"ytsearch10:{normalized(track['artist'])} {normalized(track['title'])}"
    result = subprocess.run([tool("yt-dlp"), "--dump-single-json", "--skip-download", "--no-warnings", query],
                            check=False, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise AdapterError("match", error_text(result))
    try:
        entries = json.loads(result.stdout).get("entries") or []
    except json.JSONDecodeError as exc:
        raise AdapterError("match", "yt-dlp search returned invalid JSON") from exc
    candidates = [item for item in entries if item and item.get("id")]
    max_views = max((int(item.get("view_count") or 0) for item in candidates), default=0)
    ranked = []
    for item in candidates:
        (base_score, detail) = score(track, item)
        if detail["title"] < 60 or detail["artist"] < 60 or detail["duration"] < 25:
            continue
        views = int(item.get("view_count") or 0)
        popularity = 20.0 * math.log10(views + 1) / math.log10(max_views + 1) if max_views else 0.0
        detail["popularity_bonus"] = round(popularity, 2)
        ranked.append(((round(min(base_score + popularity, 100.0), 2), detail), item))
    if not ranked:
        raise AdapterError("match", "no sufficiently similar public YouTube candidates were found")
    (confidence, detail), best = max(ranked, key=lambda pair: pair[0][0])
    if confidence < 72:
        raise AdapterError("match", f"best candidate confidence was too low ({confidence})")
    best = dict(best)
    best["source_url"] = best.get("webpage_url") or best.get("original_url") or f"https://www.youtube.com/watch?v={best['id']}"
    return best, confidence, detail


def filename(value: str) -> str:
    return (re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", value).strip(" .")[:180] or "Spotify track")


def apply_tags(path: Path, track: dict[str, Any], timeout: int) -> bool:
    with tempfile.TemporaryDirectory(prefix="qiaomu-spotify-tags-") as temp:
        tagged = Path(temp) / "tagged.mp3"
        command = [tool("ffmpeg"), "-v", "error", "-i", str(path), "-map", "0:a:0", "-c:a", "copy",
                   "-id3v2_version", "3", "-metadata", f"title={track['title']}",
                   "-metadata", f"artist={track['artist']}", "-metadata", f"album={track['album']}"]
        if track.get("year"):
            command += ["-metadata", f"date={track['year']}"]
        command += ["-y", str(tagged)]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
        if result.returncode or not tagged.is_file() or not tagged.stat().st_size:
            return False
        shutil.copy2(tagged, path)
        return True


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run([tool("ffprobe"), "-v", "error", "-show_entries", "stream=codec_type,codec_name,bit_rate",
                             "-show_entries", "format=format_name,duration,size", "-of", "json", str(path)],
                            check=False, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise AdapterError("verify", error_text(result))
    payload = json.loads(result.stdout); streams = payload.get("streams") or []
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float((payload.get("format") or {}).get("duration") or 0)
    if not audio or duration <= 0 or path.stat().st_size <= 0:
        raise AdapterError("verify", f"{path.name} has no valid audio stream")
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "container": (payload.get("format") or {}).get("format_name"),
            "audio_codec": audio.get("codec_name"), "audio_bitrate": audio.get("bit_rate"),
            "duration_seconds": round(duration, 3)}


@contextmanager
def track_lock(output_dir: Path, track_id: str) -> Iterator[None]:
    lock_dir = Path(tempfile.gettempdir()) / "qiaomu-download-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(f"spotify|{output_dir}|{track_id}".encode()).hexdigest()
    handle = (lock_dir / f"{digest}.lock").open("a+b")
    try:
        if os.name == "posix":
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise AdapterError("download", "this Spotify track is already downloading") from exc
        yield
    finally:
        if os.name == "posix":
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def download_track(raw_url: str, output_dir: Path, timeout: int) -> dict[str, Any]:
    spotify_url, track_id = normalize_track_url(raw_url)
    output_dir = output_dir.expanduser().resolve(); output_dir.mkdir(parents=True, exist_ok=True)
    tool("ffmpeg"); tool("ffprobe")
    track = fetch_metadata(spotify_url, min(timeout, 60))
    source, confidence, detail = resolve_source(track, min(timeout, 180))
    base = filename(f"{track['artist']} - {track['title']} [{track_id}]"); output = output_dir / f"{base}.mp3"
    with track_lock(output_dir, track_id):
        existed = output.exists()
        if not existed:
            result = subprocess.run([tool("yt-dlp"), "--no-playlist", "--no-overwrites", "-x", "--audio-format", "mp3",
                                     "--audio-quality", "128K", "--newline", "-o", str(output_dir / f"{base}.%(ext)s"),
                                     str(source["source_url"])], check=False, capture_output=True, text=True, timeout=timeout)
            if result.returncode:
                raise AdapterError("download", error_text(result))
            if not output.is_file():
                raise AdapterError("download", "yt-dlp finished but no final MP3 was found")
            tags_applied = apply_tags(output, track, min(timeout, 120))
        else:
            tags_applied = False
        verified = probe(output); verified.update(created=not existed, spotify_tags_applied=tags_applied)
    prior = strategy()
    return {"ok": True, "command": "audio", "platform": "Spotify", "spotify_url": spotify_url,
            "spotify_track_id": track_id, "title": track["title"], "artist": track["artist"], "album": track["album"],
            "metadata_source": "Spotify public page", "audio_source": "YouTube",
            "audio_source_url": source["source_url"], "audio_source_title": source.get("title"),
            "audio_source_channel": source.get("channel") or source.get("uploader"),
            "match_confidence": confidence, "match_score_detail": detail,
            "match_method": "title, artist, duration, verified-channel bonus and variant penalties",
            "prior_art": f"spotDL {prior['version']}", "drm_bypass_used": False, "spotify_login_used": False,
            "files": [verified], "warnings": ["Spotify supplied metadata only; audio was matched from a public YouTube source."]}


def doctor() -> dict[str, Any]:
    prior = strategy()
    return {"ok": True, "adapter": "spotify-public-match", "strategy_version": "1",
            "prior_art": f"spotDL {prior['version']}", "yt_dlp": shutil.which("yt-dlp"),
            "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"),
            "deno": shutil.which("deno"), "spotify_login_required": False}


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve Spotify metadata to verified public audio")
    sub = parser.add_subparsers(dest="command", required=True); sub.add_parser("doctor")
    item = sub.add_parser("download"); item.add_argument("url"); item.add_argument("--dir", default=str(Path.home() / "Downloads")); item.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    try:
        payload = doctor() if args.command == "doctor" else download_track(args.url, Path(args.dir), args.timeout)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except AdapterError as exc:
        print(json.dumps({"ok": False, "stage": exc.stage, "error": str(exc)}, ensure_ascii=False, indent=2)); raise SystemExit(2)
    except subprocess.TimeoutExpired as exc:
        print(json.dumps({"ok": False, "stage": "timeout", "error": f"command timed out: {exc}"}, ensure_ascii=False, indent=2)); raise SystemExit(2)


if __name__ == "__main__":
    main()
