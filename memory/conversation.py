"""短期对话记忆"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from config import settings as config

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str
    content: str
    image_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ConversationMemory:
    def __init__(self, window_size: int = None, llm=None,
                 on_message: callable = None, on_summary: callable = None):
        self.messages: list[Message] = []
        self.summary: str = ""
        self.window_size = window_size or config.memory_window_size
        self._llm = llm
        self._on_message = on_message  # 持久化回调(role, content, image_count)
        self._on_summary = on_summary  # 持久化回调(summary_text)

    def add_message(self, role: str, content: str, image_count: int = 0):
        self.messages.append(Message(role=role, content=content, image_count=image_count))
        if self._on_message:
            self._on_message(role, content, image_count)
        if len(self.messages) > self.window_size * 2:
            self._compress()

    def get_recent(self, n: int = None) -> list[Message]:
        return self.messages[-(n or self.window_size):]

    def get_context_string(self, n: int = None) -> str:
        recent = self.get_recent(n)
        parts = []
        if self.summary:
            parts.append(f"【历史摘要】\n{self.summary}")
        if recent:
            parts.append("【最近对话】")
            for m in recent:
                label = "用户" if m.role == "user" else "助手"
                extra = f"[附图{m.image_count}张] " if m.image_count else ""
                parts.append(f"{label}: {extra}{m.content}")
        return "\n".join(parts)

    def get_chat_history(self, n: int = None) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.get_recent(n)]

    def _compress(self):
        overflow = self.messages[:self.window_size]
        self.messages = self.messages[self.window_size:]
        if not overflow:
            return
        if self._llm is None:
            from langchain_community.chat_models import ChatTongyi
            llm = ChatTongyi(model=config.chat_model, dashscope_api_key=config.dashscope_api_key)
        else:
            llm = self._llm
        history = "\n".join(f"{'用户' if m.role == 'user' else '助手'}: {m.content}" for m in overflow)
        prompt = f"将以下对话压缩为简洁摘要（不超过200字），保留关键事实和用户偏好：\n\n{history}"
        try:
            new_summary = llm.invoke(prompt).content
            self.summary = f"{self.summary}\n{new_summary}" if self.summary else new_summary
            if self._on_summary:
                self._on_summary(self.summary)
        except Exception as e:
            logger.error("摘要压缩失败: %s", e)

    def clear(self):
        self.messages.clear()
        self.summary = ""

    @property
    def turn_count(self) -> int:
        return sum(1 for m in self.messages if m.role == "user")

    @property
    def is_empty(self) -> bool:
        return len(self.messages) == 0
