import asyncio
import re
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import Settings


_DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


@dataclass(frozen=True)
class RequestIdentity:
    user_id: str
    display_name: str
    source: str
    device_id: str
    device_label: str
    email: str | None = None

    def public_dict(self) -> dict[str, str | None]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "source": self.source,
            "device_id": self.device_id,
            "device_label": self.device_label,
            "email": self.email,
        }


def _clean_device_id(value: str | None) -> str:
    candidate = (value or "").strip()
    return candidate if _DEVICE_ID_PATTERN.fullmatch(candidate) else "anonymous"


def _clean_label(value: str | None, fallback: str) -> str:
    candidate = " ".join((value or "").strip().split())
    return candidate[:80] if candidate else fallback


def verify_google_credential(credential: str, client_id: str) -> dict:
    return id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        client_id,
    )


async def resolve_request_identity(
    request: Request,
    settings: Settings,
) -> RequestIdentity:
    device_id = _clean_device_id(request.headers.get("X-Device-Id"))
    fallback_label = (
        "Anonymous browser"
        if device_id == "anonymous"
        else f"Anonymous device - {device_id[-6:]}"
    )
    device_label = _clean_label(
        request.headers.get("X-Device-Label"),
        fallback_label,
    )

    authorization = request.headers.get("Authorization", "")
    if not authorization:
        return RequestIdentity(
            user_id=f"device:{device_id}",
            display_name=device_label,
            source="device",
            device_id=device_id,
            device_label=device_label,
        )

    scheme, _, credential = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use a Bearer token for Google sign-in.",
        )
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on the API.",
        )

    try:
        claims = await asyncio.to_thread(
            verify_google_credential,
            credential,
            settings.google_client_id,
        )
    except (GoogleAuthError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The Google sign-in token is invalid or expired.",
        ) from None

    subject = str(claims.get("sub", "")).strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The Google sign-in token has no user identifier.",
        )

    email_verified = claims.get("email_verified") in (True, "true", "True")
    verified_email = (
        str(claims.get("email", "")).strip() if email_verified else ""
    )
    display_name = _clean_label(
        str(claims.get("name", "")),
        verified_email or f"Google user - {subject[-6:]}",
    )
    return RequestIdentity(
        user_id=f"google:{subject}",
        display_name=display_name,
        source="google",
        device_id=device_id,
        device_label=device_label,
        email=verified_email or None,
    )
