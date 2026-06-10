from __future__ import annotations

from fastapi import HTTPException, status


def encrypt_token(token: str, key: str | None) -> str:
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail token encryption is not configured. Set GMAIL_TOKEN_ENCRYPTION_KEY.",
        )
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="cryptography is required for Gmail token encryption.",
        ) from exc
    return Fernet(key.encode()).encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str, key: str | None) -> str:
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail token encryption is not configured. Set GMAIL_TOKEN_ENCRYPTION_KEY.",
        )
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="cryptography is required for Gmail token encryption.",
        ) from exc
    return Fernet(key.encode()).decrypt(encrypted_token.encode()).decode()
