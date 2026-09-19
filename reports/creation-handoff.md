# Creation handoff — qiaomu-download 1.0.0

## Studied skills and sources

The design studied local `qiaomu-youtube-download`, `lwmxiaobei/yt-dlp-skill`, `MapleShaw/yt-dlp-downloader-skill`, `yutto-dev/yutto`, and the official yt-dlp README, installation wiki and FAQ. Candidate-specific details are recorded in `prior-art-research.md`.

## Retained, rejected, invented

- Retained: official stable updates, quality presets, audio/subtitles/info modes, advisory locks, progress streaming, browser Cookie support and ffprobe verification.
- Rejected: URL-only auto-download, Cookie-first access, unbounded playlists, raw custom format strings, DRM/access-control bypass and WeChat UI automation.
- Invented: generic HTTPS trust validation, public-first Cookie fallback, manager-aware upgrades, explicit WeChat routing and a cross-platform JSON result contract.

## Evidence claims

- **Design advantage:** a concise agent UX with conservative authorization, privacy and artifact checks.
- **Validated:** 11 unit tests, 12/12 trigger cases, governed package validation, official release check, three provider metadata probes and one ffprobe-verified X download.
- **Hypothesis:** sites beyond YouTube, Bilibili and X work when their current yt-dlp extractor and access conditions permit.

## Release status

The local canonical package and Codex discovery symlink are ready. Git initialization, GitHub PR, release and clean `npx skills add` proof remain gated by this machine's Xcode license acceptance and GitHub CLI authentication.
