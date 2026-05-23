"""知识库 API"""
from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/knowledge", tags=["知识库"])

_knowledge = None
_rag = None

def init(knowledge, rag):
    global _knowledge, _rag
    _knowledge, _rag = knowledge, rag


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    result = _knowledge.upload(content, file.filename)
    _rag.sync_bm25()
    return {"msg": result, "filename": file.filename}
