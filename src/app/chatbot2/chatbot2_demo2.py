# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot2_demo2.py
@time    : 2026/1/4 14:43
@desc    : 包含人工干预和时间旅行的智能客服
-----------------------------------------------------------------------
"""

from typing import TypedDict, Annotated, Optional, List
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
import json


# ======================= 1. 定义工具（模拟真实业务） =======================
@tool
def query_order_status(order_id: str) -> dict:
    """查询订单状态"""
    # 模拟数据库查询
    mock_db = {
        "ORD-001": {"status": "已发货", "product": "iPhone 15", "amount": 5999},
        "ORD-002": {"status": "处理中", "product": "MacBook Pro", "amount": 12999},
    }
    return mock_db.get(order_id, {"error": "订单不存在"})

@tool
def apply_refund(order_id: str, reason: str) -> dict:
    """申请退款（需要人工审批）"""
    return {
        "refund_id": f"RF-{order_id}",
        "status": "pending_approval",
        "message": f"退款申请已提交，原因：{reason}"
    }

@tool
def get_knowledge_base(query: str) -> str:
    """查询知识库"""
    kb = {
        "退货政策": "支持7天无理由退货，15天质量问题换货",
        "运费规则": "满99元免运费，VIP用户全年包邮",
    }
    return kb.get(query, "暂无相关信息")

# ======================= 2. 定义状态 =======================
class State(TypedDict):
    messages: Annotated[List, add_messages]
    user_name: Optional[str]
    user_profile: Optional[dict]  # 完整的用户画像
    requires_approval: bool  # 是否需要人工审批
    refund_request: Optional[dict]  # 退款申请详情

# ======================= 3. 初始化记忆组件 =======================
checkpointer = MemorySaver()
store = InMemoryStore()

# ======================= 4. 定义业务节点 =======================
def load_profile(state: State, config: RunnableConfig):
    """加载用户长期记忆"""
    cfg = config.get("configurable", {})
    user_id = cfg.get("user_id", "anonymous")

    print(f"user_id:{user_id}")

    # 从长期记忆加载用户画像
    memory = store.get((user_id, "profile"), "basic_info")
    if memory:
        profile = memory.value
        user_name = profile.get("name", "用户")
    else:
        profile = {}
        user_name = "新用户"

    return {
        "user_name": user_name,
        "user_profile": profile,
        "messages": [SystemMessage(f"已加载用户档案：{user_name}")]
    }

def analyze_intent(state: State, config: RunnableConfig):
    """分析用户意图"""
    last_message = state["messages"][-1].content

    if "订单" in last_message or "快递" in last_message:
        intent = "订单查询"
    elif "退款" in last_message or "退货" in last_message:
        intent = "退款申请"
    else:
        intent = "一般咨询"

    return {
        "messages": [AIMessage(f"[意图识别] 用户意图：{intent}")]
    }

def call_tools(state: State):
    """调用工具处理业务"""
    # 找到用户的最新一条消息
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg
            break

    print(f"user_message:{user_message}")

    if user_message and "ORD-" in user_message.content:
        # 提取订单号
        order_id = user_message.content.split("ORD-")[1].split()[0]
        print(f"order_id:{order_id}")
        order_info = query_order_status.invoke(f"ORD-{order_id}")
        return {
            "messages": [AIMessage(f"订单状态：{json.dumps(order_info, ensure_ascii=False)}")]
        }

    return {"messages": [AIMessage("请提供订单号格式：ORD-001")]}

def extract_memory(state: State, config: RunnableConfig):
    """自动提取用户偏好并保存到长期记忆"""
    cfg = config.get("configurable", {})
    user_id = cfg.get("user_id", "anonymous")

    # 分析对话内容提取偏好
    all_content = " ".join([m.content for m in state["messages"]])
    preferences = {}

    if "喜欢" in all_content:
        preferences["likes"] = "从对话中提取的兴趣点"

    if preferences:
        store.put(
            (user_id, "profile"),
            "preferences",
            preferences
        )

    return {}

def human_approval(state: State):
    """检查是否需要人工审批"""
    last_message = state["messages"][-1].content

    # 模拟审批规则：退款金额 > 5000 需要审批
    if "退款" in last_message:
        return {
            "requires_approval": True,
            "messages": [AIMessage("[系统] 检测到高风险操作，需要人工审批")]
        }

    return {"requires_approval": False}

def handle_approval(state: State):
    """处理人工审批结果"""
    if state["requires_approval"]:
        # 模拟人工审批通过
        return {
            "messages": [AIMessage("[审批] 人工已批准，继续处理")],
            "requires_approval": False
        }

    return {}

# ======================= 5. 构建智能工作流 =======================
builder = StateGraph(State)
# 添加节点
builder.add_node("load_profile", load_profile)
builder.add_node("analyze_intent", analyze_intent)
builder.add_node("tools", call_tools)
builder.add_node("extract_memory", extract_memory)
builder.add_node("human_approval", human_approval)
builder.add_node("handle_approval", handle_approval)
# 添加边
builder.add_edge(START, "load_profile")
builder.add_edge("load_profile", "analyze_intent")
builder.add_edge("analyze_intent", "tools")

# 条件分支：根据审批需求决定路径
def check_approval(state: State):
    return "needs_approval" if state["requires_approval"] else "continue"

builder.add_edge("tools", "human_approval")
builder.add_conditional_edges(
    "human_approval",
    check_approval,
    {
        "needs_approval": "handle_approval",
        "continue": "extract_memory"
    }
)
builder.add_edge("handle_approval", "extract_memory")
builder.add_edge("extract_memory", END)

# 编译图
graph = builder.compile(checkpointer=checkpointer, store=store)

def run_customer_service_scenario():
    """运行完整客服场景模拟"""

    print("🎯 智能客服 Agent 启动")
    print("=" * 60)

    # 场景1：新用户咨询订单
    config_new_user: RunnableConfig = {
        "configurable": {
            "thread_id": "conv_new_user_001",
            "user_id": "new_user_001"
        }
    }

    print("\n【场景1】新用户查询订单")
    result = graph.invoke(
        {"messages": [HumanMessage("我想查订单 ORD-001")]},
        config_new_user
    )
    print(f"最终回复: {result['messages'][-1].content}")

    # 场景2：VIP用户申请退款（触发审批）
    config_vip: RunnableConfig = {
        "configurable": {
            "thread_id": "conv_vip_001",
            "user_id": "vip_user_001"
        }
    }

    # 初始化VIP用户档案
    store.put(
        ("vip_user_001", "profile"),
        "basic_info",
        {"name": "王总", "level": "VIP", "total_spend": 50000}
    )

    print("\n【场景2】VIP用户申请高价值退款")
    result = graph.invoke(
        {"messages": [HumanMessage("我要申请订单 ORD-002 的退款，金额12999元")]},
        config_vip
    )
    print(f"最终回复: {result['messages'][-1].content}")

    # 场景3：时间旅行 - 查看历史状态
    print("\n【场景3】时间旅行 - 查看对话历史")
    history = list(graph.get_state_history(config_vip))
    print(f"该对话共有 {len(history)} 个状态快照")
    for i, snapshot in enumerate(history[:3]):
        print(f"  步骤 {i}: {snapshot.metadata.get('step', 0)} 步")

    # 场景4：状态分叉 - 模拟如果审批拒绝会怎样
    print("\n【场景4】状态分叉 - 探索替代路径")
    # 获取审批前的状态
    approval_state = graph.get_state(config_vip)
    # 可以在此处修改状态并重新执行

    # 场景5：长期记忆验证
    print("\n【场景5】验证长期记忆")
    vip_profile = store.get(("vip_user_001", "profile"), "basic_info")
    if vip_profile:
        print(f"  VIP用户档案: {vip_profile.value}")

    # 查看所有日志
    print("\n【长期记忆】所有操作日志:")
    all_logs = store.search(("vip_user_001", "logs"))
    for log in all_logs:
        print(f"  - {log.value}")

if __name__ == '__main__':
    print("chatbot2_demo2...")
    run_customer_service_scenario()
