import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resume.models import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Resume | None:
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id, Resume.user_id == user_id, Resume.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Resume]:
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
            .order_by(Resume.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self, *, user_id: uuid.UUID, file_url: str, original_filename: str, raw_text: str | None,
        is_master: bool,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            file_url=file_url,
            original_filename=original_filename,
            raw_text=raw_text,
            is_master=is_master,
        )
        self.db.add(resume)
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def clear_master_flag(self, user_id: uuid.UUID) -> None:
        """Only one resume can be `is_master` at a time — called before setting
        a new one so the invariant holds without a DB-level constraint that
        would be awkward to express for a nullable-boolean 'exactly one true'."""
        await self.db.execute(
            update(Resume).where(Resume.user_id == user_id, Resume.is_master.is_(True))
            .values(is_master=False)
        )

    async def soft_delete(self, resume: Resume) -> None:
        resume.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
