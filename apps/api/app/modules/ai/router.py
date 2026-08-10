import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import Integer, func, select

from app.core.deps import CurrentUser, DbSession
from app.modules.ai.cover_letter import CoverLetterService
from app.modules.ai.factory import get_orchestrator
from app.modules.ai.interview_prep import InterviewPrepService
from app.modules.ai.jd_analyzer import JDAnalyzerService
from app.modules.ai.models import AIUsageLog
from app.modules.ai.orchestrator import AIGenerationError
from app.modules.ai.resume_optimizer import ResumeOptimizerService
from app.modules.ai.schemas import AtsScoreResult, JDAnalysisResult, SkillGapResult
from app.modules.ai.skill_gap import SkillGapService
from app.modules.jobs.repository import JobRepository
from app.modules.resume.repository import ResumeRepository
from app.modules.skills.repository import SkillRepository

router = APIRouter(prefix="/ai", tags=["ai"])


async def _get_owned_job(db: DbSession, current_user: CurrentUser, job_id: uuid.UUID):
    job = await JobRepository(db).get_by_id(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


async def _get_owned_resume(db: DbSession, current_user: CurrentUser, resume_id: uuid.UUID):
    resume = await ResumeRepository(db).get_by_id(resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


def _handle_ai_errors(exc: Exception):
    if isinstance(exc, AIGenerationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.post("/jobs/{job_id}/analyze", response_model=JDAnalysisResult)
async def analyze_job(job_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    job = await _get_owned_job(db, current_user, job_id)
    orchestrator = get_orchestrator(db, current_user.id)
    service = JDAnalyzerService(orchestrator, SkillRepository(db))
    try:
        result = await service.analyze_and_store(job)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        _handle_ai_errors(exc)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/skill-gap", response_model=SkillGapResult)
async def get_skill_gap(job_id: uuid.UUID, resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    job = await _get_owned_job(db, current_user, job_id)
    resume = await _get_owned_resume(db, current_user, resume_id)
    orchestrator = get_orchestrator(db, current_user.id)
    service = SkillGapService(orchestrator)
    try:
        result = await service.analyze(job=job, resume=resume)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        _handle_ai_errors(exc)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/ats-score", response_model=AtsScoreResult)
async def get_ats_score(job_id: uuid.UUID, resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    job = await _get_owned_job(db, current_user, job_id)
    resume = await _get_owned_resume(db, current_user, resume_id)
    orchestrator = get_orchestrator(db, current_user.id)
    service = ResumeOptimizerService(orchestrator)
    try:
        result = await service.score(job=job, resume=resume)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        _handle_ai_errors(exc)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/cover-letter", status_code=status.HTTP_201_CREATED)
async def generate_cover_letter(
    job_id: uuid.UUID, resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser, tone: str = "professional"
):
    job = await _get_owned_job(db, current_user, job_id)
    resume = await _get_owned_resume(db, current_user, resume_id)
    orchestrator = get_orchestrator(db, current_user.id)
    service = CoverLetterService(orchestrator)
    try:
        document = await service.generate_and_store(job=job, resume=resume, tone=tone)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        _handle_ai_errors(exc)
    await db.commit()
    return {"id": document.id, "content": document.content, "created_at": document.created_at}


@router.post("/jobs/{job_id}/interview-questions")
async def generate_interview_questions(
    job_id: uuid.UUID, resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser
):
    job = await _get_owned_job(db, current_user, job_id)
    resume = await _get_owned_resume(db, current_user, resume_id)
    orchestrator = get_orchestrator(db, current_user.id)
    service = InterviewPrepService(orchestrator)
    try:
        questions = await service.generate_and_store(job=job, resume=resume)
    except (AIGenerationError, ValueError) as exc:
        await db.rollback()
        _handle_ai_errors(exc)
    await db.commit()
    return [
        {"id": q.id, "category": q.category, "question": q.question, "suggested_answer_notes": q.suggested_answer_notes}
        for q in questions
    ]


@router.get("/usage")
async def get_ai_usage(db: DbSession, current_user: CurrentUser):
    """Backs the AI cost dashboard — total spend, tokens, and cache-hit savings for the current user."""
    result = await db.execute(
        select(
            AIUsageLog.operation,
            func.count().label("calls"),
            func.sum(AIUsageLog.input_tokens).label("input_tokens"),
            func.sum(AIUsageLog.output_tokens).label("output_tokens"),
            func.sum(AIUsageLog.estimated_cost_usd).label("cost_usd"),
            func.sum(AIUsageLog.cache_hit.cast(Integer)).label("cache_hits"),
        )
        .where(AIUsageLog.user_id == current_user.id)
        .group_by(AIUsageLog.operation)
    )
    rows = result.all()

    return {
        "by_operation": [
            {
                "operation": r.operation,
                "calls": r.calls,
                "input_tokens": int(r.input_tokens or 0),
                "output_tokens": int(r.output_tokens or 0),
                "cost_usd": float(r.cost_usd or 0),
                "cache_hits": int(r.cache_hits or 0),
            }
            for r in rows
        ],
        "total_cost_usd": float(sum((r.cost_usd or 0) for r in rows)),
    }
