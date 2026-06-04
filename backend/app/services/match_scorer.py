import re
from dataclasses import dataclass


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}")
DEFAULT_CATEGORY_WEIGHTS = {
    "required_skills": 0.55,
    "ats_keywords": 0.30,
    "preferred_skills": 0.15,
}


@dataclass(frozen=True)
class ScoreCategory:
    key: str
    label: str
    weight: float
    score: float
    contribution: float
    matched_keywords: list[str]
    missing_keywords: list[str]

    @property
    def matched_count(self) -> int:
        return len(self.matched_keywords)

    @property
    def total_count(self) -> int:
        return self.matched_count + len(self.missing_keywords)


@dataclass(frozen=True)
class MatchScoreBreakdown:
    total_score: float
    categories: list[ScoreCategory]
    explanation: str


def normalize_keyword(value: str) -> str:
    cleaned = value.strip().lower().strip(".,;:()[]{}")
    return re.sub(r"\s+", " ", cleaned)


def compute_keyword_match_score(resume_text: str, keywords: list[str]) -> tuple[float, list[str]]:
    matched, missing = classify_keywords(resume_text, keywords)
    if not matched and not missing:
        return 0.0, []
    score = round((len(matched) / (len(matched) + len(missing))) * 100, 2)
    return score, missing


def classify_keywords(resume_text: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    normalized_resume = resume_text.lower()
    unique_keywords = sorted({normalize_keyword(keyword) for keyword in keywords if keyword.strip()})
    matched = [keyword for keyword in unique_keywords if keyword_is_present(normalized_resume, keyword)]
    missing = [keyword for keyword in unique_keywords if not keyword_is_present(normalized_resume, keyword)]
    return matched, missing


def keyword_is_present(normalized_resume: str, keyword: str) -> bool:
    pattern = rf"(?<![a-zA-Z0-9]){re.escape(keyword)}(?![a-zA-Z0-9])"
    return re.search(pattern, normalized_resume) is not None


def build_match_score_breakdown(
    resume_text: str,
    required_skills: list[str],
    preferred_skills: list[str],
    ats_keywords: list[str],
) -> MatchScoreBreakdown:
    category_inputs = [
        ("required_skills", "Required skills", required_skills),
        ("ats_keywords", "ATS keywords", ats_keywords),
        ("preferred_skills", "Preferred skills", preferred_skills),
    ]
    populated_categories = [
        (key, label, keywords)
        for key, label, keywords in category_inputs
        if {normalize_keyword(keyword) for keyword in keywords if keyword.strip()}
    ]
    active_weight_total = sum(DEFAULT_CATEGORY_WEIGHTS[key] for key, _, _ in populated_categories)

    if not active_weight_total:
        return MatchScoreBreakdown(
            total_score=0.0,
            categories=[],
            explanation="No scorable skills or ATS keywords were extracted from the job description.",
        )

    categories = []
    unrounded_total_score = 0.0
    for key, label, keywords in populated_categories:
        matched, missing = classify_keywords(resume_text, keywords)
        total_count = len(matched) + len(missing)
        category_score = round((len(matched) / total_count) * 100, 2)
        normalized_weight = DEFAULT_CATEGORY_WEIGHTS[key] / active_weight_total
        unrounded_total_score += category_score * normalized_weight
        contribution = round(category_score * normalized_weight, 2)
        categories.append(
            ScoreCategory(
                key=key,
                label=label,
                weight=round(normalized_weight * 100, 2),
                score=category_score,
                contribution=contribution,
                matched_keywords=matched,
                missing_keywords=missing,
            )
        )

    total_score = round(unrounded_total_score, 2)
    explanation = (
        "Weighted score based on keyword evidence found in the uploaded base resume. "
        "Each category score is matched keywords divided by extracted keywords. "
        "Weights are redistributed proportionally when a category is empty."
    )
    return MatchScoreBreakdown(total_score=total_score, categories=categories, explanation=explanation)


def extract_fallback_keywords(job_description: str, limit: int = 30) -> list[str]:
    stop_words = {
        "and",
        "are",
        "for",
        "the",
        "with",
        "you",
        "our",
        "will",
        "that",
        "this",
        "from",
        "have",
        "your",
        "work",
        "team",
        "role",
    }
    tokens = [normalize_keyword(token) for token in TOKEN_PATTERN.findall(job_description)]
    counts: dict[str, int] = {}
    for token in tokens:
        if token in stop_words or len(token) < 3:
            continue
        counts[token] = counts.get(token, 0) + 1
    return [keyword for keyword, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]
