# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot_demo4.py
@time    : 2025/12/31 14:39
@desc    : 聊天机器人(包含自定义工具和记忆功能)
-----------------------------------------------------------------------
"""
from contextlib import ExitStack

from dotenv import load_dotenv
import os
from typing import Annotated
import requests
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv(dotenv_path="../../env/.env")

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model_name = "claude-opus-4-5-20251101"
tavily_api_key = os.getenv("TAVILY_API_KEY")

# 定义天气查询工具
class WeatherInput(BaseModel):
    location:str= Field(description="城市名称，如Beijing、Shanghai、ChangSha")

@tool(args_schema=WeatherInput)
def get_weather(location:str) :
    """
    查询指定城市的当前天气
    :param location:
    :return:
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": os.getenv("OPENWEATHERMAP_API_KEY"),  # 需要去openweathermap.org注册
        "units": "metric",
        "lang": "zh_cn"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"{location}当前天气：{weather}，温度：{temp}°C"
        else:
            return f"查询失败：{data.get('message', '未知错误')}"
    except Exception as e:
        return f"查询出错：{str(e)}"


tools = [get_weather]
llm = ChatAnthropic(model=model_name)
llm_with_tools = llm.bind_tools(tools)

# 持久化存储
stack = ExitStack()
memory = stack.enter_context(
    SqliteSaver.from_conn_string("weather_agent.sqlite")
)

class State(TypedDict):
    """
    定义状态
    """
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    """
    定义大模型调用节点
    :param state:
    :return:
    """
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def stream_graph_updates(user_input: str,config):
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()

if __name__ == '__main__':
    print("chatbot_demo4...")

    config = {"configurable": {"thread_id": "1"}}

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )

    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    graph = graph_builder.compile(checkpointer=memory)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input, config)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input, config)
            break



