# Proposed recurring subscription contract — design only

**Not implemented or enabled.** This is an acceptance specification, not payment code.

## Customer state machine

`visitor -> interested -> registered_free -> checkout_pending -> trial_active / active_paid -> grace_period -> suspended -> canceled`

Each transition requires a reason and trusted event. The source of truth for `active_paid` is a verified settlement or subscription event from the merchant, **not** a browser redirect, a POST claiming success, a screenshot or a planned invoice.

## Required tables (future)

- `organizations(id, owner_user_id, name)`
- `memberships(user_id, organization_id, role)`
- `plans(id, price_idr, included_minutes, included_storage_gb)`
- `subscriptions(id, organization_id, provider, provider_subscription_id, status, current_period_end)`
- `payment_events(provider_event_id UNIQUE, signature_verified, payload_checksum, processed_at, outcome)`
- `usage_entries(organization_id, job_id UNIQUE, processing_seconds, storage_bytes)`
- `audit_jobs(id, organization_id, status, metadata, object_key)`

All tenant tables need RLS plus server-side organization membership checks, scoped objects and per-tenant quotas. Secrets and tokens never appear in browser responses.

## Payments

Do not use or copy another business's merchant credentials. Before first subscription: confirm the AIWallet merchant account's recurring capability, verify payment method tokenization, provide cancellation/refunds, test idempotency and signed webhooks, fail closed when gateway is unavailable, support billing retries and rejected credit cards, verify the complete charge + cancellation lifecycle in sandbox, and obtain a separate explicit production launch decision. Advertised proposed prices may change after costs are measured.

## Usage and margins

Use processing seconds (not just number of videos) and disk bytes for cost metering. Each plan needs hard monthly limits and overage consent. Do not offer unlimited video transcoding or AI generation at low fixed prices without measured compute economics.
