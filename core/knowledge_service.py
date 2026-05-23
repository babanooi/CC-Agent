"""知识库管理服务"""
import os, hashlib, logging
from datetime import datetime
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from retrieval.embedding import EmbeddingService
from config import settings as config

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self):
        self.embedding = EmbeddingService()
        os.makedirs(config.persist_directory, exist_ok=True)
        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap,
            separators=config.separators,
        )

    def upload(self, text: str, filename: str) -> str:
        if not text.strip():
            return "[失败] 内容为空"
        md5 = hashlib.md5(text.encode()).hexdigest()
        if self._check_md5(md5):
            return "[跳过] 内容已存在"
        chunks = self.splitter.split_text(text) if len(text) > config.max_split_char_number else [text]
        metadatas = [{"source": filename, "chunk_id": i, "time": datetime.now().isoformat()}
                     for i in range(len(chunks))]
        self.chroma.add_texts(texts=chunks, metadatas=metadatas)
        self._save_md5(md5)
        return f"[成功] 已载入 {len(chunks)} 条片段"

    def _check_md5(self, md5: str) -> bool:
        os.makedirs(os.path.dirname(config.md5_path), exist_ok=True)
        if not os.path.exists(config.md5_path):
            return False
        with open(config.md5_path, "r") as f:
            return md5 in f.read()

    def _save_md5(self, md5: str):
        with open(config.md5_path, "a") as f:
            f.write(md5 + "\n")
