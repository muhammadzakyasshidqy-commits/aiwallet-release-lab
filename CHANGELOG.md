## 0.9.0 — 2026-11-11

- Fixed CLI/software `__version__` drift relative to package version.
- Clarified commercial distinction: forever-free Apache-2.0 self-hosted core and optional *customer* managed hosting (interest only, not yet billable).
- Restored optional explicit-consent interest form to the **marketing site only**; local QC dashboard remains without cloud signup or tracking.
- Added pinned-checksum Windows one-click GitHub publishing flow: owner logs in on GitHub's official website; repo/tag/assets/CI verified without force-push or handling credentials in chat.
- No paid cloud operation or subscription was purchased by the product owner.

# Changelog

## 0.8.0 — 2026-11-11

- Removed the proposed recurring Creator Cloud and Studio Workspace paid plans from the public website and local dashboard.
- Free Apache-2.0 forever: no paid seats, automatic billing, telemetry or waitlist signup.
- Optional one-time professional installation/integration assistance is independent of the free software.
- Tightened local dashboard Content-Security-Policy to disallow the former remote waitlist endpoint.
- Added standalone GitHub source publication guidance and tests protecting the no-subscription policy.
- Retained v0.7 technical QC, local Render Watch and SHA-bound editorial review unchanged.
- 101 local automated tests on Python 3.13/Linux and FFmpeg 7.1.5.
- GitHub repository publication and independent multi-OS CI remain unverified.

## 0.7.0 — 2026-11-11

- Added explicit human editorial review separate from automated technical QC.
- Five manually scored criteria, revision notes, source SHA-256 binding and local review history.
- Optional CLI `--editorial-review` policy requiring a matching approved human review, fail-closed on stale/missing JSON.
- Local dashboard can save and export revisions; no reviewer authentication or cryptographic signature implied.
- Added adversarial gate and API tests; corrected stale local UI release label.
- The open-source core remains free; managed subscriptions and GitHub-native CI are not claimed live.

## 0.6.0 — 2026-11-10

- Local-only `releaselab watch` for stable new render exports and in-place revisions.
- Old green verdict is invalidated immediately upon source signature change.
- Persistent, resumable, atomic HTML/JSON/CSV queue receipts, no source media copy.
- Safe one-shot mode with CI exit codes, symlink and output-path protections, bounded scans and advisory single-writer locking.
- No busy writes while idle, corrupted state reference validation, and portable builder script.
- Real separate-process integration test for new and replaced renders.
- No hosted auto-processing, recurring payment or official social publishing in this version.

## 0.5.0 — 2026-11-10

- Generic CSV/JSON timecoded black/freeze/silence markers from existing audit receipts without re-encoding.
- `releaselab markers audit.json --output markers.csv` with bounded receipt parsing, timestamp validation and spreadsheet formula-escape.
- Local FastAPI endpoint to download marker CSV from a saved audit, and dashboard timeline of measured defects.
- Standalone Report Explorer: import an audit.json entirely in the browser, explore intervals and export CSV (no video/receipt upload).
- No false claims of NLE-specific compatibility, drop-frame timecode, full-scan coverage, cloud subscriptions or GitHub status.

## 0.4.0 — 2026-11-10

- Policy-adaptive black/freeze/silence detector thresholds, recorded in each receipt.
- Fail-closed policy when events are below detector precision or an event list was truncated.
- `releaselab verify` re-scans media to validate evidence; it is not a cryptographic signature.
- Receipt HTML shows exact scan coverage and filter sensitivity.
- Adversarial real-FFmpeg regression tests for sub-default black, freeze and silence events.
- No automatic charges, remote video uploads, or fabricated customer claims.


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
