"""
CloudAgent 智能客服系统 - 入口
"""
import uuid
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.rag_service import RagService
from core.knowledge_service import KnowledgeService
from core.session_service import SessionManager
from api import chat, knowledge, user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CloudAgent 智能客服", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# 请求追踪中间件
@app.middleware("http")
async def request_tracing(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id
    start = time.time()
    logger.info("[%s] %s %s", request_id, request.method, request.url.path)
    response = await call_next(request)
    elapsed = time.time() - start
    response.headers["X-Request-ID"] = request_id
    logger.info("[%s] %s %s → %d (%.2fs)", request_id, request.method, request.url.path, response.status_code, elapsed)
    return response


# 初始化服务并挂载到 app.state
rag = RagService()
rag.sync_bm25()
knowledge_svc = KnowledgeService()
session_mgr = SessionManager(llm=rag.llm)

app.state.rag = rag
app.state.knowledge = knowledge_svc
app.state.sessions = session_mgr

# 注册路由
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"service": "CloudAgent", "version": "2.0", "status": "running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "bm25_docs": rag.bm25.doc_count,
        "active_sessions": len(session_mgr.sessions),
    }
