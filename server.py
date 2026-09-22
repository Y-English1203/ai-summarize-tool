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


os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
load_dotenv()

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
print("向量库加载完成")


app = FastAPI()

class Question(BaseModel):
    question: str

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