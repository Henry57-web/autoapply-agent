from enum import Enum

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models import Application, ApplicationMetadata, ApplicationStatus, CandidateProfile, Resume, ResumeVersion
from app.schemas.applications import (
    ApplicationDetail,
    ApplicationMetadataUpdate,
    ApplicationStatusUpdate,
    ApplicationSummary,
    CandidateProfileDetail,
    CandidateProfileSummary,
    ResumeDetail,
    ResumeSummary,
)
from app.services.application_presenter import build_application_detail, build_application_summary
from app.services.docx_export import build_cover_letter_docx, build_resume_docx
from app.services.document_parser import UnsupportedDocumentError, extract_text_from_upload
from app.services.resume_version_service import create_base_resume_version


router = APIRouter(tags=["applications"])


class ExportDocument(str, Enum):
    resume = "resume"
    cover_letter = "cover-letter"


@router.post("/candidate-profiles", response_model=CandidateProfileDetail, status_code=status.HTTP_201_CREATED)
async def save_candidate_profile(
    profile: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> CandidateProfileDetail:
    try:
        raw_text = await extract_text_from_upload(profile)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Profile has no readable text.")

    candidate_profile = CandidateProfile(file_name=profile.filename or "candidate-profile", raw_text=raw_text)
    db.add(candidate_profile)
    await db.commit()
    await db.refresh(candidate_profile)
    return _profile_detail(candidate_profile)


@router.get("/candidate-profiles", response_model=list[CandidateProfileSummary])
async def list_candidate_profiles(db: AsyncSession = Depends(get_db_session)) -> list[CandidateProfileSummary]:
    profiles = await db.scalars(select(CandidateProfile).order_by(CandidateProfile.created_at.desc()))
    return [_profile_summary(profile) for profile in profiles]


@router.post("/resumes", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def save_resume(
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> ResumeDetail:
    try:
        raw_text = await extract_text_from_upload(resume)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Resume has no readable text.")

    saved_resume = Resume(file_name=resume.filename or "resume", raw_text=raw_text)
    db.add(saved_resume)
    await db.flush()
    await create_base_resume_version(db, saved_resume)
    await db.commit()
    await db.refresh(saved_resume)
    return _resume_detail(saved_resume)


@router.get("/resumes", response_model=list[ResumeSummary])
async def list_resumes(db: AsyncSession = Depends(get_db_session)) -> list[ResumeSummary]:
    resumes = await db.scalars(select(Resume).order_by(Resume.created_at.desc()))
    return [_resume_summary(resume) for resume in resumes]


@router.get("/applications", response_model=list[ApplicationSummary])
async def list_applications(db: AsyncSession = Depends(get_db_session)) -> list[ApplicationSummary]:
    query = (
        select(Application)
        .options(selectinload(Application.status), selectinload(Application.metadata_record))
        .order_by(Application.created_at.desc())
    )
    applications = await db.scalars(query)
    return [build_application_summary(application) for application in applications]


@router.get("/applications/{application_id}", response_model=ApplicationDetail)
async def get_application(application_id: str, db: AsyncSession = Depends(get_db_session)) -> ApplicationDetail:
    application = await _get_application(db, application_id)
    resume_version = await db.get(ResumeVersion, application.resume_version_id)
    resume = await db.get(Resume, application.resume_id)
    if not resume_version or not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tailored resume version not found.")
    return build_application_detail(application, resume, resume_version)


@router.patch("/applications/{application_id}/status", response_model=ApplicationSummary)
async def update_application_status(
    application_id: str,
    payload: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ApplicationSummary:
    application = await _get_application(db, application_id)
    if application.status:
        application.status.status = payload.status
    else:
        db.add(ApplicationStatus(application_id=application.id, status=payload.status))
    await db.commit()
    return build_application_summary(await _get_application(db, application_id))


@router.patch("/applications/{application_id}/metadata", response_model=ApplicationDetail)
async def update_application_metadata(
    application_id: str,
    payload: ApplicationMetadataUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ApplicationDetail:
    application = await _get_application(db, application_id)
    metadata_record = application.metadata_record
    if not metadata_record:
        metadata_record = ApplicationMetadata(application_id=application.id)
        db.add(metadata_record)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(metadata_record, field, value)
    await db.commit()
    return await get_application(application_id, db)


@router.get("/applications/{application_id}/export/{document}")
async def export_application_document(
    application_id: str,
    document: ExportDocument,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    application = await _get_application(db, application_id)
    title = application.job_title or "Target Role"
    company = application.company_name or "Target Company"
    if document == ExportDocument.resume:
        resume_version = await db.get(ResumeVersion, application.resume_version_id)
        if not resume_version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tailored resume version not found.")
        buffer = build_resume_docx(f"Tailored Resume - {title}", resume_version.content)
        filename = "tailored-resume.docx"
    else:
        buffer = build_cover_letter_docx(f"Cover Letter - {title} at {company}", application.cover_letter or "")
        filename = "cover-letter.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _get_application(db: AsyncSession, application_id: str) -> Application:
    query = (
        select(Application)
        .options(selectinload(Application.status), selectinload(Application.metadata_record))
        .where(Application.id == application_id)
        .execution_options(populate_existing=True)
    )
    application = await db.scalar(query)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return application


def _profile_summary(profile: CandidateProfile) -> CandidateProfileSummary:
    return CandidateProfileSummary(id=profile.id, file_name=profile.file_name, created_at=profile.created_at)


def _profile_detail(profile: CandidateProfile) -> CandidateProfileDetail:
    return CandidateProfileDetail(**_profile_summary(profile).model_dump(), raw_text=profile.raw_text)


def _resume_summary(resume: Resume) -> ResumeSummary:
    return ResumeSummary(id=resume.id, file_name=resume.file_name, created_at=resume.created_at)


def _resume_detail(resume: Resume) -> ResumeDetail:
    return ResumeDetail(**_resume_summary(resume).model_dump(), raw_text=resume.raw_text)
