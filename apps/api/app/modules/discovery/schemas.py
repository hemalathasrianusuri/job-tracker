from typing import Literal

from pydantic import BaseModel


class DiscoveredJob(BaseModel):
    source: Literal["greenhouse", "lever", "ashby", "url"]
    source_id: str
    title: str
    location: str | None
    url: str
    raw_description: str
    company_name: str


class ImportJobRequest(BaseModel):
    """Re-submits a DiscoveredJob (as returned by /discovery/search) to be
    saved as a tracked job. The frontend round-trips the object it already
    has rather than the backend re-fetching by ID — avoids a second network
    call to Greenhouse/Lever/Ashby and avoids needing to cache search results."""
    job: DiscoveredJob


class ImportUrlRequest(BaseModel):
    url: str
