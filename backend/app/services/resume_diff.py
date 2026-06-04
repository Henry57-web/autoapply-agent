from difflib import SequenceMatcher
import re


def build_resume_diff(original_resume: str, tailored_resume: str) -> dict:
    original_lines = original_resume.splitlines()
    tailored_lines = tailored_resume.splitlines()
    lines: list[dict[str, str]] = []

    for operation, original_start, original_end, tailored_start, tailored_end in SequenceMatcher(
        None,
        original_lines,
        tailored_lines,
    ).get_opcodes():
        if operation in {"equal", "delete", "replace"}:
            kind = "unchanged" if operation == "equal" else "removed"
            lines.extend({"kind": kind, "text": line} for line in original_lines[original_start:original_end])
        if operation in {"insert", "replace"}:
            lines.extend({"kind": "added", "text": line} for line in tailored_lines[tailored_start:tailored_end])

    return {
        "added_lines": sum(line["kind"] == "added" for line in lines),
        "removed_lines": sum(line["kind"] == "removed" for line in lines),
        "unchanged_lines": sum(line["kind"] == "unchanged" for line in lines),
        "lines": lines,
    }


def build_resume_diff_summary(
    original_resume: str,
    tailored_resume: str,
    ats_keywords: list[str] | None = None,
) -> dict:
    line_diff = build_resume_diff(original_resume, tailored_resume)
    original_lines = [line.strip() for line in original_resume.splitlines() if line.strip()]
    tailored_lines = [line.strip() for line in tailored_resume.splitlines() if line.strip()]
    original_bullets = [line for line in original_lines if _is_bullet(line)]
    tailored_bullets = [line for line in tailored_lines if _is_bullet(line)]
    removed_bullets = [line for line in original_bullets if line not in tailored_bullets]
    added_bullets = [line for line in tailored_bullets if line not in original_bullets]
    rewritten_bullets, unmatched_removed = _match_rewritten_bullets(removed_bullets, added_bullets)

    return {
        "schema_version": 2,
        "added_keywords": [
            keyword
            for keyword in ats_keywords or []
            if keyword.lower() not in original_resume.lower() and keyword.lower() in tailored_resume.lower()
        ],
        "rewritten_bullets": rewritten_bullets,
        "removed_or_weakened": unmatched_removed,
        "reordered_sections": _reordered_sections(original_lines, tailored_lines),
        "technology_changes": {
            "added": sorted(_technologies(tailored_resume) - _technologies(original_resume)),
            "removed": sorted(_technologies(original_resume) - _technologies(tailored_resume)),
        },
        "line_diff": line_diff,
    }


def _is_bullet(line: str) -> bool:
    return line.startswith(("-", "•", "*")) and bool(line.lstrip("-•* ").strip())


def _reordered_sections(original_lines: list[str], tailored_lines: list[str]) -> list[str]:
    original_sections = [line for line in original_lines if _looks_like_heading(line)]
    tailored_sections = [line for line in tailored_lines if _looks_like_heading(line)]
    shared = [line for line in original_sections if line in tailored_sections]
    tailored_shared = [line for line in tailored_sections if line in shared]
    if shared == tailored_shared:
        return []
    return [f"{line} changed position" for line in shared if shared.index(line) != tailored_shared.index(line)]


def _looks_like_heading(line: str) -> bool:
    return line.lower().strip() in {
        "education",
        "experience",
        "professional experience",
        "project experience",
        "projects",
        "skills",
        "technical skills",
        "honors & awards",
        "certifications",
        "summary",
        "professional summary",
    }


def _technologies(content: str) -> set[str]:
    known = {
        "airflow",
        "aws",
        "azure",
        "docker",
        "fastapi",
        "gcp",
        "hdfs",
        "java",
        "javascript",
        "kafka",
        "kubernetes",
        "looker",
        "mysql",
        "postgresql",
        "power bi",
        "python",
        "pytorch",
        "react",
        "spark",
        "sql",
        "tableau",
        "tensorflow",
    }
    normalized = re.sub(r"[^a-z0-9+#.]+", " ", content.lower())
    return {technology for technology in known if technology in normalized}


def _match_rewritten_bullets(
    removed_bullets: list[str],
    added_bullets: list[str],
) -> tuple[list[dict[str, str]], list[str]]:
    remaining_added = list(added_bullets)
    rewritten = []
    unmatched_removed = []
    for original in removed_bullets:
        candidates = [
            (SequenceMatcher(None, original.lower(), updated.lower()).ratio(), updated)
            for updated in remaining_added
        ]
        score, updated = max(candidates, default=(0, ""))
        if score >= 0.45:
            rewritten.append({"original": original, "new": updated})
            remaining_added.remove(updated)
        else:
            unmatched_removed.append(original)
    return rewritten, unmatched_removed
