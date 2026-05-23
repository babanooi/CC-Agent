"""
CloudAgent 智能客服系统 - 综合测试脚本
测试意图分类、多轮对话、长期记忆、评测体系
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix SSL if needed
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def test_intent_classifier():
    """测试意图分类器"""
    print("=" * 60)
    print("测试1：意图分类器（Qwen-Turbo）")
    print("=" * 60)

    from agent.intent import IntentClassifier
    classifier = IntentClassifier()

    tests = [
        ("你好呀", "chitchat"),
        ("小米15 Pro电池多大？", "product_query"),
        ("小米15 Pro和华为Mate 70 Pro哪个好？", "product_compare"),
        ("我手机充不进电了怎么办", "troubleshoot"),
        ("5000块推荐个手机", "purchase_advice"),
    ]

    correct = 0
    for question, expected in tests:
        result = classifier.classify(question)
        actual = result["intent"]
        ok = actual == expected
        if ok: correct += 1
        print(f"  {'✅' if ok else '❌'} [{actual}] conf={result['confidence']:.2f} | {question}")
        if not ok:
            print(f"     预期: {expected}")

    print(f"\n  准确率: {correct}/{len(tests)} ({correct/len(tests)*100:.0f}%)\n")
    return correct == len(tests)


def test_multi_turn():
    """测试多轮对话 + 查询改写"""
    print("=" * 60)
    print("测试2：多轮对话 + 查询改写")
    print("=" * 60)

    from core.rag_service import RagService
    from core.session_service import SessionManager

    rag = RagService()
    rag.sync_bm25_index()
    sm = SessionManager()
    session = sm.create_session(user_id="test_user")

    conversations = [
        "小米15 Pro怎么样？",
        "它和华为Mate 70 Pro比呢？",  # 指代消解
        "那续航呢？",                   # 省略补全
    ]

    for q in conversations:
        result = rag.chat(q, session.memory)
        intent = result["intent"]["intent"]
        rewritten = result["rewritten_query"]["rewritten"]
        docs = result["retrieved_docs"]
        print(f"  用户: {q}")
        print(f"  意图: {intent} | 改写: {rewritten[:30]}... | 检索: {docs}条")
        print(f"  回答: {result['answer'][:80]}...")
        print()

    print(f"  会话轮数: {session.memory.turn_count}")
    return True


def test_long_term_memory():
    """测试长期记忆"""
    print("=" * 60)
    print("测试3：长期记忆 + 用户画像")
    print("=" * 60)

    from memory.long_term import LongTermMemory
    from memory.user_profile import UserProfileExtractor

    # 创建用户记忆
    ltm = LongTermMemory("test_user_001")
    ltm.update_profile({"budget": "5000左右", "usage": "拍照"})
    ltm.add_preference("喜欢拍照")
    ltm.add_preference("看重续航")
    ltm.add_mentioned_product("小米15 Pro")
    ltm.add_session_summary("用户预算5000，主要需求是拍照和续航")

    # 读取验证
    ltm2 = LongTermMemory("test_user_001")
    context = ltm2.get_context_string()
    print(f"  用户画像上下文:\n{context[:300]}")
    print(f"  文件路径: {ltm2.file_path}")
    print(f"  数据完整: {'✅' if ltm2.data['profile'] else '❌'}")

    # 清理测试数据
    os.remove(ltm2.file_path)
    return True


def test_evaluation():
    """测试评测框架"""
    print("=" * 60)
    print("测试4：评测框架")
    print("=" * 60)

    from evaluation.rag_evaluator import RAGEvaluator

    evaluator = RAGEvaluator()
    test_data = evaluator.load_test_data()
    print(f"  测试数据: {len(test_data)} 条")

    # 测试检索评估
    mock_docs = [
        {"metadata": {"source": "xiaomi15pro.txt"}},
        {"metadata": {"source": "huawei_mate70pro.txt"}},
    ]
    retrieval = evaluator.eval_retrieval(mock_docs, ["xiaomi15pro.txt"])
    print(f"  检索评估: Precision={retrieval['precision']}, Recall={retrieval['recall']}, MRR={retrieval['mrr']}")

    return True


def test_api_structure():
    """测试API结构"""
    print("=" * 60)
    print("测试5：API路由结构")
    print("=" * 60)

    from api.chat import RAG, UPDATE

    routes = []
    for route in RAG.routes:
        routes.append(f"  {route.methods} {route.path}")
    for route in UPDATE.routes:
        routes.append(f"  {route.methods} {route.path}")

    print(f"  共 {len(routes)} 个路由:")
    for r in routes:
        print(f"    {r}")

    return len(routes) > 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CloudAgent 智能客服系统 - 综合测试")
    print("=" * 60 + "\n")

    tests = [
        ("意图分类器", test_intent_classifier),
        ("API结构", test_api_structure),
        ("长期记忆", test_long_term_memory),
    ]

    # 只有修复依赖后才能运行这些测试
    try:
        from langchain_core.output_parsers import StrOutputParser
        tests.append(("多轮对话", test_multi_turn))
        tests.append(("评测框架", test_evaluation))
    except ImportError:
        print("⚠️ langchain_core 依赖未修复，跳过 RAG 相关测试\n")

    passed = 0
    total = len(tests)
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            print(f"  ❌ {name} 测试失败: {e}\n")

    print("\n" + "=" * 60)
    print(f"  测试结果: {passed}/{total} 通过")
    print("=" * 60)
