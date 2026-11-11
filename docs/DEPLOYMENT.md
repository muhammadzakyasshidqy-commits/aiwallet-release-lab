# Public distribution and local deployment

Official website (checked with HTTP): https://aiwallet-studio-qz.higgsfield.app/
Open-source core runs on the user device, not in the website runtime. Public download links point to source ZIP, wheel and portable CLI; each package can be checked against `releases/manifest.json` and `SHA256SUMS.txt`.

### Local start

- Install Python 3.11+, FFmpeg and FFprobe.
- Install source using `pip install -e '.[web]'` (optional dashboard), then `releaselab doctor` and `releaselab serve`.
- Visit `http://127.0.0.1:7860` locally. Do not expose the alpha dashboard publicly without authentication and rate limits.

### Marketing website

The site is static and does not upload users' video or use analytics tracking. The static marketing site offers an optional customer managed cloud interest form (no payments). Its Supabase backend stores explicit opt-in emails under RLS; the local core makes no calls to that service. Managed hosting and recurring billing are not implemented.

### GitHub

The canonical public source repository is pending authorized Contents-write access. ZIP distribution from a website is not equivalent to a GitHub release or green Actions.
