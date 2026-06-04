import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.session import get_db_session
from app.main import app
from app.models import Application, CandidateProfile, Job, JobStatusEvent, Resume, ResumeVersion
from app.schemas.mvp import JobAnalysis, MatchScoreBreakdown, TailoredResume
from app.services.job_import.fetcher import JobPageFetchError
from app.services.legacy_backfill import run_legacy_backfill


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
MOCK_IMPORTS = [
    (
        "https://boards.greenhouse.io/acme/jobs/1",
        '<div class="company-name">Acme AI</div><h1 class="app-title">MLE</h1>'
        '<div class="location">New York, NY</div><div id="content">'
        "Build production AI systems with Python, FastAPI, evaluation tooling, observability, "
        "and reliable deployment practices for customer-facing products.</div>",
        "Greenhouse",
    ),
    (
        "https://jobs.lever.co/dataworks/1",
        '<div class="posting-company">Data Works</div><div class="posting-headline"><h2>Data Engineer</h2></div>'
        '<div class="posting-categories"><span class="location">Remote</span></div><div class="content">'
        "Design batch and streaming pipelines with Python, SQL, Airflow, monitoring, and cloud "
        "warehouses while partnering with analytics teams.</div>",
        "Lever",
    ),
    (
        "https://jobs.ashbyhq.com/agentlabs/1",
        '<div data-testid="company-name">Agent Labs</div><h1>AI Product Manager</h1>'
        '<div data-testid="location">San Francisco, CA</div><div data-testid="job-description">'
        "Lead AI agent product strategy, define evaluation metrics, and partner with engineering "
        "to ship reliable workflows for customers.</div>",
        "Ashby",
    ),
]
TABLES = [
    "job_status_events",
    "application_metadata",
    "application_statuses",
    "jobs",
    "applications",
    "resume_versions",
    "candidate_profiles",
    "resumes",
]


@unittest.skipUnless(TEST_DATABASE_URL, "Set TEST_DATABASE_URL to run PostgreSQL integration tests.")
class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        cls.sessions = async_sessionmaker(cls.engine, expire_on_commit=False)

        async def test_session():
            async with cls.sessions() as session:
                yield session

        app.dependency_overrides[get_db_session] = test_session
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.pop(get_db_session, None)
        cls.client.close()
        asyncio.run(cls.engine.dispose())

    def setUp(self) -> None:
        asyncio.run(self._truncate())

    async def _truncate(self) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))

    async def _seed_resume(self) -> Resume:
        async with self.sessions() as db:
            resume = Resume(file_name="base.txt", raw_text="Haoyang Lin\nSkills\n- Python\n- SQL")
            db.add(resume)
            await db.commit()
            await db.refresh(resume)
            return resume

    def _create_job(self, company: str = "Acme", title: str = "MLE") -> dict:
        response = self.client.post(
            "/api/v1/jobs",
            json={"company": company, "title": title, "description": "Build reliable production AI systems."},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_generate_flow_persists_job_resume_version_and_application_links(self) -> None:
        analysis = JobAnalysis(
            job_title="Machine Learning Engineer",
            company_name="Acme AI",
            ats_keywords=["Python", "FastAPI"],
            missing_keywords=["Kubernetes"],
            match_score=82,
            match_score_breakdown=MatchScoreBreakdown(total_score=82, explanation="Strong match"),
            match_summary="Strong match",
        )
        tailored = TailoredResume(
            headline="Machine Learning Engineer",
            summary="Production-focused engineer",
            rewritten_bullets=["Built reliable AI APIs"],
            ats_optimized_resume="Haoyang Lin\nSkills\n- Python\n- FastAPI",
        )
        with (
            patch("app.services.tailoring_service.TailoringService.analyze_job", AsyncMock(return_value=analysis)),
            patch(
                "app.services.tailoring_service.TailoringService.generate_tailored_resume",
                AsyncMock(return_value=tailored),
            ),
            patch(
                "app.services.tailoring_service.TailoringService.generate_cover_letter",
                AsyncMock(return_value="Dear Hiring Manager"),
            ),
        ):
            response = self.client.post(
                "/api/v1/mvp/run",
                data={
                    "job_description": "Build reliable production machine learning APIs with Python, FastAPI, "
                    "model evaluation, observability, cloud infrastructure, and cross-functional collaboration.",
                    "company": "Acme AI",
                    "title": "Machine Learning Engineer",
                },
                files={
                    "candidate_profile": ("profile.txt", b"MLE candidate with production AI experience"),
                    "resume": ("resume.txt", b"Haoyang Lin\nSkills\n- Python\n- SQL"),
                },
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["job_id"])
        self.assertTrue(payload["resume_version_id"])
        asyncio.run(self._assert_generate_links(payload))

    async def _assert_generate_links(self, payload: dict) -> None:
        async with self.sessions() as db:
            application = await db.get(Application, payload["application_id"])
            job = await db.get(Job, payload["job_id"])
            version = await db.get(ResumeVersion, payload["resume_version_id"])
            self.assertEqual(application.resume_version_id, version.id)
            self.assertEqual(job.application_id, application.id)
            self.assertEqual(version.job_id, job.id)
            self.assertFalse(version.is_base)

    def test_job_crud_status_events_and_milestones(self) -> None:
        job = self._create_job()
        job_id = job["id"]
        self.assertEqual(self.client.get("/api/v1/jobs").status_code, 200)
        detail = self.client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(detail.status_code, 200)
        updated = self.client.patch(
            f"/api/v1/jobs/{job_id}",
            json={"company": "Acme Labs", "match_score": 91, "ats_keywords": ["Python"]},
        )
        self.assertEqual(updated.json()["company"], "Acme Labs")
        for next_status, timestamp in [
            ("APPLIED", "applied_at"),
            ("OA_RECEIVED", "oa_received_at"),
            ("INTERVIEW", "interview_at"),
            ("OFFER", "offer_at"),
        ]:
            response = self.client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": next_status})
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.json()[timestamp])
        asyncio.run(self._assert_status_events(job_id, expected=5))
        self.assertEqual(self.client.delete(f"/api/v1/jobs/{job_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/jobs/{job_id}").status_code, 404)

    async def _assert_status_events(self, job_id: str, expected: int) -> None:
        async with self.sessions() as db:
            events = list(await db.scalars(select(JobStatusEvent).where(JobStatusEvent.job_id == job_id)))
            self.assertEqual(len(events), expected)

    def test_dashboard_aggregates_pipeline(self) -> None:
        jobs = [self._create_job(title=f"Role {index}") for index in range(6)]
        statuses = ["APPLIED", "OA_RECEIVED", "INTERVIEW", "OFFER", "REJECTED"]
        scores = [40, 50, 60, 70, 80, 90]
        for job, score in zip(jobs, scores):
            self.client.patch(f"/api/v1/jobs/{job['id']}", json={"match_score": score})
        for job, status_name in zip(jobs, statuses):
            self.client.patch(f"/api/v1/jobs/{job['id']}/status", json={"status": status_name})
        dashboard = self.client.get("/api/v1/dashboard").json()
        self.assertEqual(dashboard["total_jobs"], 6)
        self.assertEqual(dashboard["applied"], 1)
        self.assertEqual(dashboard["oa"], 1)
        self.assertEqual(dashboard["interviews"], 1)
        self.assertEqual(dashboard["offers"], 1)
        self.assertEqual(dashboard["rejected"], 1)
        self.assertEqual(dashboard["average_match_score"], 65)
        self.assertEqual(dashboard["highest_match_score"], 90)

    def test_resume_version_crud_downloads_and_base_protection(self) -> None:
        resume = asyncio.run(self._seed_resume())
        base = self.client.post(
            "/api/v1/resume-versions",
            json={
                "source_resume_id": resume.id,
                "name": "Base Resume",
                "is_base": True,
                "content_text": resume.raw_text,
                "created_from": "BASE_UPLOAD",
            },
        ).json()
        tailored = self.client.post(
            "/api/v1/resume-versions",
            json={
                "source_resume_id": resume.id,
                "name": "Acme MLE Resume",
                "company": "Acme",
                "job_title": "MLE",
                "content_text": f"{resume.raw_text}\n- FastAPI",
            },
        ).json()
        self.assertEqual(len(self.client.get("/api/v1/resume-versions").json()), 2)
        self.assertEqual(self.client.get(f"/api/v1/resume-versions/{tailored['id']}").status_code, 200)
        for file_format in ("txt", "md", "pdf"):
            response = self.client.get(f"/api/v1/resume-versions/{tailored['id']}/download?format={file_format}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content)
        self.assertEqual(self.client.delete(f"/api/v1/resume-versions/{base['id']}").status_code, 409)
        self.assertEqual(self.client.delete(f"/api/v1/resume-versions/{tailored['id']}").status_code, 204)

    def test_job_import_rejects_login_sources_and_unsafe_urls(self) -> None:
        login = self.client.post(
            "/api/v1/job-import/url",
            json={"url": "https://www.linkedin.com/jobs/view/123"},
        )
        self.assertEqual(login.status_code, 422)
        self.assertIn("paste the job description manually", login.json()["detail"].lower())
        with patch(
            "app.services.job_import.service.fetch_job_page",
            AsyncMock(side_effect=JobPageFetchError("Blocked unsafe URL.")),
        ):
            unsafe = self.client.post(
                "/api/v1/job-import/url",
                json={"url": "https://example.com/private"},
            )
        self.assertEqual(unsafe.status_code, 422)
        self.assertIn("paste the job description manually", unsafe.json()["detail"].lower())

    def test_job_import_parses_supported_platform_mock_html(self) -> None:
        for url, html, source in MOCK_IMPORTS:
            with self.subTest(source=source), patch(
                "app.services.job_import.service.fetch_job_page",
                AsyncMock(return_value=html),
            ):
                response = self.client.post("/api/v1/job-import/url", json={"url": url})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["source"], source)
            self.assertTrue(response.json()["description"])

    def test_legacy_backfill_is_idempotent(self) -> None:
        first, second = asyncio.run(self._run_legacy_backfill_twice())
        self.assertEqual(first.jobs_created, 1)
        self.assertEqual(first.resume_versions_created, 2)
        self.assertEqual(second.jobs_created, 0)
        self.assertEqual(second.resume_versions_created, 0)
        self.assertGreaterEqual(second.skipped_existing, 3)

    async def _run_legacy_backfill_twice(self):
        async with self.sessions() as db:
            profile = CandidateProfile(file_name="profile.txt", raw_text="MLE profile")
            resume = Resume(file_name="resume.txt", raw_text="Skills\n- Python")
            db.add_all([profile, resume])
            await db.flush()
            db.add(
                Application(
                    candidate_profile_id=profile.id,
                    resume_id=resume.id,
                    job_description="Build reliable machine learning systems.",
                    job_title="MLE",
                    company_name="Legacy AI",
                    analysis={
                        "match_score": 74,
                        "ats_keywords": ["Python"],
                        "tailored_resume": {
                            "headline": "MLE",
                            "summary": "Relevant experience",
                            "rewritten_bullets": ["Built APIs"],
                            "ats_optimized_resume": "Skills\n- Python\n- FastAPI",
                        },
                    },
                )
            )
            await db.commit()
        async with self.sessions() as db:
            first = await run_legacy_backfill(db)
        async with self.sessions() as db:
            second = await run_legacy_backfill(db)
        return first, second


if __name__ == "__main__":
    unittest.main()
