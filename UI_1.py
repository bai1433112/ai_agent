import os
import time
import tempfile
import requests
import streamlit as st
import json
from chatbot_cv import Cv_Chatbot

# 全局配置：临时文件存储（用于后续删除，功能暂未实现）
temp_file_path_list = []

# ---------------------- 页面基础配置 ----------------------
st.set_page_config(
    page_title="AI 多模态对话助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- 初始化会话状态 ----------------------
# 确保所有必要的会话状态已初始化，避免KeyError
required_states = {
    "history": [],  # 对话历史：存储{role, content, type}
    "is_voice_mode": False,  # 是否开启语音模式
    "polling": False,  # 是否正在轮询语音结果
    "voice_result_received": False,  # 是否已收到语音结果
    "rag_loaded": False,  # 知识库是否加载完成
    "temp_files": []  # 存储临时文件路径（优化管理）
}
for key, default in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------- 后端接口配置 ----------------------
FASTAPI_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{FASTAPI_URL}/chat"
RAG_ENDPOINT = f"{FASTAPI_URL}/chat/rag"
VOICE_RESULT_ENDPOINT = f"{FASTAPI_URL}/voice_result"

# ---------------------- 初始化核心组件 ----------------------
cv_chatbot = Cv_Chatbot()

# ---------------------- 页面标题与说明 ----------------------
col1, col2 = st.columns([0.85, 0.15])
with col1:
    st.title("🤖 AI 多模态对话助手（轮询版）")
with col2:
    # 显示当前模式状态标签
    mode_label = "语音模式" if st.session_state.is_voice_mode else "文本/文件模式"
    mode_color = "🔴" if st.session_state.is_voice_mode else "🟢"
    st.markdown(f"<div style='text-align: center; margin-top: 15px; font-size: 14px;'>{mode_color} {mode_label}</div>",
                unsafe_allow_html=True)

# 简短使用说明
st.markdown("""
    <div style='background-color: #f0f8fb; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 13px;'>
    📌 支持功能：文本对话、语音交互、图片识别、表格分析、知识库上传 | 语音模式需先点击「启动语音监听」并说出唤醒词
    </div>
""", unsafe_allow_html=True)

# ---------------------- 侧边栏：文件上传与知识库 ----------------------
with st.sidebar:
    st.header("📁 知识库管理", divider="blue")

    # 文件上传区域
    uploaded_files = st.file_uploader(
        "选择要上传的文件（支持多文件）",
        type=None,  # 允许所有文件类型
        accept_multiple_files=True,
        help="支持PDF、CSV、MD、图片、表格等格式，上传后将加入知识库"
    )

    # 处理文件上传逻辑
    if uploaded_files:
        st.subheader("已选择文件", divider="gray")
        # 显示已选择的文件名
        for idx, file in enumerate(uploaded_files, 1):
            st.markdown(f"{idx}. {file.name} ({round(file.size / 1024, 2)}KB)")

        # 处理文件按钮（添加加载状态）
        if st.button("🚀 处理并上传知识库", type="primary"):
            with st.spinner("正在处理文件..."):
                file_path_list = []
                for file in uploaded_files:
                    # 创建临时文件
                    ext = os.path.splitext(file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                        f.write(file.getvalue())
                        f.flush()
                        temp_path = f.name
                        temp_file_path_list.append(temp_path)
                        st.session_state.temp_files.append(temp_path)
                        file_path_list.append(temp_path)

                # 调用RAG接口上传知识库
                try:
                    response = requests.post(
                        RAG_ENDPOINT,
                        json={"file_path_list": file_path_list},
                        params={"mode": "nlp"},
                        timeout=30  # 延长超时时间
                    )
                    response.raise_for_status()
                    st.session_state.rag_loaded = True
                    st.success("✅ 知识库上传成功！")
                except Exception as e:
                    st.error(f"❌ 知识库上传失败：{str(e)}")

    # 知识库状态显示
    if st.session_state.rag_loaded:
        st.markdown("""
            <div style='background-color: #d4edda; padding: 8px 12px; border-radius: 6px; margin-top: 10px;'>
            📚 知识库已加载 | 支持基于上传文件的问答
            </div>
        """, unsafe_allow_html=True)

    # 清除临时文件按钮（可选功能）
    if st.session_state.temp_files:
        if st.button("🗑️ 清除临时文件", type="secondary", help="删除上传文件生成的临时文件"):
            for temp_path in st.session_state.temp_files:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
            st.session_state.temp_files.clear()
            temp_file_path_list.clear()
            st.success("临时文件已清除")

    # 侧边栏底部说明
    st.markdown("""
        <div style='margin-top: 30px; font-size: 11px; color: #666;'>
        ⚠️ 临时文件将在会话结束后自动清理<br>
        支持文件类型：PDF、CSV、MD、PNG、JPG、XLSX
        </div>
    """, unsafe_allow_html=True)

# ---------------------- 主对话区域 ----------------------
st.header("💬 对话区域", divider="blue")

# 显示对话历史（优化样式和加载逻辑）
for msg in st.session_state["history"]:
    with st.chat_message(
            msg["role"],
            avatar="👤" if msg["role"] == "human" else "🤖"
    ):
        if msg["type"] == "text":
            # 优化文本显示样式
            st.markdown(f"<div style='line-height: 1.6;'>{msg['content']}</div>", unsafe_allow_html=True)
        elif msg["type"] == "image":
            # 优化图片显示大小和样式
            msg["content"].seek(0)
            st.image(msg["content"], width=300, caption="上传的图片", use_column_width=False)

# ---------------------- 输入区域（文本/文件/语音） ----------------------
# 聊天输入框（支持文本+多文件上传）
input = st.chat_input(
    "请输入消息、上传文件或启动语音模式...",
    accept_file="multiple",
    file_type=['png', 'jpg', 'jpeg', "xlsx", "csv", "pdf", "md"],
    key="main_chat_input"
)

# 处理输入逻辑
if input:
    # 1. 处理文本输入
    if input.text:
        with st.spinner("AI正在思考..."):
            try:
                response = requests.post(
                    CHAT_ENDPOINT,
                    json={"prompt": input.text},
                    params={"mode": "nlp"},
                    timeout=20
                )
                response.raise_for_status()

                # 更新对话历史
                st.session_state.history.append({
                    "role": "human",
                    "content": input.text,
                    "type": "text"
                })
                st.session_state.history.append({
                    "role": "assistant",
                    "content": response.text,
                    "type": "text"
                })

                st.rerun()
            except Exception as e:
                st.error(f"❌ 文本对话失败：{str(e)}")

    # 2. 处理文件上传（图片/表格等）
    if input.files:
        st.success(f"✅ 已接收 {len(input.files)} 个文件，正在处理...")

        for file in input.files:
            file_name = file.name.lower()
            file_size = round(file.size / 1024, 2)

            # 判断文件类型
            if file_name.endswith(('.png', '.jpg', '.jpeg')):
                file_type = "image"
                file_caption = "图像文件"
            elif file_name.endswith(('.xlsx', '.csv', '.json')):
                file_type = "table"
                file_caption = "表格文件"
            elif file_name.endswith(('.pdf', '.md')):
                file_type = "document"
                file_caption = "文档文件"
            else:
                st.warning(f"⚠️ 不支持的文件类型：{file.name}，已跳过")
                continue

            # 显示用户上传的文件
            with st.chat_message("human", avatar="👤"):
                if file_type == "image":
                    st.image(file, width=200, caption=f"{file_caption}：{file.name}")
                else:
                    st.markdown(f"📄 {file_caption}：{file.name}（{file_size}KB）")

                # 同时保存文本输入（如果有的话）
                if input.text:
                    st.markdown(f"💬 附加说明：{input.text}")

                # 更新对话历史
                st.session_state.history.append({
                    "role": "human",
                    "content": file,
                    "type": file_type
                })
                if input.text:
                    st.session_state.history.append({
                        "role": "human",
                        "content": input.text,
                        "type": "text"
                    })

            # 处理文件并调用对应接口
            with st.spinner(f"正在处理 {file_caption}..."):
                try:
                    if file_type == "image":
                        # 图片文件：转为base64调用CV接口
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                            f.write(file.getvalue())
                            f.flush()
                            base64_str = cv_chatbot.img2base64(f.name)
                            prompt = cv_chatbot.get_prompt(base64_str)
                            os.remove(f.name)  # 立即删除临时图片文件

                        # 调用CV模式接口
                        response = requests.post(
                            CHAT_ENDPOINT,
                            json={"prompt": prompt},
                            params={"mode": "cv"},
                            timeout=30
                        )

                    else:
                        # 表格/文档文件：保存为临时文件调用NLP接口
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as f:
                            f.write(file.getvalue())
                            f.flush()
                            temp_path = f.name
                            st.session_state.temp_files.append(temp_path)

                        # 调用NLP模式接口
                        response = requests.post(
                            CHAT_ENDPOINT,
                            json={"prompt": temp_path},
                            params={"mode": "nlp"},
                            timeout=30
                        )

                    response.raise_for_status()

                    # 更新AI回复
                    st.session_state.history.append({
                        "role": "assistant",
                        "content": response.json() if file_type != "text" else response.text,
                        "type": "text"
                    })

                except Exception as e:
                    st.error(f"❌ 处理 {file.name} 失败：{str(e)}")

        st.rerun()

# ---------------------- 语音模式控制区域 ----------------------
st.markdown("---")
col_voice1, col_voice2, col_voice3 = st.columns([0.3, 0.3, 0.4])

with col_voice1:
    # 启动语音监听按钮
    if st.button(
            "🎤 启动语音监听",
            type="primary" if not st.session_state.is_voice_mode else "secondary",
            disabled=st.session_state.polling,
            use_container_width=True
    ):
        st.session_state.is_voice_mode = True
        try:
            # 启动语音监听
            response = requests.post(
                CHAT_ENDPOINT,
                json={"prompt": "开始语音监听"},
                params={"mode": "voice"},
                timeout=10
            )
            response.raise_for_status()

            # 更新历史记录
            st.session_state.history.append({
                "role": "human",
                "content": "已启动语音模式，请说出唤醒词...",
                "type": "text"
            })

            # 开始轮询语音结果
            st.session_state.polling = True
            st.session_state.voice_result_received = False
            polling_count = 0
            max_polls = 60  # 1分钟超时

            with st.spinner("🎙️ 正在监听语音...（请说出唤醒词）"):
                while st.session_state.polling and polling_count < max_polls:
                    try:
                        # 轮询结果接口
                        result_response = requests.get(VOICE_RESULT_ENDPOINT, timeout=5)
                        result_data = result_response.json()

                        if "response" in result_data and result_data["response"] is not None:
                            # 收到语音结果
                            st.session_state.history.append({
                                "role": "assistant",
                                "content": result_data["response"],
                                "type": "text"
                            })
                            st.session_state.voice_result_received = True
                            st.session_state.polling = False
                            st.success("🎉 语音对话完成！")
                            break
                        else:
                            # 未收到结果，继续轮询
                            polling_count += 1
                            time.sleep(1)

                    except Exception as e:
                        st.warning(f"轮询失败：{str(e)}，将继续尝试...")
                        time.sleep(1)
                        polling_count += 1

            # 轮询超时处理
            if not st.session_state.voice_result_received:
                st.error("⏱️ 轮询超时，未获取到语音结果（请检查：1.唤醒词是否正确 2.后端服务是否正常 3.麦克风是否可用）")

            # 重置状态
            st.session_state.polling = False
            st.session_state.is_voice_mode = False
            st.rerun()

        except Exception as e:
            st.error(f"❌ 启动语音模式失败：{str(e)}")
            st.session_state.is_voice_mode = False

with col_voice2:
    # 关闭语音监听按钮
    if st.button(
            "🛑 关闭语音监听",
            type="secondary",
            disabled=not (st.session_state.is_voice_mode or st.session_state.polling),
            use_container_width=True
    ):
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={"prompt": "关闭语音监听"},
                params={"mode": "voice"},
                timeout=10
            )
            response.raise_for_status()

            st.session_state.is_voice_mode = False
            st.session_state.polling = False
            st.session_state.history.append({
                "role": "human",
                "content": "已关闭语音模式",
                "type": "text"
            })
            st.success("✅ 语音监听已关闭")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 关闭语音模式失败：{str(e)}")

with col_voice3:
    # 轮询状态显示
    if st.session_state.polling:
        st.markdown("""
            <div style='background-color: #fff3cd; padding: 12px; border-radius: 8px; height: 100%; display: flex; align-items: center;'>
            🟡 正在轮询语音结果...<br>
            超时时间：60秒 | 请说出唤醒词
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 12px; border-radius: 8px; height: 100%;'>
            📝 语音模式说明：<br>
            1. 点击启动监听<br>
            2. 说出唤醒词触发对话<br>
            3. 等待AI语音回复
            </div>
        """, unsafe_allow_html=True)

# ---------------------- 底部说明 ----------------------
st.markdown("""
    <div style='text-align: center; margin-top: 30px; font-size: 11px; color: #888;'>
    © 2025 AI 多模态对话助手 | 后端服务地址：{} | 如有问题请检查服务是否正常运行
    </div>
""".format(FASTAPI_URL), unsafe_allow_html=True)