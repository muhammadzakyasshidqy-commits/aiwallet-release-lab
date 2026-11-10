# Publishing and subscription deployment

## Currently verified

- The local open-source workbench, CLI and API pass 17 automated tests on Linux.
- The opt-in early-access endpoint at `https://jwdxpigxgasybqaovsma.supabase.co/functions/v1/aiwallet-release-interest` returned 200 on GET, 204 on OPTIONS, 400 on invalid input and 201 on a synthetic valid submission. The synthetic record was deleted after testing.
- Backing table `public.aiwallet_release_interest` has RLS enabled and no anon/authenticated direct access.

## Not yet verified

- Public GitHub repository release: connected GitHub integration refuses writes with `403 Resource not accessible by integration` despite reported owner-level repository permissions.
- New production web domain: previous attempts to create Vercel/Render deployments failed with permissions/billing errors, and Higgsfield's deployed site returned 401 to an anonymous visitor. Supabase Edge Functions on the default URL are not suitable as HTML sites because the gateway serves HTML as `text/plain`.
- Full paid SaaS, Midtrans subscription, user authentication, team isolation, and production media workers are not present.

## Recommended publishing topology

`www.aiwalletstudio.com` (if acquired) → static frontend/marketing and signup → API application under a separate approved host → user login, object storage, workers, billing. Do **not** point customers directly at a raw Supabase function URL for an HTML webpage. The existing Supabase Edge Function is suitable for JSON forms and back-office workflows, not the public brand identity.

## Safety requirements before public deployment

- Replace loopback-only single-user API with protected user accounts, tenant authorization, CSRF/session checks, quotas, audit logs, independent storage, cancellation and full deletion.
- Secure processed media in private object storage with scoped time-limited signed URLs.
- Verify server-side payment entitlements only from signed, confirmed gateway notifications.
- Publish Privacy Policy, Terms, cancellation/refund policy and billing support.
- Obtain explicit user approval before a payment-producing production activation.
