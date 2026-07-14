from datetime import datetime, timezone
from uuid import UUID, uuid4

from tortoise.transactions import in_transaction

from app.models.entities import Conversation, Message


def conversation_dict(conversation: Conversation) -> dict:
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


def message_dict(message: Message) -> dict:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "role": message.role,
        "content": message.content,
        "position": message.position,
        "created_at": message.created_at,
    }


class ConversationRepository:
    async def list_conversations(self) -> list[dict]:
        conversations = await Conversation.all().order_by("-updated_at")
        return [conversation_dict(item) for item in conversations]

    async def create_conversation(self, title: str = "New chat") -> dict:
        conversation = await Conversation.create(title=title.strip() or "New chat")
        result = conversation_dict(conversation)
        result["messages"] = []
        return result

    async def get_conversation(self, conversation_id: str | UUID) -> dict | None:
        conversation = await Conversation.get_or_none(id=conversation_id)
        if conversation is None:
            return None

        messages = await Message.filter(
            conversation_id=conversation.id
        ).order_by("position")
        result = conversation_dict(conversation)
        result["messages"] = [message_dict(message) for message in messages]
        return result

    async def update_title(
        self,
        conversation_id: str | UUID,
        title: str,
    ) -> dict | None:
        conversation = await Conversation.get_or_none(id=conversation_id)
        if conversation is None:
            return None
        conversation.title = title.strip()
        conversation.updated_at = datetime.now(timezone.utc)
        await conversation.save(update_fields=("title", "updated_at"))
        return await self.get_conversation(conversation.id)

    async def delete_conversation(self, conversation_id: str | UUID) -> bool:
        deleted_count = await Conversation.filter(id=conversation_id).delete()
        return deleted_count > 0

    async def add_message(
        self,
        conversation_id: str | UUID,
        role: str,
        content: str,
        message_id: str | UUID | None = None,
    ) -> dict:
        async with in_transaction() as connection:
            conversation = (
                await Conversation.filter(id=conversation_id)
                .using_db(connection)
                .select_for_update()
                .first()
            )
            if conversation is None:
                raise ValueError("Conversation not found")

            latest = (
                await Message.filter(conversation_id=conversation.id)
                .using_db(connection)
                .order_by("-position")
                .first()
            )
            next_position = 0 if latest is None else latest.position + 1
            message = await Message.create(
                id=message_id or uuid4(),
                conversation=conversation,
                role=role,
                content=content,
                position=next_position,
                using_db=connection,
            )
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save(
                using_db=connection,
                update_fields=("updated_at",),
            )

        return message_dict(message)

    async def delete_latest_assistant_message(
        self,
        conversation_id: str | UUID,
    ) -> bool:
        async with in_transaction() as connection:
            conversation = (
                await Conversation.filter(id=conversation_id)
                .using_db(connection)
                .select_for_update()
                .first()
            )
            if conversation is None:
                return False

            message = (
                await Message.filter(
                    conversation_id=conversation.id,
                    role="assistant",
                )
                .using_db(connection)
                .order_by("-position")
                .first()
            )
            if message is None:
                return False

            await message.delete(using_db=connection)
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save(
                using_db=connection,
                update_fields=("updated_at",),
            )
        return True

    async def message_history(
        self,
        conversation_id: str | UUID,
    ) -> list[dict]:
        conversation = await self.get_conversation(conversation_id)
        return conversation["messages"] if conversation else []

    async def auto_title(
        self,
        conversation_id: str | UUID,
        first_message: str,
    ) -> None:
        conversation = await Conversation.get_or_none(id=conversation_id)
        if conversation is None or conversation.title != "New chat":
            return

        compact = " ".join(first_message.split())
        title = compact[:48].rstrip()
        if len(compact) > 48:
            title += "…"
        await self.update_title(conversation.id, title or "New chat")
