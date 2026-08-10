import json

from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import SkillGapResult
from app.modules.jobs.models import Job
from app.modules.resume.models import Resume


class SkillGapService:
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    async def analyze(self, *, job: Job, resume: Resume) -> SkillGapResult:
        if not job.parsed_requirements:
            raise ValueError("Job hasn't been analyzed yet — run JD analysis first")
        if not resume.raw_text:
            raise ValueError("Resume has no extracted text to compare against")

        return await self.orchestrator.complete_structured(
            prompt_name="skill_gap",
            variables={
                "job_requirements_json": json.dumps(job.parsed_requirements),
                "resume_text": resume.raw_text,
            },
            response_model=SkillGapResult,
            operation="skill_gap",
        )
