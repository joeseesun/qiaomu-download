#!/usr/bin/env python3
"""Download, verify, and extract the pinned upstream backend without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    aliases = {"aarch64": "arm64", "amd64": "x86_64", "i386": "x86"}
    return f"{system}-{aliases.get(machine, machine)}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_target(root: Path, member: str) -> Path:
    target = (root / member).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError(f"archive path escapes destination: {member}")
    return target


def extract(archive: Path, destination: Path) -> None:
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                safe_target(destination, item.filename)
                unix_mode = (item.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise ValueError("archive links are not allowed")
            bundle.extractall(destination)
        return
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as bundle:
            for item in bundle.getmembers():
                safe_target(destination, item.name)
                if item.issym() or item.islnk():
                    raise ValueError("archive links are not allowed")
                if not (item.isfile() or item.isdir()):
                    raise ValueError("archive special files are not allowed")
            bundle.extractall(destination)
        return
    raise ValueError(f"unsupported archive: {archive.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the pinned wx_channels_download backend.")
    parser.add_argument("--install-root", help="Scoped destination root")
    parser.add_argument("--platform", dest="target_platform", help="Override platform key for fixture testing")
    parser.add_argument("--accept-upstream-license", action="store_true", help="Confirm upstream license review")
    args = parser.parse_args()
    if not args.accept_upstream_license:
        raise SystemExit("refusing download: pass --accept-upstream-license after reviewing upstream LICENSE")

    lock = json.loads((ROOT / "release-lock.json").read_text(encoding="utf-8"))
    key = args.target_platform or platform_key()
    asset = lock["assets"].get(key)
    if not asset:
        raise SystemExit(f"unsupported platform: {key}")
    install_root = Path(args.install_root or os.environ.get("QIAOMU_WX_VIDEO_HOME", Path.home() / ".local/share/qiaomu-wx-video"))
    backend_root = install_root / "backend"
    destination = backend_root / lock["tag"]
    marker = destination / ".qiaomu-install.json"
    if marker.is_file():
        installed = json.loads(marker.read_text(encoding="utf-8"))
        if installed.get("archive_sha256") == asset["sha256"] and installed.get("platform") == key:
            print(json.dumps({"ok": True, "cached": True, "platform": key, "tag": lock["tag"], "install_dir": str(destination), "sha256": asset["sha256"]}, ensure_ascii=False, indent=2))
            return
    if destination.exists():
        raise SystemExit(f"refusing to overwrite incomplete or unknown install: {destination}")
    backend_root.mkdir(parents=True, exist_ok=True)
    os.chmod(backend_root, 0o700)
    url = f"https://github.com/{lock['upstream']}/releases/download/{lock['tag']}/{asset['name']}"

    temp_dir = Path(tempfile.mkdtemp(prefix="qiaomu-wx-video-download-"))
    stage = Path(tempfile.mkdtemp(prefix=f".{lock['tag']}-stage-", dir=backend_root))
    archive = temp_dir / asset["name"]
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "qiaomu-wx-video/0.1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = sha256(archive)
        if actual.lower() != asset["sha256"].lower():
            raise SystemExit(f"SHA-256 mismatch: expected {asset['sha256']}, got {actual}")
        extract(archive, stage)
        for candidate in stage.rglob("wx_video_download*"):
            if candidate.is_file() and not candidate.name.endswith((".yaml", ".md")):
                candidate.chmod(candidate.stat().st_mode | 0o700)
        marker_payload = {"tag": lock["tag"], "platform": key, "asset": asset["name"], "archive_sha256": actual, "source": url}
        (stage / ".qiaomu-install.json").write_text(json.dumps(marker_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stage.replace(destination)
        print(json.dumps({"ok": True, "platform": key, "tag": lock["tag"], "install_dir": str(destination), "sha256": actual}, ensure_ascii=False, indent=2))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main()
