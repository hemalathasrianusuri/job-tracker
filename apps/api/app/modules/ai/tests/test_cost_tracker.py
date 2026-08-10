from app.modules.ai.cost_tracker import estimate_cost_usd


def test_known_model_uses_exact_pricing():
    cost = estimate_cost_usd(
        provider="claude", model="claude-sonnet-4-5-20250929", input_tokens=1_000_000, output_tokens=0
    )
    assert cost == 3.00


def test_free_provider_known_model_is_zero_cost():
    cost = estimate_cost_usd(
        provider="gemini", model="gemini-2.5-flash", input_tokens=1_000_000, output_tokens=1_000_000
    )
    assert cost == 0.0


def test_unrecognized_model_falls_back_to_provider_pricing_not_blanket_expensive_rate():
    """Regression test: if GEMINI_MODEL is changed to a variant not in the
    pricing table (e.g. 'gemini-2.5-flash-lite'), the estimate must fall back
    to Gemini's $0 provider-level default — NOT silently apply Claude's $3/$15
    rate, which would wildly overstate cost for a free-tier call. This bug
    existed for one commit while adding Gemini/Groq support before being
    caught and fixed here."""
    cost = estimate_cost_usd(
        provider="gemini", model="gemini-2.5-flash-lite-preview-unknown",
        input_tokens=1_000_000, output_tokens=1_000_000,
    )
    assert cost == 0.0


def test_unrecognized_model_and_unrecognized_provider_uses_conservative_fallback():
    """Only when BOTH the model and the provider are unrecognized should the
    conservative (expensive) fallback apply — better to overestimate an
    unknown provider's cost than silently hide it as free."""
    cost = estimate_cost_usd(
        provider="some-new-provider", model="some-new-model", input_tokens=1_000_000, output_tokens=0
    )
    assert cost == 3.00
