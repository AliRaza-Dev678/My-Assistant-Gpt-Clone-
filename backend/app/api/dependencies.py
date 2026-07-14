from fastapi import Request

from app.repositories.conversations import ConversationRepository
from app.services.assistant import AssistantService


def get_repository(request: Request) -> ConversationRepository:
    return request.app.state.repository


def get_assistant(request: Request) -> AssistantService:
    return request.app.state.assistant
