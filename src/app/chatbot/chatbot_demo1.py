# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot_demo1.py
@time    : 2025/12/24 14:31
@desc    : 聊天机器人(基础)
-----------------------------------------------------------------------
"""

from dotenv import load_dotenv
import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_anthropic import ChatAnthropic

load_dotenv(dotenv_path="../../env/.env")
api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model_name = "claude-opus-4-5-20251101"

llm = ChatAnthropic(model=model_name)

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
    return {"messages": [llm.invoke(state["messages"])]}

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

if __name__ == '__main__':
    print("chatbot_demo1...")
    #print(f"api_key: {api_key},base_url: {base_url},model_name: {model_name}")

    graph_builder = StateGraph(State)

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
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



