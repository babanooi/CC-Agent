"""对话 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["对话"])

# 服务实例由 main.py 注入
_rag = None
_sessions = None

def init(rag, sessions):
    global _rag, _sessions
    _rag, _sessions = rag, sessions


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    user_id: str = "default"


@router.post("")
async def chat(req: ChatRequest):
    session = _sessions.get_or_create(req.session_id, req.user_id)
    result = _rag.chat(req.question, session.memory, req.user_id)
    return {"answer": result["answer"], "session_id": session.session_id,
            "turn_count": session.memory.turn_count, "intent": result.get("intent", {}),
            "verification": result.get("verification", {})}


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    session = _sessions.get_or_create(req.session_id, req.user_id)
    # 简化版流式（实际可扩展为逐token）
    result = _rag.chat(req.question, session.memory, req.user_id)
    return StreamingResponse(iter([result["answer"]]), media_type="text/plain")


@router.post("/{session_id}/end")
async def end_session(session_id: str, user_id: str = "default"):
    session = _sessions.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "会话不存在")
    _rag.end_session(user_id, session.memory)
    _sessions.remove(session_id)
    return {"msg": f"会话 {session_id} 已结束"}


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    session = _sessions.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "会话不存在")
    return {"session_id": session_id, "messages": session.memory.get_chat_history(),
            "summary": session.memory.summary}
