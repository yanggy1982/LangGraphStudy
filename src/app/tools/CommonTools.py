# -*- coding:utf-8 -*-

"""
***********************************************************************

@author  : yangguangyuan
@file    : CommonTools.py
@time    : 2025/12/31 16:55
@desc    : 通用工具
-----------------------------------------------------------------------
"""
import os
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class WeatherInput(BaseModel):
    """
    天气工具输入
    """
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

