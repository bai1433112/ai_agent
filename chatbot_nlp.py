import os

from langchain_core.tracers import ConsoleCallbackHandler
import json
from utils import load_config
from chatbot import ChatBot
from utils import load_config
os.environ["USER_AGENT"] = "my-app/0.1"

class nlp_chatbot(ChatBot):
    def __init__(self):
        super().__init__()
        self.config = load_config()

    def get_llm_response(self, query):
        try:
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": query}], "verbose": True},
                config={"configurable": {"thread_id": self.thread_id}},
                stream_mode="values"
            )

            raw = result["messages"][-1].content

            # 关键：尝试把模型返回内容当 JSON 解析
            try:
                import json
                obj = json.loads(raw)
                if isinstance(obj, dict) and "response" in obj:
                    return obj["response"]
                else:
                    return raw  # 不是标准结构就返回原文本
            except json.JSONDecodeError:
                return raw  # 模型返回的不是 JSON 字符串，就直接返回

        except Exception as e:
            return f"模型调用失败: {e}"


if __name__ == '__main__':

    chatbot = nlp_chatbot()

    ret7 = chatbot.get_llm_response("今晚的月色真好，我能邀请你跳一支舞吗？")
    # ret8 = chatbot.get_llm_response("现在训练一个随机森林回归模型，特征列用'Age',目标列'Fare',调用machine_learning_train工具")

    print("ret7",ret7)
    # print("ret8",ret8)












