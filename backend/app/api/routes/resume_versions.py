from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.resume_versions import (
    ResumeDownloadFormat,
    ResumeVersionCreate,
    ResumeVersionDetail,
    ResumeVersionSummary,
)
from app.services.resume_version_presenter import build_resume_version_detail, build_resume_version_summary
from app.services.resume_version_service import (
    build_resume_version_download,
    create_resume_version,
    delete_resume_version,
    get_job_resume_version,
    get_resume_version,
    list_resume_versions,
)


router = APIRouter(tags=["resume-versions"])


@router.get("/resume-versions", response_model=list[ResumeVersionSummary])
async def get_resume_versions(
    search: str | None = None,
    role_type: str | None = None,
    company: str | None = None,
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ResumeVersionSummary]:
    versions = await list_resume_versions(
        db,
        search=search,
        role_type=role_type,
        company=company,
        direction=direction,
    )
    return [build_resume_version_summary(version) for version in versions]


@router.get("/resume-versions/{version_id}", response_model=ResumeVersionDetail)
async def get_resume_version_detail(
    version_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> ResumeVersionDetail:
    return build_resume_version_detail(await get_resume_version(db, version_id))


@router.post("/resume-versions", response_model=ResumeVersionDetail, status_code=status.HTTP_201_CREATED)
async def post_resume_version(
    payload: ResumeVersionCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ResumeVersionDetail:
    version = await create_resume_version(db, payload)
    await db.commit()
    await db.refresh(version)
    return build_resume_version_detail(version)


@router.delete("/resume-versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_resume_version(version_id: str, db: AsyncSession = Depends(get_db_session)) -> Response:
    await delete_resume_version(db, await get_resume_version(db, version_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/resume-versions/{version_id}/download")
async def download_resume_version(
    version_id: str,
    file_format: ResumeDownloadFormat = Query(alias="format"),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    buffer, filename, media_type = build_resume_version_download(
        await get_resume_version(db, version_id),
        file_format,
    )
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/jobs/{job_id}/resume-version", response_model=ResumeVersionDetail)
async def get_linked_job_resume_version(
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> ResumeVersionDetail:
    return build_resume_version_detail(await get_job_resume_version(db, job_id))
