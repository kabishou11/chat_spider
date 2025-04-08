import streamlit as st
import asyncio
import os
import json
import pandas as pd
from tag_down3 import run_tag_down

CONFIG_FILE = "config.json"

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:  # 指定 UTF-8 编码
                return json.load(f)
        except UnicodeDecodeError as e:
            st.error(f"配置文件解码错误: {e}，请确保文件使用 UTF-8 编码")
            return {}
        except json.JSONDecodeError as e:
            st.error(f"配置文件格式错误: {e}，使用默认配置")
            return {}
        except Exception as e:
            st.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    return {}

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:  # 指定 UTF-8 编码
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存配置文件失败: {e}")

st.markdown("""
<style>
@keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
}
.fade-in {
    animation: fadeIn 1s ease-in;
}
</style>
""", unsafe_allow_html=True)

def main():
    saved_config = load_config()
    if "config" not in st.session_state:
        st.session_state.config = saved_config

    st.title("Twitter 爬虫")
    st.markdown('<div class="fade-in">欢迎使用 Twitter 数据爬取工具！</div>', unsafe_allow_html=True)

    st.subheader("爬取参数设置")
    with st.form(key="crawler_form"):
        cookie = st.text_area("Twitter Cookie", value=st.session_state.config.get("cookie", ""), height=100)
        tag = st.text_input("标签 (Tag)", value=st.session_state.config.get("tag", "#ig"))
        _filter = st.text_input("搜索条件 (Filter)", value=st.session_state.config.get("filter", "filter:links -filter:replies until:2025-03-28 since:2025-03-27"))
        down_count = st.number_input("下载数量", min_value=50, max_value=10000, value=st.session_state.config.get("down_count", 100), step=50)
        media_latest = st.checkbox("从 [最新] 标签页下载", value=st.session_state.config.get("media_latest", True))
        text_down = st.checkbox("仅下载文本内容", value=st.session_state.config.get("text_down", False))
        submit_button = st.form_submit_button(label="开始下载", type="primary")

    st.session_state.config.update({
        "cookie": cookie, "tag": tag, "filter": _filter,
        "down_count": down_count, "media_latest": media_latest,
        "text_down": text_down
    })
    save_config(st.session_state.config)

    if submit_button:
        if not cookie or "auth_token" not in cookie or "ct0" not in cookie:
            st.error("请提供有效的 Twitter Cookie！")
        else:
            with st.spinner("正在下载，请稍候..."):
                try:
                    result = asyncio.run(run_tag_down(
                        cookie=cookie, tag=tag, _filter=_filter,
                        down_count=down_count, media_latest=media_latest, text_down=text_down
                    ))
                    st.success(f"下载完成！共下载 {result['total_downloaded']} 条数据，保存路径: {result['folder_path']}")
                    if "csv_path" in result and os.path.exists(result["csv_path"]):
                        df = pd.read_csv(result["csv_path"])
                        st.write("爬取结果预览：")
                        st.dataframe(df.head(10))
                        with open(result["csv_path"], "rb") as file:
                            st.download_button(
                                label="下载 CSV 文件",
                                data=file,
                                file_name=os.path.basename(result["csv_path"]),
                                mime="text/csv"
                            )
                except Exception as e:
                    st.error(f"下载失败: {str(e)}")

if __name__ == "__main__":
    main()