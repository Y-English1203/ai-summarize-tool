import json
import requests

with open("eval_set.json", "r", encoding="utf-8") as f:
    eval_set = json.load(f)

hit = 0
for item in eval_set:
    r = requests.post("http://127.0.0.1:8000/ask", json={"question": item["question"]})
    answer = r.json().get("answer", "")
    keywords_hit = sum(1 for kw in item["expected_keywords"] if kw in answer)
    if keywords_hit >= len(item["expected_keywords"]) * 0.5:
        hit += 1
    print(f"[{'✓' if keywords_hit >= len(item['expected_keywords']) * 0.5 else '✗'}] {item['question']}")

print(f"\n命中率：{hit}/{len(eval_set)} = {hit/len(eval_set)*100:.1f}%")