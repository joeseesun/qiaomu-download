# Trust report

## Boundaries

- Input: one user-supplied HTTPS URL and optional output preferences.
- Network: target website, official `api.github.com/repos/yt-dlp/yt-dlp/releases/latest`, the pinned backend release, and fixed WeChat resolvers only after explicit consent.
- Credentials: optional local browser Cookie access only after anonymous extraction fails.
- Filesystem: selected output directory, temporary advisory lock, newly created format fragments.

## Controls

- URL validation rejects credentials, custom ports, localhost and literal non-public IPs.
- Playlists and overwrites are disabled.
- Download success requires ffprobe validation.
- Duplicate downloads to the same output directory are locked.
- Signals and timeouts stop child processes.
- WeChat Channels use the embedded adapter; WeChat UI automation is prohibited.
- Sending a WeChat share URL to a fixed resolver requires explicit consent; Cookies, login state and captures never leave the machine.
- The optional local backend is pinned by release and SHA-256; certificate trust and proxy mutation remain separately authorized operations.
- No embedded secrets or telemetry.

## Known limits

- yt-dlp extractors track third-party sites and can break when those sites change.
- A public hostname can theoretically change DNS after validation; yt-dlp owns subsequent network resolution.
- Availability, regional rules, account entitlements and platform terms remain external constraints.
