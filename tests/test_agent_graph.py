"""测试 Agent 图结构"""
import pytest


@pytest.fixture(scope="module")
def graph():
    """构建图（不依赖 LLM 进行结构测试）"""
    try:
        from core.rag_service import RagService
        rag = RagService()
        return rag.agent_graph
    except Exception:
        pytest.skip("无法构建 Agent 图（可能缺少 API key）")


class TestAgentGraphStructure:
    def test_graph_built(self, graph):
        assert graph is not None

    def test_nodes_exist(self, graph):
        nodes = list(graph.get_graph().nodes.keys())
        for node in {"classify_intent", "vision_analyze", "rewrite_query",
                     "react_generate", "chitchat", "verify", "output", "retry"}:
            assert node in nodes, f"节点 {node} 缺失"
        # ReAct 模式已移除独立的 retrieve + generate 节点
        assert "retrieve" not in nodes, "retrieve 节点应在 ReAct 模式中被移除"
        assert "generate" not in nodes, "generate 节点应在 ReAct 模式中被移除"

    def test_edges_exist(self, graph):
        edges = graph.get_graph().edges
        assert len(edges) > 0
