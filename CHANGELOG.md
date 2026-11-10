## 0.4.0 — 2026-11-10

- Policy-adaptive black/freeze/silence detector thresholds, recorded in each receipt.
- Fail-closed policy when events are below detector precision or an event list was truncated.
- `releaselab verify` re-scans media to validate evidence; it is not a cryptographic signature.
- Receipt HTML shows exact scan coverage and filter sensitivity.
- Adversarial real-FFmpeg regression tests for sub-default black, freeze and silence events.
- No automatic charges, remote video uploads, or fabricated customer claims.

# Changelog

## 0.3.0 — 2026-11-10
- Configurable fail-closed studio policies using bounded JSON with explicit scan-coverage validation.
- Audio silence timecode detection; additional evidence in portable HTML receipt.
- Explicit warning when using metadata-only quick mode for release decisions.
- Missing checks treated as regressions during export comparison.
- Local dashboard restricted to loopback Host headers (DNS rebinding defense).
- Studio policy CLI/Batch/GitHub Action support; additional adversarial tests.
- Added documentation for GitHub distribution and safe recurring billing launch.

# Changelog

## v0.2.0 — export gates and team handoff

- Local batch audit for a bounded set of videos, exporting combined HTML/JSON/CSV and individual receipts.
- CI-ready `gate` command and composite GitHub Action; exit status 3 for blocked releases.
- `compare` command for regression detection between video export revisions.
- CSV formula-injection protection, HTML escaping and symlink rejection in batch operations.
- Explicit warning when a video exceeds the first 90 seconds of technical scans.
- Added reproducible tests for adversarial file names, invalid files, batch limits, gate logic and comparisons.
- Subscription remains waitlist-only; no recurring payments, paid entitlements or falsely claimed ranking.

# Changelog

## 0.1.0 — 2026-11-10

Initial local-first release: FFprobe technical metadata, FFmpeg 90-second audio/black/freeze scan, SHA-256 report identity, PDF-free portable HTML and JSON, local web UI, SQLite report history, CLI, Docker configuration, automated tests, CI, and licensing documentation. No hosted subscription or social autopublishing.
