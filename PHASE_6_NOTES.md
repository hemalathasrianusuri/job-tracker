# Phase 6: Analytics — Complete

## What's built

**`modules/analytics/`** — server-side aggregation, replacing Phase 4's client-side "fetch 200 rows and count in the browser" placeholder:

- `GET /analytics/summary` — total applications, active pipeline count, offers/accepted/rejected/withdrawn/ghosted, response rate, average ATS match score, distinct companies applied to. Backs the dashboard's stat cards and funnel chart.
- `GET /analytics/demand` — top skills across the user's own saved jobs (populated by the Phase 5 JD analyzer via `job_skills`), grouped by category, plus top companies applied to.

All aggregation happens in SQL (`GROUP BY` + `COUNT`/`AVG`), not in Python after fetching every row — this is what makes it actually scale past a couple hundred jobs, unlike the Phase 4 placeholder it replaces.

**Frontend**: `lib/hooks/use-analytics.ts` + a rebuilt `dashboard/page.tsx` consuming the real endpoints, plus a new demand-analytics skill-pill section.

**Scoping note**: "Demand analytics" here is explicitly scoped to *your own* saved jobs, not a global market-demand figure. With one Postgres instance and no cross-user job corpus, presenting a single user's search as "market demand" would be misleading — flagged in `analytics/repository.py` directly so it isn't silently misrepresented later if this becomes multi-tenant.

## A real bug found and fixed during verification

While writing a test for the response-rate/active-pipeline math (not just checking that the endpoint returns *a* number, but that it returns the *right* number), I found a genuine inconsistency: the backend's `TERMINAL_STATUSES` set (`jobs/enums.py`) didn't include `OFFER`, while the frontend's equivalent (`lib/types/job.ts`, built in Phase 4) already treated `offer` as terminal. That meant `active_pipeline` was silently counting people with an active offer as still "in progress," which is wrong — receiving an offer is a decision point, not a stage you're still progressing through.

Test before fix: `active_pipeline` computed as 19 for a dataset that should produce 18.
Fixed by adding `JobStatus.OFFER` to the backend's `TERMINAL_STATUSES`, with a comment cross-referencing the frontend definition so the two don't drift apart silently again.

This is exactly the kind of bug that a "does it import" check would never catch — it required testing actual output against hand-computed expected values.

## Verification performed

- Full app import with analytics wired in — 31 total routes across 7 modules
- Real logic test: constructed a fake status-count distribution, computed expected `active_pipeline` and `response_rate_pct` by hand, asserted the service produces exactly those numbers — caught the OFFER bug above
- Zero-jobs edge case (empty account) — confirmed no division-by-zero on `response_rate_pct`

## Next: Phase 7 — Deployment (not yet built)

Production Dockerfiles for both apps, CI/CD via GitHub Actions (lint → test → build → security scan → deploy), and Render/Vercel/Supabase deployment config. The `docker-compose.yml` shipped with this project is dev-dependencies-only (Postgres + Redis) — not a production deployment story.
