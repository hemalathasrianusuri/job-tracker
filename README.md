# AI Job Tracker & Career Assistant

An AI-powered job search platform: track applications through a 13-stage pipeline, get AI-driven job description analysis, skill-gap detection, ATS resume scoring, tailored cover letters, and interview prep — all built on a provider-agnostic AI orchestrator. Defaults to a fully free stack (Gemini primary, Groq fallback); Claude/OpenAI are available as paid alternatives if you'd rather use them.

Built in 9 phases — see `phase-1-architecture.md` and `PHASE_2_..._9_NOTES.md` for the reasoning behind each one. This README is the practical "how do I run this" doc.

---

## Prerequisites

- **Python 3.12+**
- **Node.js 20+** and npm
- **Docker** (for Postgres + Redis) — or install both natively if you prefer
- A **free Gemini API key** ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) and/or **free Groq API key** ([console.groq.com/keys](https://console.groq.com/keys)) — no credit card needed for either, and the app defaults to using them. Claude/OpenAI keys work too if you'd rather use a paid provider (see `AI_PRIMARY_PROVIDER`/`AI_FALLBACK_PROVIDER` in `.env`)
- A **Google Cloud OAuth Client ID/Secret** (only needed for "Continue with Google" login — separate from the Gemini API key above; email/password auth works without it)

---

## 1. Start the database and cache

From the project root:

```bash
docker compose up -d
```

This starts:
- **Postgres 16 with pgvector** on `localhost:5432` (user `postgres`, password `postgres`, db `job_tracker`)
- **Redis** on `localhost:6379`

Check they're healthy: `docker compose ps` should show both as `healthy` within ~10 seconds.

---

## 2. Backend setup

```bash
cd apps/api
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Now edit `.env`:

```bash
SECRET_KEY=              # generate one: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
GEMINI_API_KEY=          # free, no credit card — aistudio.google.com/apikey
GROQ_API_KEY=            # free, no credit card — console.groq.com/keys
GOOGLE_CLIENT_ID=        # optional, only for Google sign-in — see step 4 below
GOOGLE_CLIENT_SECRET=    # optional
```

The app defaults to Gemini as primary AI provider and Groq as fallback — both free. If you'd rather use a paid provider, set `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` and change `AI_PRIMARY_PROVIDER`/`AI_FALLBACK_PROVIDER` to `claude`/`openai` in `.env`.

Everything else in `.env.example` already points at the Docker Compose services and is fine for local dev as-is.

Run migrations (creates all 12 tables: users, companies, resumes, jobs, job_status_history, skills, job_skills, user_skills, skill_prerequisites, ai_usage_log, generated_documents, interview_questions):

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** — you should see the full interactive API docs (32 endpoints across 8 modules: auth, jobs, companies, resume, ai, analytics, discovery, learning). `GET /health` should return `{"status": "ok", "environment": "development"}`.

Leave this terminal running.

### Optional: enable async resume processing

By default, resume text extraction happens synchronously during upload — no extra services needed. If you want the Celery pipeline (extraction + AI skill extraction as background tasks) instead:

```bash
docker compose --profile async up -d       # starts a worker + Flower monitoring dashboard
```

Then set `ENABLE_ASYNC_RESUME_PROCESSING=true` in `apps/api/.env` and restart the API. Flower's dashboard is at **http://localhost:5555**.

---

## 3. Frontend setup

In a new terminal:

```bash
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

Visit **http://localhost:3000** — you'll land on the login page. Register an account (email/password works without any Google setup), and you'll be redirected to the dashboard.

**Before your first real use**, it's worth running `npm run typecheck` — the frontend code was verified with manual import/export cross-checks in this environment rather than a live `tsc` run (see `PHASE_4_NOTES.md` for why), so this is the one gap worth closing yourself.

---

## 4. (Optional) Google OAuth setup

If you want "Continue with Google" to work:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (type: Web application)
3. Authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
4. Copy the Client ID and Secret into `apps/api/.env`
5. Restart the API

---

## 5. Trying out the AI and discovery features

Once you're logged in:

1. **Add a job** — either "Log application" (now with a job-description textarea) or "Import from a posting URL" on the Jobs page, which fetches and lets you review before saving
2. **Upload a resume** — the Resume page, drag-and-drop
3. Back in `/docs`, call `POST /ai/jobs/{job_id}/analyze` — extracts skills/requirements from the JD
4. Call `POST /ai/jobs/{job_id}/skill-gap?resume_id=...` — compares your resume against it
5. Call `POST /ai/jobs/{job_id}/ats-score?resume_id=...` — ATS score + bullet rewrites
6. Visit the **Learning** page, pick the job and resume — see a free-resource roadmap for what's missing
7. Check `GET /ai/usage` — see what each call cost

To search a company's public job board directly: `GET /discovery/search?source=greenhouse&company=<their-slug>` (also works with `lever` and `ashby`).

---

## Deploying to production

**Recommended path** (matches Phase 1's tech decisions): Render for the API, Vercel for the frontend, Supabase for Postgres + Storage.

1. **Supabase**: create a project, enable the `vector` extension, copy the connection string and `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`
2. **Render**: connect this repo, it'll pick up `render.yaml` automatically (New → Blueprint). Fill in the `sync: false` env vars in the Render dashboard (`DATABASE_URL`, `REDIS_URL`, Supabase and AI provider keys)
3. **Vercel**: import `apps/web` as the project root, set `NEXT_PUBLIC_API_URL` to your Render API URL + `/api/v1`
4. Push to `main` — `ci-backend.yml` and `ci-frontend.yml` run automatically; `deploy.yml` triggers Render + Vercel deploys after CI passes (needs `RENDER_DEPLOY_HOOK_URL`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` repo secrets — see the workflow file for where each comes from)

**Self-host alternative**: `docker-compose.prod.yml` runs everything (Postgres, Redis, API, web, Caddy for TLS) on a single VM. Set `POSTGRES_PASSWORD` and `NEXT_PUBLIC_API_URL` env vars, edit `Caddyfile` with your real domain, then `docker compose -f docker-compose.prod.yml up -d --build`.

**Before deploying either way**: neither Dockerfile has been build-tested in this environment (no Docker daemon available here) — run `docker build -t test ./apps/api` and `docker build -t test ./apps/web` locally first. Everything else in this project was verified by actually running it; this is the one exception, flagged rather than hidden. See `PHASE_7_NOTES.md` for the full verification breakdown, including real CVEs found and fixed in the dependency set (`pip-audit` went from ~40 findings across 4 packages to zero).

---

## Project structure

```
job-tracker/
├── docker-compose.yml          # Postgres (pgvector) + Redis for local dev
├── docker-compose.prod.yml     # Self-host alternative: full stack + Caddy TLS
├── Caddyfile                   # Reverse proxy config for the self-host path
├── render.yaml                 # Render Blueprint (recommended: API deploy target)
├── phase-1-architecture.md     # Architecture decisions & reasoning (read this first)
├── PHASE_2_NOTES.md            # Auth: JWT rotation, Google OAuth, security decisions
├── PHASE_3_NOTES.md            # Jobs/Companies/Resume CRUD APIs
├── PHASE_4_NOTES.md            # Frontend: design tokens, signature pipeline visual
├── PHASE_5_NOTES.md            # AI Engine: orchestrator, 5 AI features, verification
├── PHASE_6_NOTES.md            # Analytics: server-side aggregation, a real bug found & fixed
├── PHASE_7_NOTES.md            # Deployment: CI/CD, real CVEs found & fixed, honest gaps
├── PHASE_8_NOTES.md            # Gap closure: discovery, learning, Celery pipeline, missing UI
├── PHASE_9_NOTES.md            # Free AI provider default: Gemini + Groq, a real cost-tracking bug fixed
├── (this file)                 # Setup instructions
├── .github/
│   ├── workflows/               # ci-backend, ci-frontend, deploy, secrets-scan
│   └── dependabot.yml
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/           # settings, security, middleware, storage
│   │   │   ├── modules/        # domain-driven: auth, jobs, companies, resume, ai, skills, analytics, discovery, learning
│   │   │   ├── workers/        # Celery app + resume processing task chain (opt-in)
│   │   │   └── db/             # SQLAlchemy base, session
│   │   ├── alembic/versions/   # 0001 (users) → 0003 (skills/AI tables)
│   │   ├── Dockerfile          # Production image (multi-stage, gunicorn)
│   │   ├── requirements.txt
│   │   └── requirements-dev.txt # + pytest, ruff, pip-audit
│   └── web/                    # Next.js frontend
│       ├── app/                 # App Router pages: dashboard, jobs, resume, learning
│       ├── components/         # UI primitives + feature components
│       ├── lib/                 # API client, hooks, types, stores
│       ├── Dockerfile          # Production image (standalone Next.js output)
│       └── vercel.json
```

---

## What's built vs. what's not (be realistic about this)

**Fully built and verified** (backend: real app-import + logic tests + `TestClient` routing checks in a throwaway venv each phase; frontend: manual import/export cross-checks):
- Auth (JWT rotation, Google OAuth)
- Jobs/Companies/Resume CRUD with the full 13-stage status pipeline, including resume delete
- Next.js dashboard + jobs tracker UI + resume upload page + learning roadmap page
- AI orchestrator with provider fallback, JSON retry, caching, cost tracking — 7 AI features (JD analysis, skill gap, ATS scoring, cover letters, interview prep, resume skill extraction, learning roadmaps), running on a **free-by-default provider stack** (Gemini primary, Groq fallback — see `PHASE_9_NOTES.md`); Claude/OpenAI available as paid alternatives
- Server-side analytics (dashboard summary, demand analytics) — logic-tested against hand-computed expected values, which caught and fixed a real terminal-status inconsistency between frontend and backend (see `PHASE_6_NOTES.md`)
- CI/CD pipelines, security headers, dependency scanning — `pip-audit` found and Phase 7 fixed real CVEs across 4 packages, down to zero
- Job discovery: Greenhouse/Lever/Ashby adapters + URL-paste import, with the JD textarea in the create-job form that makes AI analysis usable
- The Celery async pipeline: resume upload → text extraction → AI skill extraction → `user_skills`, opt-in via `ENABLE_ASYNC_RESUME_PROCESSING`
- 25 real pytest tests (was 15, +6 provider factory + 4 cost-tracker tests, one of which caught a real pricing-fallback bug — see `PHASE_9_NOTES.md`), checked into the repo and run in CI on every push

**Not built — three items, all genuinely blocked by this sandbox's environment rather than scope decisions (see `PHASE_8_NOTES.md`):**
- **Docker build verification** — no Docker daemon was available in this sandbox. Both Dockerfiles are carefully written and reviewed but not build-tested; run `docker build` on both before trusting them in production.
- **Live calls to Greenhouse/Lever/Ashby, arbitrary job-posting URLs, and real Gemini/Groq/Claude/OpenAI APIs** — this sandbox's network allowlist doesn't reach any of those domains. The discovery adapters' *normalization logic* is genuinely unit-tested against fixtures matching each provider's documented response shape; the actual HTTP round-trip hasn't been exercised against a live board. Same for the AI orchestrator: its fallback/retry/parsing logic is tested against fake providers, not real API responses — including Gemini's specific behavior through the OpenAI-compatibility layer, added in Phase 9. Do a real smoke test of each before relying on it.
- **`deploy.yml`** is a template — written against current Render/Vercel CLI conventions but not run against real accounts.

If you want to close these too: they all require running the code somewhere with the access this sandbox doesn't have (a Docker daemon, network egress to those specific domains, real cloud accounts) — there's no more scoping work to do, just execution against real infrastructure.
