"""Agent 工具定义"""
from langchain_core.tools import tool

_rag_service = None

def set_rag_service(service):
    global _rag_service
    _rag_service = service

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        from core.rag_service import RagService
        _rag_service = RagService()
    return _rag_service


@tool
def search_knowledge(query: str, top_k: int = 6) -> str:
    """从3C数码产品知识库检索信息。回答产品参数问题时使用。"""
    docs = get_rag_service().hybrid.search_as_documents(query, top_k=top_k)
    if not docs:
        return "未找到相关信息"
    return "\n\n".join(f"[{d.metadata.get('source','')}] {d.page_content}" for d in docs)


@tool
def compare_products(product_names: list[str]) -> str:
    """对比多款产品参数。用户想比较不同产品时使用。"""
    service = get_rag_service()
    all_docs = []
    for name in product_names:
        all_docs.extend(service.hybrid.search_as_documents(name, top_k=3))
    if not all_docs:
        return "未找到产品信息"
    return "\n\n".join(f"[{d.metadata.get('source','')}] {d.page_content}" for d in all_docs)


@tool
def get_troubleshoot_guide(problem: str) -> str:
    """获取故障排查指南。用户遇到手机问题时使用。"""
    docs = get_rag_service().hybrid.search_as_documents(problem, top_k=8)
    if not docs:
        return "未找到排查信息，建议联系售后"
    return "\n\n".join(f"[{d.metadata.get('source','')}] {d.page_content}" for d in docs)
