import requests

API_KEY = "sk-proj-6lLgO3K2g28B60Z85fZXT3BlbkFJArdOVFejkIZfPHFoj4KM"  # 替换为你的密钥

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 测试 1: 查模型列表（最简单、不花钱的测试）
print("=== 测试 1: 获取模型列表 ===")
resp = requests.get("https://api.openai.com/v1/models", headers=headers)
print(f"状态码: {resp.status_code}")
print(resp.json() if resp.status_code == 200 else f"错误: {resp.text}")

# 测试 2: 调用 /v1/responses（你出错的端点）
print("\n=== 测试 2: 调用 /v1/responses ===")
payload = {
    "model": "gpt-4o",
    "input": "Hi"
}
resp2 = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
print(f"状态码: {resp2.status_code}")
if resp2.status_code != 200:
    print(f"错误: {resp2.text}")
else:
    print("成功")