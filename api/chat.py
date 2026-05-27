"""对话 API"""
import base64
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config import settings as config

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    user_id: str = "default"


def _get_rag(request: Request):
    return request.app.state.rag


def _get_sessions(request: Request):
    return request.app.state.sessions


def _validate_images(files: list[UploadFile]) -> list[str]:
    """校验图片并转为 base64 列表"""
    if len(files) > config.max_images_per_message:
        raise HTTPException(400, f"单次最多上传 {config.max_images_per_message} 张图片")
    result = []
    max_bytes = config.max_image_size_mb * 1024 * 1024
    for f in files:
        data = f.file.read()
        if len(data) > max_bytes:
            raise HTTPException(400, f"图片 {f.filename} 超过 {config.max_image_size_mb}MB 限制")
        b64 = base64.b64encode(data).decode("utf-8")
        # 拼接 data URI 前缀，DashScope 多模态 API 需要
        content_type = f.content_type or "image/jpeg"
        result.append(f"data:{content_type};base64,{b64}")
    return result


# ==================== 纯文本接口（保持不变，向后兼容）====================

@router.post("")
async def chat(req: ChatRequest, request: Request):
    rag = _get_rag(request)
    sessions = _get_sessions(request)
    session = sessions.get_or_create(req.session_id, req.user_id)
    result = await rag.chat(req.question, session.memory, req.user_id)
    return {
        "answer": result["answer"], "session_id": session.session_id,
        "turn_count": session.memory.turn_count, "intent": result.get("intent", {}),
        "verification": result.get("verification", {}),
    }


@router.post("/stream")
async def chat_stream(req: ChatRequest, request: Request):
    rag = _get_rag(request)
    sessions = _get_sessions(request)
    session = sessions.get_or_create(req.session_id, req.user_id)

    async def generate():
        async for token in rag.chat_stream(req.question, session.memory, req.user_id):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


# ==================== 图片对话接口（multipart/form-data）====================

@router.post("/image")
async def chat_image(
    question: str = Form(...),
    session_id: str | None = Form(None),
    user_id: str = Form("default"),
    images: list[UploadFile] = File(default=[]),
    request: Request = None,
):
    rag = _get_rag(request)
    sessions = _get_sessions(request)

    # 校验并转 base64
    image_b64_list = _validate_images(images) if images else []

    session = sessions.get_or_create(session_id, user_id)
    result = await rag.chat(question, session.memory, user_id, images=image_b64_list)
    return {
        "answer": result["answer"], "session_id": session.session_id,
        "turn_count": session.memory.turn_count, "intent": result.get("intent", {}),
        "verification": result.get("verification", {}),
        # 返回图像识别结果给前端
        "image_desc": result.get("image_desc", ""),
        "detected_products": result.get("detected_products", []),
    }


@router.post("/image/stream")
async def chat_image_stream(
    question: str = Form(...),
    session_id: str | None = Form(None),
    user_id: str = Form("default"),
    images: list[UploadFile] = File(default=[]),
    request: Request = None,
):
    rag = _get_rag(request)
    sessions = _get_sessions(request)

    image_b64_list = _validate_images(images) if images else []
    session = sessions.get_or_create(session_id, user_id)

    async def generate():
        async for token in rag.chat_stream(question, session.memory, user_id, images=image_b64_list):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


# ==================== 会话管理 ====================

@router.post("/{session_id}/end")
async def end_session(session_id: str, request: Request, user_id: str = "default"):
    rag = _get_rag(request)
    sessions = _get_sessions(request)
    session = sessions.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "会话不存在")
    await rag.end_session(user_id, session.memory)
    sessions.remove(session_id)
    return {"msg": f"会话 {session_id} 已结束"}


@router.get("/{session_id}/history")
async def get_history(session_id: str, request: Request):
    sessions = _get_sessions(request)
    session = sessions.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "会话不存在")
    messages = session.memory.get_chat_history()
    # 把 image_count 也返回给前端
    full_messages = [
        {"role": m.role, "content": m.content, "image_count": getattr(m, "image_count", 0)}
        for m in session.memory.get_recent()
    ]
    return {"session_id": session_id, "messages": full_messages,
            "summary": session.memory.summary}
