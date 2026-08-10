# Phase 8: Closing the Gaps — Complete

Prompted by a review comment on the README's "not built" list: rather than leave those items as permanent caveats, this phase builds four of the seven, and is explicit about the three that remain genuinely blocked by this sandbox's constraints.

## What's built

**1. Job discovery** (`modules/discovery/`) — Greenhouse, Lever, and Ashby adapters (all public APIs, no auth), plus a general URL-import fallback for any board without one. Each adapter splits into a pure `normalize_*_job()` function and a `fetch_*_jobs()` wrapper — the split matters because it made the normalization logic unit-testable without live network access. 7 tests, using fixtures shaped per each provider's public docs, all pass.

**2. Learning roadmap** (`modules/learning/`) — chains onto the existing Phase 5 skill-gap analysis; a new prompt constrained to the specific free-resource providers from the original spec (freeCodeCamp, MDN, official docs, roadmap.sh, etc.) turns missing skills into an ordered, resourced roadmap.

**3. The Celery async pipeline** — actually built this time, not just described. `resume.extract_text` → `resume.extract_skills` as a real two-task chain, the second step populating `user_skills` (a table that had existed since Phase 5 with nothing writing to it). Opt-in via `ENABLE_ASYNC_RESUME_PROCESSING` (default off), with `worker`/`flower` added to both compose files on an opt-in `async` profile — so the verified synchronous path from Phases 3-7 is completely unaffected unless you deliberately turn this on.

**4. The two missing frontend forms** — resume upload page (drag-and-drop, list, delete — added a DELETE endpoint too, which didn't exist), a JD textarea in the create-job dialog, a learning roadmap page, and an "import from URL" flow wired to the discovery endpoints.

## Verification performed

Same discipline as every prior phase:
- Full test suite: **15 tests pass** (was 8; +7 discovery adapter tests)
- `ruff check` (E9/F): clean
- `pip-audit`: zero known vulnerabilities (re-confirmed after adding `beautifulsoup4`)
- Live routing check via `TestClient` with a real local Redis: all 11 new/existing endpoints across every module resolve and enforce auth correctly
- Celery app + both tasks confirmed to register correctly (`celery_app.tasks` contains `resume.extract_text` and `resume.extract_skills`)
- All 8 YAML config files (both compose files, all 4 GitHub Actions workflows, `render.yaml`, `dependabot.yml`) parse as valid YAML
- Frontend: re-ran the same import-resolution and named-export cross-checks from Phase 4 across all 44 files (was 30) — clean

## What's still honestly not done

Three items remain blocked by this environment, not by scope decisions — unchanged from Phase 7:

- **Docker build verification** — still no Docker daemon available in this sandbox. `docker build` on both Dockerfiles remains the one thing to check yourself before trusting them.
- **Live calls to Greenhouse/Lever/Ashby and real Claude/OpenAI APIs** — this sandbox's network allowlist doesn't include those domains (or arbitrary URLs for the import-from-URL feature). The adapter *normalization logic* is genuinely tested against documented response shapes; the actual HTTP round-trip to a live board or a live LLM has not been exercised. Try `GET /discovery/search?source=greenhouse&company=<a-real-Greenhouse-company-slug>` against a running instance before relying on it.
- **`deploy.yml` against real Render/Vercel accounts** — still a template, still untested against real infrastructure.

If you want to close these too, the honest next step for all three is the same: run them somewhere with the actual access this sandbox doesn't have, and report back what breaks.
