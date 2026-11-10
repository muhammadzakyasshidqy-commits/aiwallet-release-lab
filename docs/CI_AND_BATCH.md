# Automated quality gates, batch scanning and regression comparisons

The tool checks **technical recommendations**, not binding upload-platform requirements. Check `ruleset` and the report's `advice` before treating any result as a release blocker.

## CI gate

```bash
releaselab gate path/to/export.mp4 --quick --fail-on warn
# 0 = gate accepted; 3 = check threshold was reached; 2 = cannot audit file
```

`--fail-on warn` is strict, `fail` blocks only future hard-failure checks, and `none` is a diagnostic-only opt-out. Reports can be saved with `--output ./release-report`.

A composite `action.yml` is included for people who want to use this as a GitHub Action **from a checked-out source tree**. The workflow in `examples/github-ci-gate.yml` is an implementation example; no action is published on Marketplace yet.

## Batch

```bash
releaselab batch ./exports --output ./release-batch --max-files 40
releaselab batch ./exports --recursive --quick --fail-on fail
```

Outputs: `index.html`, `summary.csv`, `manifest.json`, and a separate portable JSON/HTML audit per video. No original video is copied into the output. Input file count is bounded (default 40; hard maximum 200). Scan depth is bounded to the first 90 seconds. Longer videos receive a limitation warning.

The CSV mitigates formula injection for user-supplied filenames, but share a report publicly only after considering whether filenames or embedded frames identify private clients.

## Compare

```bash
releaselab compare export-v1.mp4 export-v2.mp4 --quick -o ./comparison.json
```

Shows width/height/FPS/duration deltas, changed rule statuses, regression count and SHA-256 equality. Returns code 3 if a new technical regression is detected. If source export is intentionally changed (e.g. cinematic cut or silent creative), a technical warning can be valid.

**Limitations:** There is no optical flow, face safety, copyright scan, human composition score, subtitle proofreading, legally binding platform compliance certification, or guaranteed distribution/virality.
