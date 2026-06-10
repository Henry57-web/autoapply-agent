from difflib import SequenceMatcher

from app.models import Job


def match_email_to_job(
    jobs: list[Job],
    *,
    subject: str | None,
    sender: str | None,
    snippet: str | None,
    body_text: str | None = None,
) -> tuple[Job | None, float, str]:
    haystack = " ".join(part or "" for part in (subject, sender, snippet, body_text)).lower()
    best: tuple[Job | None, float, str] = (None, 0, "No match")
    for job in jobs:
        score = 0.0
        reasons: list[str] = []
        company = (job.company or "").strip().lower()
        title = (job.title or "").strip().lower()
        if company and company in haystack:
            score += 0.58
            reasons.append("company")
        if title and title in haystack:
            score += 0.46
            reasons.append("title")
        if company:
            score += 0.08 * SequenceMatcher(None, company, haystack[:120]).ratio()
        if title:
            score += 0.08 * SequenceMatcher(None, title, haystack[:160]).ratio()
        if score > best[1]:
            best = (job, min(score, 1.0), ", ".join(reasons) or "fuzzy")
    if best[1] < 0.45:
        return None, best[1], "Below matching threshold"
    return best
