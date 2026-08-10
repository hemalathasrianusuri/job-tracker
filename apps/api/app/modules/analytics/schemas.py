from pydantic import BaseModel


class StatusBreakdownItem(BaseModel):
    status: str
    count: int


class DashboardSummary(BaseModel):
    total_applications: int
    active_pipeline: int
    offers: int
    accepted: int
    rejected: int
    withdrawn: int
    ghosted: int
    response_rate_pct: float
    avg_ats_match_score: float | None
    companies_applied: int
    status_breakdown: list[StatusBreakdownItem]


class SkillDemandItem(BaseModel):
    skill: str
    category: str
    job_count: int


class CompanyDemandItem(BaseModel):
    company: str
    job_count: int


class DemandAnalytics(BaseModel):
    top_skills: list[SkillDemandItem]
    top_companies: list[CompanyDemandItem]
    skills_by_category: dict[str, list[SkillDemandItem]]
