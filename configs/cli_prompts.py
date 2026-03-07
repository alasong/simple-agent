"""
CLI Agent 提示词配置

避免在代码中硬编码提示词，从 YAML 配置文件加载
支持热更新和运行时修改
"""

import os
from typing import Dict, List

# 尝试加载 YAML 配置
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class PromptTemplates:
    """提示词模板配置"""
    
    # 默认值（当 YAML 不可用时使用）
    _default_date_keywords = [
        "今天", "日期", "几号", "星期", "时间", "现在几点"
    ]
    
    _default_weather_keywords = [
        "天气", "气温", "下雨", "刮风", "雾霾", "空气质量"
    ]
    
    _default_realtime_keywords = [
        "新闻", "头条", "最新", "股价", "比分", "排名", "热搜", "疫情"
    ]
    
    _default_date_query_prompt = "（请使用 GetCurrentDateTool 获取当前日期）"
    
    _default_weather_prompt_template = (
        "（**重要：当前准确日期是{date_str}。"
        "请务必使用 WebSearchTool 搜索最新天气信息，设置 fetch_content=true，严禁编造数据！**）"
    )
    
    _default_realtime_prompt_template = "（请使用 WebSearchTool 搜索获取最新信息）"
    
    _default_log_weather_detection = "[CLI Agent] 检测到天气查询，先获取系统当前日期..."
    _default_log_current_date = "[CLI Agent] 系统当前日期：{date_str}"
    
    # 类属性，存储从 YAML 加载的配置
    _config: Dict = None
    _loaded: bool = False
    
    # 缓存的属性
    _date_keywords: List[str] = None
    _weather_keywords: List[str] = None
    _realtime_keywords: List[str] = None
    _date_query_prompt: str = None
    _weather_prompt_template: str = None
    _realtime_prompt_template: str = None
    _log_weather_detection: str = None
    _log_current_date: str = None
    
    @classmethod
    def _load_config(cls):
        """从 YAML 加载配置"""
        if cls._loaded:
            return
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'configs',
            'cli_keywords.yaml'
        )
        
        if YAML_AVAILABLE and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[Warning] 加载 CLI 关键词配置失败：{e}，使用默认值")
                cls._config = {}
        else:
            cls._config = {}
        
        cls._loaded = True
    
    @classmethod
    def _get_keywords(cls, key: str, default: List[str]) -> List[str]:
        """获取关键词列表"""
        if not cls._loaded:
            cls._load_config()
        result = cls._config.get(key) if cls._config else None
        return result if result else default
    
    @classmethod
    def _get_template(cls, section: str, key: str, default: str) -> str:
        """获取模板字符串"""
        if not cls._loaded:
            cls._load_config()
        section_data = cls._config.get(section, {}) if cls._config else {}
        result = section_data.get(key)
        return result if result else default
    
    # ========== 日期相关 ==========
    @classmethod
    def get_date_keywords(cls) -> List[str]:
        """日期查询关键词"""
        return cls._get_keywords('date_keywords', cls._default_date_keywords)
    
    @classmethod
    def get_date_query_prompt(cls) -> str:
        """日期查询提示词"""
        return cls._get_template('templates', 'date_query', cls._default_date_query_prompt)
    
    # ========== 天气查询 ==========
    @classmethod
    def get_weather_keywords(cls) -> List[str]:
        """天气查询关键词"""
        return cls._get_keywords('weather_keywords', cls._default_weather_keywords)
    
    @classmethod
    def get_weather_prompt_template(cls) -> str:
        """天气查询提示词模板"""
        return cls._get_template('templates', 'weather', cls._default_weather_prompt_template)
    
    # ========== 实时信息 ==========
    @classmethod
    def get_realtime_keywords(cls) -> List[str]:
        """实时信息关键词"""
        return cls._get_keywords('realtime_keywords', cls._default_realtime_keywords)
    
    @classmethod
    def get_realtime_prompt_template(cls) -> str:
        """实时信息提示词模板"""
        return cls._get_template('templates', 'realtime', cls._default_realtime_prompt_template)
    
    # ========== 日志消息 ==========
    @classmethod
    def get_log_weather_detection(cls) -> str:
        """天气检测日志消息"""
        return cls._get_template('log_messages', 'weather_detection', cls._default_log_weather_detection)
    
    @classmethod
    def get_log_current_date(cls, date_str: str) -> str:
        """当前日期日志消息"""
        template = cls._get_template('log_messages', 'current_date', cls._default_log_current_date)
        return template.format(date_str=date_str)
    
    @classmethod
    def get_weather_prompt(cls, date_str: str) -> str:
        """获取天气查询提示词"""
        template = cls.get_weather_prompt_template()
        return template.format(date_str=date_str)


class WeekdayConfig:
    """星期配置"""
    
    _default_weekdays = [
        "星期一", "星期二", "星期三", "星期四",
        "星期五", "星期六", "星期日"
    ]
    
    @classmethod
    def get_weekday(cls, weekday_index: int) -> str:
        """获取星期字符串"""
        # 尝试从 YAML 加载
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'configs',
            'cli_keywords.yaml'
        )
        
        if YAML_AVAILABLE and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    weekdays = config.get('weekdays')
                    if weekdays and 0 <= weekday_index < len(weekdays):
                        return weekdays[weekday_index]
            except Exception:
                pass
        
        # 返回默认值
        if 0 <= weekday_index < len(cls._default_weekdays):
            return cls._default_weekdays[weekday_index]
        return "未知"
