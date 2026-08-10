import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.providers.base import LLMProvider
from app.modules.ai.providers.claude_provider import ClaudeProvider
from app.modules.ai.providers.gemini_provider import GeminiProvider
from app.modules.ai.providers.groq_provider import GroqProvider
from app.modules.ai.providers.openai_provider import OpenAIProvider

_PROVIDER_BUILDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


class UnknownProviderError(Exception):
    pass


def build_provider(name: str) -> LLMProvider:
    builder = _PROVIDER_BUILDERS.get(name)
    if builder is None:
        raise UnknownProviderError(
            f"Unknown AI provider '{name}' — must be one of {sorted(_PROVIDER_BUILDERS)}"
        )
    return builder()


def get_orchestrator(db: AsyncSession, user_id: uuid.UUID) -> AIOrchestrator:
    primary = build_provider(settings.AI_PRIMARY_PROVIDER)
    fallback = build_provider(settings.AI_FALLBACK_PROVIDER)
    return AIOrchestrator(primary=primary, fallback=fallback, db=db, user_id=user_id)
