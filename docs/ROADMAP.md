# Roadmap

## v0.1 — shipped

- [x] Single-video QC with explainable checks.
- [x] Local browser UI, CLI and portable reports.
- [x] File lifecycle, length/size constraints, SQLite, report deletion.
- [x] 20 automated tests and basic CI.

## v0.2 — proposed

- [ ] Folder/batch scanner with cancellation and status.
- [ ] Optional configurable output profiles and safely documented rulesets.
- [ ] User-adjustable safe-zone guides and visual text-boundary checking.
- [ ] Download a `.zip` release manifest with poster and QC report.
- [ ] Reproducible FFmpeg test fixtures for Windows and macOS.

## v0.3 — proposed

- [ ] Review comments and manual signoff fields.
- [ ] Duplicates/version comparisons using checksums and metadata.
- [ ] Optional editor extension export connectors, no credentials or scraping.
- [ ] Accessibility checks (captions presence if supplied, contrast from stills).

## Managed hosting — only after validation

- [ ] Tenant auth, privacy/RLS, queue, file storage, retention and deletion.
- [ ] Usage metering, invoice workflow and verified recurring payments.
- [ ] Paid team workspaces and approval audit trails.
- [ ] Official platform integrations if platform APIs and partner approvals allow.

All items unchecked are *not yet implemented*.

## v0.3 delivered

- Reproducible studio JSON policy in CLI, batch and GitHub Action (not officially platform-certified).
- Black/freeze/silence timecodes; safer scan coverage semantics.
- Strict localhost Host headers, 45 regression tests.

## Still unshipped

- GitHub repository publication and independently verified Actions runs.
- Multi-tenant hosted SaaS, recurring billing, cancellation lifecycle and paid entitlements.
- Measured weekly active users, real customers and recurring revenue.


## v0.4 delivered — 10 November 2026

- [x] Adaptive detector sensitivity for studio policy thresholds.
- [x] Fail closed on missing precision or truncated timeline evidence.
- [x] `releaselab verify` checks source SHA-256, ruleset/version, metadata and all technical measurements by re-running FFmpeg.
- [x] 54 automated tests on Python 3.13/Linux, including real FFmpeg short-event fixtures.
- [ ] GitHub source publishing and Actions verification (connector write access blocked).
- [ ] Paid hosted tier, recurring billing, entitlement management (not shipped or charged).
- [ ] Verified user traction and independent adoption.

## v0.5 delivered
- Local-first timecoded marker CSV/JSON and browser-only receipt inspection; no cloud video processing.
- Next external validation: real editor workflows, Windows/macOS FFmpeg parity, signed reproducible artifacts, authorized GitHub source publication, and paid tenant isolation before subscription activation.

## Next priority after v0.5

- Win a useful wedge: map editor-marked quality issues back to timestamps and reduce false alerts with independent real-world video examples.
- Validate timecode import contracts separately for Premiere, Resolve and other NLEs before advertising native integration.
- Improve long-video scan coverage and cost limits without false pass.
- Real GitHub canonical repository and cross-platform CI, then substantive contributions and adoption.
- Hosted multi-tenant managed QC with auth, quotas and verified billing only after cost and privacy gates.

## v0.6 delivered — render watch

- [x] `releaselab watch ./exports -o ./qc-live`: detect stable exports locally and inspect only changed videos.
- [x] Fail closed when video changes while FFmpeg is running, or source signature changes before new QC.
- [x] Atomic local JSON/HTML/CSV results, restart-safe resumability, one-shot mode for scheduled tasks.
- [x] Symlink and input/output safety; bounded file count and CLI intervals.
- [ ] Real external beta testers, Windows/macOS validation, GitHub repo/Actions, paying SaaS.
