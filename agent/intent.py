"""意图分类器（Qwen-Turbo）"""
import json, re, logging
from langchain_community.chat_models import ChatTongyi
from config import settings as config

logger = logging.getLogger(__name__)

INTENTS = {
    "product_query": {"desc": "询问产品参数功能规格", "examples": ["小米15 Pro电池多大？"]},
    "product_compare": {"desc": "对比两款产品差异", "examples": ["小米和华为哪个好？"]},
    "troubleshoot": {"desc": "手机故障需要排查", "examples": ["充不进电怎么办？"]},
    "purchase_advice": {"desc": "想要购买建议推荐", "examples": ["5000块推荐什么？"]},
    "chitchat": {"desc": "闲聊打招呼告别", "examples": ["你好", "谢谢"]},
}


class IntentClassifier:
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatTongyi(model=config.classifier_model, dashscope_api_key=config.dashscope_api_key, temperature=0)
        return self._llm

    def _build_prompt(self) -> str:
        desc = "\n".join(f"- {k}: {v['desc']}" for k, v in INTENTS.items())
        return (f"将用户消息分类为以下类别之一：\n{desc}\n\n"
                + '{"intent":"类别名","confidence":0.95,"reason":"原因"}'
                + "\n只输出JSON。")

    def classify(self, message: str, history: str = "") -> dict:
        input_text = f"对话历史：\n{history}\n\n用户消息：{message}" if history else f"用户消息：{message}"
        prompt = f"{self._build_prompt()}\n\n{input_text}"
        try:
            response = self._get_llm().invoke(prompt).content.strip()
            return self._parse_response(response)
        except Exception as e:
            logger.error("意图分类失败: %s", e)
            return {"intent": "product_query", "confidence": 0.3, "reason": str(e)}

    async def aclassify(self, message: str, history: str = "", llm=None, has_image: bool = False) -> dict:
        parts = []
        if history:
            parts.append(f"对话历史：\n{history}")
        if has_image:
            parts.append("注意：用户同时发送了图片，问题可能涉及图片中的产品/故障。"
                         "仅凭文字无法判断时，优先归类为 product_query 或 troubleshoot。")
        parts.append(f"用户消息：{message}")
        input_text = "\n\n".join(parts)
        prompt = f"{self._build_prompt()}\n\n{input_text}"
        try:
            model = llm or self._get_llm()
            response = (await model.ainvoke(prompt)).content.strip()
            return self._parse_response(response)
        except Exception as e:
            logger.error("意图分类失败: %s", e)
            return {"intent": "product_query", "confidence": 0.3, "reason": str(e)}

    @staticmethod
    def _parse_response(response: str) -> dict:
        try:
            result = json.loads(response)
        except Exception:
            m = re.search(r"\{[^}]+\}", response)
            result = json.loads(m.group()) if m else {"intent": "product_query", "confidence": 0.5}
        if result.get("intent") not in INTENTS:
            result["intent"] = "product_query"
            result["confidence"] = 0.5
        return result
