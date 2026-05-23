"""
RAG 核心服务
组装各层组件，提供统一的业务接口
"""
import logging
from langchain_community.chat_models import ChatTongyi
from retrieval.embedding import EmbeddingService
from retrieval.bm25 import BM25Retriever
from retrieval.vector import VectorRetriever, HybridRetriever
from retrieval.reranker import Reranker
from memory.conversation import ConversationMemory
from memory.long_term import LongTermMemory
from memory.user_profile import UserProfileExtractor
from memory.query_rewriter import QueryRewriter
from agent.intent import IntentClassifier
from agent.graph import build_graph
from agent import router as intent_router
from agent.tools import set_rag_service
from config import settings as config

logger = logging.getLogger(__name__)


class RagService:
    def __init__(self):
        # 检索层
        self.embedding = EmbeddingService()
        self.bm25 = BM25Retriever()
        self.vector = VectorRetriever(self.embedding)
        self.hybrid = HybridRetriever(self.vector, self.bm25)
        self.reranker = Reranker()

        # 记忆层
        self.profile_extractor = UserProfileExtractor()
        self._long_term_cache: dict[str, LongTermMemory] = {}

        # Agent 层
        self.intent_classifier = IntentClassifier()
        self.agent_graph = build_graph(self)

        # 注入工具
        set_rag_service(self)

        # 大模型
        self.llm = ChatTongyi(model=config.chat_model, dashscope_api_key=config.dashscope_api_key, streaming=True)

        logger.info("RagService 初始化完成")

    def sync_bm25(self):
        try:
            data = self.vector.store._collection.get(include=["documents", "metadatas"])
            if data["documents"]:
                self.bm25.clear()
                self.bm25.add_documents(data["documents"], data["metadatas"])
                logger.info("BM25 同步完成: %d 条", len(data["documents"]))
        except Exception as e:
            logger.error("BM25 同步失败: %s", e)

    def _get_long_term(self, user_id: str) -> LongTermMemory:
        if user_id not in self._long_term_cache:
            self._long_term_cache[user_id] = LongTermMemory(user_id)
        return self._long_term_cache[user_id]

    def chat(self, question: str, memory: ConversationMemory = None, user_id: str = "default") -> dict:
        """主对话接口"""
        long_mem = self._get_long_term(user_id)
        result = self.agent_graph.invoke({
            "question": question,
            "chat_history": memory.get_context_string() if memory else "",
            "user_profile": long_mem.get_context_string(),
            "intent": "", "intent_confidence": 0, "rewritten_query": "",
            "context": "", "answer": "", "verification": {},
            "retry_count": 0, "is_chitchat": False, "final_output": {},
        })
        output = result.get("final_output", result)
        if memory:
            memory.add_message("user", question)
            memory.add_message("assistant", output.get("answer", ""))
        return output

    def end_session(self, user_id: str, memory: ConversationMemory):
        if memory.is_empty:
            return
        long_mem = self._get_long_term(user_id)
        extracted = self.profile_extractor.extract(memory.get_context_string())
        if extracted.get("profile"):
            long_mem.update_profile(extracted["profile"])
        for p in extracted.get("preferences", []):
            long_mem.add_preference(p)
        for p in extracted.get("mentioned_products", []):
            long_mem.add_mentioned_product(p)
        if extracted.get("summary"):
            long_mem.add_session_summary(extracted["summary"])
