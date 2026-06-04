import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.job_import import router
from app.schemas.job_import import JobImportConfidence, JobImportResult
from app.services.job_import.fetcher import JobPageFetchError, _validate_public_url
from app.services.job_import.parsers import parse_job_page
from app.services.job_import.source_detector import detect_job_source


GREENHOUSE_HTML = """
<html><body>
  <div class="company-name">Acme AI</div>
  <h1 class="app-title">Machine Learning Engineer</h1>
  <div class="location">New York, NY</div>
  <div id="content">Build production AI systems and agent workflows with Python, FastAPI, and model evaluation. Partner with engineering teams to ship reliable services.</div>
</body></html>
"""
LEVER_HTML = """
<html><body>
  <div class="posting-company">Data Works</div>
  <div class="posting-headline"><h2>Data Engineer</h2></div>
  <div class="posting-categories"><span class="location">Remote - US</span></div>
  <div class="content">Design batch and streaming pipelines using SQL, Python, and cloud data warehouses. Maintain reliable datasets for analytics users.</div>
</body></html>
"""
ASHBY_HTML = """
<html><body>
  <div data-testid="company-name">Agent Labs</div>
  <h1>AI Product Manager</h1>
  <div data-testid="location">San Francisco, CA</div>
  <div data-testid="job-description">Lead AI agent product strategy, partner with engineering, and define evaluation metrics for reliable customer-facing workflows.</div>
</body></html>
"""


class SourceDetectorTests(unittest.TestCase):
    def test_detects_supported_platforms(self) -> None:
        self.assertEqual(detect_job_source("https://boards.greenhouse.io/acme/jobs/1").name, "Greenhouse")
        self.assertEqual(detect_job_source("https://jobs.lever.co/acme/1").name, "Lever")
        self.assertEqual(detect_job_source("https://jobs.ashbyhq.com/acme/1").name, "Ashby")
        self.assertEqual(detect_job_source("https://acme.wd5.myworkdayjobs.com/en-US/jobs/1").name, "Workday")

    def test_marks_login_prone_platforms_as_unsupported(self) -> None:
        self.assertFalse(detect_job_source("https://www.linkedin.com/jobs/view/1").import_supported)
        self.assertFalse(detect_job_source("https://app.joinhandshake.com/jobs/1").import_supported)


class PlatformParserTests(unittest.TestCase):
    def test_parses_greenhouse_html(self) -> None:
        parsed = parse_job_page(GREENHOUSE_HTML, "greenhouse")
        self.assertEqual(parsed.company, "Acme AI")
        self.assertEqual(parsed.title, "Machine Learning Engineer")
        self.assertEqual(parsed.location, "New York, NY")
        self.assertIn("production AI systems", parsed.description or "")

    def test_parses_lever_html(self) -> None:
        parsed = parse_job_page(LEVER_HTML, "lever")
        self.assertEqual(parsed.company, "Data Works")
        self.assertEqual(parsed.title, "Data Engineer")
        self.assertEqual(parsed.location, "Remote - US")

    def test_parses_ashby_html(self) -> None:
        parsed = parse_job_page(ASHBY_HTML, "ashby")
        self.assertEqual(parsed.company, "Agent Labs")
        self.assertEqual(parsed.title, "AI Product Manager")
        self.assertEqual(parsed.location, "San Francisco, CA")

    def test_json_ld_allows_missing_deadline(self) -> None:
        parsed = parse_job_page(
            '<script type="application/ld+json">'
            '{"@type":"JobPosting","title":"MLE","description":"Build reliable machine learning services '
            'and evaluation systems for customer-facing AI products.","hiringOrganization":{"name":"Acme"}}'
            "</script>",
            "generic",
        )

        self.assertIsNone(parsed.deadline)


class FetcherSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_private_network_url(self) -> None:
        with self.assertRaises(JobPageFetchError):
            await _validate_public_url("http://localhost/jobs/1")

    async def test_rejects_embedded_credentials(self) -> None:
        with self.assertRaises(JobPageFetchError):
            await _validate_public_url("https://user:password@example.com/jobs/1")

    async def test_rejects_nonstandard_port(self) -> None:
        with self.assertRaises(JobPageFetchError):
            await _validate_public_url("https://example.com:8080/jobs/1")


class JobImportApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        self.client = TestClient(app)

    @patch("app.api.routes.job_import.JobImportService")
    def test_import_url_returns_structured_fields(self, service_class) -> None:
        service_class.return_value.import_url = AsyncMock(
            return_value=JobImportResult(
                source="Greenhouse",
                company="Acme AI",
                title="MLE",
                location="New York, NY",
                description="Build reliable production machine learning systems with Python and model evaluation tooling.",
                confidence=JobImportConfidence(
                    company=0.95,
                    title=0.98,
                    location=0.9,
                    salary=0,
                    deadline=0,
                    description=0.95,
                ),
                warnings=["Salary not found", "Deadline not found"],
                raw_url="https://boards.greenhouse.io/acme/jobs/1",
            )
        )

        response = self.client.post("/api/v1/job-import/url", json={"url": "https://boards.greenhouse.io/acme/jobs/1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "Greenhouse")
        self.assertEqual(response.json()["company"], "Acme AI")

    def test_import_url_rejects_invalid_url(self) -> None:
        response = self.client.post("/api/v1/job-import/url", json={"url": "not-a-url"})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
