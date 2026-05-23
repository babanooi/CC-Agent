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
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ConversationMemory:
    def __init__(self, window_size: int = None):
        self.messages: list[Message] = []
        self.summary: str = ""
        self.window_size = window_size or config.memory_window_size

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
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
                parts.append(f"{label}: {m.content}")
        return "\n".join(parts)

    def get_chat_history(self, n: int = None) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.get_recent(n)]

    def _compress(self):
        overflow = self.messages[:self.window_size]
        self.messages = self.messages[self.window_size:]
        if not overflow:
            return
        from langchain_community.chat_models import ChatTongyi
        history = "\n".join(f"{'用户' if m.role == 'user' else '助手'}: {m.content}" for m in overflow)
        prompt = f"将以下对话压缩为简洁摘要（不超过200字），保留关键事实和用户偏好：\n\n{history}"
        try:
            llm = ChatTongyi(model=config.chat_model, dashscope_api_key=config.dashscope_api_key)
            new_summary = llm.invoke(prompt).content
            self.summary = f"{self.summary}\n{new_summary}" if self.summary else new_summary
        except Exception as e:
            logger.error("摘要压缩失败: %s", e)

    def clear(self):
        self.messages.clear(); self.summary = ""

    @property
    def turn_count(self) -> int:
        return sum(1 for m in self.messages if m.role == "user")

    @property
    def is_empty(self) -> bool:
        return len(self.messages) == 0
