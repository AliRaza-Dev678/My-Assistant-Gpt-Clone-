from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_repository
from app.models.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
)
from app.repositories.conversations import ConversationRepository


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    repository: ConversationRepository = Depends(get_repository),
):
    return await repository.list_conversations()


@router.post(
    "",
    response_model=ConversationDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    repository: ConversationRepository = Depends(get_repository),
):
    return await repository.create_conversation(payload.title)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    repository: ConversationRepository = Depends(get_repository),
):
    conversation = await repository.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationDetail)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    repository: ConversationRepository = Depends(get_repository),
):
    conversation = await repository.update_title(conversation_id, payload.title)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    repository: ConversationRepository = Depends(get_repository),
):
    if not await repository.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
