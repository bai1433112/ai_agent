import streamlit as st
import pandas as pd
from untils import exam_generator
import time
import json

# 页面设置
st.set_page_config(
    page_title="智能试卷生成器",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .exam-preview {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #bee5eb;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化session状态"""
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
    if 'generated_exam' not in st.session_state:
        st.session_state.generated_exam = ""
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    if 'use_simple_mode' not in st.session_state:
        st.session_state.use_simple_mode = False


def load_model():
    """加载模型"""
    if not st.session_state.model_loaded:
        with st.spinner("正在加载AI模型，请稍候...这可能需要几分钟"):
            success = exam_generator.load_model()
            if success:
                st.session_state.model_loaded = True
                st.session_state.use_simple_mode = False
                st.success("✅ AI模型加载成功！")
            else:
                st.session_state.use_simple_mode = True
                st.warning("⚠️ AI模型加载失败，已启用简化模式")


def main():
    """主应用"""
    st.markdown('<div class="main-header">📝 智能试卷生成器</div>', unsafe_allow_html=True)

    # 初始化session状态
    init_session_state()

    # 侧边栏
    with st.sidebar:
        st.header("🔧 设置")

        # 模型状态
        st.subheader("模型状态")
        if st.session_state.model_loaded:
            st.success("✅ AI模型已加载")
            if st.button("🔄 重新加载模型"):
                st.session_state.model_loaded = False
                load_model()
        else:
            if st.session_state.use_simple_mode:
                st.warning("⚠️ 简化模式")
            else:
                st.warning("⚠️ 模型未加载")
            if st.button("🚀 加载AI模型"):
                load_model()

        st.divider()

        # 使用说明
        st.subheader("💡 使用说明")
        if st.session_state.use_simple_mode:
            st.markdown("""
            **简化模式说明：**
            1. 填写试卷生成参数
            2. 点击'生成试卷'按钮
            3. 查看并下载生成的试卷框架
            """)
        else:
            st.markdown("""
            **AI模式说明：**
            1. 首先点击'加载模型'按钮
            2. 填写试卷生成参数  
            3. 点击'生成试卷'按钮
            4. 查看并下载生成的试卷
            """)

        # 历史记录
        if st.session_state.generation_history:
            st.divider()
            st.subheader("📚 生成历史")
            for i, history in enumerate(st.session_state.generation_history[-5:]):
                with st.expander(f"记录 {i + 1}: {history['subject']} - {history['topic']}"):
                    st.write(f"时间: {history['timestamp']}")
                    st.write(f"科目: {history['subject']}")
                    st.write(f"主题: {history['topic']}")

    # 主内容区
    tab1, tab2, tab3 = st.tabs(["📋 生成试卷", "👀 预览试卷", "📊 使用统计"])

    with tab1:
        if st.session_state.use_simple_mode:
            st.markdown(
                '<div class="warning-box">当前处于简化模式，将生成试卷框架。如需AI生成完整内容，请点击侧边栏"加载AI模型"</div>',
                unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">请填写以下参数来生成定制试卷</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # 基本参数
            subject = st.selectbox(
                "选择科目",
                ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "计算机"]
            )

            grade = st.selectbox(
                "选择年级",
                ["小学一年级", "小学二年级", "小学三年级", "小学四年级", "小学五年级", "小学六年级",
                 "初中一年级", "初中二年级", "初中三年级",
                 "高中一年级", "高中二年级", "高中三年级", "大学"]
            )

            exam_type = st.selectbox(
                "考试类型",
                ["单元测试", "期中考试", "期末考试", "模拟考试", "随堂测验", "作业练习"]
            )

        with col2:
            # 高级参数
            topic = st.text_input(
                "考察主题",
                placeholder="例如：二次函数、古代诗词、牛顿定律...",
                help="请输入具体的知识点或主题"
            )

            difficulty = st.select_slider(
                "试卷难度",
                options=["简单", "中等", "困难", "竞赛级"]
            )

            num_questions = st.slider(
                "题目数量",
                min_value=5,
                max_value=30,
                value=15,
                help="建议题目数量在5-30题之间"
            )

        # 题型选择
        st.subheader("📝 选择题型")
        question_types = st.multiselect(
            "选择需要的题型",
            ["选择题", "填空题", "简答题", "计算题", "论述题"],
            default=["选择题", "填空题", "简答题"]
        )

        # 生成按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_btn = st.button(
                "🎯 生成试卷",
                type="primary",
                use_container_width=True
            )

        if generate_btn:
            if not topic:
                st.error("❌ 请填写考察主题")
            elif not question_types:
                st.error("❌ 请至少选择一种题型")
            else:
                with st.spinner("正在生成试卷，请稍候..."):
                    start_time = time.time()

                    # 生成试卷
                    if st.session_state.model_loaded:
                        exam_content = exam_generator.generate_exam(
                            subject=subject,
                            grade=grade,
                            exam_type=exam_type,
                            topic=topic,
                            question_types=question_types,
                            num_questions=num_questions,
                            difficulty=difficulty
                        )
                    else:
                        exam_content = exam_generator.generate_exam_simple(
                            subject=subject,
                            grade=grade,
                            exam_type=exam_type,
                            topic=topic,
                            question_types=question_types,
                            num_questions=num_questions,
                            difficulty=difficulty
                        )

                    end_time = time.time()
                    generation_time = round(end_time - start_time, 2)

                    # 保存到session state
                    st.session_state.generated_exam = exam_content

                    # 记录生成历史
                    history_record = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "subject": subject,
                        "grade": grade,
                        "topic": topic,
                        "generation_time": generation_time,
                        "mode": "AI" if st.session_state.model_loaded else "简化"
                    }
                    st.session_state.generation_history.append(history_record)

                    st.success(f"✅ 试卷生成完成！耗时: {generation_time}秒")
                    st.rerun()

    with tab2:
        st.subheader("📄 试卷预览")

        if st.session_state.generated_exam:
            st.markdown('<div class="exam-preview">', unsafe_allow_html=True)
            st.text_area(
                "生成的试卷",
                st.session_state.generated_exam,
                height=500,
                key="exam_preview"
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # 下载按钮
            col1, col2, col3 = st.columns(3)
            with col2:
                st.download_button(
                    label="💾 下载试卷",
                    data=st.session_state.generated_exam,
                    file_name=f"{subject}_{grade}_{topic}_试卷.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("👆 请先在'生成试卷'标签页中生成试卷")

    with tab3:
        st.subheader("📊 使用统计")

        if st.session_state.generation_history:
            # 转换为DataFrame用于显示
            df = pd.DataFrame(st.session_state.generation_history)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("总生成次数", len(st.session_state.generation_history))

                # 科目分布
                if 'subject' in df.columns:
                    subject_counts = df['subject'].value_counts()
                    st.bar_chart(subject_counts)

            with col2:
                if 'generation_time' in df.columns:
                    avg_time = df['generation_time'].mean()
                    st.metric("平均生成时间", f"{avg_time:.2f}秒")

                # 最近生成记录
                st.write("最近生成记录:")
                st.dataframe(df.tail(5), use_container_width=True)
        else:
            st.info("暂无生成记录")


if __name__ == "__main__":
    main()