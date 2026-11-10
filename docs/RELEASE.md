# Public release checklist

## Core safety and quality

- [x] License file and open source promise agree (Apache-2.0).
- [x] CLI, web endpoints and media inspections run against synthetic fixtures.
- [x] No fake customer/testimonial/revenue or star claims.
- [x] No network calls in the media analysis core.
- [x] Files bounded and removed after processing; report exports escape user-supplied names.
- [ ] Validate Docker image build on Linux host (not verified in this environment).
- [ ] Verify native Windows/macOS installation and E2E GUI tests (browser automation blocked by environment policy during this run).

## GitHub publication

- [x] All repository files, tests, documentation and CI configuration prepared.
- [ ] GitHub code push accepted and public repository URL verified.
- [ ] README instructions tested on fresh independent machine.
- [ ] GitHub Actions green and release tag/v0.5.0 published.
- [ ] README screenshot made from actual loaded browser UI (browser access unavailable in this environment).

## SaaS / subscription

- [x] Opt-in early-access interest endpoint deployed and verified, isolated by RLS and no direct public DB privileges.
- [ ] Verified multi-tenant SaaS environment and data protection.
- [ ] Payment provider recurring feature enabled and production webhook tested.
- [ ] Client billing consent, cancellation, refunds, entitlement states.
- [ ] At least three paid pilot orders or explicit demand confirmations.

These unchecked gates prevent an honest claim of public release or live paid subscription.


## v0.4 release gate

- [x] Policy minimum detector precision recorded in technical receipts.
- [x] Strict threshold below old detector precision no longer yields a false PASS.
- [x] Reproducibility CLI returns exit 3 for mismatches/tampering.
- [x] 54 test cases passed locally with FFmpeg 7.1.5 on Python 3.13.
- [ ] macOS/Windows CI and GitHub release remain unverified.

## v0.5 release gate

- [x] Generic CSV and JSON timecoded event markers tested against real FFmpeg receipts.
- [x] CSV formula injection protection and bounded invalid-input rejection.
- [x] Local dashboard marker CSV download.
- [x] Report Explorer DOM tested at 1440×900 and 390×844 using local HTML/CSS/JS; marker CSV exported in browser, malicious receipt names did not generate markup, no JavaScript errors or document overflow.
- [ ] GitHub source and Actions CI must be verified separately; do not claim green CI.
- [ ] Video quality, copyright, and social-platform posting are not certified by technical QC.
