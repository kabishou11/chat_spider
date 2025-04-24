import json
import os
import streamlit as st

CONFIG_FILE = "config.json"
CHAT_HISTORY_FILE = "chat_history.json"

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"加载 config.json 失败: {e}，使用默认配置")
            return {}
    return {}

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存 config.json 失败: {e}")

def load_chat_history():
    """加载聊天历史"""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"加载 chat_history.json 失败: {e}，使用默认空历史")
            return []
    return []

def save_chat_history(history):
    """保存聊天历史"""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存 chat_history.json 失败: {e}")
        