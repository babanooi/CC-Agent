"""
统一配置文件
所有配置项集中管理，支持环境变量覆盖
"""
import os

# ==================== 服务配置 ====================
HOST = os.getenv("APP_HOST", "127.0.0.1")
PORT = int(os.getenv("APP_PORT", "8080"))

# ==================== DashScope API ====================
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")

# ==================== 模型配置 ====================
embedding_model = "text-embedding-v4"
chat_model = "qwen3-max"
rerank_model = "gte-rerank-v2"
classifier_model = "qwen-turbo"  # 意图分类、验证、画像提取等轻量任务
vision_model = "qwen3-vl"       # 多模态视觉理解

# ==================== 图片上传限制 ====================
max_images_per_message = 3
max_image_size_mb = 10

# ==================== 文档分块 ====================
chunk_size = 500
chunk_overlap = 100
separators = ["\n\n", "\n", "。", "？", "！", "；", "，", "、", " ", ""]
max_split_char_number = 1000

# ==================== 向量数据库 ====================
collection_name = "rag"
persist_directory = ".chroma_db"

# ==================== 检索配置 ====================
bm25_top_k = 10
vector_top_k = 10
hybrid_top_k = 10
rrf_k = 60
similarity_num = 6
rerank_top_k = 6

# ==================== 记忆配置 ====================
memory_window_size = 10
session_timeout_hours = 24

# ==================== 数据路径 ====================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
md5_path = os.path.join(DATA_DIR, "md5.text")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
QA_DIR = os.path.join(DATA_DIR, "qa_pairs")
MEMORY_DIR = os.path.join(DATA_DIR, "user_memory")
