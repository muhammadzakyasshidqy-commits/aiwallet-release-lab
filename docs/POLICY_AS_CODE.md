# Policy as Code: delivery specifications, not platform rules

Release Lab's built-in PASS/CHECK logic is **heuristic**. Real studios may require different export policies. v0.4 adds a deterministic JSON policy gate for CI and batch release receipts.

The project includes `policies/studio-vertical.json` as an **example delivery contract**. Its requirements are intentionally conservative and **are not official rules** of Instagram, TikTok or YouTube. Edit it for each client before treating it as a contractual acceptance policy.

## Commands

```bash
releaselab gate my-video.mp4 --policy policies/studio-vertical.json --fail-on none
# Exit 0: policy passed. Exit 3: policy violation. Exit 2: malformed input/tool error.

releaselab batch ./exports --recursive --policy policies/studio-vertical.json --output ./release-batch
```

`--fail-on warn` (the default) additionally blocks generic heuristic warnings. `--fail-on none` disables only **generic** warnings; the explicitly selected policy remains enforced. To turn off policy enforcement, do not pass `--policy`.

`--quick` skips audio/visual scans, emits an explicit CHECK finding, and **cannot** meet `require_full_scan:true`. Files longer than 90 seconds cannot meet this requirement with v0.4 because FFmpeg scanning deliberately stops after 90 seconds; that is a known constraint, not something the gate should quietly approve.

## Supported JSON fields

Every policy needs `schema: "aiwallet.release-policy/v1"` and a non-empty `name`. Optional fields:

| Group | Fields |
|---|---|
| Geometry | `min_width`, `min_height` |
| Frame rate | `min_fps`, `max_fps` |
| Runtime | `min_duration_seconds`, `max_duration_seconds` |
| Codecs | `allowed_codecs` (array of FFprobe codec names) |
| Sound | `require_audio`, `min_lufs`, `max_lufs`, `max_true_peak_dbfs` |
| Scan coverage | `require_full_scan` |
| Timeline | `max_black_segment_seconds`, `max_freeze_segment_seconds`, `max_silence_segment_seconds` |

All measurements have finite, bounded values. Unknown keys, invalid types, and contradictory minimum/maximum ranges fail closed before release decisions. A configured measurement that could not be obtained is **not** treated as PASS. Never use `--quick` to certify a final export.

A team policy is a policy *you* own. Users must listen, watch, check rights/consent, and review creative content separately. Release Lab does not certify copyright ownership, regulatory compliance, or social-platform approval.
