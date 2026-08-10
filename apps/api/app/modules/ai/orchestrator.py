"""
Single entry point for every AI-powered feature in the app. Rationale for
centralizing this: provider fallback, JSON-parsing-with-retry, caching, and
cost logging are cross-cutting concerns that every one of the 5 AI services
(JD analyzer, skill gap, ATS scorer, cover letter, interview prep) needs
identically. Putting it here means those services are ~20 lines each instead
of each reimplementing retry/fallback/caching logic slightly differently.
"""

import hashlib
import json
import uuid
from typing import TypeVar

import redis.asyncio as redis
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.modules.ai import cost_tracker
from app.modules.ai.prompts.loader import render_prompt
from app.modules.ai.providers.base import LLMProvider, LLMProviderError

T = TypeVar("T", bound=BaseModel)

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

_JSON_RETRY_NUDGE = (
    "\n\nYour previous response could not be parsed as valid JSON matching the "
    "required schema. Respond with ONLY the JSON object — no markdown fences, "
    "no commentary, no trailing text."
)


class AIGenerationError(Exception):
    """Raised when both providers fail or the response can't be validated after retry."""


def _extract_json(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences despite instructions not to — strip them."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()


class AIOrchestrator:
    def __init__(self, *, primary: LLMProvider, fallback: LLMProvider, db: AsyncSession, user_id: uuid.UUID):
        self.primary = primary
        self.fallback = fallback
        self.db = db
        self.user_id = user_id

    def _cache_key(self, prompt_name: str, rendered_prompt: str) -> str:
        digest = hashlib.sha256(rendered_prompt.encode()).hexdigest()
        return f"ai_cache:{prompt_name}:{digest}"

    async def complete_structured(
        self,
        *,
        prompt_name: str,
        variables: dict[str, str],
        response_model: type[T],
        operation: str,
        system: str = "Respond with valid JSON only, matching the schema described in the prompt.",
        use_cache: bool = True,
    ) -> T:
        rendered = render_prompt(prompt_name, **variables)
        cache_key = self._cache_key(prompt_name, rendered)

        if use_cache:
            cached = await _redis.get(cache_key)
            if cached:
                await cost_tracker.log_usage(
                    self.db, user_id=self.user_id, provider="cache", operation=operation,
                    model="cache", input_tokens=0, output_tokens=0, cache_hit=True,
                )
                return response_model.model_validate_json(cached)

        result = await self._call_with_fallback_and_retry(
            system=system, user=rendered, response_model=response_model, operation=operation
        )

        if use_cache:
            await _redis.set(cache_key, result.model_dump_json(), ex=settings.AI_CACHE_TTL_SECONDS)

        return result

    async def _call_with_fallback_and_retry(
        self, *, system: str, user: str, response_model: type[T], operation: str
    ) -> T:
        last_error: Exception | None = None

        for provider in (self.primary, self.fallback):
            for attempt_prompt in (user, user + _JSON_RETRY_NUDGE):
                try:
                    response = await provider.complete(
                        system=system, user=attempt_prompt, max_tokens=settings.AI_MAX_OUTPUT_TOKENS
                    )
                except LLMProviderError as exc:
                    last_error = exc
                    break  # provider itself failed — don't retry the same prompt on it, try the next provider

                try:
                    parsed = response_model.model_validate_json(_extract_json(response.content))
                except (ValidationError, json.JSONDecodeError) as exc:
                    last_error = exc
                    continue  # bad JSON — retry once on the SAME provider with the nudge

                await cost_tracker.log_usage(
                    self.db, user_id=self.user_id, provider=provider.name, operation=operation,
                    model=response.model, input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens, cache_hit=False,
                )
                return parsed

        raise AIGenerationError(
            f"Failed to generate a valid response for '{operation}' from both providers: {last_error}"
        )
