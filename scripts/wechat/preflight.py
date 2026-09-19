#!/usr/bin/env python3
"""Validate a WeChat Channels URL and inspect the local backend without mutation."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def normalize_url(raw: str) -> str:
    value = raw.strip().strip("<>[](){}\"'")
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("share URL must use HTTPS")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("share URL must not contain credentials or a custom port")
    if (parsed.hostname or "").lower() != "weixin.qq.com":
        raise ValueError("expected host weixin.qq.com")
    if not parsed.path.startswith("/sph/") or len(parsed.path) <= len("/sph/"):
        raise ValueError("expected a /sph/<token> share URL")
    return urlunsplit(("https", "weixin.qq.com", parsed.path, parsed.query, ""))


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    aliases = {"aarch64": "arm64", "amd64": "x86_64", "i386": "x86"}
    return f"{system}-{aliases.get(machine, machine)}"


def backend_candidates() -> list[str]:
    values: list[str] = []
    configured = os.environ.get("QIAOMU_WX_VIDEO_BACKEND")
    if configured:
        values.append(configured)
    found = shutil.which("wx_video_download")
    if found:
        values.append(found)
    home = Path(os.environ.get("QIAOMU_WX_VIDEO_HOME", Path.home() / ".local/share/qiaomu-wx-video"))
    for name in ("wx_video_download", "wx_video_download.exe"):
        for path in home.glob(f"backend/*/{name}"):
            values.append(str(path))
    return list(dict.fromkeys(values))


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only preflight for qiaomu-wx-video.")
    parser.add_argument("--url", required=True, help="WeChat Channels share URL")
    args = parser.parse_args()
    try:
        normalized = normalize_url(args.url)
        error = None
    except ValueError as exc:
        normalized = None
        error = str(exc)
    candidates = backend_candidates()
    payload = {
        "ok": error is None,
        "normalized_url": normalized,
        "error": error,
        "platform": platform_key(),
        "backend_candidates": candidates,
        "local_api_2022_listening": port_open("127.0.0.1", 2022),
        "local_proxy_2023_listening": port_open("127.0.0.1", 2023),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if error:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
