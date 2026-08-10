"""
Ashby's public job board API: GET https://api.ashbyhq.com/posting-api/job-board/{company}
Docs: https://developers.ashbyhq.com/reference/jobpostingsync — public, no auth.

Same caveat as the other two adapters: not exercised live in this sandbox.
"""

import httpx

from app.modules.discovery.html_utils import strip_html
from app.modules.discovery.schemas import DiscoveredJob

ASHBY_BASE = "https://api.ashbyhq.com/posting-api/job-board"


def normalize_ashby_job(raw: dict, company_slug: str) -> DiscoveredJob:
    return DiscoveredJob(
        source="ashby",
        source_id=str(raw.get("id", "")),
        title=raw.get("title", "Untitled role"),
        location=raw.get("location"),
        url=raw.get("jobUrl", ""),
        raw_description=strip_html(raw.get("descriptionHtml", "")),
        company_name=company_slug,
    )


async def fetch_ashby_jobs(company_slug: str) -> list[DiscoveredJob]:
    url = f"{ASHBY_BASE}/{company_slug}"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
    data = response.json()
    return [normalize_ashby_job(job, company_slug) for job in data.get("jobs", [])]
