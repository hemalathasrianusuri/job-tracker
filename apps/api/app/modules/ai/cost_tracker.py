"""
Static $/1M-token pricing table. This WILL drift from reality — providers
change prices without much notice. Treat these as estimates for the cost
dashboard, not billing-grade figures. Update from the provider's current
pricing page periodically; nothing else in the codebase depends on exact
accuracy here.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AIUsageLog

# (input $/1M tokens, output $/1M tokens)
PRICING_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5-20250929": (3.00, 15.00),
    "gpt-4o": (2.50, 10.00),
    "gemini-2.5-flash": (0.0, 0.0),
    "llama-3.3-70b-versatile": (0.0, 0.0),
}

# Fallback pricing keyed by PROVIDER (not exact model string) — used when the
# model string doesn't match the table above, e.g. if GEMINI_MODEL is changed
# to a different Gemini variant. Without this, an unrecognized free-provider
# model would silently fall back to Claude/OpenAI's paid rate and wildly
# overstate cost. This is a real bug that was caught and fixed while writing
# this — see PHASE_9_NOTES.md.
DEFAULT_PRICING_BY_PROVIDER: dict[str, tuple[float, float]] = {
    "claude": (3.00, 15.00),
    "openai": (2.50, 10.00),
    "gemini": (0.0, 0.0),
    "groq": (0.0, 0.0),
}
_FALLBACK_PRICING = (3.00, 15.00)  # only used if provider itself is unrecognized


def estimate_cost_usd(*, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    if model in PRICING_PER_MILLION_TOKENS:
        input_price, output_price = PRICING_PER_MILLION_TOKENS[model]
    else:
        input_price, output_price = DEFAULT_PRICING_BY_PROVIDER.get(provider, _FALLBACK_PRICING)
    return round((input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price, 5)


async def log_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    provider: str,
    operation: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_hit: bool,
) -> None:
    cost = 0.0 if cache_hit else estimate_cost_usd(
        provider=provider, model=model, input_tokens=input_tokens, output_tokens=output_tokens
    )
    db.add(
        AIUsageLog(
            user_id=user_id,
            provider=provider,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            cache_hit=cache_hit,
        )
    )
    await db.flush()
