from app.schemas.emails import EmailType


KEYWORDS: list[tuple[EmailType, tuple[str, ...]]] = [
    ("OFFER", ("offer", "congratulations", "pleased to offer")),
    ("REJECTION", ("unfortunately", "not move forward", "not moving forward", "other candidates")),
    ("INTERVIEW_INVITATION", ("interview", "meet with", "schedule a call", "technical screen")),
    ("INTERVIEW_REMINDER", ("interview reminder", "reminder for your interview")),
    ("OA_INVITATION", ("online assessment", "coding assessment", "hackerrank", "codesignal", "oa invitation")),
    ("OA_REMINDER", ("assessment reminder", "complete your assessment", "reminder to complete")),
    ("APPLICATION_CONFIRMATION", ("application received", "thank you for applying", "we received your application")),
    ("RECRUITER_OUTREACH", ("recruiter", "sourcer", "opportunity", "would like to connect")),
]


def classify_email(subject: str | None, sender: str | None, snippet: str | None, body_text: str | None = None) -> EmailType:
    haystack = " ".join(part or "" for part in (subject, sender, snippet, body_text)).lower()
    for email_type, keywords in KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            if email_type == "INTERVIEW_INVITATION" and "reminder" in haystack:
                return "INTERVIEW_REMINDER"
            if email_type == "OA_INVITATION" and "reminder" in haystack:
                return "OA_REMINDER"
            return email_type
    return "OTHER"
