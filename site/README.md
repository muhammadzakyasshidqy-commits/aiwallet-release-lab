# AIWallet Release Lab marketing website

This is a static site for the **free, Apache-2.0** local-first Release Lab. No paid plans, waitlist form, subscription, auto-renewal, user video uploads or analytics trackers. The published website provides source ZIP / CLI / wheel / git bundle downloads, a synthetic technical report, and an in-browser receipt explorer that reads local JSON.

Use `index.html`, `style.css`, `app.js`, `tools/`, `demo/`, `assets/` and `releases/` together when deploying. No external JavaScript library. Reports are technical evidence, not a guarantee of creative quality or social platform acceptance.

Production website: https://aiwallet-studio-qz.higgsfield.app/

Versioned release downloads are built by `build_release.py` from a passing test run, then independently verified after deployment. The original ZIP/Git bundle under `releases/` is the code distribution.
