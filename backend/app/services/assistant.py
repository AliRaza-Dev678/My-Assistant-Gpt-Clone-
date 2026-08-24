import os
from collections.abc import AsyncIterator
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.core.config import Settings
from app.services.identity import RequestIdentity


SYSTEM_PROMPT = """
You are RazaMind, a thoughtful, accurate, and practical AI
assistant. Be concise by default, but give step-by-step detail when the user is
learning or building something. Use Markdown where it improves readability.
When you provide code, make it runnable and explain important assumptions.
Never claim to have completed actions you did not perform.
""".strip()


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class AssistantConfigurationError(RuntimeError):
    pass


class AssistantService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._configure_langsmith()
        self._model: ChatGroq | None = None
        self._graph = None

    def _configure_langsmith(self) -> None:
        if not self.settings.langsmith_enabled:
            os.environ["LANGSMITH_TRACING"] = "false"
            return
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = self.settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = self.settings.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = self.settings.langsmith_endpoint

    def _get_model(self) -> ChatGroq:
        if not self.settings.groq_api_key:
            raise AssistantConfigurationError(
                "GROQ_API_KEY is missing. Add it to backend/.env and restart the API."
            )
        if self._model is None:
            self._model = ChatGroq(
                api_key=self.settings.groq_api_key,
                model=self.settings.groq_model,
                temperature=self.settings.temperature,
                streaming=True,
            )
        return self._model

    async def _chat_node(self, state: ChatState) -> dict:
        response = await self._get_model().ainvoke(state["messages"])
        return {"messages": [response]}

    def _build_graph(self):
        graph = StateGraph(ChatState)
        graph.add_node("assistant", self._chat_node)
        graph.add_edge(START, "assistant")
        graph.add_edge("assistant", END)
        return graph.compile()

    def _get_graph(self):
        if self._graph is None:
            self._get_model()
            self._graph = self._build_graph()
        return self._graph

    @staticmethod
    def _to_langchain_messages(history: list[dict]) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        for item in history:
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item["role"] == "assistant":
                messages.append(AIMessage(content=item["content"]))
        return messages

    @staticmethod
    def _content_text(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
            return "".join(parts)
        return ""

    def build_run_config(
        self,
        *,
        thread_id: str,
        conversation_title: str,
        identity: RequestIdentity,
    ) -> RunnableConfig:
        metadata: dict[str, str] = {
            "thread_id": thread_id,
            "conversation_id": thread_id,
            "conversation_title": conversation_title,
            "thread_label": f"{identity.display_name} - {conversation_title}",
            "user_id": identity.user_id,
            "user_display_name": identity.display_name,
            "identity_source": identity.source,
            "device_id": identity.device_id,
            "device_label": identity.device_label,
        }
        return {
            "run_name": "RazaMind turn",
            "tags": ["chat", self.settings.app_env, identity.source],
            "metadata": metadata,
        }

    async def stream_reply(
        self,
        history: list[dict],
        *,
        thread_id: str,
        conversation_title: str,
        identity: RequestIdentity,
    ) -> AsyncIterator[str]:
        graph = self._get_graph()
        state = {"messages": self._to_langchain_messages(history)}
        config = self.build_run_config(
            thread_id=thread_id,
            conversation_title=conversation_title,
            identity=identity,
        )

        async for part in graph.astream(
            state,
            config=config,
            stream_mode="messages",
            version="v2",
        ):
            if not isinstance(part, dict) or part.get("type") != "messages":
                continue
            data = part.get("data")
            message_chunk = data[0] if isinstance(data, (tuple, list)) else None
            if message_chunk is None:
                continue
            text = self._content_text(getattr(message_chunk, "content", ""))
            if text:
                yield text
