# Phase 5: AI Engine — Complete

## What's built

**`modules/ai/orchestrator.py`** — the single entry point every AI feature calls through. Handles, in one place:
- **Provider fallback**: primary fails (network/API error) → automatically retries on the fallback provider
- **JSON retry**: response fails schema validation → one retry on the *same* provider with an explicit nudge, before falling back
- **Caching**: idempotent operations (JD analysis) are cached in Redis keyed by a hash of the exact rendered prompt; cache hits log at $0 cost
- **Cost logging**: every real call logs tokens + estimated cost to `ai_usage_log`, feeding the `/ai/usage` cost dashboard endpoint

**Five AI services**, each ~20-40 lines because the orchestrator absorbs the shared complexity:
- `jd_analyzer.py` — extracts structured requirements, persists to `job.parsed_requirements` AND resolves each skill into the canonical taxonomy (`modules/skills/`)
- `skill_gap.py` — compares resume against a job's parsed requirements, scored gaps with priority/impact/difficulty
- `resume_optimizer.py` — ATS scoring + bullet rewrites (not cached — re-running after a resume edit should never return a stale score)
- `cover_letter.py` — generates and stores a `GeneratedDocument`
- `interview_prep.py` — generates and stores 12 categorized `InterviewQuestion` rows

**`modules/skills/`** — the canonical skill taxonomy from the Phase 1 revision, now actually populated by the JD analyzer. `skill_prerequisites` (the knowledge graph) and `user_skills` exist and are ready for Phase 6's learning engine to use — not populated yet, that's Phase 6 scope.

**Prompts** — 5 versioned `.md` files in `modules/ai/prompts/`, using `string.Template` (`$variable`) instead of `str.format` deliberately: every prompt instructs the model to output JSON, which contains literal braces that would silently collide with `.format()`'s placeholder syntax. Verified this distinction actually matters (see below).

## Verification performed

This phase's core value is the orchestrator's *behavior* under failure conditions, not just that it imports — so I wrote and ran real tests against it using fake providers (no API key required):

1. **Happy path** — valid JSON from primary on the first try
2. **Markdown fence stripping** — models sometimes wrap JSON in ` ```json ` despite instructions not to
3. **Retry-on-bad-JSON** — primary returns garbage once, succeeds on retry with the nudge appended
4. **Fallback** — primary raises an error, fallback provider is used automatically
5. **Total failure** — both providers exhausted → raises `AIGenerationError` cleanly (not a raw exception leaking to the caller)

All 5 passed. I also confirmed the `string.Template` decision was load-bearing by rendering a prompt with literal `{curly braces}` in the job description — substitution succeeded, which would have silently broken with `str.format`.

Plus the standard checks from earlier phases: full app import with all 6 AI routes registered, and all 12 tables (including the 6 new ones) registering correctly in Alembic's metadata.

**Not tested**: actual calls to Claude/OpenAI's real APIs (no API key in this sandbox) — the orchestrator logic around them is verified, but a live call could still surface something the mocks don't (rate limits, actual response formatting quirks). Recommend running one real end-to-end call per endpoint before considering this done.

## Local setup addition

```bash
# apps/api/.env — add real keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

alembic upgrade head  # applies 0003
```

## Next: Phase 6 — Analytics

Demand analytics (top skills/frameworks/languages across saved jobs, using the `job_skills` table this phase populated), the full dashboard (replacing Phase 4's lightweight client-side count with a real `/analytics/summary` endpoint), and the learning roadmap engine using `skill_prerequisites`.
