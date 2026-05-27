"""知识库 API"""
from fastapi import APIRouter, UploadFile, File, Request

router = APIRouter(prefix="/knowledge", tags=["知识库"])


def _get_knowledge(request: Request):
    return request.app.state.knowledge


def _get_rag(request: Request):
    return request.app.state.rag


@router.post("/upload")
async def upload(file: UploadFile = File(...), request: Request = None):
    knowledge = _get_knowledge(request)
    rag = _get_rag(request)
    content = (await file.read()).decode("utf-8")
    result = knowledge.upload(content, file.filename)
    rag.sync_bm25()
    return {"msg": result, "filename": file.filename}
