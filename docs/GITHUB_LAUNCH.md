# GitHub launch and actual ranking criteria

**Status:** Source release ready. GitHub repository publication not verified. A connected GitHub tool returned `403 Resource not accessible by integration` for content writes on the account's existing website repository. This is a permission issue, **not** a publish success. A public repository path must be verified before announcing availability on GitHub.

## Publish a true open-source repository

1. Create a **new public repository** named `aiwallet-release-lab` under the verified account. Keep the existing AIWallet website repo separate. Do not copy the proprietary customer data, social-session cookies, or any tokens.
2. Extract this ZIP into the new repository's root (not one nested directory).
3. Run `python -m pip install -e '.[web,dev]' && pytest -q && releaselab doctor` with FFmpeg installed.
4. Set repository About/Topics based on what genuinely ships (`ffmpeg`, `video-qc`, `reels`, `shorts`, `local-first`, `open-source`); attach a screenshot of the real demo and the sample report.
5. Publish a semver `v0.6.0` release containing the source archive and a SHA-256 checksum. Do not represent a ZIP upload as GitHub source control.
6. Enable Issues, Discussions, Security Policy, Dependabot, and Actions CI. Verify CI runs on multiple supported Python versions before advertising it as green.
7. Add the repository URL and the real release asset URL to the website **after** they exist.

## How to earn an actual category lead

No system can guarantee a #1 position, followers, stars, or paid buyers. Strong practical adoption would require distribution and retention, not just an impressive landing page.

- **Weeks 1–2:** obtain verified on-device results from 10 distinct creators (with consent); fix setup problems.
- **Weeks 3–4:** ship repeatable batch QC and editor/CI integration examples; measure how many users run the tool twice.
- **Months 2–3:** target 30 meaningful issue/discussion replies and a few external pull requests. Measure weekly repeat teams, not raw impressions.
- **Later:** launch managed hosting only after the subscription security and cost gates in `docs/SUBSCRIPTION_CONTRACT.md` pass.

Do not buy stars, mass-comment, imitate contributors, promise viral performance, or fabricate testimonials.

## Verified v0.6 release assets

The standalone receipt explorer offers a zero-signup reason to try the tool before installing Python or FFmpeg. Publish a screenshot of an actual synthetic receipt with timecoded events. The CSV exporter is generic: do not claim Premiere or Resolve native imports without verifying a documented target format.
