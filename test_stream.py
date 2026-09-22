import requests
import time
url = "http://127.0.0.1:8001/ask/stream"
payload = {"question": "请详细解释大学生焦虑心理的应对策略，至少写500字"}

print("开始接收流式数据：\n")
with requests.post(url, json=payload, stream=True) as r:
    for line in r.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data: "):
                content = decoded[6:]
                if content == "[DONE]":
                    print("\n\n【流式传输结束】")
                else:
                    print(content, end="", flush=True)
                    time.sleep(0.05) 