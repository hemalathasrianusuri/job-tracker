import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        result = await self.db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def get_by_name_ci(self, name: str) -> Company | None:
        result = await self.db.execute(
            select(Company).where(func.lower(Company.name) == name.strip().lower())
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, domain: str | None = None) -> Company:
        company = Company(name=name.strip(), domain=domain)
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def get_or_create(self, name: str) -> Company:
        """Case-insensitive so 'Google', 'google', 'GOOGLE' all resolve to one row —
        this is what keeps demand-analytics-by-company meaningful later."""
        existing = await self.get_by_name_ci(name)
        if existing:
            return existing
        return await self.create(name)
