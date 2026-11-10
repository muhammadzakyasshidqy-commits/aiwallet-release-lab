# Dedicated GitHub publication checklist (not yet complete)

**Candidate repository:** `muhammadzakyasshidqy-commits/aiwallet-release-lab` (not claimed to exist). **Public site:** https://aiwallet-studio-qz.higgsfield.app/

The installed GitHub connector reads the owner's existing repository but previously returned HTTP 403 `Resource not accessible by integration` on Content writes. An account login alone might not grant App **Contents: Read and write** permission. This permission must be granted explicitly to the connected GitHub App/repository. Do not share personal access tokens or passwords through chat.

## Publish safely

1. Authorize GitHub Contents-write for the new repository and create it under the owner's GitHub account, or connect a Browser session with an authenticated GitHub tab. Keep existing unrelated repos unchanged.
2. Import `AIWallet_ReleaseLab_v0.8.0.git.bundle` (full Git history and tag) into an empty repository, or unzip the source ZIP into its root. **Never** publish test secrets, session cookies or user videos.
3. Run `python -m pip install -e '.[web,dev]'` and `pytest -q`; check local FFmpeg and FFprobe versions.
4. Verify Actions CI **on the canonical public repo**, across all supported Python versions. The local test result is not CI.
5. Publish GitHub Release `v0.8.0` with source, Python wheel, portable CLI, SHA-256 file. Check each public download.
6. Only then add GitHub URLs to the public website, announce in relevant communities with real demonstration and issues enabled.

Release Lab is free Apache-2.0. **No recurring subscriptions or paid tiers.** Optional one-time services are outside the repository's free software license.

Category ranking cannot be guaranteed and must be sourced from independent GitHub results, date, and exact scope. Do not automate fake stars, spam or fabricated testimonials.
