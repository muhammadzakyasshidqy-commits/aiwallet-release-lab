# Billing enablement checklist: no charging code in v0.3

AIWallet Release Lab v0.3 is free Apache-2.0 source plus a **voluntary early-access interest form**, not a paid subscription system. The site must continue to mark prices as provisional. The following infrastructure must pass end-to-end before a paid button is turned on:

1. **Separate merchant identity:** Establish an AIWallet merchant account. Do **not** reuse a payment account belonging to another business without verified authority and merchant configuration.
2. **Provider eligibility:** Confirm recurring channel access with Midtrans, available payment methods, supported tokenization/consent UX, currencies, refunds, cancellation and recurring merchant features. Source: https://docs.midtrans.com/reference/create-subscription
3. **Strong membership model:** Identity provider, organization ownership, role-scoped reads/writes, RLS on each tenant table, deny-by-default service API, server-side entitlements only.
4. **Lifecycle:** `trial -> checkout_pending -> active_paid -> past_due -> grace -> suspended/canceled`. Transitions from payments require signed events plus independent status verification and idempotency. A newly created subscription schedule is **not** proof of a successful charge.
5. **Webhooks:** Verify signature or merchant-defined authentication, cross-check transaction/merchant ID/status/amount, isolate event duplicates, enforce event ordering, and retain audit records without card credentials. See https://docs.midtrans.com/reference/http-notification.
6. **Usage/cost:** Meter bounded scanning CPU seconds and storage; plan must specify quotas, rollover/no-rollover, invoice receipts, tax treatment, and data retention. No unlimited compute promise.
7. **Self-service:** Cancellation, account deletion, export, privacy notice, refund/contact and support workflows tested by a real sandbox purchase and cancellation.
8. **Launch:** Get explicit production approval after successful sandbox lifecycle. No passwords, tokens, OTP, card data or unverified billing states in the public bundle.

Price hypotheses: Creator Cloud Rp149,000/month and Studio Workspace Rp499,000/month, **not a checkout**. The open-source local edition remains free regardless of hosted plans.
