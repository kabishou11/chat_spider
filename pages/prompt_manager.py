import streamlit as st
from utils import load_config, save_config

# 默认提示词模板示例
TEMPLATE_EXAMPLES = {
    "数据分析专家": """
你是一个高级数据分析专家，擅长从 CSV 数据中提取洞见。
数据文件内容如下：
{file_contents}

用户的问题是：{user_input}

请你：
1. 分析数据中的关键趋势和模式。
2. 回答用户的问题，并提供数据支持。
3. 提出可能的后续分析建议。
""",
    "新闻摘要助手": """
你是一个新闻摘要助手，负责从新闻数据中提取关键信息。
新闻文件内容如下：
{file_contents}

用户的问题是：{user_input}

请你：
1. 总结每条新闻的核心要点。
2. 回答用户关于新闻内容的问题。
3. 提供相关背景或补充信息。
""",
}

# 加载提示词模板
def load_prompt_templates():
    config = load_config()
    return config.get("prompt_templates", {})

# 保存提示词模板
def save_prompt_template(name, template):
    config = load_config()
    config["prompt_templates"] = config.get("prompt_templates", {})
    config["prompt_templates"][name] = template
    save_config(config)

# 删除提示词模板
def delete_prompt_template(name):
    config = load_config()
    templates = config.get("prompt_templates", {})
    if name in templates:
        del templates[name]
        config["prompt_templates"] = templates
        save_config(config)

# 重命名提示词模板
def rename_prompt_template(old_name, new_name):
    config = load_config()
    templates = config.get("prompt_templates", {})
    if old_name in templates and new_name not in templates:
        templates[new_name] = templates.pop(old_name)
        config["prompt_templates"] = templates
        save_config(config)

# 主函数
def main():
    st.set_page_config(page_title="提示词模板管理", layout="wide")
    st.title("提示词模板管理")
    st.markdown("""
    在这里管理你的提示词模板，支持创建、编辑、删除、重命名模板，并提供示例和提示词工程指导。
    """)

    # 使用 tabs 分区管理功能
    tab1, tab2, tab3 = st.tabs(["📋 模板管理", "➕ 添加模板", "🌟 模板示例"])

    # 模板管理
    with tab1:
        st.subheader("现有模板管理")
        templates = load_prompt_templates()
        if templates:
            col_select, col_content = st.columns([1, 2])
            with col_select:
                selected_template = st.selectbox("选择模板", list(templates.keys()), key="manage_select")
            with col_content:
                template_content = st.text_area("编辑模板内容", value=templates[selected_template], height=300, key="manage_content")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("保存", key="manage_save"):
                    save_prompt_template(selected_template, template_content)
                    st.success(f"模板 '{selected_template}' 更新成功！")
            with col_btn2:
                new_name = st.text_input("新名称", key="rename_input")
                if st.button("重命名", key="manage_rename") and new_name:
                    if new_name in templates:
                        st.error("新名称已存在，请使用其他名称！")
                    else:
                        rename_prompt_template(selected_template, new_name)
                        st.success(f"模板已重命名为 '{new_name}'！")
                        st.rerun()
            with col_btn3:
                if st.button("删除", key="manage_delete"):
                    delete_prompt_template(selected_template)
                    st.success(f"模板 '{selected_template}' 删除成功！")
                    st.rerun()
        else:
            st.info("暂无模板，请在“添加模板”标签页创建。")

    # 添加新模板
    with tab2:
        st.subheader("添加新模板")
        new_name = st.text_input("模板名称", key="add_name")
        new_content = st.text_area("模板内容", height=300, key="add_content")
        if st.button("添加模板", key="add_button") and new_name:
            if new_name in load_prompt_templates():
                st.error("模板名称已存在，请使用其他名称！")
            else:
                save_prompt_template(new_name, new_content)
                st.success(f"模板 '{new_name}' 添加成功！")
                st.rerun()

    # 模板示例
    with tab3:
        st.subheader("提示词模板示例")
        st.markdown("以下是精心设计的模板示例，可直接使用或作为灵感来源：")
        for name, example in TEMPLATE_EXAMPLES.items():
            with st.expander(f"{name}", expanded=False):
                st.code(example, language="markdown")
                if st.button(f"使用此模板", key=f"use_{name}"):
                    save_prompt_template(name, example)
                    st.success(f"模板 '{name}' 已添加到你的模板列表！")

if __name__ == "__main__":
    main()