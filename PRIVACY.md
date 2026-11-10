# Privacy and data handling

## Community / self-hosted release

The default local CLI and dashboard analyze files on the same machine, do not require an account, and do not send media or analytics telemetry to AIWallet, social networks, or other cloud providers.

- The original video is held only as a temporary local file during workbench processing and then removed.
- A local JPEG still image and audit JSON are saved in a local SQLite-backed report history until you delete the report.
- Filenames, SHA-256 checksums, measurements, and time of audit are part of the report. They may reveal information about a project, so do not publish reports without reviewing them.
- The CLI writes audit files wherever you choose via `--output`. Those outputs remain until you remove them.
- The project does not collect cookies, tokens, account credentials or device identifiers.

## Voluntary hosted early-access interest

The separate early-access form asks for name, email, selected proposed plan, and explicit consent. Only when it is submitted are those fields transmitted over HTTPS to the AIWallet Supabase project. A hidden anti-spam field is not persisted. No video is transmitted as part of signup.

The data is stored in `public.aiwallet_release_interest`, protected by RLS with no anonymous direct table access. Records are used to contact a prospective customer about availability and research, not for auto-renewal or payment. There are no subscription payments in this release. The current alpha does not provide an automated retention/purge schedule; requests for access, corrections or deletion can be sent to `muhammadzakyasshidqy@gmail.com`. Do not share your passwords or private media via the interest form.

Project owner must confirm legal disclosures, retention practices and local data protection duties before general commercial launch.
