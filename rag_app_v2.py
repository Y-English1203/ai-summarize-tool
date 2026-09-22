import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

st.title("私有文档AI助手 V2 (向量检索版)")

uploaded_file = st.file_uploader("上传PDF", type="pdf")

if uploaded_file:
    # 保存临时文件
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 1. 加载并切分
    loader = PyPDFLoader("temp.pdf")
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    
    # 2. 存入向量数据库 (需要设置嵌入模型，这里用阿里云DashScope免费额度，或替换为你已有的API)
    # ⚠️ 如果没有DashScope Key，先去 https://dashscope.console.aliyun.com/ 免费领一个
    
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    vectorstore = Chroma.from_documents(chunks, embeddings)
    
    st.success(f"已建立向量索引，共 {len(chunks)} 个片段。")
    
    prompt = st.chat_input("针对文档提问：")
    if prompt:
        st.chat_message("user").write(prompt)
        
        # 3. 语义检索（不再是关键词匹配！）
        retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
        relevant_docs = retriever.invoke(prompt)
        
        # 4. 拼接上下文并生成回答，同时要求返回页码引用
        context = "\n\n".join([f"[第{doc.metadata.get('page', '?')+1}页] {doc.page_content}" for doc in relevant_docs])
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"你是一个严格的文档助手。请只根据以下文档内容回答，并在结尾注明引用了哪些页码。如果文档未提及，请回答'文档未提及'。\n\n文档内容：\n{context}"},
                {"role": "user", "content": prompt}
            ]
        )
        st.chat_message("assistant").write(response.choices[0].message.content)