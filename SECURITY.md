# Security policy

Release Lab 0.6 is a **local, single-user application**. Do not expose the FastAPI service directly to the public Internet. It has no user authentication, organization isolation, billing, or permissions system yet.

- The media inspection core never contacts Instagram, TikTok, YouTube, or any AI provider. The optional early-access interest form transmits name/email/selected plan to the maintainer's Supabase only after explicit consent; this is not telemetry or billing.
- Uploaded originals are inspected by FFmpeg and deleted after analysis. Poster images and metadata reports are retained until deleted.
- File inputs are capped at 256 MiB; processing has bounded FFmpeg command timeouts. FFmpeg/FFprobe use argument lists (no shell string interpolation).
- The Docker port is bound to `127.0.0.1` on the host. Only add a reverse proxy after implementing authentication, CSRF protections, rate limiting, quotas, and secure uploads.
- Avoid uploading unknown or untrusted files to any version of FFmpeg that is missing security updates. Keep FFmpeg patched.
- Reports contain SHA-256 fingerprints and filenames; keep report folders private if they reveal client data.

Watch mode processes only changed, stable, regular video files; it saves current status atomically and skips symlinks. **Do not share report directories** (report names and media SHA-256 are sensitive client metadata). There is no built-in report retention policy; review old reports manually.

Please report suspected vulnerabilities **privately** to `muhammadzakyasshidqy@gmail.com` with `SECURITY: AIWallet Release Lab` in the subject. Do not publish exploit details before a fix.

## Human review trust boundary (v0.7)

Local editorial approval stores an unverified reviewer name and answers in SQLite. Neither the dashboard nor CLI authenticates the reviewer or signs the approval; do not use it for legal, regulatory or external provenance. The gate checks exact video SHA-256 and ruleset only. The local app must remain bound to loopback and must not be published on the internet.
