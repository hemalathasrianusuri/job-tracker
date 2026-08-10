import json

from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import MissingSkill
from app.modules.learning.schemas import LearningRoadmapResult


class LearningService:
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    async def build_roadmap(self, missing_skills: list[MissingSkill]) -> LearningRoadmapResult:
        if not missing_skills:
            return LearningRoadmapResult(roadmap=[])

        skills_payload = [
            {
                "name": s.skill,
                "priority_score": s.priority_score,
                "learning_difficulty": s.learning_difficulty,
                "estimated_hours": s.estimated_learning_hours,
            }
            for s in missing_skills
        ]

        return await self.orchestrator.complete_structured(
            prompt_name="learning_roadmap",
            variables={"skills_json": json.dumps(skills_payload)},
            response_model=LearningRoadmapResult,
            operation="learning_roadmap",
            # Cacheable: the same missing-skill set should produce the same
            # roadmap, and resource recommendations don't need to be fresh
            # per-request the way an ATS score does.
            use_cache=True,
        )
