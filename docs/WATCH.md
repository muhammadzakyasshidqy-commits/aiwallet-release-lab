# Watch mode: automatic local QC for exported video

`releaselab watch` runs on your own machine. No cloud video upload, social account tokens, or proprietary background services are involved. Python 3.11+ and current FFmpeg/FFprobe must be installed.

## Start

```bash
mkdir exports
releaselab watch ./exports --output ./qc-watch --stable-seconds 3 --poll-interval 2
```

Drop a newly rendered `.mp4`, `.mov`, `.m4v`, `.webm` or `.mkv` into `exports`. The source file's size and filesystem timestamps must remain unchanged for at least three seconds before Release Lab audits it. If you overwrite the file, its earlier PASS/FAIL verdict is invalidated immediately and rechecked once stable. A file changed **during** FFmpeg analysis does not receive a completed verdict.

The output folder must be **outside** the watched folder. This prevents the tool from recursively auditing its own artifacts. The command prints structured JSON lines when the first scan begins and when new results finish. Stop with Ctrl+C.

Open `qc-watch/index.html` for a portable current queue: `state.json` (persisted signatures, checksums, receipts), `summary.csv` and `reports/<video-id>/audit.json` + `audit.html`. Source media stays in `exports`. Reports may include original filenames and thumbnails; protect local directories accordingly.

## Scheduled one-shot mode

```bash
releaselab watch ./exports --output ./qc-watch --once --policy ./policies/studio-vertical.json
```

`--once` has no stability delay. Use it only when your renderer has finished writing files, ideally via a post-render hook or an atomic rename into the watched directory. Exit statuses: `0` = nonempty set, all current results accepted by the chosen gate; `3` = one or more current results blocked or source folder empty; `2` = invalid command/file, environment or policy error. All scan results are heuristic technical QC, not legal/platform certification.

`--quick` skips visual and audio segment scans. Use a strict policy for important releases; otherwise quick results may accept videos without full AV inspection. Default FFmpeg scan covers the first 90 seconds and reports limited scope for longer videos.

## Safety and limits

- No media copy or remote upload. No installation on the user's machine is implied by downloading the code.
- No symlinked video inputs, symlinked folder roots, or output beneath watched input.
- File count bounded to 1–200, default 40. Maximum media size 256 MiB.
- One writer per output directory. OS advisory locking prevents two watchers writing to the same output at once; a lock file may remain on disk after exit but does not mean the process is still alive.
- File stability uses filesystem metadata, not a renderer-provided completion signal. Do not claim an external render succeeded just because the signature stopped changing briefly.
- Store includes completed reports locally; deleting a video from input removes its row from the current queue but deliberately does **not** delete older reports on disk. Remove sensitive reports explicitly as part of your retention process.
- State corruption is detected and stops the command rather than blindly overwriting a broken record.
- No hosted team features or recurring payment capability in the open-source core.

## Troubleshooting

`Batas` errors: reduce batch size, choose a new folder, or raise `--max-files` within 200. A video still being written remains pending. A malformed media file is reported as BLOCKED rather than silently skipped. A changed policy/fail-on value triggers a fresh scan before any new PASS.
