# AIWallet Release Lab: commercial thesis and constraints

## One product, two buying decisions

**Who gets value immediately:** Creators or agencies exporting many vertical videos, especially if mistakes in framing/audio cost review cycles.

**Open-source user:** runs QC locally, builds trust by seeing precise checks; can submit improvements and rule presets. Distribution via GitHub, technical posts, demo videos, integration examples and real contributor discussions.

**Managed buyer (future):** teams wanting managed execution, durable report links, shared review queues, policies, retention, and uptime. Paid hosting/support is the product; the open-source license remains genuinely open.

## Competitor gaps (hypotheses, not claims of superiority)

- Full video agents and editors (e.g. OpenMontage and Remotion) focus on creating and rendering; Release Lab checks export readiness without controlling the creative source.
- Social schedulers (e.g. Postiz) manage publication; Release Lab does not use their OAuth sessions and can run before any social platform is connected.
- FFmpeg power users can reproduce these checks individually; the product sells a coherent, documented release receipt that non-engineers can interpret.

The unproven hypothesis is willingness to pay for team-level workflows rather than CLI access. Interview 15 prospective users and observe repeat usage before treating it as validated.

## Proposed pricing, **not active**

Community: Rp0, unlimited local use, Apache-2.0.
Creator Cloud: Rp149,000/month, proposed maximum 100 processing minutes and 30-day report retention. Exact quotas subject to measured processing/storage cost.
Studio Workspace: Rp499,000/month, proposed 400 minutes and up to five editors. Per-seat/overage policy must be defined before billing.

Proposed cost guardrail: target gross margin >70% after rendering, storage, bandwidth, payments and support. For Creator Cloud at Rp149,000, that means direct cost should be less than **Rp44,700/month** per subscription before overhead. For Studio Workspace at Rp499,000, direct cost should be less than **Rp149,700/month**. These are targets, not measured economics. Do not offer unlimited GPU processing or AI generation at a fixed low price.

## Indonesian payments

Midtrans provides a subscription API with tokenization and prerequisites such as enabled One Click. A production-grade recurring flow must support explicit customer consent, per-merchant enablement, idempotency, secure token custody, verified asynchronous notifications, cancellation, retries, refund/support operations, and correct entitlement granting based on payment confirmation. **This repository has none of that yet.** Do not reuse another unrelated business's Midtrans merchant automatically.

## Growth scorecard toward a *category-leading* GitHub project

| Period | Objective (not guaranteed) | Evidence |
|---|---|---|
| First release | 45 passing tests, a 1-minute quick start, real video audit, one-screen demo | CI, release assets, screen recording |
| First 30 days | 20 unique real users, 5 meaningful issues or PRs, 3 repeat users | opted-in issue/forum feedback, usage interviews |
| 30–90 days | 100 real stars, 10 meaningful external contributors, 2 integration adapters, 3 paid discovery calls | GitHub metrics + CRM evidence |
| Beyond | Earn strong search/distribution position through differentiated capabilities | stars earned naturally, retention, paid pilots |

No fake stars, automated mass comments, paid fake reviews, scraping private data, or claims of being GitHub #1. Ranking depends on community adoption, not merely repository configuration.

## Commercial release gates

1. Demonstrate at least 10 real weekly repeat users of the core.
2. Verify cloud cost per 1, 5, and 30-minute real sample video.
3. Implement tenant isolation, auth, audit logging, data deletion and privacy policy.
4. Verify merchant recurring eligibility and all billing state transitions.
5. Test failed payments, refunds, downtime and quota exhaustion.
6. Only after these gates: enable paid signup and recurring charges.

## Interest collection implemented

The public JSON endpoint at `https://jwdxpigxgasybqaovsma.supabase.co/functions/v1/aiwallet-release-interest` collects *only* voluntarily submitted name, email, selected proposed plan and contact consent, and responds `201` on success. CORS is enabled for the explicit opt-in form. The backing table has RLS enabled with no direct anonymous or authenticated read/write grants. No subscriptions are charged or activated. Test interest records used for acceptance are deleted after verification.
