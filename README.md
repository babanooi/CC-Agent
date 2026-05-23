# CC-Agent — 3C 数码智能客服系统

基于 RAG（检索增强生成）的智能问答系统，面向 3C 数码产品客服场景，支持产品咨询、故障排查、购买推荐、竞品对比等多意图自动分流。

## 核心特性

- **混合检索**：BM25 关键词 + 向量语义双路召回，RRF 融合 + 重排序精排
- **意图路由**：自动识别用户意图，按意图切换检索深度和 Prompt 策略
- **回答验证**：LLM 自动评估忠实度和相关性，不通过则重新检索生成
- **上下文理解**：对话前自动改写问题（指代消解、省略补全），解决多轮对话指代模糊
- **长期记忆**：会话结束自动提取用户画像和偏好，持久化供下次对话使用
- **自动化评测**：支持忠实度、相关性、Precision@K 等多维度量化评估

## 技术栈

Python / LangGraph / DashScope (Qwen) / ChromaDB / FastAPI

## 项目结构

```
├── agent/          # LangGraph 状态机编排、意图分类、路由策略
├── api/            # FastAPI REST 接口
├── config/         # 统一配置
├── core/           # 核心服务层（RAG、知识库、会话管理）
├── data/           # 知识库数据、测试用例
├── evaluation/     # RAG 评测框架
├── memory/         # 短期对话记忆 + 长期用户画像
├── retrieval/      # BM25、向量检索、重排序、Embedding
└── scripts/        # 数据导入脚本
```

## 快速启动

```bash
pip install -r requirements.txt
python main.py
```

服务启动后访问 http://127.0.0.1:8080/docs 查看 API 文档。
