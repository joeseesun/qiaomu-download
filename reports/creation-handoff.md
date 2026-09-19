# Creation handoff — qiaomu-download 1.2.0

## Studied skills and sources

The design studied local `qiaomu-youtube-download`, `lwmxiaobei/yt-dlp-skill`, `MapleShaw/yt-dlp-downloader-skill`, `yutto-dev/yutto`, the owned qiaomu-wx-video implementation, and the official yt-dlp README, installation wiki and FAQ. Candidate-specific details are recorded in `prior-art-research.md`.

## Retained, rejected, invented

- Retained: official stable updates, quality presets, audio/subtitles/info modes, advisory locks, progress streaming, browser Cookie support and ffprobe verification.
- Rejected: URL-only auto-download, Cookie-first access, unbounded playlists, raw custom format strings, DRM/access-control bypass and WeChat UI automation.
- Adapted from qiaomu-wx-video: embedded URL validation, fixed resolvers, local feed capture, signed URL preservation, decrypt, full-decode verification and locked backend installer.
- Invented for this integration: a standalone embedded dispatcher, explicit resolver-consent flag, structured `manual_action_required` / `wechat_setup_required` states, and one JSON contract across yt-dlp and WeChat outputs.

## Evidence claims

- **Design advantage:** a concise agent UX with conservative authorization, privacy and artifact checks.
- **Validated:** 25 unit tests, 22/22 trigger cases including URL-only object inference with explicit download intent, governed package validation, package validation, embedded-adapter doctor, no-UI/consent unit coverage, official release check, three provider metadata probes and one ffprobe-verified X download. Live WeChat media evidence is inherited from the specialist implementation and not rerun in this integration pass.
- **Hypothesis:** sites beyond YouTube, Bilibili and X work when their current yt-dlp extractor and access conditions permit.

## Release status

The local canonical package and Codex discovery symlink are ready. The integration is implemented on local feature branch `codex/integrate-wechat-video`. GitHub publication and a v1.2.0 clean-install proof remain pending because publication was not requested in this turn.
