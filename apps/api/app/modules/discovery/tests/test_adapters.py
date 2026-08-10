from app.modules.discovery.adapters.ashby import normalize_ashby_job
from app.modules.discovery.adapters.greenhouse import normalize_greenhouse_job
from app.modules.discovery.adapters.lever import normalize_lever_job
from app.modules.discovery.html_utils import extract_title, strip_html


def test_strip_html_removes_tags_scripts_and_styles():
    html = "<html><head><style>.x{}</style></head><body><script>evil()</script><h1>Title</h1><p>Body text</p></body></html>"
    result = strip_html(html)
    assert "evil()" not in result
    assert "{}" not in result
    assert "Title" in result
    assert "Body text" in result


def test_extract_title_prefers_title_tag():
    html = "<html><head><title>Backend Engineer at Acme</title></head><body><h1>Different H1</h1></body></html>"
    assert extract_title(html) == "Backend Engineer at Acme"


def test_extract_title_falls_back_to_h1():
    html = "<html><body><h1>Backend Engineer</h1></body></html>"
    assert extract_title(html) == "Backend Engineer"


def test_normalize_greenhouse_job_matches_documented_shape():
    # Fixture shaped per https://developers.greenhouse.io/job-board.html
    raw = {
        "id": 12345,
        "title": "Senior Backend Engineer",
        "location": {"name": "Remote - US"},
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/12345",
        "content": "<p>We need someone who knows <b>Python</b>.</p>",
    }
    result = normalize_greenhouse_job(raw, "acme")
    assert result.source == "greenhouse"
    assert result.source_id == "12345"
    assert result.title == "Senior Backend Engineer"
    assert result.location == "Remote - US"
    assert "Python" in result.raw_description
    assert "<b>" not in result.raw_description


def test_normalize_lever_job_matches_documented_shape():
    # Fixture shaped per https://github.com/lever/postings-api
    raw = {
        "id": "abc-123",
        "text": "Staff Engineer",
        "categories": {"location": "New York, NY"},
        "hostedUrl": "https://jobs.lever.co/acme/abc-123",
        "descriptionPlain": "Build our core platform.",
    }
    result = normalize_lever_job(raw, "acme")
    assert result.source == "lever"
    assert result.title == "Staff Engineer"
    assert result.location == "New York, NY"
    assert result.raw_description == "Build our core platform."


def test_normalize_ashby_job_matches_documented_shape():
    # Fixture shaped per https://developers.ashbyhq.com/reference/jobpostingsync
    raw = {
        "id": "xyz-789",
        "title": "Platform Engineer",
        "location": "San Francisco",
        "jobUrl": "https://jobs.ashbyhq.com/acme/xyz-789",
        "descriptionHtml": "<p>Join our platform team.</p>",
    }
    result = normalize_ashby_job(raw, "acme")
    assert result.source == "ashby"
    assert result.title == "Platform Engineer"
    assert "Join our platform team" in result.raw_description


def test_normalize_handles_missing_optional_fields_gracefully():
    """Real-world API responses aren't always complete — a job with no
    location or content shouldn't crash normalization."""
    raw = {"id": 1, "title": "Some Role", "absolute_url": "https://x.com"}
    result = normalize_greenhouse_job(raw, "acme")
    assert result.location is None
    assert result.raw_description == ""
