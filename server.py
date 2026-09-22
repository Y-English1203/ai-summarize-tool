from fastapi.responses import StreamingResponse
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1" 
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from fastapi import FastAPI
from pydantic import BaseModel
from agent_rag_v2 import agent, AgentState
from openai import OpenAI
from dotenv import load_dotenv


os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
load_dotenv()


load_dotenv()
# 在 server.py 里独立初始化一个 client
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
# ====== 启动时自动加载 PDF ======
def load_vectorstore():
    from pypdf import PdfReader
    from langchain_core.documents import Document
    
    reader = PdfReader("test.pdf")
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            # 手动把页码塞进 metadata
            docs.append(Document(page_content=text, metadata={"page": i}))
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return Chroma.from_documents(chunks, embeddings)

vectorstore = load_vectorstore()
from hybrid_retriever import HybridRetriever
retriever = HybridRetriever(vectorstore)
print("混合检索器初始化完成")
print("向量库加载完成")
class Question(BaseModel):
    question: str

app = FastAPI()
@app.post("/ask/stream")
async def ask_stream(q: Question):
    """SSE 流式输出接口"""
    # 第一步：先做检索（这部分很快，不需要流式）
@app.post("/ask")
def ask(q: Question):
    # 使用混合检索替换单一的向量检索
    docs = retriever.retrieve(q.question, top_k=5)

    context = "\n\n".join(docs)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"请严格根据以下文档内容回答问题。\n\n文档内容：\n{context}"},
            {"role": "user", "content": q.question}
        ]
    )
    return {"answer": response.choices[0].message.content}
    docs = retriever.invoke(q.question)
    
    context_parts = []
    for doc in docs:
        page = doc.metadata.get('page', '未知')
        if isinstance(page, int):
            page = page + 1
        context_parts.append(f"[第{page}页] {doc.page_content}")
    context = "\n\n".join(context_parts)
    
    # 第二步：流式生成回答
    async def event_generator():
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"请严格根据以下文档回答，末尾标注引用页码。\n\n文档内容：\n{context}"},
                {"role": "user", "content": q.question}
            ],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                # SSE 格式：data: 内容\n\n
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/ask")
def ask(q: Question):
    initial_state: AgentState = {
        "question": q.question,
        "need_retrieval": False,
        "context": "",
        "answer": "",
        "has_citation": False,
        "retry_count": 0,
        "max_retries": 2,
        "vectorstore": vectorstore
    }
    result = agent.invoke(initial_state)
    return {"answer": result["answer"]}