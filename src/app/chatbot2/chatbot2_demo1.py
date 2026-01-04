# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot2_demo1.py
@time    : 2026/1/4 10:18
@desc    : 
-----------------------------------------------------------------------
"""
from typing import TypedDict
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore


# ======================= 1. 定义状态 =======================
class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str # 从长期记忆加载的用户名

# ======================= 2. 初始化记忆组件 =======================
# 短期记忆：每个thread独立
checkpointer = MemorySaver()

# 长期记忆：跨thread共享
store = InMemoryStore()

# ======================= 3. 定义节点 =======================
def chatbot(state: State, config: RunnableConfig):
    """聊天节点：演示如何读取configurable中的自定义字段"""
    # 从config读取自定义配置项
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"]["user_id"]
    session_type = config["configurable"].get("session_type","normal")
    device_id = config["configurable"].get("device_id","unknown")

    print(f"【后台日志】用户 {user_id} 在设备 {device_id} 发起 {session_type} 类型会话")

    # 长期记忆：加载用户画像
    namespace = (user_id,"profile")
    memory = store.get(namespace,"basic_info")
    user_name = memory.value["name"] if memory else "陌生人"

    # 生成回复
    last_message = state["messages"][-1].content

    response = f"你好{user_name}！你说的是：{last_message} (线程: {thread_id})"

    return {
        "messages": [response],
        "user_name": user_name
    }

def save_log(state: State, config: RunnableConfig):
    """日志节点：将会话记录保存到长期记忆"""

    user_id = config["configurable"]["user_id"]
    session_id = config["configurable"]["thread_id"]

    # 保存操作日志到长期记忆
    namespace = (user_id, "logs")
    log_entry = {
        "session_id": session_id,
        "message_count": len(state["messages"]),
        "last_message": state["messages"][-1].content,
        "timestamp": "2026-01-04"
    }
    store.put(namespace, f"log_{session_id}", log_entry)

    return {}  # 不修改状态

# ======================= 4. 构建图 =======================
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("save_log", save_log)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", "save_log")
builder.add_edge("save_log", END)

graph = builder.compile(
    checkpointer=checkpointer,
    store=store
)

# ======================= 5. 测试多用户多会话 =======================
# 用户1：第一次会话
config_user1_session1 = {
    "configurable": {
        "thread_id": "user1_conv1",  # 会话1
        "user_id": "user_001",       # 用户ID
        "session_type": "support",   # 自定义：会话类型
        "device_id": "mobile_123"    # 自定义：设备ID
    }
}

# 初始化用户1的长期记忆
store.put(
    ("user_001", "profile"),
    "basic_info",
    {"name": "Alice", "level": "VIP"}
)

# 用户1：第一次对话
print("\n========== 用户1-会话1 第一次提问 ==========")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "我的订单有问题"}]},
    config_user1_session1
)
print(f"回复: {result['messages'][-1]}")

# 用户1：同一会话第二次对话（有短期记忆）
print("\n========== 用户1-会话1 第二次提问 ==========")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "具体是支付问题"}]},
    config_user1_session1
)
print(f"回复: {result['messages'][-1]}")

# 用户1：新开一个会话（无短期记忆，但有长期记忆）
config_user1_session2 = {
    "configurable": {
        "thread_id": "user1_conv2",  # 新会话
        "user_id": "user_001",       # 同一用户
        "session_type": "sales",
        "device_id": "desktop_456"
    }
}

print("\n========== 用户1-会话2 第一次提问 ==========")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "推荐个产品"}]},
    config_user1_session2
)
print(f"回复: {result['messages'][-1]}")

# 用户2：完全不同的用户
config_user2_session1 = {
    "configurable": {
        "thread_id": "user2_conv1",
        "user_id": "user_002",
        "session_type": "support",
        "device_id": "mobile_789"
    }
}

# 初始化用户2的长期记忆
store.put(
    ("user_002", "profile"),
    "basic_info",
    {"name": "Bob", "level": "Normal"}
)

print("\n========== 用户2-会话1 第一次提问 ==========")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "我的订单有问题"}]},
    config_user2_session1
)
print(f"回复: {result['messages'][-1]}")

# ==================== 6. 验证长期记忆 ====================
print("\n========== 查看长期记忆存储 ==========")

# 查看用户1的日志
user1_logs = store.search(("user_001", "logs"))
print(f"用户1共有 {len(user1_logs)} 条日志记录")
for log in user1_logs:
    print(f"  - 会话 {log.value['session_id']}: {log.value['message_count']} 条消息")

# 查看用户2的日志
user2_logs = store.search(("user_002", "logs"))
print(f"用户2共有 {len(user2_logs)} 条日志记录")


if __name__ == '__main__':
    print("chatbot2_demo1...")
