# Re-run a release receipt (v0.4)

Each `audit.json` captures the source bytes SHA-256, FFprobe video/audio metadata,
FFmpeg detector settings, timecoded findings, and the technical software/ruleset
versions. There is no hidden model score.

## Verify

```bash
releaselab audit ./my-export.mp4 -o ./qc
releaselab verify ./my-export.mp4 ./qc/audit.json
releaselab verify ./my-export.mp4 ./qc/audit.json --policy ./policies/studio-vertical.json
```

Return codes: 0 = repeated technical observations are identical (and optional policy passes);
3 = a mismatch or policy block; 2 = input validation failure (invalid JSON, bad path, etc.).
The command computes the actual source file SHA-256, validates the recorded
software version/ruleset, re-runs FFmpeg with the exact recorded filter thresholds,
then compares metadata, checks, measurements and summary. Creation time and
rendered report HTML are excluded from that comparison.

A video changed by one byte is not the same source. An edited JSON summary is
not automatically trusted, even when its hash references an unchanged video.

## Policy sensitivity and truncation

The built-in `blackdetect`, `freezedetect`, and `silencedetect` FFmpeg filters have
minimum event durations. A policy forbidding events shorter than those thresholds
cannot claim the scan proves an all-clear. The policy-driven `gate` and `batch`
commands select a more sensitive FFmpeg threshold and record it inside the
receipt. When rechecking a historical report that used insufficient sensitivity,
policy evaluation **blocks** rather than passing. If too many timeline events
are detected, reports retain the first 30 for readability and flag the
truncated evidence as insufficient for strict policy.

These heuristics are not perfect frame-level detectors and do not certify
social network requirements, accessibility, rights, authenticity, creative
quality, or commercial performance. Source media never leaves the local CLI.
No SaaS waiting list or paid subscription exists in v0.8.

## Security model

Do not accept a receipt from an unknown party as a signed attestation: anyone can
make a different report against different content or modify a local binary.
The current v0.4 schema is **not signed**. SHA-256 detects changes to the
referenced file, not who created it. CI consumers should run the verifier on
their own trusted build agent and trusted source media.
