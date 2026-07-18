import re
from dataclasses import dataclass

from fastapi import Request

_DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


@dataclass(frozen=True)
class RequestIdentity:
    user_id: str
    display_name: str
    source: str
    device_id: str
    device_label: str

    def public_dict(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "source": self.source,
            "device_id": self.device_id,
            "device_label": self.device_label,
        }


def _clean_device_id(value: str | None) -> str:
    candidate = (value or "").strip()
    return candidate if _DEVICE_ID_PATTERN.fullmatch(candidate) else "anonymous"


def _clean_label(value: str | None, fallback: str) -> str:
    candidate = " ".join((value or "").strip().split())
    return candidate[:80] if candidate else fallback


async def resolve_request_identity(request: Request) -> RequestIdentity:
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

    return RequestIdentity(
        user_id=f"device:{device_id}",
        display_name=device_label,
        source="device",
        device_id=device_id,
        device_label=device_label,
    )
