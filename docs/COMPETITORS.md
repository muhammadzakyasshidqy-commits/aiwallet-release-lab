# Existing alternatives and differentiation (2026-11-10)

The goal is **earned utility** in one narrow video export workflow, not a fabricated GitHub ranking.

- [BAVC QCTools](https://github.com/bavc/qctools) — archival-grade video telemetry, charts, FFmpeg statistics; considerably deeper signal analysis than Release Lab.
- [qc-video](https://github.com/ddfzhh/qc-video) — an existing batch/video QC tool with timecode reports including dropped frames, interlacing, flashing, blur and audio problems. Release Lab does **not** own the generic idea of FFmpeg-based defect scanning.
- [mpvQC](https://github.com/mpvqc/mpvQC) — libmpv desktop QA reports and reusable JSON document format.
- [Clapshot](https://github.com/elonen/clapshot) — actual multi-user self-hosted collaborative video review, with annotations and authentication. Release Lab's proposed collaboration tier is NOT implemented today.
- [VidMetric](https://github.com/j-convey/VidMetric) — PSNR/SSIM/VMAF reference comparisons. Release Lab currently does not perform those reference-based image quality metrics.

## Tested differentiators already shipped in Release Lab

1. Narrow creator-facing vertical-format preflight with open-source CLI, local browser workbench and intuitive technical receipts.
2. Fail-closed studio policy JSON with detector sensitivity adapted to each threshold.
3. Re-running a source video against a receipt to catch mismatched technical evidence.
4. Batch/CI release gates, immutable local source hash, and generic event CSV to hand off a QC checklist.
5. Browser-only Report Explorer for existing receipts; local file inspection without transferring private video or JSON to the vendor.

## Validation before a "top project" claim

Verify public source repository, OS/FFmpeg compatibility, issue response quality, external contributions and repeat usage. Track stars only as an outcome of genuine use. Never describe external projects' current star counts without a dated source and clear ranking scope.
