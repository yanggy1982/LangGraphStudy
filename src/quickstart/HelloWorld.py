# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : HelloWorld.py
@time    : 2025/12/24 14:21
@desc    : LangGraph版Hello World
-----------------------------------------------------------------------
"""

from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

if __name__ == '__main__':
    print("HelloWorld...")

    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    graph = graph.compile()

    graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
