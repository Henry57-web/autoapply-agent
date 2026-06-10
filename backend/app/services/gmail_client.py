from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx
from fastapi import HTTPException, status

from app.schemas.emails import EmailIngest


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


@dataclass
class OAuthTokenResult:
    refresh_token: str | None
    access_token: str
    expires_at: datetime | None
    email_address: str | None
    scopes: list[str]


class GmailClient:
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    messages_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    def __init__(self, *, client_id: str | None, client_secret: str | None, redirect_uri: str | None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def authorization_url(self, state: str) -> str:
        self._require_configured()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": GMAIL_READONLY_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "include_granted_scopes": "false",
        }
        return f"{self.auth_base_url}?{httpx.QueryParams(params)}"

    async def exchange_code(self, code: str) -> OAuthTokenResult:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.token_url,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google OAuth token exchange failed.")
        payload = response.json()
        return _token_result(payload)

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.token_url,
                data={
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gmail token refresh failed.")
        return _token_result(response.json(), fallback_refresh_token=refresh_token)

    async def fetch_recent_messages(self, access_token: str, *, days: int) -> list[EmailIngest]:
        headers = {"Authorization": f"Bearer {access_token}"}
        query = f"newer_than:{days}d (application OR assessment OR interview OR recruiter OR offer OR unfortunately)"
        async with httpx.AsyncClient(timeout=30) as client:
            listing = await client.get(
                self.messages_url,
                headers=headers,
                params={"q": query, "maxResults": 50},
            )
            if listing.status_code >= 400:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gmail message listing failed.")
            messages = listing.json().get("messages", [])
            results: list[EmailIngest] = []
            for message in messages:
                detail = await client.get(
                    f"{self.messages_url}/{message['id']}",
                    headers=headers,
                    params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                )
                if detail.status_code >= 400:
                    continue
                results.append(_message_to_ingest(detail.json()))
        return results

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gmail OAuth is not configured. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REDIRECT_URI.",
            )


def _token_result(payload: dict, fallback_refresh_token: str | None = None) -> OAuthTokenResult:
    expires_in = payload.get("expires_in")
    return OAuthTokenResult(
        refresh_token=payload.get("refresh_token") or fallback_refresh_token,
        access_token=payload["access_token"],
        expires_at=(datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))) if expires_in else None,
        email_address=payload.get("id_token_email"),
        scopes=str(payload.get("scope", GMAIL_READONLY_SCOPE)).split(),
    )


def _message_to_ingest(payload: dict) -> EmailIngest:
    headers = {item.get("name", "").lower(): item.get("value") for item in payload.get("payload", {}).get("headers", [])}
    received_at = _parse_received_at(headers.get("date"), payload.get("internalDate"))
    return EmailIngest(
        gmail_message_id=payload["id"],
        thread_id=payload.get("threadId"),
        subject=headers.get("subject"),
        sender=headers.get("from"),
        received_at=received_at,
        raw_snippet=(payload.get("snippet") or "")[:500],
        body_text="",
    )


def _parse_received_at(date_header: str | None, internal_date: str | None) -> datetime:
    if date_header:
        try:
            parsed = parsedate_to_datetime(date_header)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    if internal_date:
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)
    return datetime.now(timezone.utc)
