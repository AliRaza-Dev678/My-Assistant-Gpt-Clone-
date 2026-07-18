import asyncio
import json
import logging
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    get_assistant,
    get_repository,
    get_request_identity,
)
from app.models.schemas import MessageCreate
from app.repositories.conversations import ConversationRepository
from app.services.assistant import (
    AssistantConfigurationError,
    AssistantService,
)
from app.services.identity import RequestIdentity


router = APIRouter(prefix="/conversations", tags=["chat"])
logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    payload = json.dumps(jsonable_encoder(data), ensure_ascii=False)
    return "event: " + event + "\ndata: " + payload + "\n\n"


async def stream_assistant_response(
    conversation_id: str,
    repository: ConversationRepository,
    assistant: AssistantService,
    identity: RequestIdentity,
    conversation_title: str,
) -> AsyncIterator[str]:
    assistant_message_id = str(uuid4())
    yield sse(
        "meta",
        {
            "assistant_message_id": assistant_message_id,
            "thread_id": conversation_id,
            "identity_label": identity.display_name,
        },
    )
    chunks: list[str] = []

    try:
        history = await repository.message_history(conversation_id)
        async for token in assistant.stream_reply(
            history,
            thread_id=conversation_id,
            conversation_title=conversation_title,
            identity=identity,
        ):
            chunks.append(token)
            yield sse("token", {"content": token})

        content = "".join(chunks).strip()
        if content:
            message = await repository.add_message(
                conversation_id,
                "assistant",
                content,
                assistant_message_id,
            )
            yield sse("done", {"message": message})
        else:
            yield sse("error", {"message": "The model returned an empty response."})
    except AssistantConfigurationError as error:
        yield sse("error", {"message": str(error)})
    except asyncio.CancelledError:
        partial = "".join(chunks).strip()
        if partial:
            await repository.add_message(
                conversation_id,
                "assistant",
                partial,
                assistant_message_id,
            )
        raise
    except Exception:
        logger.exception(
            "Assistant response stream failed for conversation %s",
            conversation_id,
        )
        yield sse(
            "error",
            {"message": "The assistant could not complete this response. Try again."},
        )


@router.post("/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    payload: MessageCreate,
    repository: ConversationRepository = Depends(get_repository),
    assistant: AssistantService = Depends(get_assistant),
    identity: RequestIdentity = Depends(get_request_identity),
):
    conversation = await repository.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message cannot be blank")

    user_message = await repository.add_message(conversation_id, "user", content)
    await repository.auto_title(conversation_id, content)
    conversation = await repository.get_conversation(conversation_id)

    async def event_stream():
        yield sse("user", {"message": user_message})
        async for event in stream_assistant_response(
            conversation_id,
            repository,
            assistant,
            identity,
            conversation["title"] if conversation else "New chat",
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{conversation_id}/regenerate")
async def regenerate_message(
    conversation_id: str,
    repository: ConversationRepository = Depends(get_repository),
    assistant: AssistantService = Depends(get_assistant),
    identity: RequestIdentity = Depends(get_request_identity),
):
    conversation = await repository.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conversation["messages"]:
        raise HTTPException(status_code=409, detail="There is no response to regenerate")

    await repository.delete_latest_assistant_message(conversation_id)
    history = await repository.message_history(conversation_id)
    if not history or history[-1]["role"] != "user":
        raise HTTPException(status_code=409, detail="There is no response to regenerate")

    return StreamingResponse(
        stream_assistant_response(
            conversation_id,
            repository,
            assistant,
            identity,
            conversation["title"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
