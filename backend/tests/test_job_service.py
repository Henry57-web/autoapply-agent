import unittest
from datetime import date

from app.models import Application
from app.services.job_service import _derive_strengths, _parse_date, _sync_application_from_job_update


class JobServiceTests(unittest.TestCase):
    def test_parse_date_accepts_iso_dates(self) -> None:
        self.assertEqual(str(_parse_date("2026-06-15")), "2026-06-15")

    def test_parse_date_ignores_invalid_values(self) -> None:
        self.assertIsNone(_parse_date("next Friday"))

    def test_derive_strengths_deduplicates_matched_keywords(self) -> None:
        strengths = _derive_strengths(
            {
                "match_score_breakdown": {
                    "categories": [
                        {"matched_keywords": ["python", "sql"]},
                        {"matched_keywords": ["sql", "fastapi"]},
                    ]
                }
            }
        )

        self.assertEqual(strengths, ["python", "sql", "fastapi"])


class ApplicationSyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_syncs_job_edits_into_application_and_metadata(self) -> None:
        application = Application(
            id="application-id",
            candidate_profile_id="profile-id",
            resume_id="resume-id",
            job_description="Old description",
            company_name="Old company",
            job_title="Old title",
            analysis={"match_score": 20, "ats_keywords": ["sql"]},
        )
        application.metadata_record = None
        db = StubDb()

        await _sync_application_from_job_update(
            db,
            application,
            {
                "company": "New company",
                "title": "MLE",
                "description": "New description",
                "match_score": 88,
                "ats_keywords": ["python"],
                "missing_skills": ["kubernetes"],
                "deadline": date(2026, 6, 30),
            },
        )

        self.assertEqual(application.company_name, "New company")
        self.assertEqual(application.job_title, "MLE")
        self.assertEqual(application.job_description, "New description")
        self.assertEqual(application.analysis["match_score"], 88)
        self.assertEqual(application.analysis["ats_keywords"], ["python"])
        self.assertEqual(application.analysis["missing_keywords"], ["kubernetes"])
        self.assertEqual(db.added[0].deadline, "2026-06-30")


class StubDb:
    def __init__(self) -> None:
        self.added = []

    def add(self, record) -> None:
        self.added.append(record)


if __name__ == "__main__":
    unittest.main()
