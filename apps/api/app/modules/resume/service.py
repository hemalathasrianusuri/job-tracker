import uuid

from app.core.settings import settings
from app.core.storage import StorageClient
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.text_extraction import extract_text

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB — resumes are text-heavy PDFs, this is generous
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class ResumeUploadError(Exception):
    pass


class ResumeService:
    def __init__(self, repo: ResumeRepository, storage: StorageClient):
        self.repo = repo
        self.storage = storage

    async def upload(
        self,
        *,
        user_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        set_as_master: bool,
    ):
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            raise ResumeUploadError("File exceeds the 5MB limit")
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ResumeUploadError("Only PDF and DOCX resumes are supported")

        if settings.ENABLE_ASYNC_RESUME_PROCESSING:
            # Text extraction + AI skill extraction happen in the Celery
            # chain (see workers/tasks/resume_tasks.py) after upload commits —
            # the router enqueues the task once it has a resume.id to work with.
            raw_text = None
        else:
            try:
                raw_text = extract_text(file_bytes=file_bytes, content_type=content_type, filename=filename)
            except Exception:
                # Extraction failure shouldn't block the upload — the file is still
                # stored and usable for tailored-resume generation later, just
                # without a text preview until re-processed.
                raw_text = None

        file_url = await self.storage.upload(
            file_bytes=file_bytes, filename=filename, content_type=content_type
        )

        if set_as_master:
            await self.repo.clear_master_flag(user_id)

        return await self.repo.create(
            user_id=user_id,
            file_url=file_url,
            original_filename=filename,
            raw_text=raw_text,
            is_master=set_as_master,
        )
