# 我的AI学习项目集

## 核心项目
1. **Agentic RAG v2 - 带质量审核和自动重试** (`agent_rag_v2.py`) - 基于 **LangGraph** 状态机实现“意图识别 → 检索 → 生成 → 质量审核 → 自动重试”的完整 Agent 工作流，支持页码引用和离线运行。
2. **Agentic RAG v1** (`agent_rag.py`) - 基于 Function Calling 的自主检索 Agent，能自动判断是否查文档。
3. **私有文档AI助手 V2** (`rag_app_v2.py`) - 基于向量检索的 RAG 系统（ChromaDB + HuggingFace）。
4. **Web智能对话应用** (`app.py`) - 基于 Streamlit 的网页版 AI 对话。
5. **智能文档摘要工具** (`summarize.py`) - 纯 Python 实现文本摘要。

## 项目演示

**Agentic RAG v2：带页码引用与质量审核**
![Agentic RAG v2 演示](demo_agent_v2.png)

**Agentic RAG v1：Function Calling 路由**
![Agentic RAG 演示](demo_agent.png)

## 技术栈
Python、Streamlit、LangGraph、LangChain、ChromaDB、HuggingFace (bge-small-zh-v1.5)、DeepSeek API、Function Calling、PyPDF、python-dotenv、Git

## 运行方式
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   # 启动 FastAPI 服务
uvicorn server:app --reload
# 浏览器打开 http://127.0.0.1:8000/docs 进行接口测试