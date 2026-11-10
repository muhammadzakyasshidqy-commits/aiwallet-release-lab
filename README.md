# AIWallet Release Lab

**Local-first quality control for short-form video, with explainable checks and exportable release evidence.**

A creator can make a beautiful video and still upload an accidental 16:9 export, a silent file, an over-loud mix, an unsupported codec or a long unintended freeze. Release Lab inspects the *technical* side of a video, explains its findings, and produces a portable QA report. It does **not** generate views, rate creativity, scrape social networks, or publish on behalf of an account.

**Status:** v0.4.0 alpha · Core available · Early-access interest form live · Hosted subscription and recurring checkout are not yet available.

## What runs today

- Local CLI + responsive browser-based workbench.
- Optional self-contained Python **zipapp** for CLI usage on systems with Python + FFmpeg; the browser dashboard still requires FastAPI and Uvicorn.
- **Batch export audit, CI release gate, revision comparisons**, and reports suitable for an editor/publisher handoff.
- Real FFprobe metadata: width, height, ratio, codec, FPS, duration, audio, interlacing.
- Bounded FFmpeg scans: integrated loudness and true peak, black frames, frozen sections and audio silence with timecodes.
- Detailed PASS / CHECK findings with caveats instead of an unexplained AI score.
- Custom JSON Studio Policy as Code: fail-closed thresholds, scan-coverage requirement, CI/batch integration, and explicit policy violations.
- Strict local `Host` validation to reduce DNS rebinding risk when using the localhost dashboard.
- Portable `audit.json`, standalone `audit.html` (with embedded still image) and SHA-256 fingerprint.
- Local SQLite history, file upload, report export, individual report deletion.
- No network request from the **audit core** to an AI vendor or social network. Only the separately labeled, voluntary managed-hosting interest form sends a name/email/plan to the AIWallet Supabase endpoint after consent. Original video is **deleted from work storage after analysis**; the still image and report are stored locally until deleted.
- Explicit scan limit: first **90 seconds** (full media metadata and SHA-256 are not truncated). Limits are documented and shown in result JSON.

### Run without installing Python packages (CLI only)

If you have Python 3.11+ and FFmpeg, use the portable `releaselab-0.4.0.pyz` artifact:

```bash
python releaselab-0.4.0.pyz doctor
python releaselab-0.4.0.pyz audit video.mp4 --output ./report
python releaselab-0.4.0.pyz batch ./exports --quick
```

The packaged browser dashboard still requires `pip install -e '.[web]'` (FastAPI, Uvicorn); zipapp is intentionally a dependency-free CLI only.

### Why this focus?

Editors and publishing systems already exist. Release Lab concentrates on an overlooked handoff: *is the export technically safe to release?* This keeps the free project useful without claiming to replace Premiere, CapCut, or full social schedulers.

## 60-second start

Requirements: Python 3.11+, FFmpeg **and** FFprobe installed. Linux, macOS and Windows are supported where FFmpeg can run; real hardware tests are documented separately.

```bash
python -m pip install -e '.[web]'
releaselab doctor
releaselab serve
```

Open **http://127.0.0.1:7860** on the same computer. Drag in a video and press **Jalankan QC**. Your source file stays local.

## Release workflows

```bash
# Scan one file as a CI gate (exit 3 when warnings should block release)
releaselab gate ./video.mp4 --quick --fail-on warn

# Scan up to 40 videos in a folder, generate combined report HTML/CSV/JSON
releaselab batch ./exports -o ./release-batch

# Compare revision exports for technical regressions
releaselab compare ./cut-v1.mp4 ./cut-v2.mp4 --quick -o ./comparison.json
```

See [CI and batch documentation](docs/CI_AND_BATCH.md) and the included `action.yml` for integrating the gate into a GitHub workflow. A technical gate is a configurable convention, not proof that Instagram/TikTok/YouTube accepted the video.

CLI without web dependencies:

```bash
python -m pip install -e .
releaselab audit clip.mp4 --output ./release-report
releaselab audit clip.mp4 --output ./quick-report --quick
```

### Adaptive QC and verifiable technical receipts (v0.4)

A strict studio policy can require a maximum black/freeze/silence segment shorter
than the built-in detector defaults (0.4 / 2.5 / 0.8 seconds). Earlier versions
could miss such events while still reporting a PASS. **v0.4 adapts the FFmpeg
minimum event duration to the configured policy** and records that sensitivity.
A pre-existing report analyzed with lower sensitivity is **blocked**, rather than
used as false evidence of a PASS. Lists of events capped for readability also
block strict policy decisions when the full event set was truncated.

```bash
# Explicit studio policy with adaptive detector settings; exit 3 when blocked.
releaselab gate clip.mp4 --policy policies/studio-vertical.json --output ./qc --fail-on none

# Re-run detector scans and compare the actual video with every technical field
# of a receipt. Exit 0 for repeatable evidence, 3 for a mismatch.
releaselab verify clip.mp4 ./qc/audit.json --policy policies/studio-vertical.json
```

`verify` is a **repeatability check, not a cryptographic signature**: it does not
prove a publisher's identity, copyright ownership, creative approval, or genuine
platform distribution. The report ruleset and software version must match.
Old receipts remain readable but cannot silently receive a current-version
verification verdict. The optional policy must also pass. Full checks are
bounded to the first 90 seconds; quick-only receipts are labeled metadata-only.
See [verification documentation](docs/RECEIPT_VERIFICATION.md).

### A release policy for CI

```bash
releaselab gate clip.mp4 --policy policies/studio-vertical.json --fail-on none
releaselab batch ./exports --policy policies/studio-vertical.json --output ./batch
```

This example policy is a **studio preference**, not a platform rule. It requires full audio/visual scanning and a documented codec/resolution/loudness window. A skipped scan or a missing measurement blocks the policy. See [Policy as Code](docs/POLICY_AS_CODE.md).

For Docker (host access restricted to loopback):

```bash
docker compose up --build
# http://127.0.0.1:7860
```

Do not expose this alpha server publicly: **there is no multi-user authentication or billing inside the local app**. See [SECURITY.md](SECURITY.md).

## What a report means

| Finding | Release Lab rule | Important limitation |
|---|---|---|
| Vertical frame | Aspect 0.54–0.58 | Other ratios may be intentional |
| Resolution | ≥720×1280 | Not an official platform specification |
| Video codec | Prefer H.264 | HEVC/AV1 may work on some platforms |
| Duration | 3–180 seconds for workflow | Not an official duration ceiling |
| Frame rate | Approximately 24–60 fps | Choose based on original footage |
| Audio | Detect presence, approximate LUFS and dBTP | Mastering is still a listening task |
| Black/freeze/silence | Detect segments and timecodes in first 90 seconds | Could be deliberate transitions, holds or pauses |
| Fingerprint | SHA-256 of entire file | Identifies bytes, not copyright ownership |

A CHECK result is not necessarily a bad video. This is **technical QA**, not a content moderation verdict or a promise of distribution performance.

## Business model: open source + optional managed subscription

The core is **Apache-2.0** and free to self-host, modify or use commercially. The planned paid offering would charge for hosted infrastructure, cross-device history, team review and managed processing capacity, not the right to inspect code. This is how an honestly open-source product can support recurring revenue.

| Mode | Status | Intended price | Included now? |
|---|---|---:|---|
| Community / Self-hosted | Working alpha | Rp0 | Yes: CLI, dashboard, local reports |
| Creator Cloud | Hypothesis / early-access interest | Rp149,000 per month | Not yet: hosted processing, backups, multi-device history |
| Studio Workspace | Hypothesis / early-access interest | Rp499,000 per month | Not yet: seats, approvals, review history |

*Prices above are proposals for customer discovery, not an active subscription checkout. The **early-access interest form is active**, accepts voluntarily submitted name/email/plan with consent, and stores them in a Supabase table protected by RLS. This does not activate a paid account.* There is **no automated recurring charge**, **no auto-renewal**, and **no paid gating** in the release. Indonesian recurring billing would require merchant-specific enablement, tokenization, webhook signature verification, refunds and cancellation handling. See `docs/BUSINESS.md`.

## REST API (localhost only)

- `GET /api/health` — non-sensitive readiness and version.
- `POST /api/audits` — multipart video file; limited to 256 MiB and bounded processing. Returns report + poster link.
- `GET /api/reports` — list local report summaries.
- `GET /api/reports/{id}` — exact JSON report.
- `GET /api/reports/{id}/poster` — JPEG frame.
- `GET /api/reports/{id}/html` — portable HTML report download.
- `DELETE /api/reports/{id}` — permanently delete local report and poster.

No social-network credentials are needed. There is no auto-publish action.

## Tests and reproducibility

```bash
python -m pip install -e '.[web,dev]'
python -m pytest -q
python -m compileall -q src
```

Tests synthesize MP4 files with FFmpeg and verify metadata inspection, real audio/silence/black scans, HTML escaping, file limits, cleanup, report persistence, and API endpoints. CI tests Python 3.11–3.13 on Linux; platform compatibility beyond that must be verified before release claims.

## Development and community

- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Privacy](PRIVACY.md) · [Architecture](docs/ARCHITECTURE.md)
- [Commercialization plan](docs/BUSINESS.md) · [Policy as Code](docs/POLICY_AS_CODE.md) · [Distribution](docs/DISTRIBUTION.md) · [Billing readiness](docs/BILLING_READINESS.md) · [Roadmap](docs/ROADMAP.md) · [Subscription design](docs/SUBSCRIPTION_CONTRACT.md) · [Release checklist](docs/RELEASE.md)
- The standalone website in `site/` includes a synthetic MP4 test fixture, an authentic FFmpeg report, and an independently auditable BIMO technical report, but not the user-owned BIMO original or client footage. A local agent instruction skill is included in `.agents/skills/aiwallet-release-lab/`.
- The project intentionally avoids mass-commenting, platform login circumvention and automated posting without explicit per-account authorization.
- Current public marketing page and release downloads: https://aiwallet-studio-qz.higgsfield.app/ . **GitHub publication is not yet verified**, so do not mistake a ZIP release for a canonical GitHub repository.

**Maintainer:** AIWallet Studio · Tangerang, Indonesia. Project outreach: [email](mailto:muhammadzakyasshidqy@gmail.com).

## Open-source launch

The source ZIP is a working release artifact, **not a verified GitHub publication**. See [GitHub launch instructions](docs/GITHUB_LAUNCH.md) for verified publication steps and the category growth scorecard.
