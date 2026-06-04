import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


SALARY_PATTERN = re.compile(
    r"(?:\$|USD\s*)\d[\d,]*(?:\.\d+)?\s*(?:-|–|to)\s*(?:\$|USD\s*)?\d[\d,]*(?:\.\d+)?(?:\s*(?:per\s+(?:year|hour)|annually|yearly|/yr|/hour|/hr))?",
    re.IGNORECASE,
)
DEADLINE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


@dataclass
class ParsedJobPage:
    company: str | None = None
    title: str | None = None
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    description: str | None = None
    confidence: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def parse_job_page(html: str, parser_key: str) -> ParsedJobPage:
    soup = BeautifulSoup(html, "html.parser")
    structured = _parse_json_ld(soup)
    parser = {
        "greenhouse": _parse_greenhouse,
        "lever": _parse_lever,
        "ashby": _parse_ashby,
    }.get(parser_key, _parse_generic)
    parsed = parser(soup)
    return _merge(structured, parsed, soup)


def extract_page_text(html: str, limit: int = 30_000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return _clean_text(soup.get_text("\n", strip=True))[:limit]


def _parse_greenhouse(soup: BeautifulSoup) -> ParsedJobPage:
    return ParsedJobPage(
        company=_select_text(soup, ".company-name", ".company"),
        title=_select_text(soup, ".app-title", "h1"),
        location=_select_text(soup, ".location"),
        description=_select_text(soup, "#content", ".job__description", ".content"),
        confidence={"company": 0.85, "title": 0.95, "location": 0.9, "description": 0.9},
    )


def _parse_lever(soup: BeautifulSoup) -> ParsedJobPage:
    return ParsedJobPage(
        company=_select_text(soup, ".posting-company", ".main-header-logo"),
        title=_select_text(soup, ".posting-headline h2", "h1"),
        location=_select_text(soup, ".posting-categories .location", ".location"),
        description=_select_text(soup, ".content", ".section-wrapper"),
        confidence={"company": 0.8, "title": 0.95, "location": 0.9, "description": 0.9},
    )


def _parse_ashby(soup: BeautifulSoup) -> ParsedJobPage:
    return ParsedJobPage(
        company=_select_text(soup, "[data-testid='company-name']", ".company-name"),
        title=_select_text(soup, "h1"),
        location=_select_text(soup, "[data-testid='location']", ".location"),
        description=_select_text(soup, "[data-testid='job-description']", ".job-description", "main"),
        confidence={"company": 0.8, "title": 0.9, "location": 0.85, "description": 0.85},
    )


def _parse_generic(soup: BeautifulSoup) -> ParsedJobPage:
    title = _select_text(soup, "h1")
    meta_description = soup.find("meta", attrs={"name": "description"})
    description = _select_text(soup, "main", "article", "[role='main']")
    if not description and meta_description:
        description = str(meta_description.get("content") or "").strip()
    return ParsedJobPage(
        title=title,
        description=description,
        confidence={"title": 0.6 if title else 0, "description": 0.55 if description else 0},
    )


def _parse_json_ld(soup: BeautifulSoup) -> ParsedJobPage:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("@type") != "JobPosting":
                continue
            organization = entry.get("hiringOrganization") or {}
            location = entry.get("jobLocation") or {}
            if isinstance(location, list):
                location = location[0] if location else {}
            address = location.get("address") or {} if isinstance(location, dict) else {}
            return ParsedJobPage(
                company=organization.get("name") if isinstance(organization, dict) else None,
                title=entry.get("title"),
                location=_join_location(address),
                salary=_json_ld_salary(entry.get("baseSalary")),
                deadline=str(entry["validThrough"])[:10] if entry.get("validThrough") else None,
                description=_html_to_text(entry.get("description")),
                confidence={
                    "company": 0.98,
                    "title": 0.99,
                    "location": 0.95,
                    "salary": 0.9,
                    "deadline": 0.9,
                    "description": 0.98,
                },
            )
    return ParsedJobPage()


def _merge(primary: ParsedJobPage, secondary: ParsedJobPage, soup: BeautifulSoup) -> ParsedJobPage:
    page_text = _clean_text(soup.get_text("\n", strip=True))
    values = {}
    confidence = {}
    for name in ("company", "title", "location", "salary", "deadline", "description"):
        value = getattr(primary, name) or getattr(secondary, name)
        if name == "salary" and not value:
            match = SALARY_PATTERN.search(page_text)
            value = match.group(0) if match else None
        if name == "deadline" and not value:
            match = DEADLINE_PATTERN.search(page_text)
            value = match.group(1) if match else None
        values[name] = _clean_text(value) if value else None
        confidence[name] = primary.confidence.get(name, secondary.confidence.get(name, 0.65 if value else 0))
    return ParsedJobPage(**values, confidence=confidence, warnings=[*primary.warnings, *secondary.warnings])


def _select_text(soup: BeautifulSoup, *selectors: str) -> str | None:
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            value = _clean_text(element.get_text("\n", strip=True))
            if value:
                return value
    return None


def _html_to_text(value: str | None) -> str | None:
    return _clean_text(BeautifulSoup(value or "", "html.parser").get_text("\n", strip=True)) or None


def _clean_text(value: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", value)).strip()


def _join_location(address: dict) -> str | None:
    values = [address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")]
    return ", ".join(str(value) for value in values if value) or None


def _json_ld_salary(value) -> str | None:
    if not isinstance(value, dict):
        return None
    currency = value.get("currency", "")
    inner = value.get("value") or {}
    if not isinstance(inner, dict):
        return None
    minimum, maximum = inner.get("minValue"), inner.get("maxValue")
    unit = inner.get("unitText")
    if minimum is None or maximum is None:
        return None
    return " ".join(part for part in (currency, f"{minimum}-{maximum}", unit) if part)
