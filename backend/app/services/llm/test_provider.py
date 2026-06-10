from typing import Any


class TestProvider:
    async def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        if "cover_letter" in system_prompt:
            return {"cover_letter": "Test cover letter for the target role."}
        if "ats_optimized_resume" in system_prompt:
            resume = str(user_payload.get("resume") or "")
            return {
                "headline": "Test Target Role",
                "summary": "Test summary grounded in the supplied profile.",
                "rewritten_bullets": ["Built reliable test systems with Python."],
                "ats_optimized_resume": resume or "Test Resume",
            }
        return {
            "job_title": "Test Role",
            "company_name": "Test Company",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["FastAPI"],
            "responsibilities": ["Build reliable systems"],
            "ats_keywords": ["Python", "SQL", "FastAPI"],
            "missing_keywords": [],
            "match_score": 0,
            "match_summary": "Deterministic test provider response.",
        }
