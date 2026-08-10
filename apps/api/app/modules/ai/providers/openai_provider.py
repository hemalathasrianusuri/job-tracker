from openai import APIError, AsyncOpenAI

from app.core.settings import settings
from app.modules.ai.providers.base import LLMProvider, LLMProviderError, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    async def complete(self, *, system: str, user: str, max_tokens: int) -> LLMResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except APIError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            model=self._model,
        )
