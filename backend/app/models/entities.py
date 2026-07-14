from uuid import uuid4

from tortoise import Model, fields


class Conversation(Model):
    id = fields.UUIDField(primary_key=True, default=uuid4)
    title = fields.CharField(max_length=80, default="New chat")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "conversations"
        ordering = ["-updated_at"]


class Message(Model):
    id = fields.UUIDField(primary_key=True, default=uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation",
        related_name="messages",
        on_delete=fields.CASCADE,
    )
    role = fields.CharField(max_length=16)
    content = fields.TextField()
    position = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"
        ordering = ["position"]
        unique_together = (("conversation", "position"),)
        indexes = (("conversation", "position"),)
