import unittest

from app.services.match_scorer import (
    build_match_score_breakdown,
    compute_keyword_match_score,
    extract_fallback_keywords,
)


class MatchScorerTests(unittest.TestCase):
    def test_compute_keyword_match_score_returns_missing_keywords(self) -> None:
        score, missing = compute_keyword_match_score(
            "Built Python APIs with FastAPI and PostgreSQL.",
            ["Python", "FastAPI", "OpenAI", "PostgreSQL"],
        )

        self.assertEqual(score, 75.0)
        self.assertEqual(missing, ["openai"])

    def test_extract_fallback_keywords_strips_trailing_punctuation(self) -> None:
        keywords = extract_fallback_keywords("Python, FastAPI, APIs. Python APIs.")

        self.assertIn("python", keywords)
        self.assertIn("apis", keywords)
        self.assertNotIn("apis.", keywords)

    def test_build_match_score_breakdown_returns_weighted_contributions(self) -> None:
        breakdown = build_match_score_breakdown(
            resume_text="Built Python APIs with FastAPI and PostgreSQL.",
            required_skills=["Python", "FastAPI"],
            ats_keywords=["Python", "SQL"],
            preferred_skills=["Docker"],
        )

        self.assertEqual(breakdown.total_score, 70.0)
        self.assertEqual(len(breakdown.categories), 3)
        self.assertEqual(breakdown.categories[0].contribution, 55.0)
        self.assertEqual(breakdown.categories[1].contribution, 15.0)
        self.assertEqual(breakdown.categories[2].contribution, 0.0)

    def test_build_match_score_breakdown_redistributes_empty_category_weight(self) -> None:
        breakdown = build_match_score_breakdown(
            resume_text="Built Python APIs.",
            required_skills=["Python"],
            ats_keywords=["Python", "SQL"],
            preferred_skills=[],
        )

        self.assertEqual(breakdown.total_score, 82.35)
        self.assertEqual([category.weight for category in breakdown.categories], [64.71, 35.29])


if __name__ == "__main__":
    unittest.main()
