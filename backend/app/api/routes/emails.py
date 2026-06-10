from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.session import get_db_session
from app.models import Email
from app.schemas.emails import (
    EmailSummary,
    EmailType,
    EmailUpdate,
    GmailConnectionStatus,
    GmailOAuthStart,
    GmailSyncRequest,
    GmailSyncResult,
)
from app.services.email_service import (
    get_email,
    get_or_create_connection,
    list_emails,
    save_oauth_connection,
    save_oauth_state,
    sync_gmail,
    update_email,
    validate_oauth_state,
)
from app.services.gmail_client import GMAIL_READONLY_SCOPE, GmailClient
from app.api.routes.jobs import _job_summary


router = APIRouter(tags=["emails"])


@router.get("/gmail/status", response_model=GmailConnectionStatus)
async def gmail_status(
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GmailConnectionStatus:
    connection = await get_or_create_connection(db)
    return GmailConnectionStatus(
        connected=connection.status == "CONNECTED",
        email_address=connection.email_address,
        scopes=connection.scopes or [],
        last_sync_at=connection.last_sync_at,
        requires_configuration=not _gmail_client(settings).is_configured or not settings.gmail_token_encryption_key,
    )


@router.get("/gmail/oauth/start", response_model=GmailOAuthStart)
async def gmail_oauth_start(
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GmailOAuthStart:
    state = token_urlsafe(24)
    await save_oauth_state(db, state)
    return GmailOAuthStart(
        authorization_url=_gmail_client(settings).authorization_url(state),
        scope=GMAIL_READONLY_SCOPE,
        state=state,
    )


@router.get("/gmail/oauth/callback")
async def gmail_oauth_callback(
    code: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    await validate_oauth_state(db, state)
    token = await _gmail_client(settings).exchange_code(code)
    if not token.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return a refresh token. Reconnect Gmail and approve offline access.",
        )
    await save_oauth_connection(
        db,
        settings,
        refresh_token=token.refresh_token,
        email_address=token.email_address,
        scopes=token.scopes,
        expires_at=token.expires_at,
    )
    return RedirectResponse("http://localhost:3000/settings?gmail=connected")


@router.post("/gmail/sync", response_model=GmailSyncResult)
async def post_gmail_sync(
    payload: GmailSyncRequest,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GmailSyncResult:
    return await sync_gmail(db, settings, days=payload.days)


@router.get("/emails", response_model=list[EmailSummary])
async def get_emails(
    search: str | None = None,
    email_type: EmailType | None = Query(default=None),
    unmatched: bool = False,
    db: AsyncSession = Depends(get_db_session),
) -> list[EmailSummary]:
    return [_email_summary(email) for email in await list_emails(db, search=search, email_type=email_type, unmatched=unmatched)]


@router.patch("/emails/{email_id}", response_model=EmailSummary)
async def patch_email(email_id: str, payload: EmailUpdate, db: AsyncSession = Depends(get_db_session)) -> EmailSummary:
    email = await update_email(db, await get_email(db, email_id), email_type=payload.email_type, job_id=payload.job_id, clear_job=payload.clear_job)
    return _email_summary(email)


def _email_summary(email: Email) -> EmailSummary:
    return EmailSummary(
        id=email.id,
        gmail_message_id=email.gmail_message_id,
        thread_id=email.thread_id,
        job_id=email.job_id,
        subject=email.subject,
        sender=email.sender,
        received_at=email.received_at,
        email_type=email.email_type,
        raw_snippet=email.raw_snippet,
        is_processed=email.is_processed,
        created_at=email.created_at,
        linked_job=_job_summary(email.job, has_resume_version=False) if email.job else None,
    )


def _gmail_client(settings: Settings) -> GmailClient:
    return GmailClient(
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        redirect_uri=settings.gmail_redirect_uri,
    )
