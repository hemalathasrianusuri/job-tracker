from bs4 import BeautifulSoup


def strip_html(html: str) -> str:
    """Converts job-posting HTML (from Greenhouse/Lever content fields or a
    pasted URL's page source) into clean plain text for the AI JD analyzer.
    Deliberately simple — the analyzer is tolerant of imperfect formatting,
    so this doesn't need to preserve structure, just strip markup noise."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_title(html: str) -> str | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else None
