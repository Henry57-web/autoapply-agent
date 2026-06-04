import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.api.routes.resume_versions import router
from app.db.session import get_db_session
from app.models import ResumeVersion
from app.schemas.mvp import JobAnalysis, MatchScoreBreakdown, TailoredResume
from app.services.resume_diff import build_resume_diff_summary
from app.services.resume_version_service import build_resume_version_download, delete_resume_version
from app.services.tailoring_service import TailoringService


NOW = datetime.now(timezone.utc)


def make_version(*, is_base: bool = False) -> ResumeVersion:
    return ResumeVersion(
        id="version-id",
        resume_id="resume-id",
        job_id="job-id",
        title="Haoyang Lin Data Engineer Resume",
        name="Haoyang Lin Data Engineer Resume",
        role_type="DATA_ENGINEER",
        version_number=3,
        is_base=is_base,
        company="Datadog",
        job_title="Data Engineer",
        content="Haoyang Lin\n\nSkills\n- Python\n- Spark",
        content_json={},
        diff_summary={"added_keywords": ["Spark"]},
        created_from="BASE_UPLOAD" if is_base else "TAILORING_RESULT",
        ats_keywords=["Python", "Spark"],
        match_score=88,
        created_at=NOW,
        updated_at=NOW,
    )


class ResumeDiffSummaryTests(unittest.TestCase):
    def test_persists_added_keyword_and_rewritten_bullet_summary(self) -> None:
        summary = build_resume_diff_summary(
            "Skills\n- Python\nExperience\n- Built APIs",
            "Skills\n- Python\n- Spark\nExperience\n- Built reliable data APIs",
            ["Python", "Spark"],
        )

        self.assertEqual(summary["added_keywords"], ["Spark"])
        self.assertEqual(summary["rewritten_bullets"][0]["original"], "- Built APIs")
        self.assertEqual(summary["rewritten_bullets"][0]["new"], "- Built reliable data APIs")
        self.assertIn("line_diff", summary)


class ResumeDownloadTests(unittest.TestCase):
    def test_download_txt_md_and_pdf(self) -> None:
        version = make_version()
        txt, txt_name, txt_type = build_resume_version_download(version, "txt")
        md, md_name, md_type = build_resume_version_download(version, "md")
        pdf, pdf_name, pdf_type = build_resume_version_download(version, "pdf")

        self.assertIn("Python", txt.getvalue().decode("utf-8"))
        self.assertTrue(txt_name.endswith(".txt"))
        self.assertEqual(txt_type, "text/plain; charset=utf-8")
        self.assertTrue(md.getvalue().decode("utf-8").startswith("# Haoyang Lin"))
        self.assertTrue(md_name.endswith(".md"))
        self.assertEqual(md_type, "text/markdown; charset=utf-8")
        self.assertTrue(pdf_name.endswith(".pdf"))
        self.assertEqual(pdf_type, "application/pdf")
        self.assertIn("Spark", PdfReader(pdf).pages[0].extract_text())


class ResumeDeleteTests(unittest.IsolatedAsyncioTestCase):
    async def test_base_resume_version_cannot_be_deleted(self) -> None:
        with self.assertRaisesRegex(Exception, "Base resume versions cannot be deleted"):
            await delete_resume_version(AsyncMock(), make_version(is_base=True))

    async def test_non_base_resume_version_can_be_deleted(self) -> None:
        db = AsyncMock()
        version = make_version()

        await delete_resume_version(db, version)

        db.delete.assert_awaited_once_with(version)
        db.commit.assert_awaited_once()


class ResumeVersionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def fake_session():
            yield AsyncMock()

        app.dependency_overrides[get_db_session] = fake_session
        self.client = TestClient(app)

    @patch("app.api.routes.resume_versions.list_resume_versions", new_callable=AsyncMock)
    def test_list_resume_versions(self, list_versions: AsyncMock) -> None:
        list_versions.return_value = [make_version()]

        response = self.client.get("/api/v1/resume-versions")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Haoyang Lin Data Engineer Resume")

    @patch("app.api.routes.resume_versions.get_resume_version", new_callable=AsyncMock)
    def test_resume_version_detail(self, get_version: AsyncMock) -> None:
        get_version.return_value = make_version()

        response = self.client.get("/api/v1/resume-versions/version-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], "job-id")
        self.assertEqual(response.json()["diff_summary"]["added_keywords"], ["Spark"])

    @patch("app.api.routes.resume_versions.get_resume_version", new_callable=AsyncMock)
    def test_download_resume_version_pdf(self, get_version: AsyncMock) -> None:
        get_version.return_value = make_version()

        response = self.client.get("/api/v1/resume-versions/version-id/download?format=pdf")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


class TailoringWorkflowVersionTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.services.tailoring_service.create_job_for_application", new_callable=AsyncMock)
    @patch("app.services.tailoring_service.create_tailored_resume_version", new_callable=AsyncMock)
    @patch("app.services.tailoring_service.create_base_resume_version", new_callable=AsyncMock)
    async def test_generate_creates_version_and_links_it_to_job(
        self,
        create_base: AsyncMock,
        create_tailored: AsyncMock,
        create_job: AsyncMock,
    ) -> None:
        service = TailoringService.__new__(TailoringService)
        service.analyze_job = AsyncMock(
            return_value=JobAnalysis(
                job_title="MLE",
                company_name="Acme",
                match_score=75,
                match_score_breakdown=MatchScoreBreakdown(total_score=75, explanation="Good match"),
                match_summary="Good match",
            )
        )
        service.generate_tailored_resume = AsyncMock(
            return_value=TailoredResume(
                headline="MLE",
                summary="Good match",
                rewritten_bullets=["Built reliable APIs"],
                ats_optimized_resume="Haoyang Lin\n\nSkills\n- Python",
            )
        )
        service.generate_cover_letter = AsyncMock(return_value="Dear Hiring Manager")
        version = SimpleNamespace(id="version-id", job_id=None)
        create_tailored.return_value = version
        create_job.return_value = SimpleNamespace(id="job-id")
        resume = SimpleNamespace(id="resume-id", file_name="resume.txt", raw_text="Haoyang Lin")
        profile = SimpleNamespace(id="profile-id", file_name="profile.txt", raw_text="Profile")
        db = FakeWorkflowDb(profile, resume)

        result = await service.run_mvp_workflow(
            db,
            "profile.txt",
            "Profile",
            "resume.txt",
            "Resume",
            "Job description",
            candidate_profile_id="profile-id",
            resume_id="resume-id",
        )

        create_base.assert_awaited_once_with(db, resume)
        create_tailored.assert_awaited_once()
        self.assertEqual(version.job_id, "job-id")
        self.assertEqual(result.resume_version_id, "version-id")


class FakeWorkflowDb:
    def __init__(self, profile, resume) -> None:
        self.records = {"profile-id": profile, "resume-id": resume}
        self.added = []

    async def get(self, _, record_id):
        return self.records.get(record_id)

    def add(self, record) -> None:
        self.added.append(record)

    async def flush(self) -> None:
        for record in self.added:
            if not getattr(record, "id", None):
                record.id = f"{record.__class__.__name__.lower()}-id"

    async def commit(self) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
