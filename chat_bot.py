from openai import OpenAI
import os
from dotenv import load_dotenv   # <--- 这一行必须有

load_dotenv()  # <--- 这一行必须有，去读你的 .env 文件

# 初始化客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 调用对话接口
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个专业的技术文档工程师，回答通俗易懂，带简单示例。"},
        {"role": "user", "content": "写一段Python快速排序代码，并简单解释原理。"}
    ],
    temperature=0.7,
    max_tokens=1024
)

# 提取并打印 AI 的回答
print("AI 回答：")
print(response.choices[0].message.content)