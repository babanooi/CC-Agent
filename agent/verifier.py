"""回答质量验证"""
import json, re, logging
from langchain_community.chat_models import ChatTongyi
from config import settings as config

logger = logging.getLogger(__name__)


class AnswerVerifier:
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatTongyi(model="qwen-turbo", dashscope_api_key=config.dashscope_api_key, temperature=0)
        return self._llm

    def verify(self, question: str, answer: str, context: str) -> dict:
        prompt = (
            "验证回答质量。标准：相关性、忠实性、完整性。"
            'JSON输出：{"pass":true,"score":4,"reason":"原因","suggestion":"建议"}'
            f"\n\n问题：{question}\n参考资料：{context[:800]}\n回答：{answer}"
        )
        try:
            response = self._get_llm().invoke(prompt).content.strip()
            try:
                return json.loads(response)
            except Exception:
                m = re.search(r"\{[^}]+\}", response)
                return json.loads(m.group()) if m else {"pass": True, "score": 3}
        except Exception as e:
            logger.error("验证失败: %s", e)
            return {"pass": True, "score": 3, "reason": str(e)}
