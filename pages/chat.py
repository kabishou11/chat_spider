import streamlit as st
import os
import json
import pandas as pd
import requests
from datetime import datetime

CONFIG_FILE = "config.json"
CHAT_HISTORY_FILE = "chat_history.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    st.warning("config.json 文件为空，使用默认配置。")
                    return {}
        except json.JSONDecodeError as e:
            st.error(f"config.json 文件格式错误: {e}，使用默认配置。")
            return {}
        except Exception as e:
            st.error(f"加载 config.json 失败: {e}，使用默认配置。")
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存 config.json 失败: {e}")

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    st.warning("chat_history.json 文件为空，使用默认空历史。")
                    return []
        except json.JSONDecodeError as e:
            st.error(f"chat_history.json 文件格式错误: {e}，使用默认空历史。")
            return []
        except Exception as e:
            st.error(f"加载 chat_history.json 失败: {e}，使用默认空历史。")
            return []
    return []

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存 chat_history.json 失败: {e}")

# 自定义 CSS
st.markdown("""
<style>
@keyframes slideIn {
    0% { transform: translateY(20px); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}
.chat-container {
    animation: slideIn 0.5s ease-out;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    background-color: #f9f9f9;
}
.history-item {
    border-bottom: 1px solid #e0e0e0;
    padding: 10px 0;
}
.history-item:last-child {
    border-bottom: none;
}
.stButton>button {
    width: 100%;
    margin-top: 5px;
}
.sidebar .stTextInput {
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

def main():
    saved_config = load_config()
    if "config" not in st.session_state:
        st.session_state.config = saved_config
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history()

    st.title("对话模式")
    st.markdown('<div class="chat-container">与 DeepSeek AI 进行智能对话</div>', unsafe_allow_html=True)

    # 主布局：输入区和历史区
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("对话输入")
        api_key = st.session_state.config.get("api_key", "")
        if not api_key:
            st.warning("请在侧边栏设置 DeepSeek API Key")

        # 文件上传
        uploaded_files = st.file_uploader("上传 CSV 文件", type=["csv"], accept_multiple_files=True)
        file_contents = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                file_contents.append(f"**文件: {uploaded_file.name}**\n```\n{df.to_string(index=False)}\n```")

        # 输入框
        user_input = st.text_area("输入对话内容", value=st.session_state.get("reload_input", ""), height=150)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("发送", type="primary"):
                if not api_key:
                    st.error("请设置 DeepSeek API Key！")
                elif not user_input:
                    st.error("请输入对话内容！")
                else:
                    with st.spinner("正在处理..."):
                        files_data = "\n\n".join(file_contents) if file_contents else "无上传文件"
                        prompt = f"""
你是一个高级数据分析助手，擅长处理 CSV 数据。
以下是上传的 CSV 文件数据：
{files_data}

我的问题是：{user_input}

请分析数据并回答问题。
"""
                        response = requests.post(
                            "https://api.deepseek.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                            json={
                                "model": "deepseek-chat",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 8192
                            }
                        )
                        if response.status_code == 200:
                            reply = response.json()["choices"][0]["message"]["content"]
                            st.markdown(f"**回复:**\n{reply}")
                            st.session_state.chat_history.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "input": user_input,
                                "files": [f.name for f in uploaded_files] if uploaded_files else [],
                                "response": reply
                            })
                            save_chat_history(st.session_state.chat_history)
                            if "reload_input" in st.session_state:
                                del st.session_state.reload_input
                        else:
                            st.error(f"API 请求失败: {response.status_code} - {response.text}")
        with col_btn2:
            if st.button("清空输入"):
                if "reload_input" in st.session_state:
                    del st.session_state.reload_input
                st.rerun()

    with col2:
        st.subheader("历史对话")
        if st.session_state.chat_history:
            # 分页和搜索
            search_query = st.text_input("搜索历史对话", "")
            items_per_page = 5
            total_items = len([chat for chat in st.session_state.chat_history if not search_query or search_query.lower() in chat["input"].lower()])
            total_pages = (total_items + items_per_page - 1) // items_per_page
            page = st.number_input("页码", min_value=1, max_value=max(1, total_pages), value=1, step=1)

            filtered_history = [chat for chat in reversed(st.session_state.chat_history) if not search_query or search_query.lower() in chat["input"].lower()]
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(filtered_history))

            for i, chat in enumerate(filtered_history[start_idx:end_idx]):
                with st.expander(f"对话 {len(st.session_state.chat_history) - (start_idx + i)} - {chat['timestamp']}"):
                    st.markdown(f"**输入:** {chat['input']}")
                    if chat["files"]:
                        st.markdown(f"**文件:** {', '.join(chat['files'])}")
                    st.markdown(f"**回复:** {chat['response']}")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"重新加载", key=f"reload_{start_idx + i}"):
                            st.session_state.reload_input = chat["input"]
                            st.rerun()
                    with col_btn2:
                        if st.button(f"删除", key=f"delete_{start_idx + i}"):
                            st.session_state.chat_history.pop(len(st.session_state.chat_history) - 1 - (start_idx + i))
                            save_chat_history(st.session_state.chat_history)
                            st.rerun()
            if total_pages > 1:
                st.write(f"共 {total_items} 条记录，页码 {page}/{total_pages}")
        else:
            st.write("暂无历史记录")

        if st.session_state.chat_history and st.button("清除所有历史", type="secondary"):
            st.session_state.chat_history = []
            save_chat_history(st.session_state.chat_history)
            st.rerun()

    with st.sidebar:
        st.header("设置")
        api_key = st.text_input("DeepSeek API Key", type="password", value=st.session_state.config.get("api_key", ""))
        theme = st.selectbox("主题", ["Light", "Dark"], index=0 if st.session_state.config.get("theme", "Light") == "Light" else 1)
        st.session_state.config.update({"api_key": api_key, "theme": theme})
        save_config(st.session_state.config)

        # 动态切换主题（仅示例，Streamlit 原生不支持深色模式）
        if theme == "Dark":
            st.markdown("""
            <style>
            body { background-color: #1e1e1e; color: #ffffff; }
            .stTextInput>input, .stTextArea>textarea { background-color: #333333; color: #ffffff; }
            </style>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()