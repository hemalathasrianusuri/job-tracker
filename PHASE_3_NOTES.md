# Phase 3: Backend APIs — Complete

## What's built

**`modules/companies/`** — shared lookup table, case-insensitive get-or-create so "Google"/"google"/"GOOGLE" resolve to one row (matters for demand analytics in Phase 6). Read-only autocomplete endpoint for the job-creation form.

**`modules/jobs/`** — the core tracker:
- Full CRUD, scoped to the authenticated user at the repository layer (every query filters `user_id`, so there's no route-by-route risk of leaking another user's jobs)
- `enums.py` defines the 13-state pipeline from your spec (`wishlist` → ... → `accepted`/`rejected`/`withdrawn`/`ghosted`)
- **Status changes go through a dedicated `PATCH /jobs/{id}/status` endpoint**, separate from the general update — this guarantees every transition writes a `job_status_history` row. The general `PATCH /jobs/{id}` can't silently change status and skip the audit trail.
- `applied_at` auto-stamps the first time a job leaves `wishlist`
- List endpoint supports filtering (status, company), search (title), sorting (whitelisted columns only — no raw column-name injection), and pagination
- `embedding VECTOR(1536)` column + ivfflat index created now, populated in Phase 5 — no destructive migration needed later

**`modules/resume/`** — upload endpoint with:
- A `StorageClient` abstraction (Supabase or local-disk, auto-selected by whether Supabase credentials are configured) — same pattern as the AI provider abstraction, so you can run and test Phase 3 fully without a live Supabase project
- Plain-text extraction (PDF via `pypdf`, DOCX via `python-docx`) — deliberately dumb, no structuring; that's the Phase 5 AI parser's job
- 5MB limit, PDF/DOCX only, one-master-resume invariant enforced in the repository

**Cross-cutting:**
- Rate limiting now covers all `/api/v1/*` routes (was auth-only in Phase 2) — auth endpoints get a tighter budget (1/5th) since that's where brute-force risk actually lives
- Migration `0002` adds `companies`, `resumes`, `jobs`, `job_status_history`, enables the `vector` extension

## Verification performed (not just written — actually checked)

I installed the real dependencies in a throwaway venv and imported the full app rather than just syntax-checking it. That caught two missing transitive dependencies (`itsdangerous`, `email-validator`) that `py_compile` wouldn't have flagged — both are now pinned in `requirements.txt`. Then confirmed:
- The app imports with zero errors and all 22 routes register correctly
- All 5 tables (`users`, `companies`, `resumes`, `jobs`, `job_status_history`) register in the shared SQLAlchemy metadata with their FK relationships intact

## Local setup addition

```bash
cd apps/api
pip install -r requirements.txt   # now includes the two deps found above
alembic upgrade head              # applies 0001 + 0002
```

Everything else from Phase 2's setup still applies.

## Next: Phase 4 — Frontend

The Next.js app shell: root layout (finally mounting `AuthProvider`), ShadCN theme/dark mode, dashboard layout with nav, and the Jobs tracker UI (list/kanban view, create/edit forms, status-pipeline drag-and-drop) consuming the APIs built in this phase.
