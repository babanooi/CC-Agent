"""
将 3C 产品知识库导入 RAG 系统
"""
import os
import sys

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_base import KnowledgeBaseService


def import_3c_knowledge():
    kb = KnowledgeBaseService()

    knowledge_dir = os.path.join(os.path.dirname(__file__), "data", "3c_knowledge")
    if not os.path.exists(knowledge_dir):
        print("❌ data/3c_knowledge 目录不存在")
        return

    files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
    print(f"找到 {len(files)} 个知识文档")

    for filename in files:
        filepath = os.path.join(knowledge_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        result = kb.upload_by_str(content, filename)
        print(f"  {filename}: {result}")

    print("\n✅ 3C 知识库导入完成！")

    # 同步 BM25 索引
    from rag import RagService
    rag = RagService()
    rag.sync_bm25_index()
    print("✅ BM25 索引同步完成！")


if __name__ == "__main__":
    import_3c_knowledge()
