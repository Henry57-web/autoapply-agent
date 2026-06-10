from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models import Email, GmailConnection, Job, JobStatusEvent
from app.schemas.emails import EmailIngest, EmailType, GmailSyncResult
from app.services.email_classifier import classify_email
from app.services.email_matcher import match_email_to_job
from app.services.gmail_client import GMAIL_READONLY_SCOPE, GmailClient
from app.services.token_cipher import decrypt_token, encrypt_token


STATUS_BY_EMAIL_TYPE: dict[EmailType, str] = {
    "APPLICATION_CONFIRMATION": "APPLIED",
    "OA_INVITATION": "OA_RECEIVED",
    "INTERVIEW_INVITATION": "INTERVIEW",
    "REJECTION": "REJECTED",
    "OFFER": "OFFER",
}
MILESTONE_FIELDS = {
    "APPLIED": "applied_at",
    "OA_RECEIVED": "oa_received_at",
    "INTERVIEW": "interview_at",
    "OFFER": "offer_at",
}


@dataclass
class EmailMetrics:
    pending_oa: int = 0
    upcoming_interviews: int = 0
    new_recruiter_messages: int = 0
    unmatched_emails: int = 0
    recent_rejections: int = 0
    recent_offers: int = 0


async def get_or_create_connection(db: AsyncSession) -> GmailConnection:
    connection = await db.scalar(select(GmailConnection).order_by(desc(GmailConnection.created_at)).limit(1))
    if connection:
        return connection
    connection = GmailConnection(status="DISCONNECTED", scopes=[])
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


async def save_oauth_state(db: AsyncSession, state: str) -> GmailConnection:
    connection = await get_or_create_connection(db)
    metadata = dict(connection.metadata_record or {})
    metadata["oauth_state"] = state
    connection.metadata_record = metadata
    await db.commit()
    await db.refresh(connection)
    return connection


async def validate_oauth_state(db: AsyncSession, state: str | None) -> GmailConnection:
    connection = await get_or_create_connection(db)
    expected_state = (connection.metadata_record or {}).get("oauth_state")
    if not state or not expected_state or state != expected_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Gmail OAuth state.")
    return connection


async def save_oauth_connection(db: AsyncSession, settings: Settings, *, refresh_token: str, email_address: str | None, scopes: list[str], expires_at: datetime | None) -> GmailConnection:
    if GMAIL_READONLY_SCOPE not in scopes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gmail readonly scope was not granted.")
    connection = await get_or_create_connection(db)
    metadata = dict(connection.metadata_record or {})
    metadata.pop("oauth_state", None)
    connection.status = "CONNECTED"
    connection.email_address = email_address
    connection.scopes = scopes
    connection.token_expires_at = expires_at
    connection.encrypted_refresh_token = encrypt_token(refresh_token, settings.gmail_token_encryption_key)
    connection.metadata_record = metadata
    await db.commit()
    await db.refresh(connection)
    return connection


async def list_emails(
    db: AsyncSession,
    *,
    search: str | None = None,
    email_type: EmailType | None = None,
    unmatched: bool = False,
) -> list[Email]:
    query = select(Email).options(selectinload(Email.job)).order_by(desc(Email.received_at))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Email.subject.ilike(pattern), Email.sender.ilike(pattern), Email.raw_snippet.ilike(pattern)))
    if email_type:
        query = query.where(Email.email_type == email_type)
    if unmatched:
        query = query.where(Email.job_id.is_(None))
    return list(await db.scalars(query))


async def ingest_emails(db: AsyncSession, messages: list[EmailIngest]) -> GmailSyncResult:
    jobs = list(await db.scalars(select(Job)))
    summary = GmailSyncResult(scanned=len(messages), imported=0, updated=0, matched=0, unmatched=0, status_updates=0, failed=0)
    for message in messages:
        try:
            email_type = classify_email(message.subject, message.sender, message.raw_snippet, message.body_text)
            job, confidence, reason = match_email_to_job(
                jobs,
                subject=message.subject,
                sender=message.sender,
                snippet=message.raw_snippet,
                body_text=message.body_text,
            )
            existing = await db.scalar(select(Email).where(Email.gmail_message_id == message.gmail_message_id))
            email = existing or Email(gmail_message_id=message.gmail_message_id, received_at=message.received_at)
            email.thread_id = message.thread_id
            email.subject = message.subject
            email.sender = message.sender
            email.received_at = message.received_at
            email.raw_snippet = message.raw_snippet[:500]
            email.email_type = email_type
            email.job_id = job.id if job else None
            email.is_processed = True
            email.metadata_record = {"match_confidence": confidence, "match_reason": reason}
            if existing:
                summary.updated += 1
            else:
                db.add(email)
                summary.imported += 1
            if job:
                summary.matched += 1
                if await _apply_status_if_needed(db, job, email_type):
                    summary.status_updates += 1
            else:
                summary.unmatched += 1
            await db.flush()
        except Exception as exc:  # Keep one bad email from stopping the sync.
            summary.failed += 1
            summary.errors.append(str(exc))
    await db.commit()
    return summary


async def sync_gmail(db: AsyncSession, settings: Settings, *, days: int) -> GmailSyncResult:
    connection = await get_or_create_connection(db)
    if not connection.encrypted_refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Gmail is not connected.")
    refresh_token = decrypt_token(connection.encrypted_refresh_token, settings.gmail_token_encryption_key)
    client = GmailClient(
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        redirect_uri=settings.gmail_redirect_uri,
    )
    token = await client.refresh_access_token(refresh_token)
    messages = await client.fetch_recent_messages(token.access_token, days=days)
    result = await ingest_emails(db, messages)
    connection.last_sync_at = datetime.now(timezone.utc)
    connection.token_expires_at = token.expires_at
    await db.commit()
    return result


async def update_email(db: AsyncSession, email: Email, *, email_type: EmailType | None, job_id: str | None, clear_job: bool) -> Email:
    should_apply_status = False
    if email_type:
        email.email_type = email_type
        should_apply_status = True
    if clear_job:
        email.job_id = None
    elif job_id is not None:
        job = await db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        email.job_id = job.id
        await _apply_status_if_needed(db, job, email.email_type)
        should_apply_status = False
    if should_apply_status and email.job_id:
        job = await db.get(Job, email.job_id)
        if job:
            await _apply_status_if_needed(db, job, email.email_type)
    await db.commit()
    return await get_email(db, email.id)


async def get_email(db: AsyncSession, email_id: str) -> Email:
    email = await db.scalar(select(Email).options(selectinload(Email.job)).where(Email.id == email_id))
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return email


async def get_email_metrics(db: AsyncSession) -> EmailMetrics:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    rows = dict((await db.execute(select(Email.email_type, func.count()).where(Email.received_at >= cutoff).group_by(Email.email_type))).all())
    unmatched = await db.scalar(select(func.count()).select_from(Email).where(Email.job_id.is_(None)))
    return EmailMetrics(
        pending_oa=rows.get("OA_INVITATION", 0) + rows.get("OA_REMINDER", 0),
        upcoming_interviews=rows.get("INTERVIEW_INVITATION", 0) + rows.get("INTERVIEW_REMINDER", 0),
        new_recruiter_messages=rows.get("RECRUITER_OUTREACH", 0),
        unmatched_emails=int(unmatched or 0),
        recent_rejections=rows.get("REJECTION", 0),
        recent_offers=rows.get("OFFER", 0),
    )


async def _apply_status_if_needed(db: AsyncSession, job: Job, email_type: EmailType) -> bool:
    next_status = STATUS_BY_EMAIL_TYPE.get(email_type)
    if not next_status or job.status == next_status:
        return False
    previous_status = job.status
    job.status = next_status
    milestone_field = MILESTONE_FIELDS.get(next_status)
    if milestone_field and not getattr(job, milestone_field):
        setattr(job, milestone_field, datetime.now(timezone.utc))
    db.add(
        JobStatusEvent(
            job_id=job.id,
            from_status=previous_status,
            to_status=next_status,
            source="gmail_sync",
            metadata_record={"trigger_email_type": email_type},
        )
    )
    return True
