import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from utils import load_config, save_config, load_chat_history, save_chat_history

# 全局 CSS 样式（默认使用 Light 主题）
st.markdown("""
<style>
body, .stApp { background-color: #ffffff !important; color: #000000 !important; }
.stTextInput>input { background-color: #ffffff !important; color: #000000 !important; }
.stSelectbox, .stNumberInput, .stButton>button { background-color: #f0f0f0 !important; color: #000000 !important; }
.sidebar .sidebar-content { background-color: #f9f9f9 !important; color: #000000 !important; }
.chat-container { 
    height: 60vh; 
    overflow-y: auto; 
    border: 1px solid #e0e0e0; 
    border-radius: 10px; 
    padding: 20px; 
    background-color: #f9f9f9; 
    margin-bottom: 20px; 
}
.user-message { 
    text-align: right; 
    background-color: #007bff; 
    color: white; 
    padding: 10px; 
    border-radius: 10px; 
    margin: 5px 0; 
    max-width: 70%; 
    display: inline-block; 
    float: right; 
    clear: both; 
}
.bot-message { 
    text-align: left; 
    background-color: #e9ecef; 
    color: black; 
    padding: 10px; 
    border-radius: 10px; 
    margin: 5px 0; 
    max-width: 70%; 
    display: inline-block; 
    float: left; 
    clear: both; 
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def cached_load_chat_history():
    return load_chat_history()

def load_prompt_templates():
    config = load_config()
    return config.get("prompt_templates", {})

def render_chat():
    chat_html = '<div class="chat-container">'
    for msg in st.session_state.current_conversation:
        if msg["role"] == "user":
            chat_html += f'<div class="user-message">{msg["content"]}</div>'
        else:
            chat_html += f'<div class="bot-message">{msg["content"]}</div>'
    chat_html += '</div>'
    chat_html += """
    <script>
    var chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>
    """
    st.markdown(chat_html, unsafe_allow_html=True)

def send_message(user_input, templates, api_key, uploaded_files):
    if not user_input.strip():
        return
    template = templates.get(st.session_state.selected_template, "无模板")
    file_contents = [f"**文件: {f.name}**\n```\n{pd.read_csv(f).to_string(index=False)}\n```" for f in uploaded_files] if uploaded_files else "无上传文件"
    prompt = template.format(file_contents=file_contents, user_input=user_input)
    
    # 直接显示用户消息
    st.session_state.current_conversation.append({"role": "user", "content": user_input})
    
    # 直接请求 API，不显示思考过程
    with st.spinner("思考中..."):
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": st.session_state.max_tokens}
        )
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            st.session_state.current_conversation.append({"role": "assistant", "content": reply})
        else:
            st.session_state.current_conversation.append({"role": "assistant", "content": f"### 错误\nAPI 请求失败: {response.status_code} - {response.text}"})
    
    # 更新当前会话的历史记录
    if "current_session_id" in st.session_state:
        for i, chat in enumerate(st.session_state.chat_history):
            if chat["session_id"] == st.session_state.current_session_id:
                st.session_state.chat_history[i]["conversation"] = st.session_state.current_conversation.copy()
                save_chat_history(st.session_state.chat_history)
                break
    # 清空输入框状态
    st.session_state.user_input = ""

def main():
    saved_config = load_config()
    if "config" not in st.session_state:
        st.session_state.config = saved_config
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = cached_load_chat_history()
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = []
    if "selected_template" not in st.session_state:
        templates = load_prompt_templates()
        st.session_state.selected_template = list(templates.keys())[0] if templates else "无模板"
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 8192
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    st.title("对话模式")

    # 对话显示区域
    with st.container():
        st.subheader("当前对话")
        render_chat()

    # 输入区域
    with st.container():
        col_input, col_button = st.columns([3, 1])
        with col_input:
            # 使用动态 key 确保输入框刷新
            user_input = st.text_input("输入对话内容", value="", key=f"user_input_{st.session_state.current_session_id}_{len(st.session_state.current_conversation)}")
            st.session_state.user_input = user_input
        with col_button:
            send_clicked = st.button("发送")

    api_key = st.session_state.config.get("api_key", "")
    templates = load_prompt_templates()
    uploaded_files = st.file_uploader("上传 CSV 文件", type=["csv"], accept_multiple_files=True)

    if send_clicked and user_input and api_key and templates:
        send_message(user_input, templates, api_key, uploaded_files)
        st.session_state.user_input = ""  # 再次确保清空
        st.rerun()
    elif send_clicked:
        st.error("请确保已输入内容、设置 API Key 并创建模板！")

    # 模板选择和清空对话
    col_template, col_clear = st.columns([2, 1])
    with col_template:
        if templates:
            st.session_state.selected_template = st.selectbox(
                "提示词模板",
                list(templates.keys()),
                index=list(templates.keys()).index(st.session_state.selected_template) if st.session_state.selected_template in templates else 0
            )
        else:
            st.warning("无可用模板，请先在提示词管理页面创建模板。")
    with col_clear:
        if st.button("清空对话"):
            if st.session_state.current_conversation:
                # 保存当前会话到历史记录
                existing_session = False
                for i, chat in enumerate(st.session_state.chat_history):
                    if chat["session_id"] == st.session_state.current_session_id:
                        st.session_state.chat_history[i] = {
                            "session_id": st.session_state.current_session_id,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "conversation": st.session_state.current_conversation.copy(),
                            "files": [f.name for f in uploaded_files] if uploaded_files else [],
                            "template": st.session_state.selected_template if templates else "无模板"
                        }
                        existing_session = True
                        break
                if not existing_session:
                    st.session_state.chat_history.append({
                        "session_id": st.session_state.current_session_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "conversation": st.session_state.current_conversation.copy(),
                        "files": [f.name for f in uploaded_files] if uploaded_files else [],
                        "template": st.session_state.selected_template if templates else "无模板"
                    })
                save_chat_history(st.session_state.chat_history)
            st.session_state.current_conversation = []
            st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.user_input = ""  # 清空输入框
            st.rerun()
        if st.session_state.current_conversation:
            chat_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" 
                                 for msg in st.session_state.current_conversation])
            st.download_button("导出对话", chat_text, file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    # 侧边栏：设置和历史对话
    with st.sidebar:
        st.header("设置")
        api_key = st.text_input("DeepSeek API Key", type="password", value=st.session_state.config.get("api_key", ""))
        st.session_state.max_tokens = st.number_input("Max Tokens", min_value=512, max_value=16384, value=st.session_state.max_tokens, step=512)
        st.session_state.config.update({"api_key": api_key})
        save_config(st.session_state.config)

        st.subheader("历史对话")
        if st.session_state.chat_history:
            chat_options = [f"{chat['timestamp']} - {chat['conversation'][0]['content'][:30]}..." 
                           for chat in reversed(st.session_state.chat_history)]
            selected_chat = st.selectbox("选择历史对话", chat_options)
            chat_index = len(st.session_state.chat_history) - 1 - chat_options.index(selected_chat)
            chat = st.session_state.chat_history[chat_index]

            st.write(f"**模板**: {chat.get('template', '未知')}")
            st.write(f"**文件**: {', '.join(chat['files']) if chat['files'] else '无'}")
            for msg in chat["conversation"]:
                st.write(f"**{msg['role'].capitalize()}**: {msg['content']}")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("加载", key=f"load_{chat_index}"):
                    st.session_state.current_conversation = chat["conversation"].copy()
                    st.session_state.current_session_id = chat["session_id"]
                    st.rerun()
            with col_btn2:
                if st.button("删除", key=f"delete_{chat_index}"):
                    st.session_state.chat_history.pop(chat_index)
                    save_chat_history(st.session_state.chat_history)
                    st.rerun()
        else:
            st.write("暂无历史记录")

if __name__ == "__main__":
    main()