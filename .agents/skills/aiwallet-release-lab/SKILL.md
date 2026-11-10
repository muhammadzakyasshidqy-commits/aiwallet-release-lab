---
name: aiwallet-release-lab
description: Audit local short-form video exports with FFprobe and FFmpeg and report exact technical evidence before a human authorizes publication.
---

# AIWallet Release Lab agent skill

Use this when asked to inspect an owned/local MP4, MOV, M4V, WebM or MKV export before Reels, YouTube Shorts or TikTok upload.

1. Check user permission to read the video. Never export their original footage, thumbnails, account sessions or credentials to an external service.
2. Run `releaselab doctor` to confirm FFmpeg and FFprobe are installed.
3. Run `releaselab audit <local-video-path> --output <output-dir>` using a safely quoted local path. Do not concatenate user-controlled filenames into a shell command.
4. Read `audit.json`: inspect `metadata`, `checks`, `measurements.analysis_seconds` and `summary`. List only actual findings, distinguish `warn` from failure.
5. Do not claim official social-platform compliance or artistic quality. Black frames or still frames might be creative decisions.
6. Save the HTML/JSON report with original file hash so its evidence is reproducible. Do not edit or replace the source video unless the user separately requested an edit.
7. **Never publish, schedule, comment or use social account credentials** merely because a report passes. Publication requires separate explicit permission, exact account confirmation and an approved official route.

For quick metadata-only checks use `--quick`. The full scan is limited to the first 90 seconds while SHA-256 and file metadata cover the entire file.
