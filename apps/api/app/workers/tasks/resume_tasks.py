import asyncio
import uuid

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.modules.ai.factory import get_orchestrator
from app.modules.ai.resume_skill_extractor import ResumeSkillExtractorService
from app.modules.resume.models import Resume
from app.modules.resume.text_extraction import UnsupportedFileTypeError, extract_text
from app.modules.skills.repository import SkillRepository, UserSkillRepository
from app.workers.celery_app import celery_app


async def _get_resume_unscoped(db, resume_id: str) -> Resume | None:
    """Unscoped lookup by ID only — the request-facing ResumeRepository
    requires a user_id for ownership checks, which don't apply here since a
    background task isn't acting on behalf of an authenticated request."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalar_one_or_none()


def _guess_content_type(filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def _extract_text_async(resume_id: str) -> None:
    async with AsyncSessionLocal() as db:
        resume = await _get_resume_unscoped(db, resume_id)
        if resume is None:
            return

        # The resume row only stores file_url (Supabase or local-disk static
        # URL), not raw bytes — those went straight to storage at upload
        # time without passing through this task, so re-fetch here.
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(resume.file_url)
            response.raise_for_status()

        try:
            text = extract_text(
                file_bytes=response.content,
                content_type=_guess_content_type(resume.original_filename),
                filename=resume.original_filename,
            )
        except UnsupportedFileTypeError:
            return

        resume.raw_text = text
        await db.commit()

    # Chain into skill extraction once text is available. Two separate tasks
    # (not one big function) so a transient failure in the AI call doesn't
    # force re-fetching and re-parsing the file — Celery can retry just the
    # skill-extraction step.
    extract_resume_skills_task.delay(resume_id, str(resume.user_id))


@celery_app.task(name="resume.extract_text", bind=True, max_retries=2, default_retry_delay=10)
def extract_resume_text_task(self, resume_id: str) -> None:
    try:
        asyncio.run(_extract_text_async(resume_id))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _extract_skills_async(resume_id: str, user_id: str) -> None:
    async with AsyncSessionLocal() as db:
        resume = await _get_resume_unscoped(db, resume_id)
        if resume is None or not resume.raw_text:
            return

        orchestrator = get_orchestrator(db, uuid.UUID(user_id))
        service = ResumeSkillExtractorService(orchestrator, SkillRepository(db), UserSkillRepository(db))
        await service.extract_and_store(user_id=uuid.UUID(user_id), resume_text=resume.raw_text)
        await db.commit()


@celery_app.task(name="resume.extract_skills", bind=True, max_retries=2, default_retry_delay=10)
def extract_resume_skills_task(self, resume_id: str, user_id: str) -> None:
    try:
        asyncio.run(_extract_skills_async(resume_id, user_id))
    except Exception as exc:
        raise self.retry(exc=exc)
