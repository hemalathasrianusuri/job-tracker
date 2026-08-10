from app.core.settings import settings
from app.modules.ai.providers.openai_compatible import OpenAICompatibleProvider

# Gemini's free tier (as of mid-2026: ~1,500 requests/day on Flash models, no
# credit card required) is the most generous frontier-quality free option
# currently available — see PHASE_9_NOTES.md for the comparison against
# Groq/OpenRouter/Cerebras that led here. Verify current quotas at
# ai.google.dev/gemini-api/docs/rate-limits before relying on this in
# production; free-tier terms change without much notice.
GEMINI_OPENAI_COMPAT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            name="gemini",
            api_key=settings.GEMINI_API_KEY,
            base_url=GEMINI_OPENAI_COMPAT_BASE_URL,
            model=settings.GEMINI_MODEL,
        )
