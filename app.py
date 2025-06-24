
import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="GitHub AI 项目筛选器", layout="wide")
st.title("🔍 GitHub AI 后训练项目筛选器")
st.markdown("通过关键词挖掘优质 AI 微调项目候选人")

keywords_input = st.text_input("关键词（英文逗号分隔）", "LoRA,SFT,RLHF")
min_stars = st.slider("最小 Stars", 0, 500, 5)
created_after = st.date_input("创建时间大于", pd.to_datetime("2023-01-01"))
max_repos = st.slider("最多结果数", 10, 200, 50)
github_token = st.text_input("GitHub Token（必填）", type="password")

def search_github_repos(keyword, page, headers, min_stars, created_after):
    url = "https://api.github.com/search/repositories"
    query = f"{keyword} language:Python stars:>={min_stars} created:>={created_after}"
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
        st.error("请输入 GitHub Token。")
    else:
        headers = {"Authorization": f"token {github_token}"}
        all_results = []
        created_str = created_after.strftime("%Y-%m-%d")
        with st.spinner("正在抓取 GitHub 数据..."):
            for keyword in [k.strip() for k in keywords_input.split(",") if k.strip()]:
                for page in range(1, 4):
                    data = search_github_repos(keyword, page, headers, min_stars, created_str)
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
                            "是否可能来自ZJU": "Zhejiang" in (bio or "") or "ZJU" in (bio or ""),
                            "是否ZJU邮箱": email.endswith("zju.edu.cn") if email else False
                        })
                        if len(all_results) >= max_repos:
                            break
                    time.sleep(1)
                if len(all_results) >= max_repos:
                    break
        df = pd.DataFrame(all_results)
        st.success(f"共获取 {len(df)} 个项目")
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 下载CSV文件", csv, "github_ai_candidates.csv", "text/csv")
