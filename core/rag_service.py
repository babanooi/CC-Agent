"""
RAG 核心服务
组装各层组件，提供统一的业务接口
"""
import logging
from typing import AsyncGenerator
from langchain_community.chat_models import ChatTongyi
from retrieval.embedding import EmbeddingService
from retrieval.bm25 import BM25Retriever
from retrieval.vector import VectorRetriever, HybridRetriever
from retrieval.reranker import Reranker
from memory.conversation import ConversationMemory
from memory.long_term import LongTermMemory
from memory.user_profile import UserProfileExtractor
from agent.intent import IntentClassifier
from agent.vision import VisionAnalyzer
from agent.graph import build_graph
from agent.router import get_prompt, get_strategy
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

        # 大模型（共享实例，复用连接）
        self.llm = ChatTongyi(
            model=config.chat_model,
            dashscope_api_key=config.dashscope_api_key,
            streaming=True,
        )
        self.light_llm = ChatTongyi(
            model=config.classifier_model,
            dashscope_api_key=config.dashscope_api_key,
            temperature=0,
        )
        self.react_llm = ChatTongyi(
            model=config.chat_model,
            dashscope_api_key=config.dashscope_api_key,
            streaming=False,  # tool calling 必须非流式
        )

        # 视觉层
        self.vision_analyzer = VisionAnalyzer()

        # 记忆层
        self.profile_extractor = UserProfileExtractor()
        self._long_term_cache: dict[str, LongTermMemory] = {}

        # Agent 层
        self.intent_classifier = IntentClassifier()
        self.agent_graph = build_graph(self)

        # 注入工具
        set_rag_service(self)

        logger.info("RagService 初始化完成")

    def sync_bm25(self):
        try:
            collection = self.vector.store._collection
            offset = 0
            batch_size = 500
            total = 0
            while True:
                data = collection.get(
                    include=["documents", "metadatas"],
                    limit=batch_size, offset=offset,
                )
                if not data["documents"]:
                    break
                if offset == 0:
                    self.bm25.clear()
                self.bm25.add_documents(data["documents"], data["metadatas"])
                total += len(data["documents"])
                offset += batch_size
            logger.info("BM25 同步完成: %d 条", total)
        except Exception as e:
            logger.error("BM25 同步失败: %s", e)

    def _get_long_term(self, user_id: str) -> LongTermMemory:
        if user_id not in self._long_term_cache:
            self._long_term_cache[user_id] = LongTermMemory(user_id)
        return self._long_term_cache[user_id]

    async def chat(
        self, question: str, memory: ConversationMemory = None,
        user_id: str = "default", images: list[str] = None,
    ) -> dict:
        """主对话接口（异步），支持图片"""
        long_mem = self._get_long_term(user_id)
        result = await self.agent_graph.ainvoke({
            "question": question,
            "chat_history": memory.get_context_string() if memory else "",
            "user_profile": long_mem.get_context_string(),
            "intent": "", "intent_confidence": 0, "rewritten_query": "",
            "context": "", "answer": "", "verification": {},
            "retry_count": 0, "is_chitchat": False, "final_output": {},
            "images": images or [], "image_desc": "", "detected_products": [],
        })
        output = result.get("final_output", result)
        if memory:
            img_count = len(images) if images else 0
            memory.add_message("user", question, image_count=img_count)
            memory.add_message("assistant", output.get("answer", ""))
        return output

    async def chat_stream(
        self, question: str, memory: ConversationMemory = None,
        user_id: str = "default", images: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话接口 — ReAct 预检索 + 最终答案流式输出"""
        long_mem = self._get_long_term(user_id)
        image_list = images or []
        has_image = bool(image_list)

        # 1. 视觉分析（有图片时）
        image_desc = ""
        detected_products: list[str] = []
        if has_image:
            vision_result = await self.vision_analyzer.aanalyze(image_list, question)
            image_desc = vision_result["description"]
            detected_products = vision_result.get("detected_products", [])

        # 2. 意图分类
        intent_result = await self.intent_classifier.aclassify(
            question,
            memory.get_context_string() if memory else "",
            llm=self.light_llm, has_image=has_image,
        )
        intent = intent_result["intent"]
        is_chitchat = intent == "chitchat"

        # 3. 查询改写
        if not is_chitchat:
            from memory.query_rewriter import QueryRewriter
            rewriter = QueryRewriter()
            rewrite_result = await rewriter.arewrite(
                question,
                memory.get_context_string() if memory else "",
                llm=self.llm,
            )
            query = rewrite_result["rewritten"]
        else:
            query = question

        # 4. ReAct 工具调用循环（非流式，快速决策）
        context = ""
        if not is_chitchat:
            context = await self._run_react_tool_loop(
                question=query,
                intent=intent,
                user_profile=long_mem.get_context_string(),
                chat_history=memory.get_context_string() if memory else "",
                image_desc=image_desc,
                detected_products=detected_products,
            )
        else:
            context = "闲聊"

        # 5. 构建 prompt 并用流式 LLM 输出最终回答
        if is_chitchat:
            prompt_text = f"你是友好客服助手，简洁回复闲聊。\n\n用户：{question}"
        else:
            prompt_template = get_prompt(intent)
            input_parts = []
            if long_mem.get_context_string():
                input_parts.append(f"【用户信息】\n{long_mem.get_context_string()}")
            if memory and memory.get_context_string():
                input_parts.append(f"【对话历史】\n{memory.get_context_string()}")
            if image_desc:
                products_str = "、".join(detected_products) or "未知"
                input_parts.append(f"【图片识别结果】\n用户发送了图片，识别到产品: {products_str}\n描述: {image_desc}")
            input_parts.append(f"【当前问题】\n{question}")
            full_input = "\n\n".join(input_parts)
            prompt_text = prompt_template.format(context=context, input=full_input)

        full_answer = ""
        async for chunk in self.llm.astream(prompt_text):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                full_answer += token
                yield token

        # 6. 更新记忆
        if memory:
            img_count = len(image_list)
            memory.add_message("user", question, image_count=img_count)
            memory.add_message("assistant", full_answer)

    async def _run_react_tool_loop(
        self, question: str, intent: str, user_profile: str,
        chat_history: str, image_desc: str, detected_products: list[str],
    ) -> str:
        """ReAct 循环：LLM 自主调用工具检索，返回汇总上下文"""
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
        from agent.router import get_prompt
        from agent.tools import (
            search_knowledge, compare_products, get_troubleshoot_guide,
        )
        from agent.graph import _build_input_text, _execute_tool

        tools = [search_knowledge, compare_products, get_troubleshoot_guide]
        llm_with_tools = self.react_llm.bind_tools(tools)

        prompt_template = get_prompt(intent)
        system_text = prompt_template.messages[0].prompt.template
        system = SystemMessage(content=(
            f"{system_text}\n\n"
            "重要：你可以使用工具搜索知识库来获取准确信息。"
            "在回答前，先用工具检索相关资料，不要凭记忆编造。"
            "如果一次检索信息不够，可以换关键词再搜。"
            "信息充分后，回答 'done'。"
        ))

        # 构造与图节点一致的状态结构
        dummy_state = {
            "question": question,
            "user_profile": user_profile,
            "chat_history": chat_history,
            "image_desc": image_desc,
            "detected_products": detected_products,
            "retry_count": 0,
            "verification": {},
        }
        input_text = _build_input_text(dummy_state)
        messages = [system, HumanMessage(content=input_text)]

        context_chunks: list[str] = []
        max_iter = 5

        for i in range(max_iter):
            response = await llm_with_tools.ainvoke(messages)

            if response.tool_calls:
                messages.append(response)
                for tc in response.tool_calls:
                    result_text = await _execute_tool(tc, self)
                    messages.append(ToolMessage(
                        content=result_text, tool_call_id=tc["id"],
                    ))
                    context_chunks.append(result_text)
                logger.info("Stream ReAct 第 %d 轮: %d 个工具调用", i + 1, len(response.tool_calls))
            else:
                logger.info("Stream ReAct 完成: 共 %d 轮", i + 1)
                break

        return "\n\n".join(context_chunks) if context_chunks else "无相关资料"

    async def end_session(self, user_id: str, memory: ConversationMemory):
        if memory.is_empty:
            return
        long_mem = self._get_long_term(user_id)
        extracted = await self.profile_extractor.aextract(
            memory.get_context_string(), llm=self.light_llm,
        )
        if extracted.get("profile"):
            long_mem.update_profile(extracted["profile"])
        for p in extracted.get("preferences", []):
            long_mem.add_preference(p)
        for p in extracted.get("mentioned_products", []):
            long_mem.add_mentioned_product(p)
        if extracted.get("summary"):
            long_mem.add_session_summary(extracted["summary"])
