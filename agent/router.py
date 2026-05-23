"""意图路由（选择 Prompt 模板和检索策略）"""
from langchain_core.prompts import ChatPromptTemplate


def _make_prompt(system_msg: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("system", system_msg), ("user", "{input}")])


PROMPTS = {
    "product_query": _make_prompt("你是3C数码产品客服，根据资料准确回答参数问题。简洁准确。\n\n参考资料：\n{context}"),
    "product_compare": _make_prompt("你是3C数码产品客服，用表格对比产品参数，给出总结建议。\n\n参考资料：\n{context}"),
    "troubleshoot": _make_prompt("你是技术支持助手，按步骤引导排查，语气耐心友好。\n\n参考资料：\n{context}"),
    "purchase_advice": _make_prompt("你是产品导购助手，推荐2-3款产品并说明理由。\n\n参考资料：\n{context}"),
    "chitchat": _make_prompt("你是友好的客服助手，简洁友好回复闲聊。"),
}

STRATEGIES = {
    "product_query": {"top_k": 6, "need_rerank": True},
    "product_compare": {"top_k": 10, "need_rerank": True},
    "troubleshoot": {"top_k": 8, "need_rerank": True},
    "purchase_advice": {"top_k": 10, "need_rerank": True},
    "chitchat": {"top_k": 0, "need_rerank": False},
}


def get_prompt(intent: str) -> ChatPromptTemplate:
    return PROMPTS.get(intent, PROMPTS["product_query"])


def needs_retrieval(intent: str) -> bool:
    return intent != "chitchat"


def get_strategy(intent: str) -> dict:
    return STRATEGIES.get(intent, STRATEGIES["product_query"])
