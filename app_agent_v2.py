import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from agent_rag_v2 import agent, AgentState

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
load_dotenv()

st.title("Agentic RAG v2 - 带质量审核和自动重试")

# 初始化 session state
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# 上传 PDF
uploaded_file = st.file_uploader("上传PDF", type="pdf")

if uploaded_file and st.session_state.vectorstore is None:
    with st.spinner("正在建立向量索引..."):
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader("temp.pdf")
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        st.session_state.vectorstore = Chroma.from_documents(chunks, embeddings)
    st.success("向量索引建立完成！")

# 渲染历史消息
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 用户提问
if prompt := st.chat_input("请输入你的问题："):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    initial_state: AgentState = {
        "question": prompt,
        "need_retrieval": False,
        "context": "",
        "answer": "",
        "has_citation": False,
        "retry_count": 0,
        "max_retries": 2,
        "vectorstore": st.session_state.vectorstore
    }

    with st.spinner("Agent 正在处理..."):
        result = agent.invoke(initial_state)

    # 在回答后面显示重试次数
    reply = result["answer"]
    if result["need_retrieval"] and result["retry_count"] > 0:
        reply += f"\n\n_(经过 {result['retry_count'] + 1} 次检索)_"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)