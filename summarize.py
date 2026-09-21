import re

def summarize(text, max_sentences=3):
    # 按中文/英文句号、问号、感叹号切分
    sentences = re.split(r'(?<=[。！？.!?])\s*', text.strip())
    sentences = [s for s in sentences if s.strip()]
    return "".join(sentences[:max_sentences])

if __name__ == "__main__":
    text = """
    人工智能正在改变世界。大模型可以写代码、做翻译、回答问题。
    但是很多公司需要的不是训练大模型，而是会用大模型接口做应用。
    对于应届生来说，掌握 Python 和大模型 API 调用，是一条可行的入行路径。
    """
    print("原文：")
    print(text)
    print("\n摘要：")
    print(summarize(text))