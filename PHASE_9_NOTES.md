# Phase 9: Free AI Provider Default — Complete

Prompted by a request to use the best free alternative to the Anthropic API instead of a paid default.

## What changed

**Research first, not a guess.** Searched current (mid-2026) comparisons across Gemini, Groq, Cerebras, OpenRouter, and GitHub Models. Consistent signal across sources: **Google Gemini's free tier is the strongest frontier-quality option** — no credit card, ~1,500 requests/day on Flash models, 1M-token context (comfortably fits a resume + JD in one call). **Groq** is the best free fallback — fast open-weight model inference (Llama 3.3 70B) on dedicated hardware, also no credit card.

**A genuinely useful discovery**: Google exposes Gemini through an **official OpenAI-compatible endpoint** (`https://generativelanguage.googleapis.com/v1beta/openai/`), and Groq does the same. That meant Gemini and Groq support could be added using the `openai` Python package already in `requirements.txt` — **zero new dependencies**, not even a Gemini-specific SDK.

## What's built

- `providers/openai_compatible.py` — one implementation (`OpenAICompatibleProvider`, parameterized by name/api_key/base_url/model) that both `GeminiProvider` and `GroqProvider` now use. The existing `ClaudeProvider`/`OpenAIProvider` are untouched.
- `AI_PRIMARY_PROVIDER` and `AI_FALLBACK_PROVIDER` settings — fully generalized to any of `claude`/`openai`/`gemini`/`groq`, replacing the old binary "whichever isn't primary between claude/openai" logic in the factory.
- **New defaults: `gemini` primary, `groq` fallback** — the app is free-by-default now. Claude/OpenAI remain available by setting the provider names and adding the matching key.
- `factory.py` rewritten around a name→builder dict (`build_provider(name)`), with `UnknownProviderError` for typos in config.

## A real bug caught while doing this, not after

While updating the cost-tracking pricing table to include Gemini/Groq at $0, I initially left the "unrecognized model string" fallback pointing at Claude's $3/$15-per-million rate. That's wrong in a specific, bad way: if someone changes `GEMINI_MODEL` to a newer Gemini variant not yet in the pricing dict (which will happen — these change often), the cost dashboard would silently report expensive Claude pricing for free Gemini calls. Caught this before shipping by writing the test first (`test_unrecognized_model_falls_back_to_provider_pricing_not_blanket_expensive_rate`), which failed against the naive implementation. Fixed by keying the fallback off **provider name** (gemini/groq → $0, claude/openai → their real rate) rather than one blanket default. Regression test now in `test_cost_tracker.py`.

## Verification performed

- Full test suite: **25 tests pass** (was 15; +6 provider factory tests, +4 cost-tracker tests including the regression above)
- `ruff check`: clean
- `pip-audit`: zero known vulnerabilities (no new dependencies were even added)
- Confirmed the app imports cleanly with **zero AI API keys set at all** — provider construction is lazy, only fails at actual call time, not at import/startup
- Confirmed `settings.AI_PRIMARY_PROVIDER == "gemini"` and `AI_FALLBACK_PROVIDER == "groq"` by default
- Live routing check via `TestClient`: AI endpoints still resolve and enforce auth correctly after the provider swap

**Not verified, same honest caveat as every AI-related claim in this project**: no real call to Gemini's or Groq's live API — this sandbox's network allowlist doesn't reach either domain. The provider construction and the orchestrator's fallback/retry/parsing logic around them are tested; the actual HTTP round-trip and Gemini's specific JSON-mode behavior through the OpenAI-compat layer are not. **Do a real smoke test** — call any `/ai/*` endpoint with a real `GEMINI_API_KEY` set — before relying on this.

One more thing worth knowing: free tiers change terms without much warning (multiple sources flagged Gemini already cut its free tier once in late 2025). If Gemini's `/analyze` calls start failing with quota errors, check current limits at `ai.google.dev/gemini-api/docs/rate-limits` before assuming something's broken in this code.
