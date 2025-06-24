
import requests
import pandas as pd
import time
import os
from datetime import datetime

# ==== 参数预设 ====
keywords = [
    "LoRA", "SFT", "RLHF", "transformer", "BERT", "Chatbot", "Prompt", "LLM",
    "GPT", "finetune", "tuning", "adapter", "knowledge distillation", "self-instruct"
]
min_stars = 1
max_repos = 3000
created_ranges = [
    ("2023-01-01", "2023-06-01"),
    ("2023-06-01", "2023-09-01"),
    ("2023-09-01", "2024-01-01"),
    ("2024-01-01", "2024-06-01"),
    ("2024-06-01", datetime.today().strftime("%Y-%m-%d"))
]
github_token = "your_token_here"

print("🔍 GitHub AI 后训练项目筛选工具启动中...")
print(f"关键词数量: {len(keywords)}，最小 Stars: {min_stars}，分段: {len(created_ranges)}\n")

# ==== GitHub 搜索函数 ====
def search_github_repos(keyword, page, headers, min_stars, start_date, end_date):
    url = "https://api.github.com/search/repositories"
    query = f"{keyword} language:Python stars:>={min_stars} created:{start_date}..{end_date}"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
        "page": page
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else {}

# ==== 获取用户信息 ====
def get_user_info(username, headers):
    url = f"https://api.github.com/users/{username}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        user = res.json()
        return user.get("email"), user.get("bio")
    return None, None

# ==== 主流程 ====
headers = {"Authorization": f"token {github_token}"} if github_token else {}
all_results = []

print("开始抓取 GitHub 数据...\n")
for keyword in keywords:
    for start_date, end_date in created_ranges:
        for page in range(1, 35):  # 最多 34 页 * 30 条 = ~1000 条
            data = search_github_repos(keyword, page, headers, min_stars, start_date, end_date)
            items = data.get("items", [])
            if not items:
                break
            for item in items:
                username = item["owner"]["login"]
                email, bio = get_user_info(username, headers)
                result = {
                    "项目名称": item["name"],
                    "描述": item["description"],
                    "Stars": item["stargazers_count"],
                    "链接": item["html_url"],
                    "作者": username,
                    "邮箱": email,
                    "Bio": bio,
                    "是否可能来自ZJU": any(x in (bio or "") for x in ["ZJU", "Zhejiang", "浙江大学"]),
                    "是否西湖或杭州高校邮箱": email and any(email.endswith(suffix) for suffix in [
                        "westlake.edu.cn", "hdu.edu.cn", "hznu.edu.cn", "zjgsu.edu.cn",
                        "zstu.edu.cn", "zjucm.edu.cn", "zjnu.edu.cn"
                    ])
                }
                all_results.append(result)
                if len(all_results) >= max_repos:
                    break
            time.sleep(1)
        if len(all_results) >= max_repos:
            break
    if len(all_results) >= max_repos:
        break

# ==== 导出 CSV ====
df = pd.DataFrame(all_results)
filename = "github_ai_candidates.csv"
df.to_csv(filename, index=False, encoding="utf-8-sig")
try:
    os.startfile(filename)
except:
    pass

print(f"\n✅ 数据已保存为 {filename}，共 {len(df)} 条记录。建议使用 Excel 打开以避免乱码。")
