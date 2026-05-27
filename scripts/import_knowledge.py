"""
将 3C 产品知识库导入 RAG 系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.knowledge_service import KnowledgeService
from core.rag_service import RagService


def import_3c_knowledge():
    kb = KnowledgeService()
    rag = RagService()

    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "data", "3c_knowledge")
    knowledge_dir = os.path.abspath(knowledge_dir)
    if not os.path.exists(knowledge_dir):
        print(f"❌ {knowledge_dir} 目录不存在")
        return

    files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
    print(f"找到 {len(files)} 个知识文档")

    for filename in files:
        filepath = os.path.join(knowledge_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        result = kb.upload(content, filename)
        print(f"  {filename}: {result}")

    print("\n✅ 3C 知识库导入完成！")

    rag.sync_bm25()
    print("✅ BM25 索引同步完成！")


if __name__ == "__main__":
    import_3c_knowledge()
