# AI Job Tracker & Career Assistant — Phase 1: Foundations

**Phase scope:** Requirements → Architecture → Folder Structure → Database Schema → Tech Decisions

---

## 1. Product Framing (before any code)

Before touching architecture, it's worth being explicit about what "MVP that's still portfolio-worthy" means, because the full spec you gave me is a 12–18 month roadmap for a small team, not a single build. I'm going to treat it as a **product vision doc** and carve out a real, shippable **v1** from it — then layer the rest in as v2/v3. That's what a staff engineer would actually do with this brief.

**v1 (Phases 2–7 in this plan) will ship:**
- Auth (JWT + Google OAuth)
- Manual + CSV/URL-import job tracking (full Kanban pipeline)
- Resume upload + AI ATS scoring + skill-gap analysis
- AI resume bullet rewriting + tailored resume generation
- AI cover letter generation
- AI interview question generation (role + JD specific)
- Analytics dashboard (applications, response rate, skill demand from *your own* saved jobs)
- Daily AI coach (digest, not literal automation)

**Deliberately deferred to v2+ (I'll design for it, not build it yet):**
- Live scraping/adapters for 20+ job boards — most of these (LinkedIn, Indeed, Naukri) prohibit scraping in their ToS. v1 uses **user-imported jobs** (paste a URL or JD, we parse it) plus any board that has a real public/partner API (Greenhouse, Lever, Ashby job boards are public JSON APIs — this covers most of Stripe/Coinbase/Airbnb/Cloudflare/Databricks/Rippling career pages legitimately). I'll document this trade-off more in Phase 3.
- Full admin panel, multi-tenant SaaS billing
- Browser extension for one-click capture (this is actually the highest-leverage v2 feature — more useful than scraping)

I'm flagging this now rather than silently descoping later. Tell me if you want the scraping-dependent job boards prioritized differently — legally, the answer is always "use their API or let the user paste the URL," not scrape.

---

## 2. System Architecture

```
                              ┌─────────────────────────┐
                              │   Next.js 14 (App Router)│
                              │  React + TS + ShadCN     │
                              │  TanStack Query + Zustand│
                              └────────────┬─────────────┘
                                           │ HTTPS / REST + SSE (streaming AI)
                              ┌────────────▼─────────────┐
                              │      FastAPI (Python)     │
                              │  ─────────────────────── │
                              │  /auth   /jobs   /resume  │
                              │  /ai     /analytics /docs │
                              │  Pydantic v2 validation   │
                              │  JWT middleware + RBAC    │
                              └───┬───────────┬───────┬───┘
                                  │           │       │
                  ┌───────────────┘           │       └────────────────┐
                  ▼                            ▼                        ▼
        ┌──────────────────┐        ┌──────────────────┐     ┌──────────────────┐
        │   PostgreSQL 16   │        │      Redis        │     │  Celery Workers   │
        │   + pgvector ext  │        │  cache + broker    │     │  (async AI jobs,   │
        │   (jobs, users,   │        │  session/rate-limit│     │  resume parsing,   │
        │   resumes, skills)│        └──────────────────┘     │  email digests)    │
        └──────────────────┘                                  └─────────┬──────────┘
                  ▲                                                     │
                  │                                                     ▼
        ┌──────────────────┐                                 ┌──────────────────┐
        │ Supabase Storage  │                                 │  LLM Provider(s)  │
        │ (resumes, PDFs,   │                                 │  OpenAI / Claude  │
        │  cover letters)   │                                 │  API (pluggable)  │
        └──────────────────┘                                 └──────────────────┘
```

**Key architectural decisions and why:**

| Decision | Choice | Reasoning |
|---|---|---|
| Monorepo vs polyrepo | **Monorepo** (`/apps/web`, `/apps/api`, `/packages/shared`) | Single source of truth for types (OpenAPI → TS codegen), simpler CI, easier for a solo/small team to keep frontend & backend in sync |
| Sync API calls vs async everywhere | **Sync for CRUD, async (Celery) for anything LLM/parsing** | AI calls (resume analysis, JD parsing, cover letter gen) take 3–15s. Blocking a request thread for that kills throughput. Celery + polling/SSE keeps the API responsive |
| LLM provider | **Provider-agnostic abstraction layer**, default Claude API, OpenAI as fallback ⚠️ *superseded — see Phase 9* | Never lock into one vendor for a product feature this central. A `LLMProvider` interface with `ClaudeProvider`/`OpenAIProvider` implementations lets you swap or A/B test |
| Vector search | **pgvector inside Postgres**, not a separate vector DB | At this scale (one user's jobs + resumes, not billions of vectors) a separate Pinecone/Weaviate is over-engineering. pgvector keeps one database to operate, backup, and reason about |
| Auth | **JWT (access + refresh) + Google OAuth via Authlib** | Standard, stateless, works cleanly with mobile/future clients. Refresh tokens stored httpOnly cookie, access token in memory |
| File storage | **Supabase Storage** (S3-compatible) | You specified it; also gives free tier + built-in RLS if you later want per-user bucket policies |
| Caching | **Redis** for: rate limiting, session blacklist, expensive AI-response caching (same JD analyzed twice = cache hit) | Cuts LLM cost meaningfully — JD analysis is idempotent per job posting |

---

## 3. Folder Structure

```
job-tracker/
├── apps/
│   ├── web/                          # Next.js frontend
│   │   ├── app/
│   │   │   ├── (auth)/login/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── jobs/[id]/
│   │   │   │   ├── resume/
│   │   │   │   ├── learning/
│   │   │   │   ├── analytics/
│   │   │   │   └── interview-prep/
│   │   │   └── api/                  # only for OAuth callback proxy, edge cases
│   │   ├── components/
│   │   │   ├── ui/                   # ShadCN primitives
│   │   │   ├── jobs/
│   │   │   ├── dashboard/
│   │   │   └── resume/
│   │   ├── lib/
│   │   │   ├── api-client.ts         # typed fetch wrapper (generated from OpenAPI)
│   │   │   ├── query-keys.ts
│   │   │   └── stores/               # zustand stores
│   │   └── types/                    # generated from backend OpenAPI schema
│   │
│   └── api/                          # FastAPI backend
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   │   ├── settings/         # base.py / development.py / production.py / testing.py
│       │   │   ├── security.py       # JWT, password hashing
│       │   │   ├── middleware/       # gateway *concerns*, in-process (no separate gateway service)
│       │   │   │   ├── rate_limit.py
│       │   │   │   ├── request_id.py
│       │   │   │   └── logging.py    # structlog, JSON logs
│       │   │   └── deps.py           # dependency injection (get_db, get_current_user)
│       │   ├── modules/              # domain-driven, replaces the old services/ split
│       │   │   ├── auth/             # router.py service.py repository.py schemas.py models.py tests/
│       │   │   ├── jobs/             # router.py service.py repository.py schemas.py models.py tests/
│       │   │   ├── resume/           # router.py service.py repository.py schemas.py models.py tests/
│       │   │   ├── ai/
│       │   │   │   ├── orchestrator.py      # provider selection, fallback, cost tracking
│       │   │   │   ├── providers/
│       │   │   │   │   ├── base.py  claude_provider.py  openai_provider.py
│       │   │   │   ├── prompts/             # versioned prompt files, not inline strings
│       │   │   │   │   ├── resume_analysis.md  cover_letter.md  ats.md
│       │   │   │   │   ├── skill_gap.md  career_coach.md  interview.md  roadmap.md
│       │   │   │   ├── jd_analyzer.py  skill_gap.py  resume_optimizer.py
│       │   │   │   └── cost_tracker.py      # per-call token + $ logging → AI cost dashboard
│       │   │   ├── search/           # hybrid: pgvector cosine + Postgres tsvector keyword search
│       │   │   ├── analytics/
│       │   │   ├── learning/         # skill_prerequisites graph, resource recommendations
│       │   │   ├── notifications/    # pluggable channel interface; Email implemented, others stubbed
│       │   │   └── interview/
│       │   ├── workers/              # Celery: chains = event-driven pipeline without a message broker
│       │   │   ├── celery_app.py
│       │   │   └── chains/
│       │   │       └── resume_pipeline.py   # upload → parse → extract_skills → embed → notify
│       │   ├── db/
│       │   │   ├── session.py
│       │   │   └── migrations/       # Alembic
│       │   └── shared/               # cross-module repository base classes, pagination, etc.
│       └── tests/
│           ├── unit/
│           └── integration/
│
├── packages/
│   └── shared/                       # shared enums/constants (job status, skill categories)
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── Dockerfile.api / Dockerfile.web
│
├── .github/workflows/
│   ├── ci-backend.yml
│   ├── ci-frontend.yml
│   └── deploy.yml
│
└── docs/
    ├── architecture.md
    ├── er-diagram.md
    └── api.md
```

**Why a services/ + repositories/ split in the backend:** routers should only do request/response translation. Services hold business logic. Repositories hold raw DB queries. This is the layer that lets you unit-test `skill_gap.py` without spinning up FastAPI or a database at all — critical once the AI logic gets complex.

---

## 4. Database Schema (core tables, v1 scope)

```sql
-- Users & Auth
users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT,              -- null if OAuth-only
  google_id TEXT UNIQUE,
  full_name TEXT,
  target_role TEXT,
  experience_years NUMERIC(3,1),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  deleted_at TIMESTAMPTZ              -- soft delete
);

-- Resumes
resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  file_url TEXT NOT NULL,
  raw_text TEXT,
  parsed_json JSONB,                  -- structured extraction: skills, experience, education
  is_master BOOLEAN DEFAULT false,    -- the base resume vs job-tailored variants
  ats_score NUMERIC(5,2),
  created_at TIMESTAMPTZ DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

-- Companies (normalized, reused across jobs)
companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  domain TEXT,
  logo_url TEXT,
  industry TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Jobs (the core tracker entity)
jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  company_id UUID REFERENCES companies(id),
  title TEXT NOT NULL,
  location TEXT,
  work_mode TEXT CHECK (work_mode IN ('remote','hybrid','onsite')),
  salary_min INTEGER,
  salary_max INTEGER,
  source_url TEXT,
  raw_description TEXT,
  parsed_requirements JSONB,          -- extracted skills/frameworks/experience
  status TEXT NOT NULL DEFAULT 'wishlist'
    CHECK (status IN ('wishlist','applied','oa_scheduled','oa_completed',
                       'interview_1','interview_2','interview_3','hr_round',
                       'offer','accepted','rejected','withdrawn','ghosted')),
  referral BOOLEAN DEFAULT false,
  recruiter_name TEXT,
  applied_at TIMESTAMPTZ,
  ats_match_score NUMERIC(5,2),
  resume_id UUID REFERENCES resumes(id),   -- tailored resume used
  embedding VECTOR(1536),             -- pgvector, for "similar jobs" / semantic search
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_jobs_embedding ON jobs USING ivfflat (embedding vector_cosine_ops);

-- Status history (audit trail — every stage transition, not just current status)
job_status_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  changed_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT
);

-- Skills (canonical taxonomy, reused across jobs/resumes/learning resources)
skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  category TEXT CHECK (category IN ('language','framework','cloud','database',
                                     'devops','soft_skill','ai_ml','other'))
);

job_skills (           -- many-to-many, job requires skill X at weight Y
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  skill_id UUID REFERENCES skills(id),
  importance NUMERIC(3,2) DEFAULT 1.0,
  PRIMARY KEY (job_id, skill_id)
);

user_skills (          -- what the user has, derived from resume parse + self-reported
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  skill_id UUID REFERENCES skills(id),
  proficiency TEXT CHECK (proficiency IN ('learning','comfortable','strong')),
  source TEXT CHECK (source IN ('resume','manual')),
  PRIMARY KEY (user_id, skill_id)
);

-- Learning resources (curated, free-only per your requirement)
learning_resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id),
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  provider TEXT,               -- freeCodeCamp, MDN, official docs, etc.
  resource_type TEXT CHECK (resource_type IN ('course','doc','video','project','article')),
  estimated_hours NUMERIC(5,1),
  difficulty TEXT CHECK (difficulty IN ('beginner','intermediate','advanced'))
);

-- Cover letters / AI generations (versioned, tied to a job)
generated_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  doc_type TEXT CHECK (doc_type IN ('resume','cover_letter','interview_prep')),
  content TEXT,
  file_url TEXT,
  model_used TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Interview prep artifacts
interview_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  category TEXT CHECK (category IN ('coding','system_design','behavioral','resume','company_specific')),
  question TEXT NOT NULL,
  suggested_answer_notes TEXT
);

-- Skill knowledge graph (adjacency list — no separate graph DB needed at this scale)
skill_prerequisites (
  skill_id UUID REFERENCES skills(id),
  prerequisite_skill_id UUID REFERENCES skills(id),
  PRIMARY KEY (skill_id, prerequisite_skill_id)
);
-- e.g. (Celery, requires_first: Redis) lets the learning engine sequence roadmaps correctly
-- instead of recommending resources in arbitrary order.

-- AI cost tracking (feeds the AI cost dashboard, cache-hit savings, daily usage)
ai_usage_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  provider TEXT NOT NULL,            -- 'claude' | 'openai'
  operation TEXT NOT NULL,           -- 'jd_analysis' | 'resume_optimize' | 'cover_letter' | ...
  input_tokens INTEGER,
  output_tokens INTEGER,
  estimated_cost_usd NUMERIC(10,5),
  cache_hit BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**Notes on this schema:**
- Every user-owned table has `deleted_at` for soft deletes — never hard-delete application history, it's the whole point of the tracker.
- `job_status_history` is separate from `jobs.status` deliberately: the current status is a fast-read field, but "how long did I sit in OA_COMPLETED before getting ghosted" is an analytics query that needs the full transition log.
- `embedding VECTOR(1536)` on jobs enables "find jobs similar to ones I got interviews for" later — a real differentiator feature, cheap to add now, expensive to retrofit.
- Full Alembic migration chain will version every one of these from the start (I won't hand you a single monolithic `init.sql`).

---

## 5. Tech Stack Decisions Requiring a Call From You

A few places in your spec where I'll pick a sensible default unless you say otherwise:

1. **LLM provider default** — I'll default to **Claude API** (better instruction-following for structured JSON extraction tasks like JD parsing), with OpenAI as a swappable fallback via the provider interface. Confirm this is fine.
2. **Deployment target for v1** — Render for the API + Celery worker, Vercel for Next.js (better DX than Railway for Next specifically), Supabase for Postgres+Storage. Railway as an alternative if you prefer one platform for everything.
3. **Resume parsing** — PDF/DOCX text extraction via `pypdf`/`python-docx` + LLM structuring pass, rather than a paid parsing API (Affinda, etc.) — keeps costs at zero for v1.

---

## Next: Phase 2 — Authentication

Once you confirm the above (or tell me what to change), Phase 2 builds:
- FastAPI JWT auth (access + refresh token rotation)
- Google OAuth flow
- User model + Alembic migration
- Next.js auth pages + protected route middleware

Let me know if you want to adjust anything in this phase before I move forward — especially the v1/v2 scope split in Section 1, since that's the highest-leverage decision in the whole project.
