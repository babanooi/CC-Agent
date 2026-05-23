"""
LangGraph Agent 测试脚本
测试 Agent 编排流程
"""
import sys, os, ssl, json

ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("  LangGraph Agent 编排测试")
    print("=" * 60)

    # 1. 测试图构建
    print("\n测试1：Agent 图构建")
    try:
        from agent.langgraph_agent import build_agent_graph, CloudAgent
        graph = build_agent_graph()
        print(f"  ✅ 图构建成功")
        print(f"  节点: {list(graph.get_graph().nodes.keys())}")
    except Exception as e:
        print(f"  ❌ 图构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 2. 测试 Agent 初始化
    print("\n测试2：Agent 初始化")
    try:
        agent = CloudAgent()
        print(f"  ✅ CloudAgent 初始化成功")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. 测试 Agent 运行（需要 API 连通）
    print("\n测试3：Agent 运行测试")
    test_cases = [
        {"question": "你好呀", "expect_intent": "chitchat"},
        {"question": "小米15 Pro电池多大？", "expect_intent": "product_query"},
        {"question": "小米15 Pro和华为Mate 70 Pro哪个好？", "expect_intent": "product_compare"},
    ]

    for tc in test_cases:
        try:
            result = agent.run(tc["question"])
            intent = result.get("intent", {}).get("intent", "unknown")
            answer = result.get("answer", "")[:60]
            retry = result.get("retry_count", 0)
            verified = result.get("verification", {}).get("pass", "?")

            ok = intent == tc["expect_intent"]
            print(f"  {'✅' if ok else '❌'} [{intent}] (retry={retry}, verified={verified}) | {tc['question']}")
            print(f"     回答: {answer}...")
            if not ok:
                print(f"     预期: {tc['expect_intent']}")
        except Exception as e:
            print(f"  ❌ {tc['question']} | 错误: {e}")

    # 4. 显示图结构
    print("\n测试4：Agent 图结构")
    try:
        g = graph.get_graph()
        print(f"  节点数: {len(g.nodes)}")
        print(f"  边数: {len(g.edges)}")
        print(f"  节点列表:")
        for node in g.nodes:
            print(f"    - {node}")
    except Exception as e:
        print(f"  ❌ 获取图结构失败: {e}")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)
