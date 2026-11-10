# Architecture: a small, auditable core

```text
Local browser (no telemetry)
        │ multipart POST /api/audits
        ▼
FastAPI app (loopback only)
        │ bounded streaming upload, file size <=256 MiB
        ▼
Private temporary file
        ├── FFprobe: video/audio metadata
        ├── FFmpeg: audio loudness, black/freeze scans (first <=90 seconds)
        ├── SHA-256 of entire source
        └── FFmpeg: JPEG poster
        ▼
Report JSON + poster → SQLite and local poster folder
        │
        └── source video deleted, even on error
```

- `core.py` contains the actual checks, no frameworks or outbound network access.
- `report.py` renders a portable standalone HTML report. User-provided strings are HTML-escaped.
- `cli.py` is the `releaselab` terminal interface.
- `web.py` is the optional local single-user API; handlers use a bounded streaming upload and a two-job concurrency semaphore.
- `static/*` is a zero-build responsive frontend using semantic HTML, CSS and vanilla JS.
- DB queries use parameterized SQLite statements. Report identifiers are random 32-hex UUIDs; poster paths cannot be influenced by filenames.

There is no cloud storage, social OAuth, billing API, email or analytics in the open source app. This is an intentional trust boundary, not an unfinished hidden dependency.

## Upgrade path for SaaS (not shipped)

The product remains **single-user and local-only**. It has no multi-tenant SaaS, shared media storage, recurring billing, or cloud processing. Bind the web API to loopback, enforce Host validation and upload size limits, and keep audit history in local SQLite. Do not expose this alpha server publicly without a separate security design.

## Runtime limits

- Accepted input extensions: `.mp4 .mov .m4v .webm .mkv` with real FFprobe validation.
- Max file size 256 MiB; max duration 1800 seconds; scan duration 90 seconds; video input protocol limited to local file and pipe.
- Current report status is `pass` or `warn` on a parsable video. Invalid/unreadable files are rejected rather than stored as a misleading `fail` QC report.
- Concurrency: two audits per local process. No persistent job queue: users should keep the browser tab open during a run.
- No auto-cleanup of stored reports. The user can remove reports individually or delete the data directory.
