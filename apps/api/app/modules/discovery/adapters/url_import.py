import httpx

from app.modules.discovery.html_utils import extract_title, strip_html
from app.modules.discovery.schemas import DiscoveredJob


class UrlFetchError(Exception):
    pass


async def fetch_job_from_url(url: str) -> DiscoveredJob:
    """Fetches an arbitrary job posting URL the user pasted and extracts
    plain text for the AI JD analyzer. This is the general-purpose fallback
    for any board without a public API (LinkedIn, Indeed, Naukri, etc.) —
    the user finds the listing themselves and pastes the link; nothing here
    automates browsing or bypasses a site's access controls."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (job-tracker-import-bot)"})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise UrlFetchError(f"Couldn't fetch {url}: {exc}") from exc

    html = response.text
    return DiscoveredJob(
        source="url",
        source_id=url,
        title=extract_title(html) or "Untitled role (edit after import)",
        location=None,  # not reliably extractable from arbitrary page structure
        url=url,
        raw_description=strip_html(html),
        company_name="Unknown company (edit after import)",
    )
