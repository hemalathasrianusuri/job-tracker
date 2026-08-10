import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession
from app.modules.ai.factory import get_orchestrator
from app.modules.ai.orchestrator import AIGenerationError
from app.modules.ai.skill_gap import SkillGapService
from app.modules.jobs.repository import JobRepository
from app.modules.learning.schemas import LearningRoadmapResult
from app.modules.learning.service import LearningService
from app.modules.resume.repository import ResumeRepository

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/roadmap", response_model=LearningRoadmapResult)
async def get_learning_roadmap(
    job_id: uuid.UUID, resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser
):
    """Builds a free-resource learning roadmap for the skill gap between a
    resume and a job. Runs the Phase 5 skill-gap analysis first (job must
    already be JD-analyzed via POST /ai/jobs/{job_id}/analyze), then feeds
    the missing skills into the roadmap prompt."""
    job = await JobRepository(db).get_by_id(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    resume = await ResumeRepository(db).get_by_id(resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    orchestrator = get_orchestrator(db, current_user.id)
    try:
        skill_gap = await SkillGapService(orchestrator).analyze(job=job, resume=resume)
        roadmap = await LearningService(orchestrator).build_roadmap(skill_gap.missing_skills)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        status_code = status.HTTP_502_BAD_GATEWAY if isinstance(exc, AIGenerationError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc))

    await db.commit()
    return roadmap
