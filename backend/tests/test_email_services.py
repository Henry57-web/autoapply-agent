import unittest

from app.models import Job
from app.services.email_classifier import classify_email
from app.services.email_matcher import match_email_to_job
from app.services.gmail_client import GMAIL_READONLY_SCOPE, GmailClient


class EmailClassifierTests(unittest.TestCase):
    def test_classifies_application_confirmation(self) -> None:
        self.assertEqual(
            classify_email("Application received", "jobs@example.com", "Thank you for applying. We received your application."),
            "APPLICATION_CONFIRMATION",
        )

    def test_classifies_online_assessment(self) -> None:
        self.assertEqual(
            classify_email("Datadog Online Assessment", "careers@datadog.com", "Please complete your coding assessment."),
            "OA_INVITATION",
        )

    def test_classifies_interview_invitation(self) -> None:
        self.assertEqual(classify_email("Interview invitation", "recruiting@acme.com", "Schedule a technical interview."), "INTERVIEW_INVITATION")

    def test_classifies_rejection_offer_and_recruiter(self) -> None:
        self.assertEqual(classify_email("Application update", "jobs@acme.com", "Unfortunately we will not move forward."), "REJECTION")
        self.assertEqual(classify_email("Offer", "hr@acme.com", "We are pleased to offer you the role."), "OFFER")
        self.assertEqual(classify_email("New opportunity", "recruiter@acme.com", "I am a recruiter reaching out."), "RECRUITER_OUTREACH")


class EmailMatcherTests(unittest.TestCase):
    def test_matches_existing_job_by_company(self) -> None:
        jobs = [
            Job(id="job-1", company="Datadog", title="Data Engineer Intern", description=""),
            Job(id="job-2", company="Acme AI", title="Machine Learning Engineer", description=""),
        ]

        job, confidence, reason = match_email_to_job(
            jobs,
            subject="Datadog Online Assessment for Data Engineer Intern",
            sender="careers@datadog.com",
            snippet="Your Datadog application has moved to the assessment stage.",
        )

        self.assertEqual(job.id, "job-1")
        self.assertGreaterEqual(confidence, 0.45)
        self.assertIn("company", reason)

    def test_matches_existing_job_by_title(self) -> None:
        jobs = [
            Job(id="job-1", company="Unknown", title="Product Manager Intern", description=""),
            Job(id="job-2", company="Another Co", title="Machine Learning Engineer", description=""),
        ]

        job, confidence, reason = match_email_to_job(
            jobs,
            subject="Machine Learning Engineer interview request",
            sender="recruiting@example.com",
            snippet="We would like to schedule your machine learning engineer interview.",
        )

        self.assertEqual(job.id, "job-2")
        self.assertGreaterEqual(confidence, 0.45)
        self.assertIn("title", reason)

    def test_returns_none_for_low_confidence_match(self) -> None:
        jobs = [Job(id="job-1", company="Datadog", title="Data Engineer Intern", description="")]

        job, confidence, _ = match_email_to_job(jobs, subject="Welcome newsletter", sender="hello@example.com", snippet="Weekly news")

        self.assertIsNone(job)
        self.assertLess(confidence, 0.45)


class GmailClientTests(unittest.TestCase):
    def test_authorization_url_uses_readonly_scope_and_state(self) -> None:
        client = GmailClient(client_id="client", client_secret="secret", redirect_uri="http://localhost/callback")

        url = client.authorization_url("state-123")

        self.assertIn("state=state-123", url)
        self.assertIn(GMAIL_READONLY_SCOPE.replace(":", "%3A").replace("/", "%2F"), url)
        self.assertIn("access_type=offline", url)


if __name__ == "__main__":
    unittest.main()
