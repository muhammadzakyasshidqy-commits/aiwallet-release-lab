# Editorial Review Gate (v0.7)

**Technical quality control is not creative quality.** A video can pass format, codec, loudness, black-frame, freeze and silence checks while having a weak story, confusing composition, rushed or sluggish edit, irrelevant SFX, or brand-inaccurate claims.

The five independent manual criteria are:

1. `story_hook`: hook, premise, payoff and intelligibility.
2. `visual_clarity`: subject framing, text legibility, compositing and shot continuity.
3. `pacing`: shot rhythm, transitions and pauses.
4. `sound_design`: subjective sound balance, relevance and editorial use (separate from measured LUFS).
5. `brand_accuracy`: factual claims, tone, trademarks and brand style.

Each must be explicitly marked `pass`, `changes_requested` or `not_applicable`. All-not-applicable is invalid. An approved review requires no `changes_requested` items. Approval binds to the exact SHA-256 and QC ruleset. If the file changes or ruleset differs, the editorial gate fails closed.

## Local UI

Run `pip install -e '.[web]'` and `releaselab serve`. Upload and audit a video locally, inspect it manually with an actual player/editor, fill the separate **Creative review** panel, save, and download `editorial-review.json`. The dashboard keeps every revision in its local SQLite database, but only the latest is displayed. Deleting a technical report deletes its associated reviews; no review is uploaded.

## CLI

```bash
releaselab audit clip.mp4 -o ./qc
releaselab editorial ./qc/audit.json --reviewer "Reviewer Name" \
  --story-hook pass --visual-clarity pass --pacing pass --sound-design pass \
  --brand-accuracy not_applicable --notes "Checked in real-time" \
  -o ./qc/editorial-review.json
releaselab gate clip.mp4 --policy policies/studio-vertical.json \
  --editorial-review ./qc/editorial-review.json --fail-on none
```

`releaselab gate` returns code `0` only if the technical checks and the optional editorial gate pass, `3` if the release is blocked, `2` if auditing the video itself fails.

## Integrity and trust boundary

- This is **self-attestation**, not an identity-verified reviewer signature. Someone with write access can edit a JSON file or a local SQLite database.
- SHA-256 identifies exact source bytes; it does not prove video rights, platform distribution, creative quality, reviewer identity, or production provenance.
- It does not automatically detect subtitle collisions, factual mistakes or trademark issues. Human inspection is indispensable.
- A review marked `pass` is not proof that the editor actually watched the video. Treat it as a studio workflow declaration.
- The local dashboard is designed for **loopback only** and has no multi-user authentication. Never expose it as a public server or call it a hosted enterprise approval system.
- For regulated approval, require authenticated reviewer identities and cryptographic signatures in a future tenant-based offering.
