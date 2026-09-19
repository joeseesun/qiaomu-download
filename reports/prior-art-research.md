# Prior-art research

Research date: 2026-09-19. Automated discovery produced 72 candidate families in `prior-art-candidates.json`; the following sources were inspected directly.

## Sources studied

1. **qiaomu-youtube-download 1.2.0 (local)** — mature Qiaomu wrapper with official-release checks, lock inheritance, progress streaming, browser-cookie fallback, output verification and safe fragment cleanup.
2. **lwmxiaobei/yt-dlp-skill** — broad trigger wording, quality presets, audio formats, URL extraction and multi-platform examples. Its workflow often asks again even when user intent is already clear, and it lacks a post-download media verification contract.
3. **MapleShaw/yt-dlp-downloader-skill** — concise cross-platform UX, YouTube/Bilibili/X positioning, subtitles and cookie troubleshooting. Its public interface calls raw shell commands and treats Cookie use as a common default rather than a privacy-sensitive fallback.
4. **yutto-dev/yutto** — Bilibili specialist showing the value of platform-specific depth, including collections, codecs and login-sensitive quality. It is retained as an escalation reference rather than a second runtime dependency.
5. **qiaomu-wx-video 0.1.2-local (local working tree)** — owned specialist implementation with WeChat URL validation, fixed resolver fallback, local feed capture, signed URL preservation, decrypt, full-decode verification, pinned backend installation and proxy rollback rules.
6. **yt-dlp official README, installation wiki and FAQ** — authoritative basis for extractor breadth, browser Cookie support, package-manager update routes and the fact that site support must be tested dynamically.

## Candidate-specific lessons retained

- From qiaomu-youtube-download: official stable update checks, advisory locks, bounded subprocesses, `--no-overwrites`, deterministic filenames and ffprobe verification.
- From lwmxiaobei: platform-rich trigger language and simple video/audio/info modes.
- From MapleShaw: Chinese-first examples for YouTube, Bilibili and X, plus actionable 403 guidance.
- From yutto: describe Bilibili entitlement and quality limits honestly; keep a specialist escalation path.
- From qiaomu-wx-video: retain local-first capture, explicit resolver consent, complete signed URLs, real codec verification, one manual user handoff and strict no-WeChat-UI automation.
- From official yt-dlp: make extractor capability dynamic, support `--cookies-from-browser`, and respect installation provenance when updating.

## Rejected

- Automatic download whenever a URL merely appears in conversation; explicit save/download intent is required.
- Cookie-first execution; public extraction is attempted first.
- Unbounded playlists or batches; v1 handles one URL per invocation.
- Custom yt-dlp format expressions from user text; fixed quality presets reduce command-injection and invalid-format risk.
- DRM, paywall or access-control bypass.
- WeChat UI automation; the specialist implementation is embedded behind the universal entrypoint instead of requiring a second installed Skill.
- Depending on both yt-dlp and yutto in the default path; this would double update and authentication surface.

## Invented

- A generic HTTPS validator that rejects credentials, custom ports, localhost and literal private addresses.
- A universal dispatcher that keeps WeChat outside yt-dlp while bundling the governed specialist adapter in the same package.
- Public-first Cookie fallback with visible provenance in the JSON result.
- A manager-aware updater spanning Homebrew, pipx, uv and official self-update.
- A single JSON contract shared by WeChat Channels, YouTube, Bilibili, X and generic extractors.

## Claim status

- **Design advantage:** one command surface, public-first privacy policy, verified outputs, conservative single-link scope and embedded WeChat isolation and explicit resolver consent.
- **Validated:** local unit tests, trigger fixtures, structure checks and provider probes recorded in the runtime report after execution.
- **Hypothesis:** generic support outside the tested platforms follows current yt-dlp extractor coverage and can change when providers change.

## References

- https://github.com/yt-dlp/yt-dlp/blob/master/README.md
- https://github.com/yt-dlp/yt-dlp/wiki/Installation
- https://github.com/yt-dlp/yt-dlp/wiki/FAQ
- https://github.com/lwmxiaobei/yt-dlp-skill
- https://github.com/MapleShaw/yt-dlp-downloader-skill
- https://github.com/yutto-dev/yutto
