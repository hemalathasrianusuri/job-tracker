"""
Lever's public postings API: GET https://api.lever.co/v0/postings/{company}?mode=json
Docs: https://github.com/lever/postings-api — public, no auth.

Same caveat as greenhouse.py: shape is from documented behavior, not
exercised live in this sandbox (api.lever.co isn't in the network allowlist
here). Verify against a real company slug before relying on this.
"""

import httpx

from app.modules.discovery.html_utils import strip_html
from app.modules.discovery.schemas import DiscoveredJob

LEVER_BASE = "https://api.lever.co/v0/postings"


def normalize_lever_job(raw: dict, company_slug: str) -> DiscoveredJob:
    categories = raw.get("categories") or {}
    description_html = raw.get("descriptionPlain") or raw.get("description", "")
    return DiscoveredJob(
        source="lever",
        source_id=str(raw.get("id", "")),
        title=raw.get("text", "Untitled role"),
        location=categories.get("location"),
        url=raw.get("hostedUrl", ""),
        raw_description=strip_html(description_html),
        company_name=company_slug,
    )


async def fetch_lever_jobs(company_slug: str) -> list[DiscoveredJob]:
    url = f"{LEVER_BASE}/{company_slug}"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params={"mode": "json"})
        response.raise_for_status()
    data = response.json()  # Lever returns a bare list, not {"jobs": [...]}
    return [normalize_lever_job(job, company_slug) for job in data]
