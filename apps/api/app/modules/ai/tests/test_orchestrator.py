import uuid

import pytest

from app.modules.ai.orchestrator import AIGenerationError, AIOrchestrator
from app.modules.ai.providers.base import LLMProviderError, LLMResponse
from app.modules.ai.schemas import JDAnalysisResult

VALID_JSON = (
    '{"languages": ["Python"], "frameworks": ["FastAPI"], "cloud_platforms": [], '
    '"databases": [], "devops_tools": [], "soft_skills": [], "min_experience_years": 3, '
    '"education_requirement": null, "key_responsibilities": ["Build APIs"], '
    '"difficulty_score": 6, "seniority_level": "mid"}'
)


class FakeProvider:
    """Queue of canned responses/exceptions — lets us test orchestrator
    behavior without hitting a real LLM API."""

    def __init__(self, name: str, responses: list):
        self.name = name
        self._responses = list(responses)
        self.calls = 0

    async def complete(self, *, system: str, user: str, max_tokens: int) -> LLMResponse:
        self.calls += 1
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return LLMResponse(content=item, input_tokens=100, output_tokens=50, model=f"{self.name}-model")


class FakeDB:
    """No-op stand-in — the orchestrator only calls add()/flush() for cost
    logging, which these tests don't need to assert on."""

    def add(self, obj):
        pass

    async def flush(self):
        pass


def _orchestrator(primary_responses, fallback_responses=None):
    primary = FakeProvider("claude", primary_responses)
    fallback = FakeProvider("openai", fallback_responses or [])
    orch = AIOrchestrator(primary=primary, fallback=fallback, db=FakeDB(), user_id=uuid.uuid4())
    return orch, primary, fallback


async def test_happy_path_returns_validated_model():
    orch, primary, _ = _orchestrator([VALID_JSON])
    result = await orch.complete_structured(
        prompt_name="jd_analysis",
        variables={"job_title": "Backend Engineer", "job_description": "Python + FastAPI"},
        response_model=JDAnalysisResult,
        operation="jd_analysis",
        use_cache=False,
    )
    assert result.languages == ["Python"]
    assert result.difficulty_score == 6
    assert primary.calls == 1


async def test_strips_markdown_code_fences():
    fenced = f"```json\n{VALID_JSON}\n```"
    orch, _, _ = _orchestrator([fenced])
    result = await orch.complete_structured(
        prompt_name="jd_analysis", variables={"job_title": "X", "job_description": "Y"},
        response_model=JDAnalysisResult, operation="jd_analysis", use_cache=False,
    )
    assert result.languages == ["Python"]


async def test_retries_once_on_invalid_json_then_succeeds():
    orch, primary, _ = _orchestrator(["not json at all", VALID_JSON])
    result = await orch.complete_structured(
        prompt_name="jd_analysis", variables={"job_title": "X", "job_description": "Y"},
        response_model=JDAnalysisResult, operation="jd_analysis", use_cache=False,
    )
    assert result.languages == ["Python"]
    assert primary.calls == 2


async def test_falls_back_to_second_provider_on_error():
    orch, primary, fallback = _orchestrator(
        primary_responses=[LLMProviderError("503 from primary")],
        fallback_responses=[VALID_JSON],
    )
    result = await orch.complete_structured(
        prompt_name="jd_analysis", variables={"job_title": "X", "job_description": "Y"},
        response_model=JDAnalysisResult, operation="jd_analysis", use_cache=False,
    )
    assert result.languages == ["Python"]
    assert primary.calls == 1
    assert fallback.calls == 1


async def test_raises_when_both_providers_exhaust_retries():
    orch, _, _ = _orchestrator(
        primary_responses=["garbage", "still garbage"],
        fallback_responses=["also garbage", "still also garbage"],
    )
    with pytest.raises(AIGenerationError):
        await orch.complete_structured(
            prompt_name="jd_analysis", variables={"job_title": "X", "job_description": "Y"},
            response_model=JDAnalysisResult, operation="jd_analysis", use_cache=False,
        )
