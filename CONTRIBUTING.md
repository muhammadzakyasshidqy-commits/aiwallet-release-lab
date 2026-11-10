# Contributing to AIWallet Release Lab

Contributions are welcome. Prefer measurable fixes, new tests, clearer messages, and reproducible technical rules over speculative “virality” claims.

1. Open an issue explaining the user problem, the expected behavior, and a minimal video fixture you own or may distribute.
2. Fork the repo, create one focused branch, and make a small change. Do **not** commit client footage, login cookies, passwords, social tokens, or real user data.
3. Run `python -m pytest -q` and `python -m compileall -q src`. Include a test for the behavior you changed.
4. Describe trade-offs and label any codec or loudness thresholds as recommendations rather than platform guarantees.

Core package dependencies should remain light. Avoid network access, automatic uploading or publishing, arbitrary command execution, and telemetry without an explicit separate product decision and security review.

By submitting a contribution, you agree that it is distributed under the project Apache-2.0 license.
