import json
import re
from datetime import datetime

import pandas as pd
import requests
from baidusearch.baidusearch import search
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sympy.parsing.latex import parse_latex


from utils import load_config


config = load_config()

progressor = None


class columnInput(BaseModel):
    columns: str = Field(..., description="需要填充空值的列名")

# 加载FAISS知识库
embedding = HuggingFaceEmbeddings(model_name=config["embedding"]["model"])

vector_db = FAISS.load_local("faiss_index", embedding,
                             allow_dangerous_deserialization=True)  # 加载已存储的索引


@tool("search_knowledge", description="必须用于从本地知识库获取答案")
def search_knowledge(query: str) -> str:
    """
    从本地知识库检索最相关的内容，该工具必须优先使用
    输入：用户查询文本。
    输出：检索出的知识条目文本。
    """
    if not query:
        return "没有提供检索内容"

    docs_with_scores = vector_db.similarity_search_with_score(query, k=20)
    if not docs_with_scores:
        return "知识库中没有找到相关内容"
    threshold = 0.5
    # 2. 根据阈值筛选结果（分数 < 阈值 表示相似度较高）
    filtered_docs = [doc for doc, score in docs_with_scores if score < threshold]

    return "\n\n".join(d.page_content for d in filtered_docs)

@tool("plus")
def plus(a,b):
    """
    当你需要实现加法时调用该工具
    :param city:参数 a ,b
    :return :输出 a + b
    """
    return a + b

@tool("transformer",return_direct=True)
def transformer(query):
    """
    把输入的语句转换为鲁迅的口吻，当你做最后输出时调用
    """
    llm = ChatOpenAI(
        base_url="https://api.siliconflow.cn/v1",
        openai_api_key="sk-talrfpdubittuoctscpxqyuhotkkqgcmuxrxxlmmhkqpzlxd",
        model="Qwen/Qwen2.5-7B-Instruct"
    )
    output_parser = StrOutputParser()

    transformer_prompt = ChatPromptTemplate.from_template("把{query}的语句改为鲁迅的口吻并输出")
    transformer_chain = transformer_prompt | llm | output_parser


    result = transformer_chain.invoke({"query": query})
    return result
    # print(result)



@tool("get_weather")
def get_weather(city):
    """
    查询指定城市的实时天气信息
    :param city: 城市名称
    :return: 返回一个字符串，指定城市的当前温度和天气
    """
    try:
        url = f"http://wttr.in/{city}?format=j1"
        response = requests.get(url)
        data = response.json()
        if "current_condition" in data:
            temp = data["current_condition"][0]["temp_C"]
            weather = data["current_condition"][0]["weatherDesc"][0]["value"]
            print(f"{city}当前温度：{temp}°C，天气：{weather}")
            return f"{city}当前温度：{temp}°C，天气：{weather}"
        else:
            return f"无法获取{city}的天气信息"
    except Exception as e:
        return f"查询天气时出错: {str(e)}"


@tool("get_current_time", return_direct=True)
def get_current_time(a=None):
    """
    获取当前系统时间，无需输入参数
    :return: 返回字符串，字符串为当前时间，格式为%Y年%m月%d日 %H时%M分%S秒
    """
    return f"当前时间：{datetime.now().strftime('%Y年%m月%d日 %H时%M分%S秒')}"

def clean_abstract(text):
    """清理摘要文本中的多余换行和空格"""
    # 替换换行符为空格
    text = text.replace('\n', ' ')
    # 替换连续多个空格为单个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@tool("web_search")
def web_search(query):
    """通过网络搜索获取信息，输入为搜索关键词"""
    # 直接搜索无需API密钥
    results = search(query, num_results=10)  # 找回十条

    for item in results:
        item['abstract'] = clean_abstract(item['abstract'])

    return results


def get_coordinate(address):
    """
    获取地点坐标
    :param address: 需要提取坐标的地点
    :return: 起始地点对应的坐标
    """
    api_key = config["api"]["gaode_api_key"]
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": api_key,
        "address": address
    }
    response = requests.get(url, params=params)

    data = response.json()
    if data["status"] == "1" and data["count"] != "0":
        location = data["geocodes"][0]["location"]
        return f"{location}"
    else:
        return None


@tool("navigation")
def navigation(origin, destination):
    """
    导航工具，输入起点和目标地点
    :param origin: 起始地点
    :param destination: 目标地点
    :return: 导航总距离、预计时间、下一步操作、下一步操作的行进距离
    """
    print(origin)
    print(destination)
    origin = get_coordinate(origin)
    destination = get_coordinate(destination)
    api_key = config["api"]["gaode_api_key"]
    params = {
        "key": api_key,
        "origin": origin,
        "destination": destination
    }
    url = f"https://restapi.amap.com/v3/direction/driving"
    response = requests.get(url, params=params)
    data = response.json()
    if data["status"] == "1" and data["count"] != "0":
        # print(data)
        # 获取速度最快的路线（已明确唯一，直接取第一条）
        fastest_route = data["route"]["paths"][0]

        # 解析总距离、总时间
        total_distance = int(fastest_route["distance"])
        total_time_min = int(fastest_route["duration"]) // 60
        distance_str = f"{total_distance}米（约{total_distance / 1000:.1f}公里）"

        # 解析下一步导航指令（第一步）
        first_step = fastest_route["steps"][0]
        next_instruction = first_step["instruction"]
        next_distance = first_step["distance"]  # 第一步距离
        return f"distance_str:{distance_str}, total_time_min:{total_time_min}, next_instruction:{next_instruction},next_distance: {next_distance}"
    else:
        print("导航失败")
        return



def get_tools():
    return [get_weather,
            plus,
            get_current_time,
            web_search, navigation,
            search_knowledge,
            transformer,
            ]
