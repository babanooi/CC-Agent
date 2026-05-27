"""会话管理服务"""
import uuid
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from memory.conversation import ConversationMemory
from config import settings as config

logger = logging.getLogger(__name__)


@dataclass
class Session:
    session_id: str
    user_id: str
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_active: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class SessionManager:
    def __init__(self, llm=None):
        self.sessions: dict[str, Session] = {}
        self.timeout = timedelta(hours=config.session_timeout_hours)
        self._llm = llm

    def get_or_create(self, session_id: str = None, user_id: str = "default") -> Session:
        if session_id and session_id in self.sessions:
            s = self.sessions[session_id]
            last = datetime.strptime(s.last_active, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last > self.timeout:
                del self.sessions[session_id]
            else:
                s.last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return s
        sid = session_id or str(uuid.uuid4())[:8]
        s = Session(
            session_id=sid, user_id=user_id,
            memory=ConversationMemory(llm=self._llm),
        )
        self.sessions[sid] = s
        return s

    def remove(self, session_id: str):
        self.sessions.pop(session_id, None)

    def list_all(self) -> list[dict]:
        return [{"session_id": s.session_id, "user_id": s.user_id,
                 "turn_count": s.memory.turn_count, "created_at": s.created_at}
                for s in self.sessions.values()]
