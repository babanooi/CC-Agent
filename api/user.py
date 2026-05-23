"""用户 API"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/users", tags=["用户"])

_sessions = None
_rag = None

def init(rag, sessions):
    global _rag, _sessions
    _rag, _sessions = rag, sessions


@router.get("/{user_id}/profile")
async def get_profile(user_id: str):
    from memory.long_term import LongTermMemory
    ltm = LongTermMemory(user_id)
    return {"user_id": user_id, "data": ltm.data}


@router.get("/sessions")
async def list_sessions():
    return {"sessions": _sessions.list_all()}
