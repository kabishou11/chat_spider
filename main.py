import streamlit as st

st.set_page_config(page_title="Twitter Crawler & Chat", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("功能导航")
st.sidebar.markdown("选择一个功能：")
st.sidebar.page_link("pages/crawler.py", label="Twitter 爬虫")
st.sidebar.page_link("pages/bing_crawler.py", label="Bing 爬虫")  # 新增 Bing 爬虫导航
st.sidebar.page_link("pages/chat.py", label="对话模式")
st.sidebar.page_link("pages/prompt_manager.py", label="提示词模板管理")

st.title("欢迎使用  Crawler & Chat")
st.markdown("在侧边栏选择功能，开始你的数据爬取、提示词管理或智能对话之旅！")