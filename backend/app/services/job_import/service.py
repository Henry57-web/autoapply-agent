from dataclasses import asdict

from app.core.config import get_settings
from app.schemas.job_import import JobImportConfidence, JobImportResult, LLMJobPageExtraction
from app.services.job_import.fetcher import JobPageFetchError, fetch_job_page
from app.services.job_import.parsers import ParsedJobPage, extract_page_text, parse_job_page
from app.services.job_import.source_detector import detect_job_source
from app.services.llm import LLMServiceUnavailable, create_llm_provider
from app.services.prompt_registry import load_prompt


DEFAULT_ERROR = "This page could not be imported. Please paste the job description manually."


class JobImportError(RuntimeError):
    def __init__(self, message: str = DEFAULT_ERROR, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


class JobImportService:
    def __init__(self) -> None:
        self.ai = create_llm_provider(get_settings())

    async def import_url(self, url: str) -> JobImportResult:
        source = detect_job_source(url)
        if not source.import_supported:
            raise JobImportError(f"{source.warning} {DEFAULT_ERROR}", status_code=422)
        try:
            html = await fetch_job_page(url)
        except JobPageFetchError as exc:
            raise JobImportError(f"{exc} {DEFAULT_ERROR}", status_code=422) from exc

        parsed = parse_job_page(html, source.parser_key)
        if _should_use_llm_fallback(parsed):
            parsed = await self._apply_llm_fallback(parsed, extract_page_text(html))
        if not parsed.description or len(parsed.description) < 80:
            raise JobImportError(f"The page did not contain a readable job description. {DEFAULT_ERROR}")

        confidence = _confidence(parsed)
        warnings = list(dict.fromkeys([*(source.warning and [source.warning] or []), *parsed.warnings]))
        for field in ("company", "title", "location", "salary", "deadline"):
            if not getattr(parsed, field):
                warnings.append(f"{field.replace('_', ' ').title()} not found")
            elif confidence[field] < 0.7:
                warnings.append(f"{field.replace('_', ' ').title()} confidence is low; please review")
        return JobImportResult(
            source=source.name,
            company=parsed.company,
            title=parsed.title,
            location=parsed.location,
            salary=parsed.salary,
            deadline=parsed.deadline,
            description=parsed.description,
            confidence=JobImportConfidence(**confidence),
            warnings=list(dict.fromkeys(warnings)),
            raw_url=url,
        )

    async def _apply_llm_fallback(self, parsed: ParsedJobPage, page_text: str) -> ParsedJobPage:
        try:
            data = await self.ai.generate_json(load_prompt("parse_job_page"), {"page_text": page_text})
            llm = LLMJobPageExtraction.model_validate(data)
        except (LLMServiceUnavailable, ValueError):
            parsed.warnings.append("Some fields could not be extracted automatically")
            return parsed

        values = asdict(parsed)
        for field in ("company", "title", "location", "salary", "deadline", "description"):
            if not values[field] and getattr(llm, field):
                values[field] = getattr(llm, field)
                values["confidence"][field] = getattr(llm.confidence, field)
        values["warnings"] = [*values["warnings"], *llm.warnings]
        return ParsedJobPage(**values)


def _should_use_llm_fallback(parsed: ParsedJobPage) -> bool:
    return any(not getattr(parsed, field) for field in ("company", "title", "location", "description"))


def _confidence(parsed: ParsedJobPage) -> dict[str, float]:
    return {
        field: parsed.confidence.get(field, 0.65 if getattr(parsed, field) else 0)
        for field in ("company", "title", "location", "salary", "deadline", "description")
    }
