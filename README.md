# CloudAgent — 3C 数码智能客服系统 v2.0

基于 ReAct Agent + 多模态视觉的 RAG 智能问答系统，面向 3C 数码产品客服场景。支持产品咨询、故障排查、购买推荐、竞品对比等多意图自动分流，用户可发送产品图片获取智能解答。

## v2.0 新特性

| 特性 | 说明 |
|------|------|
| **ReAct Agent 模式** | LLM 自主决定何时检索、用什么工具、搜几次，取代固定流水线 |
| **多模态视觉理解** | 用户可上传产品图/故障截图，Qwen3-VL 自动识别型号、故障类型 |
| **全链路异步化** | 全部 LLM 调用使用 `async/await`，不阻塞事件循环 |
| **真实流式输出** | LLM 逐 token 流式输出，非假流式 |
| **FastAPI 依赖注入** | `app.state` 模式取代全局变量，服务实例统一管理 |
| **LLM 实例复用** | 3 个共享 ChatTongyi 实例覆盖全部场景，不再每次请求新建 |
| **工作台前端** | React + Vite + TypeScript + Tailwind CSS，三栏专业布局 |
| **健康检查 + 请求追踪** | `/health` 端点 + `X-Request-ID` 中间件 |
| **pytest 测试体系** | 45 个测试用例，覆盖配置、检索、记忆、API、图结构、视觉模块 |

## 系统架构

```
用户请求 → classify_intent → vision_analyze(图片?) → rewrite_query
              ↓                                                    ↓
         chitchat(闲聊)                                    react_generate(ReAct循环)
              ↓                                                    ↓
              └────────────→ output ←── verify ←───────────────────┘
                                   ↑        ↓
                                   └── retry ─┘ (验证失败重试)
```

### ReAct 循环

```
react_generate:
  LLM 思考 → 调用工具(search_knowledge / compare_products / get_troubleshoot_guide)
                → 观察结果 → 信息不够? 继续调用工具
                → 信息充分 → 输出最终回答
```

### LLM 实例分布

| 实例 | 模型 | 用途 |
|------|------|------|
| `llm` (streaming) | qwen3-max | 查询改写、闲聊、流式最终输出 |
| `light_llm` | qwen-turbo | 意图分类、答案验证、画像提取 |
| `react_llm` (non-streaming) | qwen3-max | ReAct 工具调用循环 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 编排 | LangGraph (StateGraph) |
| LLM | DashScope Qwen3-max / Qwen-turbo / Qwen3-VL |
| 向量库 | ChromaDB (持久化) |
| 检索 | BM25 (jieba) + 向量语义 + RRF 融合 + gte-rerank 重排序 |
| 后端 | FastAPI + Uvicorn (Python 3.12+) |
| 前端 | React 19 + Vite + TypeScript + Tailwind CSS 3 |
| 测试 | pytest + pytest-asyncio + httpx |

## 项目结构

```
├── agent/              # LangGraph 状态机、意图分类、ReAct 节点、视觉分析
│   ├── graph.py        # 图编排（9 个节点）
│   ├── intent.py       # 意图分类器（5 类意图）
│   ├── vision.py       # VisionAnalyzer（Qwen3-VL）
│   ├── router.py       # Prompt 模板 + 检索策略
│   ├── verifier.py     # 回答质量验证
│   └── tools.py        # Agent 工具：search_knowledge / compare_products / get_troubleshoot_guide
├── api/                # FastAPI REST 接口
│   ├── chat.py         # POST /chat, /chat/stream, /chat/image, /chat/image/stream
│   ├── knowledge.py    # POST /knowledge/upload
│   └── user.py         # GET /users/{id}/profile, /users/sessions
├── core/               # 核心服务
│   ├── rag_service.py  # RagService（LLM 管理 + 对话 + 流式）
│   ├── knowledge_service.py  # 知识库分块/去重/入库
│   └── session_service.py    # 会话管理
├── retrieval/          # 检索层
│   ├── embedding.py    # DashScope text-embedding-v4
│   ├── bm25.py         # BM25 关键词检索（jieba 分词）
│   ├── vector.py       # 向量检索 + RRF 混合融合
│   └── reranker.py     # gte-rerank-v2 重排序
├── memory/             # 记忆系统
│   ├── conversation.py # 短期对话记忆（窗口 + 摘要压缩）
│   ├── long_term.py    # 长期用户画像（JSON 持久化）
│   ├── user_profile.py # LLM 画像提取
│   └── query_rewriter.py  # 指代消解/省略补全
├── evaluation/         # RAG 评测框架（LLM-as-Judge）
├── frontend/           # React 工作台前端
│   └── src/
│       ├── App.tsx     # 根组件（状态管理）
│       ├── lib/api.ts  # API 封装层
│       └── components/ # Toolbar / SessionSidebar / ChatPanel / DiagnosticsPanel / KnowledgePanel
├── config/settings.py  # 统一配置（支持环境变量覆盖）
├── tests/              # pytest 测试（45 个用例）
├── main.py             # 应用入口
├── pyproject.toml      # Python 项目配置
└── requirements.txt    # Python 依赖
```

## 快速启动

### 后端

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key
export DASHSCOPE_API_KEY=sk-your-key

# 3. 启动服务
python -m uvicorn main:app --host 127.0.0.1 --port 8080

# 4. 访问 API 文档
open http://127.0.0.1:8080/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

如需指定后端地址，创建 `frontend/.env`：
```
VITE_API_BASE_URL=http://127.0.0.1:8080
```

### 导入知识库

```bash
python scripts/import_knowledge.py
```

### 运行测试

```bash
python -m pytest tests/ -v
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/chat` | 纯文本对话（JSON body） |
| `POST` | `/chat/stream` | 流式文本对话 |
| `POST` | `/chat/image` | 图片对话（multipart） |
| `POST` | `/chat/image/stream` | 图片流式对话 |
| `POST` | `/chat/{id}/end` | 结束会话，提取用户画像 |
| `GET` | `/chat/{id}/history` | 获取会话历史 |
| `POST` | `/knowledge/upload` | 上传知识库 TXT 文件 |
| `GET` | `/users/{id}/profile` | 获取用户画像 |
| `GET` | `/users/sessions` | 活跃会话列表 |
| `GET` | `/health` | 系统健康检查 |

## 配置项

所有配置位于 `config/settings.py`，可通过同名环境变量覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_HOST` / `APP_PORT` | 127.0.0.1:8080 | 服务地址 |
| `DASHSCOPE_API_KEY` | — | DashScope API 密钥 |
| `chat_model` | qwen3-max | 主生成模型 |
| `classifier_model` | qwen-turbo | 轻量分类/验证模型 |
| `vision_model` | qwen3-vl | 多模态视觉模型 |
| `rerank_model` | gte-rerank-v2 | 重排序模型 |
| `embedding_model` | text-embedding-v4 | 向量嵌入模型 |
| `max_images_per_message` | 3 | 单次最大图片数 |
| `max_image_size_mb` | 10 | 单张图片大小限制 |

## 评测

运行评测框架验证 RAG 质量：

```python
from evaluation.rag_evaluator import RAGEvaluator
from core.rag_service import RagService

evaluator = RAGEvaluator()
rag = RagService()
report = evaluator.run_evaluation(rag)
evaluator.save_report(report)
```
