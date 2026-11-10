# Launch kit for a legitimate open-source release

**Do not announce a GitHub release until the repository upload is confirmed.** The existing AIWallet website repository is not equivalent to this product's source code. Do not claim stars, contributors, paid subscribers or public hosting without evidence.

## Repository identity (suggested)

- Name: `aiwallet-release-lab`
- Description: `Local-first technical QC for Reels & Shorts: FFmpeg checks, loudness, frozen/black frames, portable HTML/JSON reports. Apache-2.0.`
- Topics: `open-source`, `ffmpeg`, `video-quality-control`, `short-form-video`, `self-hosted`, `reels`, `shorts`, `creator-tools`, `local-first`, `python`
- License: Apache-2.0 (already present)
- Suggested initial tag: `v0.3.0`, **only after** the public repository actually contains this project and CI is green.

## Show, don't assert

For the first release post, screen-record a **real** 30-second workflow: open localhost → drag an original MP4 → run QC → show two technical findings → download the report. Include the actual FFprobe output and explain that the tool is not an AI virality predictor.

Verified initial sample: owner-provided `BIMO_Story_Cut_17s_AIWallet.mp4` (not redistributed in the repo), 1080×1920 H.264/AAC at 24fps, 17.4 s, measured -15.5 LUFS integrated and -1.3 dBFS true peak, no black/freeze events on the scan. 11 of 11 technical checks passed. It is a **technical** demonstration, not proof of artistic quality.

## Early-adopter channels

1. GitHub release notes and README GIF/screenshot from actual app UI.
2. Dev.to/Hacker News `Show HN` with working source, example report, honest limitations and install notes.
3. Relevant self-hosting and editing communities only where posts are allowed and add technical value; answer questions, don't mass post or mass comment.
4. Short developer demos on the creator's own channels showing real checks and limitations, not fabricated testimonials.
5. Ask actual users which release problems repeat weekly; rank requests by observed frequency and willingness to pay.

## Monthly metrics that matter

- **Activation:** number of unique opt-in respondents who finish their first report.
- **Reliability:** success/failure rate on a bounded set of open-license media fixtures.
- **Retention:** repeat users after 7 days (only with explicit analytics consent; the self-hosted core has no tracking).
- **Contribution:** external PRs merged, issues resolved, test cases added.
- **Commerce:** verified paid customers and net revenue, never waitlist signups counted as purchases.
- **Code health:** reproducible install time, CI stability, security reports and docs quality.

GitHub Trending is driven by actual community activity; no developer can guarantee a #1 ranking or honestly make it happen by submitting a repository alone.
