import pytest

from app.modules.ai.factory import UnknownProviderError, build_provider
from app.modules.ai.providers.claude_provider import ClaudeProvider
from app.modules.ai.providers.gemini_provider import GeminiProvider
from app.modules.ai.providers.groq_provider import GroqProvider
from app.modules.ai.providers.openai_provider import OpenAIProvider


@pytest.mark.parametrize(
    "name,expected_class",
    [
        ("claude", ClaudeProvider),
        ("openai", OpenAIProvider),
        ("gemini", GeminiProvider),
        ("groq", GroqProvider),
    ],
)
def test_build_provider_returns_correct_type(name, expected_class):
    provider = build_provider(name)
    assert isinstance(provider, expected_class)
    assert provider.name == name


def test_build_provider_raises_on_unknown_name():
    with pytest.raises(UnknownProviderError):
        build_provider("not-a-real-provider")


def test_gemini_and_groq_use_openai_compatible_base_class():
    """Both should share the same underlying implementation — this is the
    whole point of the OpenAICompatibleProvider refactor: no separate SDK,
    no duplicated request/response handling."""
    from app.modules.ai.providers.openai_compatible import OpenAICompatibleProvider

    assert isinstance(build_provider("gemini"), OpenAICompatibleProvider)
    assert isinstance(build_provider("groq"), OpenAICompatibleProvider)
