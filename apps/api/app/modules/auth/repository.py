import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.google_id == google_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str | None,
                      full_name: str | None = None, google_id: str | None = None) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            google_id=google_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
