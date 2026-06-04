from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class JobSource:
    name: str
    parser_key: str
    import_supported: bool = True
    warning: str | None = None


def detect_job_source(url: str) -> JobSource:
    hostname = (urlparse(url).hostname or "").lower()
    if "greenhouse.io" in hostname:
        return JobSource("Greenhouse", "greenhouse")
    if "lever.co" in hostname:
        return JobSource("Lever", "lever")
    if "ashbyhq.com" in hostname:
        return JobSource("Ashby", "ashby")
    if "myworkdayjobs.com" in hostname or "workday.com" in hostname:
        return JobSource("Workday", "generic", warning="Workday import is best-effort. Review all fields.")
    if "linkedin.com" in hostname:
        return JobSource(
            "LinkedIn",
            "generic",
            import_supported=False,
            warning="LinkedIn may require login. Please paste the job description manually.",
        )
    if "joinhandshake.com" in hostname or "handshake.com" in hostname:
        return JobSource(
            "Handshake",
            "generic",
            import_supported=False,
            warning="Handshake may require login. Please paste the job description manually.",
        )
    if "simplify.jobs" in hostname:
        return JobSource("Simplify", "generic")
    if hostname:
        return JobSource("Company Career Page", "generic")
    return JobSource("Unknown", "generic")
