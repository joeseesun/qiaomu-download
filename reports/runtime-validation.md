# Runtime validation

Date: 2026-09-19. Runtime: macOS arm64, Python 3.14, yt-dlp 2026.08.19. All probes used `--cookies-from-browser none`.

| Case | Result | Evidence |
|---|---|---|
| Official update check | Pass | Installed 2026.08.19 equals official latest stable 2026.08.19; manager detected as pip |
| X metadata | Pass | Twitter extractor resolved status `2100943729502953564` to media `2100943709814857729`, 544×960, 2.001 s |
| X download | Pass | MP4, 236,430 bytes, H.264 + AAC, 544×960, 2.067 s; ffprobe verified |
| YouTube metadata | Pass | YouTube extractor resolved OpenAI video `0Uu_VJeVVfo`, 1920×1080, 4,650 s |
| Bilibili metadata | Pass | BiliBili extractor resolved `BV1xx411c7mD`, 512×384, 2,055.637 s |
| Cookie boundary | Pass | No browser Cookie used in any provider probe |

The first X download attempt exposed a vertical-video quality-selector gap. The fixed selector treats 480p/720p/1080p as preferred caps and falls back to the best available format; the second run merged streams and passed ffprobe.
