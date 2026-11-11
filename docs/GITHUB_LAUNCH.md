# GitHub publication — no ChatGPT Work required

Target: `https://github.com/muhammadzakyasshidqy-commits/aiwallet-release-lab` (the repo does not yet exist unless verified live). The previous GitHub App connector has read but not Contents-write scope (403). Opening a social-account Chrome profile through Social Control cannot navigate GitHub because the operator restricts URLs to the registered social platform. Do not bypass this boundary or copy cookies/tokens/OTP.

**One-click owner handoff:** From the published `AIWallet_GitHub_OneClick_v0.9.0.zip` package, extract to a user-chosen folder on Windows. Run `scripts/LAUNCH-GITHUB.cmd` and complete GitHub's official browser/device login under `muhammadzakyasshidqy-commits`. The script downloads a pinned SHA-256 GitHub CLI (if missing), verifies the packaged complete Git history, creates *only* the dedicated public repository, pushes `main` and all tags non-force, creates the GitHub release with source/wheel/zipapp/SHA256SUMS, queries public commit and waits for CI. It writes only nonsecret `PUBLISH_RESULT.json`. It does **not** upload your videos or log credentials.

No payment, Railway, ChatGPT Work, subscription or access token pasted into chat is required. The one-time browser login is the unavoidable user interaction for a private GitHub account. The script cannot run as GitHub until you authorize it. If Git or gh auth is missing it stops or bootstraps the official free GitHub CLI. A release is not accepted until the public URL and Actions status have been verified.

After publication, view CI on `https://github.com/muhammadzakyasshidqy-commits/aiwallet-release-lab/actions` and create a public issue only with real repro steps. No artificial stars, fork farms, spam, or fabricated ranking.
