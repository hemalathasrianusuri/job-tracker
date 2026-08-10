from anthropic import AsyncAnthropic, AnthropicError

from app.core.settings import settings
from app.modules.ai.providers.base import LLMProvider, LLMProviderError, LLMResponse


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self):
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_MODEL

    async def complete(self, *, system: str, user: str, max_tokens: int) -> LLMResponse:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except AnthropicError as exc:
            raise LLMProviderError(f"Claude request failed: {exc}") from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            content=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self._model,
        )
