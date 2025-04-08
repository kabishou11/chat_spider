import streamlit as st

# 设置页面配置
st.set_page_config(page_title="Twitter Crawler & Chat", layout="wide", initial_sidebar_state="expanded")

# 定义多页面导航
st.sidebar.title("功能导航")
st.sidebar.markdown("选择一个功能：")
pages = {
    "Twitter 爬虫": "pages/crawler.py",
    "对话模式": "pages/chat.py"
}
st.sidebar.radio("跳转到", list(pages.keys()), key="navigation")