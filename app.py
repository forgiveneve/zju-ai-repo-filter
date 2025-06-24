
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="GitHub AI 项目筛选器", layout="wide")
st.title("🔍 GitHub AI 后训练项目筛选器")

keywords = [
    "LoRA", "SFT", "RLHF", "transformer", "BERT", "Chatbot", "Prompt", "LLM",
    "GPT", "finetune", "tuning", "adapter", "knowledge distillation", "self-instruct"
]
min_stars = st.slider("最小 Stars", 0, 500, 2)
max_repos = st.slider("最多结果数", 100, 3000, 1000)
github_token = st.text_input("GitHub Token（必填）", type="password")

created_ranges = [
    ("2023-01-01", "2023-06-01"),
    ("2023-06-01", "2023-09-01"),
    ("2023-09-01", "2024-01-01"),
    ("2024-01-01", "2024-06-01"),
    ("2024-06-01", datetime.today().strftime("%Y-%m-%d"))
]

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
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def get_user_info(username, headers):
    url = f"https://api.github.com/users/{username}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        user = res.json()
        return user.get("email"), user.get("bio")
    return None, None

if st.button("开始筛选"):
    if not github_token:
        st.error("请提供 GitHub Token。")
    else:
        headers = {"Authorization": f"token {github_token}"}
        all_results = []
        st.write(f"正在处理关键词: {keywords_input}")
        with st.spinner("正在抓取 GitHub 数据，请稍候..."):
            for keyword in [k.strip() for k in keywords_input.split(",") if k.strip()]:
                for start_date, end_date in created_ranges:
                    for page in range(1, 35):  # 每段最多抓 34 页（1020 条）
                        data = search_github_repos(keyword, page, headers, min_stars, start_date, end_date)
                        items = data.get("items", [])
                        if not items:
                            break
                        for item in items:
                            username = item["owner"]["login"]
                            email, bio = get_user_info(username, headers)
                            all_results.append({
                                "项目名称": item["name"],
                                "描述": item["description"],
                                "Stars": item["stargazers_count"],
                                "链接": item["html_url"],
                                "作者": username,
                                "邮箱": email,
                                "Bio": bio,
                                "是否可能来自ZJU": "Zhejiang" in (bio or "") or "ZJU" in (bio or "") or "浙江大学" in (bio or "") or "浙大" in (bio or ""),
                                "是否ZJU邮箱": email.endswith("zju.edu.cn") if email else False
                            })
                            if len(all_results) >= max_repos:
                                break
                        time.sleep(1)
                    if len(all_results) >= max_repos:
                        break
                if len(all_results) >= max_repos:
                    break
        df = pd.DataFrame(all_results)
        st.success(f"共获取 {len(df)} 个项目")
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 下载CSV文件", csv, "github_ai_candidates.csv", "text/csv")
