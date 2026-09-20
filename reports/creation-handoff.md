# Creation handoff — qiaomu-download 1.3.0

## Studied skills and sources

The design studied local `qiaomu-youtube-download`, `lwmxiaobei/yt-dlp-skill`, `MapleShaw/yt-dlp-downloader-skill`, `yutto-dev/yutto`, the owned qiaomu-wx-video implementation, spotDL 4.5.2, SpotiFlyer, and the official yt-dlp documentation. Candidate-specific details are recorded in `prior-art-research.md`.

## Retained, rejected, invented

- Retained: official stable updates, quality presets, audio/subtitles/info modes, advisory locks, progress streaming, browser Cookie support and ffprobe verification.
- Rejected: URL-only auto-download, Cookie-first access, unbounded playlists, raw custom format strings, DRM/access-control bypass and WeChat UI automation.
- Adapted from qiaomu-wx-video: embedded URL validation, fixed resolvers, local feed capture, signed URL preservation, decrypt, full-decode verification and locked backend installer.
- Invented for this integration: a standalone embedded dispatcher, explicit resolver-consent flag, structured `manual_action_required` / `wechat_setup_required` states, and one JSON contract across yt-dlp and WeChat outputs.
- Adapted from spotDL: Spotify metadata/audio separation and multi-signal matching. The implementation uses public Spotify page metadata because spotDL's metadata client stalled in the local live probe.
- Invented for Spotify: dependency-free public metadata extraction, ten-candidate confidence scoring, variant penalties, source disclosure and automatic single-track limits.

## Evidence claims

- **Design advantage:** a concise agent UX with conservative authorization, privacy and artifact checks.
- **Validated:** 30 unit tests plus trigger/package gates; a real Spotify track resolved to the artist-channel official video at 94.23 confidence, downloaded as a tagged 128 kbps MP3, and passed ffprobe verification.
- **Hypothesis:** sites beyond YouTube, Bilibili and X work when their current yt-dlp extractor and access conditions permit.

## Release status

The integration is implemented on feature branch `codex/add-spotify-adapter`. GitHub publication and a v1.3.0 clean-install proof remain pending until the release flow completes.
