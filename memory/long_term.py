"""长期记忆（用户画像持久化）"""
import json, os, logging
from datetime import datetime
from config import settings as config

logger = logging.getLogger(__name__)


class LongTermMemory:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        os.makedirs(config.MEMORY_DIR, exist_ok=True)
        self.file_path = os.path.join(config.MEMORY_DIR, f"{user_id}.json")
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"user_id": self.user_id, "profile": {}, "preferences": [],
                "mentioned_products": [], "session_summaries": [], "interaction_count": 0}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update_profile(self, profile: dict):
        self.data["profile"].update(profile); self._save()

    def add_preference(self, pref: str):
        if pref not in self.data["preferences"]:
            self.data["preferences"].append(pref); self._save()

    def add_mentioned_product(self, product: str):
        if product not in self.data["mentioned_products"]:
            self.data["mentioned_products"].append(product); self._save()

    def add_session_summary(self, summary: str):
        self.data["session_summaries"].append({"summary": summary, "time": datetime.now().isoformat()})
        self.data["session_summaries"] = self.data["session_summaries"][-20:]
        self.data["interaction_count"] += 1; self._save()

    def get_context_string(self) -> str:
        parts = []
        if self.data["profile"]:
            items = [f"- {k}: {v}" for k, v in self.data["profile"].items()]
            parts.append("【用户画像】\n" + "\n".join(items))
        if self.data["preferences"]:
            parts.append("【偏好】\n- " + "、".join(self.data["preferences"]))
        if self.data["mentioned_products"]:
            parts.append("【关注产品】\n- " + "、".join(self.data["mentioned_products"]))
        if self.data["session_summaries"]:
            recent = self.data["session_summaries"][-3:]
            items = [f"- {s['time'][:10]}: {s['summary']}" for s in recent]
            parts.append("【历史摘要】\n" + "\n".join(items))
        return "\n\n".join(parts)

    @property
    def is_empty(self) -> bool:
        return not self.data["profile"] and not self.data["preferences"]
