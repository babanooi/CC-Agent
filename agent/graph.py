"""LangGraph Agent 状态机编排 — ReAct 模式"""
import json
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)

MAX_REACT_ITERATIONS = 5


class AgentState(TypedDict):
    question: str
    intent: str
    intent_confidence: float
    rewritten_query: str
    context: str
    answer: str
    verification: dict
    retry_count: int
    chat_history: str
    user_profile: str
    is_chitchat: bool
    final_output: dict
    # 多模态字段
    images: list[str]
    image_desc: str
    detected_products: list[str]


def route_intent(state: AgentState) -> str:
    return "chitchat" if state.get("is_chitchat") else "vision_analyze"


def check_verify(state: AgentState) -> str:
    v = state.get("verification", {})
    if v.get("pass", True) or state.get("retry_count", 0) >= 1:
        return "output"
    return "retry"


def _build_input_text(state: AgentState) -> str:
    """构建 ReAct Agent 的输入上下文"""
    parts = []
    if state.get("user_profile"):
        parts.append(f"【用户画像】\n{state['user_profile']}")
    if state.get("chat_history"):
        parts.append(f"【对话历史】\n{state['chat_history']}")
    if state.get("image_desc"):
        products = "、".join(state.get("detected_products", [])) or "未知"
        parts.append(f"【图片识别】用户发送了图片，识别到产品: {products}\n描述: {state['image_desc']}")
    if state.get("retry_count", 0) > 0 and state.get("verification", {}).get("suggestion"):
        parts.append(f"【改进要求】{state['verification']['suggestion']}")
    parts.append(f"【用户问题】{state['question']}")
    return "\n\n".join(parts)


async def _execute_tool(tool_call: dict, rag_service) -> str:
    """执行单个工具调用，返回结果字符串"""
    name = tool_call["name"]
    args = tool_call.get("args", {})
    logger.info("ReAct 调用工具: %s(%s)", name, args)

    try:
        if name == "search_knowledge":
            from agent.tools import search_knowledge
            result = search_knowledge.invoke(args)
        elif name == "compare_products":
            from agent.tools import compare_products
            result = compare_products.invoke(args)
        elif name == "get_troubleshoot_guide":
            from agent.tools import get_troubleshoot_guide
            result = get_troubleshoot_guide.invoke(args)
        else:
            return f"[错误] 未知工具: {name}"
        return str(result)
    except Exception as e:
        logger.error("工具执行失败 %s: %s", name, e)
        return f"[错误] 工具 {name} 执行失败: {e}"


def build_graph(rag_service):
    """构建 LangGraph 状态图，注入 rag_service 供节点使用"""

    async def _classify_intent(state: AgentState) -> dict:
        from agent.intent import IntentClassifier
        has_image = bool(state.get("images", []))
        result = await IntentClassifier().aclassify(
            state["question"], state.get("chat_history", ""),
            llm=rag_service.light_llm, has_image=has_image,
        )
        return {
            "intent": result["intent"],
            "intent_confidence": result["confidence"],
            "is_chitchat": result["intent"] == "chitchat",
        }

    async def _vision_analyze(state: AgentState) -> dict:
        images = state.get("images", [])
        if not images:
            return {"image_desc": "", "detected_products": [], "images": []}
        result = await rag_service.vision_analyzer.aanalyze(
            images, state["question"],
        )
        desc = result["description"]
        products = result.get("detected_products", [])
        logger.info("视觉分析完成: desc=%s, products=%s", desc[:50], products)
        return {
            "image_desc": desc,
            "detected_products": products,
            "images": [],  # 清除 base64，不往后续节点传递
        }

    async def _rewrite_query(state: AgentState) -> dict:
        from memory.query_rewriter import QueryRewriter
        result = await QueryRewriter().arewrite(
            state["question"], state.get("chat_history", ""),
            llm=rag_service.llm,
        )
        return {"rewritten_query": result["rewritten"]}

    async def _react_generate(state: AgentState) -> dict:
        """ReAct 循环：LLM 自主决定何时检索、用什么工具、何时回答"""
        from agent.router import get_prompt
        from agent.tools import (
            search_knowledge, compare_products, get_troubleshoot_guide,
        )

        tools = [search_knowledge, compare_products, get_troubleshoot_guide]
        llm_with_tools = rag_service.react_llm.bind_tools(tools)

        # 构建系统提示
        intent = state.get("intent", "product_query")
        prompt_template = get_prompt(intent)
        system_text = prompt_template.messages[0].prompt.template

        system = SystemMessage(content=(
            f"{system_text}\n\n"
            "重要：你可以使用工具搜索知识库来获取准确信息。"
            "在回答前，先用工具检索相关资料，不要凭记忆编造。"
            "如果一次检索信息不够，可以换关键词再搜。"
            "信息充分后，直接输出最终回答（不要调用工具）。"
        ))

        input_text = _build_input_text(state)
        messages = [system, HumanMessage(content=input_text)]

        context_chunks: list[str] = []

        # ReAct 循环
        for iteration in range(MAX_REACT_ITERATIONS):
            response: AIMessage = await llm_with_tools.ainvoke(messages)

            if response.tool_calls:
                # LLM 决定调用工具 → 执行并反馈
                messages.append(response)
                for tc in response.tool_calls:
                    result_text = await _execute_tool(tc, rag_service)
                    messages.append(ToolMessage(
                        content=result_text, tool_call_id=tc["id"],
                    ))
                    context_chunks.append(result_text)
                logger.info("ReAct 第 %d 轮: 调用了 %d 个工具", iteration + 1, len(response.tool_calls))
            else:
                # LLM 输出最终回答
                logger.info("ReAct 完成: 共 %d 轮, %d 次工具调用",
                            iteration + 1, len(context_chunks))
                return {
                    "answer": response.content or "",
                    "context": "\n\n".join(context_chunks) if context_chunks else "无相关资料",
                }

        # 超过最大迭代次数 → 强制生成回答
        logger.warning("ReAct 达到最大迭代次数 %d，强制生成回答", MAX_REACT_ITERATIONS)
        messages.append(HumanMessage(content="请基于已获取的所有信息，直接回答用户问题。"))
        response = await rag_service.react_llm.ainvoke(messages)
        return {
            "answer": response.content or "",
            "context": "\n\n".join(context_chunks) if context_chunks else "无相关资料",
        }

    async def _chitchat(state: AgentState) -> dict:
        response = await rag_service.llm.ainvoke(
            f"你是友好客服助手，简洁回复闲聊。\n\n用户：{state['question']}"
        )
        return {"answer": response.content, "context": "闲聊"}

    async def _verify(state: AgentState) -> dict:
        from agent.verifier import AnswerVerifier
        result = await AnswerVerifier().averify(
            state["question"], state["answer"], state.get("context", ""),
            llm=rag_service.light_llm,
        )
        return {"verification": result}

    def _output(state: AgentState) -> dict:
        return {"final_output": {
            "answer": state["answer"],
            "context": state.get("context", ""),
            "intent": {"intent": state.get("intent"), "confidence": state.get("intent_confidence", 0)},
            "rewritten_query": {"rewritten": state.get("rewritten_query", state["question"])},
            "verification": state.get("verification", {}),
            "retry_count": state.get("retry_count", 0),
            "image_desc": state.get("image_desc", ""),
            "detected_products": state.get("detected_products", []),
        }}

    def _retry(state: AgentState) -> dict:
        return {"retry_count": state.get("retry_count", 0) + 1}

    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", _classify_intent)
    graph.add_node("vision_analyze", _vision_analyze)
    graph.add_node("rewrite_query", _rewrite_query)
    graph.add_node("react_generate", _react_generate)
    graph.add_node("chitchat", _chitchat)
    graph.add_node("verify", _verify)
    graph.add_node("output", _output)
    graph.add_node("retry", _retry)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges("classify_intent", route_intent, {
        "chitchat": "chitchat",
        "vision_analyze": "vision_analyze",
    })
    graph.add_edge("vision_analyze", "rewrite_query")
    graph.add_edge("rewrite_query", "react_generate")
    graph.add_edge("react_generate", "verify")
    graph.add_conditional_edges("verify", check_verify, {"output": "output", "retry": "retry"})
    graph.add_edge("retry", "react_generate")  # 验证失败 → 重新执行 ReAct
    graph.add_edge("chitchat", "output")
    graph.add_edge("output", END)

    return graph.compile()
