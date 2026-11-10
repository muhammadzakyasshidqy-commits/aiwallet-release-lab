# Static marketing site

This directory contains a completely static, standalone landing site. It is safe to deploy independently of the local FastAPI application. It does NOT pretend to run video checks in the browser: it displays a reproducible, synthetic example and links to the self-hosting source package.

## Files

- `index.html` — editorial one-page product, status and pricing.
- `style.css`, `app.js`, `assets/icon.svg` — bundled visuals and interactions. No CDN libraries.
- `demo/audit.html`, `demo/audit.json`, `demo/synthetic-black-example.mp4` — synthetic example for users to reproduce.
- `releases/aiwallet-release-lab-v0.7.0.zip` — the complete open-source core package, generated without nesting the marketing site.

The early-access dialog POSTs only after name, email, selected plan and explicit consent to the connected Supabase Edge endpoint. Payments are disabled.

Deployment is currently hosted at https://aiwallet-studio-qz.higgsfield.app/ . Check the live deployment and asset hashes separately before claiming a new version is online.

- `tools/receipt-explorer.html` (plus CSS/JS) — client-side JSON receipt viewer and generic marker CSV export; no file uploads.
