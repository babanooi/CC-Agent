"""用户画像提取"""
import json, re, logging
from langchain_community.chat_models import ChatTongyi
from config import settings as config

logger = logging.getLogger(__name__)


class UserProfileExtractor:
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatTongyi(model="qwen-turbo", dashscope_api_key=config.dashscope_api_key, temperature=0)
        return self._llm

    def extract(self, chat_history: str) -> dict:
        empty = {"profile": {}, "preferences": [], "mentioned_products": [], "summary": ""}
        if not chat_history or len(chat_history.strip()) < 50:
            return empty
        prompt = (
            "分析以下对话，提取用户信息，JSON输出："
            '{"profile":{},"preferences":[],"mentioned_products":[],"summary":"一句话总结"}'
            f"\n\n{chat_history}"
        )
        try:
            response = self._get_llm().invoke(prompt).content.strip()
            try:
                result = json.loads(response)
            except Exception:
                m = re.search(r"\{.*\}", response, re.DOTALL)
                result = json.loads(m.group()) if m else {}
            return {k: result.get(k, v) for k, v in empty.items()}
        except Exception as e:
            logger.error("画像提取失败: %s", e)
            return empty
