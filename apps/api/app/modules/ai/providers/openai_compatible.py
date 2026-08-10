from openai import APIError, AsyncOpenAI

from app.modules.ai.providers.base import LLMProvider, LLMProviderError, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """Base for any provider exposing an OpenAI-compatible /chat/completions
    endpoint. Both Google Gemini (https://generativelanguage.googleapis.com/v1beta/openai/)
    and Groq (https://api.groq.com/openai/v1) do this — using the OpenAI SDK
    with a different base_url means neither needs its own SDK dependency."""

    def __init__(self, *, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

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
            raise LLMProviderError(f"{self.name} request failed: {exc}") from exc

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            model=self._model,
        )
