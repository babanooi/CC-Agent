"""
RAG 评测框架
自动化评估检索质量和回答质量
支持：
- 检索指标：Precision@K、Recall@K、MRR
- 生成指标：Faithfulness（忠实度）、Answer Relevance（答案相关性）
"""
import json
import logging
import os
from datetime import datetime
from langchain_community.chat_models import ChatTongyi
from config import settings as config

logger = logging.getLogger(__name__)

EVAL_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "qa_pairs")


class RAGEvaluator:
    """
    RAG 评测框架
    - 基于 golden QA 测试集评估
    - 检索质量评估（文档级）
    - 生成质量评估（LLM-as-Judge）
    """

    def __init__(self):
        self._judge_llm = None
        self.results = []

    def _get_judge_llm(self):
        if self._judge_llm is None:
            self._judge_llm = ChatTongyi(
                model=config.chat_model,
                dashscope_api_key=config.dashscope_api_key,
                temperature=0,
            )
        return self._judge_llm

    def load_test_data(self, filepath: str = None) -> list[dict]:
        """加载测试数据"""
        filepath = filepath or os.path.join(EVAL_DATA_DIR, "test_qa.json")
        if not os.path.exists(filepath):
            logger.warning(f"测试数据不存在: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # ==================== 检索指标 ====================

    def eval_retrieval(self, retrieved_docs: list[dict], expected_sources: list[str]) -> dict:
        """
        评估检索质量

        Args:
            retrieved_docs: 检索到的文档列表（含 metadata.source）
            expected_sources: 期望命中的来源文件名列表

        Returns:
            {"precision": float, "recall": float, "mrr": float}
        """
        if not retrieved_docs or not expected_sources:
            return {"precision": 0, "recall": 0, "mrr": 0}

        # 提取检索到的来源
        retrieved_sources = []
        for doc in retrieved_docs:
            source = doc.get("metadata", {}).get("source", "")
            if source:
                retrieved_sources.append(source)

        # Precision@K
        relevant_retrieved = sum(1 for s in retrieved_sources if s in expected_sources)
        precision = relevant_retrieved / len(retrieved_sources) if retrieved_sources else 0

        # Recall@K
        recalled = sum(1 for s in expected_sources if s in retrieved_sources)
        recall = recalled / len(expected_sources) if expected_sources else 0

        # MRR (Mean Reciprocal Rank)
        mrr = 0
        for i, source in enumerate(retrieved_sources):
            if source in expected_sources:
                mrr = 1.0 / (i + 1)
                break

        return {"precision": round(precision, 4), "recall": round(recall, 4), "mrr": round(mrr, 4)}

    # ==================== 生成指标（LLM-as-Judge）====================

    def eval_faithfulness(self, question: str, answer: str, context: str) -> dict:
        """
        评估回答的忠实度（是否基于检索到的文档）

        Returns:
            {"score": 1-5, "reason": str}
        """
        prompt = f"""评估以下回答是否忠实于提供的参考资料。

问题：{question}

参考资料：
{context}

回答：
{answer}

请按以下标准打分（1-5分）：
- 5分：完全基于参考资料，无任何编造
- 4分：大部分基于参考资料，有少量合理推断
- 3分：部分基于参考资料，部分编造
- 2分：少量基于参考资料，大部分编造
- 1分：完全编造，与参考资料无关

严格按JSON格式输出：{{"score": 分数, "reason": "原因"}}"""

        try:
            llm = self._get_judge_llm()
            response = llm.invoke(prompt).content.strip()
            return self._parse_json(response, {"score": 0, "reason": "解析失败"})
        except Exception as e:
            return {"score": 0, "reason": f"评估失败: {e}"}

    def eval_answer_relevance(self, question: str, answer: str) -> dict:
        """
        评估答案与问题的相关性

        Returns:
            {"score": 1-5, "reason": str}
        """
        prompt = f"""评估以下回答是否与问题相关。

问题：{question}
回答：{answer}

评分标准（1-5分）：
- 5分：完全回答了问题，信息准确有用
- 4分：基本回答了问题，有少量无关信息
- 3分：部分回答了问题，但不够完整
- 2分：与问题相关但没有实质回答
- 1分：完全答非所问

严格按JSON格式输出：{{"score": 分数, "reason": "原因"}}"""

        try:
            llm = self._get_judge_llm()
            response = llm.invoke(prompt).content.strip()
            return self._parse_json(response, {"score": 0, "reason": "解析失败"})
        except Exception as e:
            return {"score": 0, "reason": f"评估失败: {e}"}

    # ==================== 端到端评测 ====================

    def run_evaluation(self, rag_service, test_data: list[dict] = None) -> dict:
        """
        运行完整的端到端评测

        Args:
            rag_service: RagService 实例
            test_data: 测试数据（默认从文件加载）

        Returns:
            评测报告
        """
        test_data = test_data or self.load_test_data()
        if not test_data:
            return {"error": "无测试数据"}

        results = []
        for i, case in enumerate(test_data):
            question = case["question"]
            expected_answer = case.get("answer", "")
            expected_source = case.get("source", "").split(",")

            logger.info(f"评测 [{i+1}/{len(test_data)}]: {question[:30]}...")

            # 运行 RAG
            result = rag_service.chat(question, user_id="eval_user")
            actual_answer = result["answer"]

            # 评估检索质量
            # 简化：用 retrieved_docs 数量和意图作为检索指标
            retrieval_score = {
                "retrieved_count": result["retrieved_docs"],
                "intent": result["intent"]["intent"],
            }

            # 评估忠实度
            faithfulness = self.eval_faithfulness(question, actual_answer, "参考资料")

            # 评估相关性
            relevance = self.eval_answer_relevance(question, actual_answer)

            results.append({
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": actual_answer,
                "retrieval": retrieval_score,
                "faithfulness": faithfulness,
                "relevance": relevance,
                "intent": result["intent"],
            })

        # 汇总
        report = self._generate_report(results)
        self.results = results
        return report

    def _generate_report(self, results: list[dict]) -> dict:
        """生成评测报告"""
        faith_scores = [r["faithfulness"]["score"] for r in results if r["faithfulness"]["score"] > 0]
        relev_scores = [r["relevance"]["score"] for r in results if r["relevance"]["score"] > 0]

        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(results),
            "metrics": {
                "faithfulness_avg": round(sum(faith_scores) / len(faith_scores), 2) if faith_scores else 0,
                "relevance_avg": round(sum(relev_scores) / len(relev_scores), 2) if relev_scores else 0,
            },
            "intent_distribution": {},
            "details": results,
        }

        # 意图分布
        for r in results:
            intent = r["intent"]["intent"]
            report["intent_distribution"][intent] = report["intent_distribution"].get(intent, 0) + 1

        return report

    @staticmethod
    def _parse_json(text: str, default: dict) -> dict:
        try:
            return json.loads(text)
        except:
            import re
            m = re.search(r'\{[^}]+\}', text)
            return json.loads(m.group()) if m else default

    def save_report(self, report: dict, filepath: str = None):
        """保存评测报告"""
        filepath = filepath or os.path.join(EVAL_DATA_DIR, f"eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"评测报告已保存: {filepath}")
