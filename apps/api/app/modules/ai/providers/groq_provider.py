from app.core.settings import settings
from app.modules.ai.providers.openai_compatible import OpenAICompatibleProvider

# Groq's free tier serves open-weight models (Llama, Qwen, etc.) on custom
# hardware fast enough to be genuinely usable, not just a slow demo — a
# reasonable free fallback alongside Gemini. Verify current model names and
# rate limits at console.groq.com/docs/rate-limits before relying on this.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            name="groq",
            api_key=settings.GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
            model=settings.GROQ_MODEL,
        )
