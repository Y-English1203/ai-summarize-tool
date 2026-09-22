import os
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI

# 1. 初始化配置
load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

st.title("我的私有文档AI助手 (RAG)")
st.caption("上传PDF，基于文档内容问答")

# 2. 上传 PDF 并提取文本
uploaded_file = st.file_uploader("上传一个PDF文件", type="pdf")

if uploaded_file is not None:
    # 读取PDF文本
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    # 简单切片（把长文本按每500字切成小块）
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    st.success(f"文档读取成功，共 {len(chunks)} 个片段。")

    # 3. 用户提问
    prompt = st.chat_input("针对文档提问：")

    if prompt:
        st.chat_message("user").write(prompt)
        
        # 4. 简易检索：算问题和每个片段里词的重合度，找最相关的3段
        # （为了让你快速跑通，这里用最朴素的关键词匹配，不引入复杂的向量库）
        def score(chunk, query):
            return sum(1 for word in query if word in chunk)
        
        top_chunks = sorted(chunks, key=lambda c: score(c, prompt), reverse=True)[:3]
        context = "\n\n".join(top_chunks)
        
        # 5. 把检索到的文档内容发给AI
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"你是一个文档助手。请严格根据以下文档内容回答问题，如果文档里没有，就回答'文档中未提及'。\n\n文档内容：\n{context}"},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        st.chat_message("assistant").write(reply)