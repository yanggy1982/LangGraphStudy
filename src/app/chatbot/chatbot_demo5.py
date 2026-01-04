# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : chatbot_demo5.py
@time    : 2025/12/31 15:49
@desc    : 聊天机器人(包含自定义工具和长期记忆功能)
-----------------------------------------------------------------------
"""
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(dotenv_path="../../env/.env")

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model_name = "claude-opus-4-5-20251101"
tavily_api_key = os.getenv("TAVILY_API_KEY")

if __name__ == '__main__':
    print("chatbot_demo5...")
