import uuid

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.core.deps import CurrentUser, DbSession
from app.core.settings import settings
from app.core.storage import get_storage_client
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import ResumeRead
from app.modules.resume.service import ResumeService, ResumeUploadError

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    set_as_master: bool = Query(default=False),
):
    service = ResumeService(ResumeRepository(db), get_storage_client())
    file_bytes = await file.read()

    try:
        resume = await service.upload(
            user_id=current_user.id,
            file_bytes=file_bytes,
            filename=file.filename or "resume",
            content_type=file.content_type or "",
            set_as_master=set_as_master,
        )
    except ResumeUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await db.commit()

    if settings.ENABLE_ASYNC_RESUME_PROCESSING:
        # Imported lazily so importing this router doesn't require Celery to
        # be configured/reachable when async processing is off (the default).
        from app.workers.tasks.resume_tasks import extract_resume_text_task
        extract_resume_text_task.delay(str(resume.id))

    return resume


@router.get("", response_model=list[ResumeRead])
async def list_resumes(db: DbSession, current_user: CurrentUser):
    return await ResumeRepository(db).list_for_user(current_user.id)


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    resume = await ResumeRepository(db).get_by_id(resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    repo = ResumeRepository(db)
    resume = await repo.get_by_id(resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    await repo.soft_delete(resume)
    await db.commit()
