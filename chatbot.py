"""
所有模态最终需要输入的模型,各模态模型类的基类
"""
import logging
import sqlite3
import time

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_classic.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver  # 适合本地部署，短期记忆
# from langgraph.checkpoint.postgres import PostgresSaver  # 适合企业级部署，长期记忆
from langgraph.checkpoint.sqlite import SqliteSaver  # 适合本地部署，长期记忆

from Middleware import MessageTrimmerMiddleware
# from langgraph.checkpoint.memory import InMemorySaver
from my_tools import *
from utils import load_config

config = load_config()


class ChatBot():

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = load_config()
        # 初始化工具
        self.tools = get_tools()
        # 设置 LangChain Agent
        self.setup_agent()

    def setup_agent(self):
        """初始化LangChain Agent,开启流式输出"""
        # 初始化语言模型 - 关键:设置 streaming=True
        self.llm = ChatOpenAI(
            openai_api_key=config["api"]["openai_api_key"],
            base_url=config["api"]["base_url"],
            model=config["chat_model"]["name"],
        )

        # 定义系统提示词
        system_prompt = r"""
        你叫小布,是一位聪明、亲切的,拥有数据处理能力的智能多模态助手，你的最终输出无论如何必须是调用transformer工具后的结果
        你必须直接返回自然语言文本，不允许返回 JSON、字典、markdown格式、\n或任何结构化格式。
        当碰到不了解的问题前一定是先去知识库检索search_knowledge，检索完再去web_search搜索
        你有以下能力:
        1. 查询天气信息
        2. 获取当前时间
        3. 进行网络搜索
        4. 根据起始地点（从省级开始描述）和目标地点（从省级开始描述）获取导航信息
        5. 检索知识库
        6.转换输出风格为鲁迅风格

        """

        # 创建带记忆的 Agent
        #创建对话持久化
        conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        checkpointer = SqliteSaver(conn)  # 文件自动创建
        # checkpointer = MemorySaver()  # 文件自动创建
        # 包装 Agent，在每次调用前修剪消息
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer, #支持长期对话 绑定对话状态持久化（长期记忆）
            # 添加消息修剪中间件
            # 添加对话消息修剪中间件，解决 “上下文过长导致模型超限 / 性能下降” 的问题。
            middleware=[MessageTrimmerMiddleware(max_messages=15)], #最大消息数是15条

        )
        # with open("create_agent_graph.png", "wb") as f:
        #     f.write(self.agent.get_graph().draw_mermaid_png())

        # 初始化对话线程ID
        # LangChain Agent 的 “对话线程标识”，用于区分不同用户的对话：
        # 同一用户的所有对话都用同一个 thread_id，Agent 会通过 checkpointer 关联该线程的所有历史消息；
        # 若支持多用户，可动态生成 thread_id（如 f"user_{user_id}"），避免不同用户的对话上下文混淆。
        self.thread_id = "conversation_1"

    def clear_conversation_history(self):
        """清除对话历史"""
        pass
