from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import JDAnalysisResult
from app.modules.jobs.models import Job
from app.modules.skills.repository import SkillRepository

# Maps our free-text extraction buckets to the canonical skill category enum
_CATEGORY_MAP = {
    "languages": "language",
    "frameworks": "framework",
    "cloud_platforms": "cloud",
    "databases": "database",
    "devops_tools": "devops",
    "soft_skills": "soft_skill",
}


class JDAnalyzerService:
    def __init__(self, orchestrator: AIOrchestrator, skill_repo: SkillRepository):
        self.orchestrator = orchestrator
        self.skill_repo = skill_repo

    async def analyze_and_store(self, job: Job) -> JDAnalysisResult:
        if not job.raw_description:
            raise ValueError("Job has no description to analyze — add raw_description first")

        result = await self.orchestrator.complete_structured(
            prompt_name="jd_analysis",
            variables={"job_title": job.title, "job_description": job.raw_description},
            response_model=JDAnalysisResult,
            operation="jd_analysis",
        )

        job.parsed_requirements = result.model_dump()

        skill_ids = []
        for field_name, category in _CATEGORY_MAP.items():
            for skill_name in getattr(result, field_name):
                skill = await self.skill_repo.get_or_create(skill_name, category)
                skill_ids.append(skill.id)

        await self.skill_repo.replace_job_skills(job_id=job.id, skill_ids=skill_ids)
        return result
