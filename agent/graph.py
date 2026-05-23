"""LangGraph Agent 状态机编排"""
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_community.chat_models import ChatTongyi
from config import settings as config

logger = logging.getLogger(__name__)


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


def classify_intent(state: AgentState) -> dict:
    from agent.intent import IntentClassifier
    result = IntentClassifier().classify(state["question"], state.get("chat_history", ""))
    return {"intent": result["intent"], "intent_confidence": result["confidence"],
            "is_chitchat": result["intent"] == "chitchat"}


def rewrite_query(state: AgentState) -> dict:
    from memory.query_rewriter import QueryRewriter
    result = QueryRewriter().rewrite(state["question"], state.get("chat_history", ""))
    return {"rewritten_query": result["rewritten"]}


def retrieve(state: AgentState, rag_service=None) -> dict:
    from agent.router import get_strategy
    query = state.get("rewritten_query", state["question"])
    strategy = get_strategy(state.get("intent", "product_query"))
    docs = rag_service.hybrid.search_as_documents(query, top_k=strategy["top_k"])
    if docs and strategy["need_rerank"]:
        doc_dicts = [{"text": d.page_content, "metadata": d.metadata} for d in docs]
        reranked = rag_service.reranker.rerank(query, doc_dicts)
        context = "\n".join([d["text"] for d in reranked]) if reranked else "\n".join([d.page_content for d in docs])
    else:
        context = "\n".join([d.page_content for d in docs]) if docs else "无相关资料"
    return {"context": context}


def generate(state: AgentState, rag_service=None) -> dict:
    from agent.router import get_prompt
    prompt_template = get_prompt(state.get("intent", "product_query"))
    input_parts = []
    if state.get("user_profile"):
        input_parts.append(f"【用户信息】\n{state['user_profile']}")
    if state.get("chat_history"):
        input_parts.append(f"【对话历史】\n{state['chat_history']}")
    input_parts.append(f"【当前问题】\n{state['question']}")
    full_input = "\n\n".join(input_parts)
    context = state.get("context", "无相关资料")
    if state.get("retry_count", 0) > 0 and state.get("verification", {}).get("suggestion"):
        context = f"【改进要求：{state['verification']['suggestion']}】\n\n{context}"
    prompt_text = prompt_template.format(context=context, input=full_input)
    llm = ChatTongyi(model=config.chat_model, dashscope_api_key=config.dashscope_api_key)
    return {"answer": llm.invoke(prompt_text).content}


def chitchat(state: AgentState) -> dict:
    llm = ChatTongyi(model=config.chat_model, dashscope_api_key=config.dashscope_api_key)
    answer = llm.invoke(f"你是友好客服助手，简洁回复闲聊。\n\n用户：{state['question']}").content
    return {"answer": answer, "context": "闲聊"}


def verify(state: AgentState) -> dict:
    from agent.verifier import AnswerVerifier
    result = AnswerVerifier().verify(state["question"], state["answer"], state.get("context", ""))
    return {"verification": result}


def prepare_output(state: AgentState) -> dict:
    return {"final_output": {
        "answer": state["answer"],
        "intent": {"intent": state.get("intent"), "confidence": state.get("intent_confidence", 0)},
        "rewritten_query": {"rewritten": state.get("rewritten_query", state["question"])},
        "verification": state.get("verification", {}),
        "retry_count": state.get("retry_count", 0),
    }}


def route_intent(state: AgentState) -> str:
    return "chitchat" if state.get("is_chitchat") else "retrieve"


def check_verify(state: AgentState) -> str:
    v = state.get("verification", {})
    return "output" if v.get("pass", True) or state.get("retry_count", 0) >= 1 else "retry"


def build_graph(rag_service):
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("retrieve", lambda s: retrieve(s, rag_service))
    graph.add_node("generate", lambda s: generate(s, rag_service))
    graph.add_node("chitchat", chitchat)
    graph.add_node("verify", verify)
    graph.add_node("output", prepare_output)
    graph.add_node("retry", lambda s: {"retry_count": s.get("retry_count", 0) + 1})
    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges("classify_intent", route_intent, {"chitchat": "chitchat", "retrieve": "rewrite_query"})
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges("verify", check_verify, {"output": "output", "retry": "retry"})
    graph.add_edge("retry", "retrieve")
    graph.add_edge("chitchat", "output")
    graph.add_edge("output", END)
    return graph.compile()
