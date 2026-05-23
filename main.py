"""
CloudAgent 智能客服系统 - 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.rag_service import RagService
from core.knowledge_service import KnowledgeService
from core.session_service import SessionManager
from api import chat, knowledge, user

app = FastAPI(title="CloudAgent 智能客服", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# 初始化服务
rag = RagService()
rag.sync_bm25()
knowledge_svc = KnowledgeService()
session_mgr = SessionManager()

# 注入服务到 API 层
chat.init(rag, session_mgr)
knowledge.init(knowledge_svc, rag)
user.init(rag, session_mgr)

# 注册路由
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"service": "CloudAgent", "version": "2.0", "status": "running"}
