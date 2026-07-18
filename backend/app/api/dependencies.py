from fastapi import Request

from app.repositories.conversations import ConversationRepository
from app.services.assistant import AssistantService
from app.services.identity import RequestIdentity, resolve_request_identity


def get_repository(request: Request) -> ConversationRepository:
    return request.app.state.repository


def get_assistant(request: Request) -> AssistantService:
    return request.app.state.assistant


async def get_request_identity(request: Request) -> RequestIdentity:
    return await resolve_request_identity(request)
