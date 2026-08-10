import uuid

from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import ResumeSkillExtractionResult
from app.modules.skills.repository import SkillRepository, UserSkillRepository


class ResumeSkillExtractorService:
    def __init__(self, orchestrator: AIOrchestrator, skill_repo: SkillRepository, user_skill_repo: UserSkillRepository):
        self.orchestrator = orchestrator
        self.skill_repo = skill_repo
        self.user_skill_repo = user_skill_repo

    async def extract_and_store(self, *, user_id: uuid.UUID, resume_text: str) -> ResumeSkillExtractionResult:
        if not resume_text.strip():
            return ResumeSkillExtractionResult(skills=[])

        result = await self.orchestrator.complete_structured(
            prompt_name="resume_skill_extraction",
            variables={"resume_text": resume_text},
            response_model=ResumeSkillExtractionResult,
            operation="resume_skill_extraction",
            use_cache=False,  # resume text is unique per person; caching buys nothing
        )

        for item in result.skills:
            skill = await self.skill_repo.get_or_create(item.name, item.category)
            await self.user_skill_repo.upsert(
                user_id=user_id, skill_id=skill.id, proficiency=item.proficiency, source="resume"
            )

        return result
