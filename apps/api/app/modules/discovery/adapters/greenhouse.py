"""
Greenhouse's public job-board API: GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
Docs: https://developers.greenhouse.io/job-board.html — no API key needed,
this is the same data Greenhouse's own embeddable job board widget uses.

NOTE: the exact response shape below is written from documented public API
behavior. It has NOT been exercised against a live response in this
environment — this sandbox's network egress allowlist doesn't include
boards-api.greenhouse.io. Verify against a real company slug (e.g. try
'stripe' or any company you know uses Greenhouse) before relying on this.
"""

import httpx

from app.modules.discovery.html_utils import strip_html
from app.modules.discovery.schemas import DiscoveredJob

GREENHOUSE_BASE = "https://boards-api.greenhouse.io/v1/boards"


def normalize_greenhouse_job(raw: dict, company_slug: str) -> DiscoveredJob:
    location = raw.get("location") or {}
    return DiscoveredJob(
        source="greenhouse",
        source_id=str(raw["id"]),
        title=raw.get("title", "Untitled role"),
        location=location.get("name"),
        url=raw.get("absolute_url", ""),
        raw_description=strip_html(raw.get("content", "")),
        company_name=company_slug,
    )


async def fetch_greenhouse_jobs(company_slug: str) -> list[DiscoveredJob]:
    url = f"{GREENHOUSE_BASE}/{company_slug}/jobs"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params={"content": "true"})
        response.raise_for_status()
    data = response.json()
    return [normalize_greenhouse_job(job, company_slug) for job in data.get("jobs", [])]
