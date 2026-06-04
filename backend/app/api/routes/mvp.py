from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import CandidateProfile, Resume
from app.schemas.mvp import ApplicationResult
from app.services.document_parser import UnsupportedDocumentError, extract_text_from_upload
from app.services.tailoring_service import TailoringService


router = APIRouter(prefix="/mvp", tags=["mvp"])


@router.post("/run", response_model=ApplicationResult)
async def run_mvp_workflow(
    resume: UploadFile | None = File(default=None),
    resume_id: str | None = Form(default=None),
    job_description: str = Form(...),
    candidate_profile: UploadFile | None = File(default=None),
    candidate_profile_id: str | None = Form(default=None),
    company: str | None = Form(default=None),
    title: str | None = Form(default=None),
    job_url: str | None = Form(default=None),
    source: str | None = Form(default=None),
    job_type: str | None = Form(default=None),
    location: str | None = Form(default=None),
    salary: str | None = Form(default=None),
    deadline: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> ApplicationResult:
    if len(job_description.strip()) < 80:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job description is too short to analyze.",
        )

    if not candidate_profile and not candidate_profile_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload a candidate profile or select a saved profile.",
        )

    if not resume and not resume_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload a resume or select a saved resume.",
        )

    try:
        if resume:
            resume_text = await extract_text_from_upload(resume)
            resume_file_name = resume.filename or "resume"
        else:
            saved_resume = await db.get(Resume, resume_id)
            if not saved_resume:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved resume not found.")
            resume_text = saved_resume.raw_text
            resume_file_name = saved_resume.file_name
        if candidate_profile:
            candidate_text = await extract_text_from_upload(candidate_profile)
            candidate_file_name = candidate_profile.filename or "candidate-profile"
        else:
            saved_profile = await db.get(CandidateProfile, candidate_profile_id)
            if not saved_profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved profile not found.")
            candidate_text = saved_profile.raw_text
            candidate_file_name = saved_profile.file_name
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not candidate_text or not resume_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Candidate profile and resume must contain readable text.",
        )

    service = TailoringService()
    return await service.run_mvp_workflow(
        db=db,
        candidate_file_name=candidate_file_name,
        candidate_profile_text=candidate_text,
        resume_file_name=resume_file_name,
        resume_text=resume_text,
        job_description=job_description,
        candidate_profile_id=candidate_profile_id if not candidate_profile else None,
        resume_id=resume_id if not resume else None,
        job_metadata={
            "company": company,
            "title": title,
            "job_url": job_url,
            "source": source,
            "job_type": job_type,
            "location": location,
            "salary": salary,
            "deadline": deadline,
            "notes": notes,
        },
    )
