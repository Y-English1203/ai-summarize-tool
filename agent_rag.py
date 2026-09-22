import os
import json
import streamlit as st
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

# ============ 0. 基础配置 ============
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

st.title("Agentic RAG - 会自己思考的文档助手")

# ============ 1. 全局变量存向量库 ============
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============ 2. 定义工具（Agent 可以调用的函数）============
def search_documents(query: str) -> str:
    """从已上传的文档中检索相关内容"""
    if st.session_state.vectorstore is None:
        return "错误：尚未上传文档"
    retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 8})
    docs = retriever.invoke(query)
    if not docs:
        return "未检索到相关内容"
def search_documents(query: str) -> str:
    """从已上传的文档中检索相关内容"""
    if st.session_state.vectorstore is None:
        return "错误：尚未上传文档"
    retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 8})
    docs = retriever.invoke(query)
    if not docs:
        return "未检索到相关内容"
    
    # 安全处理页码：如果是整数就+1（PDF页码从0开始），否则用原值
    context_parts = []
    for doc in docs:
        page = doc.metadata.get('page', '未知')
        if isinstance(page, int):
            page = page + 1
        context_parts.append(f"[第{page}页] {doc.page_content}")
    context = "\n\n".join(context_parts)
    return context
    return context

def direct_answer(question: str) -> str:
    """不查文档，直接用大模型回答"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

# 工具描述，告诉大模型有哪些工具可用
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "当用户的问题涉及上传文档的内容时，调用此函数检索相关段落",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户的查询内容"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "direct_answer",
            "description": "当用户的问题与上传文档无关时（如闲聊、常识问题），调用此函数直接回答",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "用户的问题"}
                },
                "required": ["question"]
            }
        }
    }
]

# ============ 3. 上传 PDF 并建立向量库 ============
uploaded_file = st.file_uploader("上传PDF", type="pdf")

if uploaded_file and st.session_state.vectorstore is None:
    with st.spinner("正在建立向量索引..."):
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        loader = PyPDFLoader("temp.pdf")
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        st.session_state.vectorstore = Chroma.from_documents(chunks, embeddings)
    st.success("向量索引建立完成！")

# ============ 4. Agent 主循环 ============
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("请输入你的问题："):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 第一步：让大模型决定调用哪个工具
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个智能助手。根据用户问题，决定是调用 search_documents 查文档，还是调用 direct_answer 直接回答。"},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    tool_calls = message.tool_calls

    # 第二步：执行工具
    if tool_calls:
        tool_call = tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "search_documents":
            with st.spinner("正在检索文档..."):
                context = search_documents(arguments["query"])
            # 把检索结果发给模型生成回答
            final_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": f"请严格根据以下文档内容回答，并注明引用页码。如果文档未提及，请说'文档中未提及'。\n\n文档内容：\n{context}"},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = final_response.choices[0].message.content
        else:
            reply = direct_answer(arguments["question"])
    else:
        reply = message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)