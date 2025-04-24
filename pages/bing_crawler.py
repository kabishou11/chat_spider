import streamlit as st
import os
import json
import pandas as pd
from bing_crawler import run_crawler, cancel_crawl, continue_crawl

st.set_page_config(layout="wide")

st.title("Bing 爬虫")

# 初始化状态
if "crawler_running" not in st.session_state:
    st.session_state.crawler_running = False
if "crawler_result" not in st.session_state:
    st.session_state.crawler_result = None
if "progress_text" not in st.session_state:
    st.session_state.progress_text = ""
if "progress_count" not in st.session_state:
    st.session_state.progress_count = 0
if "last_config" not in st.session_state:
    st.session_state.last_config = {}
if "log_messages" not in st.session_state:
    st.session_state.log_messages = []

# 加载上一次配置
default_config_file = r"D:\spider\chat_spider\bing\TAICCA_config.json"
if os.path.exists(default_config_file) and not st.session_state.last_config:
    with open(default_config_file, 'r', encoding='utf-8') as f:
        st.session_state.last_config = json.load(f)

# 进度回调函数
def update_progress(message, count):
    st.session_state.progress_text = message
    st.session_state.progress_count = count
    st.session_state.log_messages.append(f"{time.strftime('%H:%M:%S')}: {message}")

# 主界面布局
col_main, col_preview = st.columns([3, 1])

with col_main:
    # 状态指示
    status = "运行中" if st.session_state.crawler_running else "已停止"
    st.markdown(f"**爬虫状态**: <span style='color: {'green' if st.session_state.crawler_running else 'red'}'>{status}</span>", unsafe_allow_html=True)
    
    # 输入区域
    with st.form(key="bing_crawler_form"):
        query = st.text_input("搜索关键词", value=st.session_state.last_config.get("query", "TAICCA"))
        
        since = st.date_input("起始日期（可选）", value=None if not st.session_state.last_config.get("since") else pd.to_datetime(st.session_state.last_config["since"]), format="YYYY-MM-DD")
        until = st.date_input("结束日期（可选）", value=None if not st.session_state.last_config.get("until") else pd.to_datetime(st.session_state.last_config["until"]), format="YYYY-MM-DD")
        
        default_regions = st.session_state.last_config.get("regions", ['TW', 'CN', 'US', 'JP'])
        regions_input = st.text_area("搜索地区（每行一个地区代码，如 TW）", value="\n".join(default_regions), height=100)
        regions = [r.strip() for r in regions_input.splitlines() if r.strip()]
        
        max_results = st.number_input("最大搜索结果数", min_value=1, max_value=10000, value=st.session_state.last_config.get("max_results", 100), step=10)
        max_pages = st.number_input("最大翻页数", min_value=1, max_value=1000, value=st.session_state.last_config.get("max_pages", 10), step=1)
        max_depth = st.number_input("最大爬取深度", min_value=1, max_value=5, value=st.session_state.last_config.get("max_depth", 2), step=1)
        
        output_dir = st.text_input("输出目录", value=st.session_state.last_config.get("output_dir", r"D:\newshuju\bing"))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            submit_button = st.form_submit_button(label="开始爬取")
        with col2:
            stop_button = st.form_submit_button(label="停止爬取")
        with col3:
            continue_button = st.form_submit_button(label="继续爬取")

    # 进度显示
    progress_bar = st.progress(0)
    progress_text = st.empty()
    progress_count = st.empty()

    # 日志窗口
    st.subheader("爬取日志")
    log_container = st.empty()
    with log_container.container():
        st.text_area("日志", value="\n".join(st.session_state.log_messages), height=200, disabled=True)

    # 保存配置函数
    def save_last_config():
        config = {
            "query": query,
            "regions": regions,
            "max_results": max_results,
            "max_pages": max_pages,
            "since": since.strftime("%Y%m%d") if since else None,
            "until": until.strftime("%Y%m%d") if until else None,
            "output_dir": output_dir,
            "max_depth": max_depth
        }
        with open(default_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        st.session_state.last_config = config

    # 运行控制
    if submit_button and not st.session_state.crawler_running:
        st.session_state.crawler_running = True
        globals()['continue_crawl'] = False
        save_last_config()
        with st.spinner("正在爬取 Bing 搜索结果..."):
            since_str = since.strftime("%Y%m%d") if since else None
            until_str = until.strftime("%Y%m%d") if until else None
            
            csv_path, total_results = run_crawler(
                query=query,
                regions=regions,
                max_results=max_results,
                max_pages=max_pages,
                since=since_str,
                until=until_str,
                output_dir=output_dir,
                max_depth=max_depth,
                progress_callback=update_progress
            )
            st.session_state.crawler_result = {"csv_path": csv_path, "total_results": total_results}
            st.session_state.crawler_running = False
            
            st.success(f"爬取完成！共找到 {total_results} 个结果，结果已保存至 {csv_path}")

    if stop_button and st.session_state.crawler_running:
        globals()['cancel_crawl'] = True
        st.session_state.crawler_running = False
        save_last_config()
        st.success("爬取已中止！")

    if continue_button and not st.session_state.crawler_running:
        st.session_state.crawler_running = True
        globals()['continue_crawl'] = True
        globals()['cancel_crawl'] = False
        save_last_config()
        with st.spinner("继续爬取 Bing 搜索结果..."):
            since_str = since.strftime("%Y%m%d") if since else None
            until_str = until.strftime("%Y%m%d") if until else None
            
            csv_path, total_results = run_crawler(
                query=query,
                regions=regions,
                max_results=max_results,
                max_pages=max_pages,
                since=since_str,
                until=until_str,
                output_dir=output_dir,
                max_depth=max_depth,
                progress_callback=update_progress
            )
            st.session_state.crawler_result = {"csv_path": csv_path, "total_results": total_results}
            st.session_state.crawler_running = False
            
            st.success(f"继续爬取完成！共找到 {total_results} 个结果，结果已保存至 {csv_path}")

    # 实时更新进度
    if st.session_state.crawler_running:
        progress_bar.progress(min(st.session_state.progress_count / max_results if max_results > 0 else 0, 1.0))
        progress_text.text(st.session_state.progress_text)
        progress_count.text(f"已爬取: {st.session_state.progress_count} / {max_results}")

    # 显示结果
    if st.session_state.crawler_result:
        result = st.session_state.crawler_result
        st.write(f"爬取结果保存路径: {result['csv_path']}")
        st.write(f"总计爬取: {result['total_results']} 个结果")
        
        with open(result['csv_path'], 'rb') as f:
            st.download_button(
                label="下载 CSV 文件",
                data=f,
                file_name=os.path.basename(result['csv_path']),
                mime="text/csv"
            )

with col_preview:
    st.subheader("CSV 文件预览")
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    selected_csv = st.selectbox("选择 CSV 文件", csv_files) if csv_files else st.write("暂无 CSV 文件")
    
    if selected_csv:
        csv_path = os.path.join(output_dir, selected_csv)
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 添加筛选功能
        search_term = st.text_input("搜索内容", key="csv_search")
        if search_term:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        
        st.dataframe(df, height=500)
        
        # 导出优化后的 CSV
        if st.button("导出优化 CSV"):
            # 过滤无用行
            useless_keywords = ["请稍候", "正在等待", "加载失败"]
            filtered_df = df[~df.apply(lambda row: any(keyword in str(row) for keyword in useless_keywords), axis=1)]
            
            # 保存到新文件
            optimized_csv_path = csv_path.replace('.csv', '_optimized.csv')
            filtered_df.to_csv(optimized_csv_path, index=False, encoding='utf-8')
            
            with open(optimized_csv_path, 'rb') as f:
                st.download_button(
                    label="下载优化 CSV",
                    data=f,
                    file_name=os.path.basename(optimized_csv_path),
                    mime="text/csv"
                )
            st.success(f"优化 CSV 已保存至 {optimized_csv_path}")

# 保存和加载配置
if st.button("手动保存当前配置"):
    save_last_config()
    st.success(f"配置已保存至 {default_config_file}")

config_file_input = st.file_uploader("加载其他配置", type=["json"])
if config_file_input:
    config = json.load(config_file_input)
    st.session_state.last_config = config
    st.success("配置已加载！请调整参数后重新提交。")
    st.rerun()