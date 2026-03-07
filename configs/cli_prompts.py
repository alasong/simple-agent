"""
CLI Agent 提示词配置

避免在代码中硬编码提示词，统一管理所有 prompt 模板
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptTemplates:
    """提示词模板配置"""
    
    # ========== 日期相关 ==========
    DATE_KEYWORDS = [
        "今天", "日期", "几号", "星期", "时间", "现在几点"
    ]
    
    DATE_QUERY_PROMPT = "（请使用 GetCurrentDateTool 获取当前日期）"
    
    # ========== 天气查询 ==========
    WEATHER_KEYWORDS = [
        "天气", "气温", "下雨", "刮风", "雾霾", "空气质量"
    ]
    
    WEATHER_PROMPT_TEMPLATE = (
        "（**重要：当前准确日期是{date_str}。"
        "请务必使用 WebSearchTool 搜索最新天气信息，设置 fetch_content=true，严禁编造数据！**）"
    )
    
    # ========== 实时信息 ==========
    REALTIME_KEYWORDS = [
        "新闻", "头条", "最新", "股价", "比分", "排名", "热搜", "疫情"
    ]
    
    REALTIME_PROMPT_TEMPLATE = "（请使用 WebSearchTool 搜索获取最新信息）"
    
    # ========== 日志消息 ==========
    LOG_WEATHER_DETECTION = "[CLI Agent] 检测到天气查询，先获取系统当前日期..."
    LOG_CURRENT_DATE = "[CLI Agent] 系统当前日期：{date_str}"
    
    @classmethod
    def get_weather_prompt(cls, date_str: str) -> str:
        """获取天气查询提示词"""
        return cls.WEATHER_PROMPT_TEMPLATE.format(date_str=date_str)
    
    @classmethod
    def get_date_log(cls, date_str: str) -> str:
        """获取日期日志消息"""
        return cls.LOG_CURRENT_DATE.format(date_str=date_str)


@dataclass
class WeekdayConfig:
    """星期配置"""
    WEEKDAYS = [
        "星期一", "星期二", "星期三", "星期四",
        "星期五", "星期六", "星期日"
    ]
    
    @classmethod
    def get_weekday(cls, weekday_index: int) -> str:
        """获取星期字符串"""
        return cls.WEEKDAYS[weekday_index]
