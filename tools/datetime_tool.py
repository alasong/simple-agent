"""
DateTimeTool - 日期时间工具

获取和处理日期时间信息，支持时区、格式化、计算等功能
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from core.tool import BaseTool, ToolResult

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False


class DateTimeTool(BaseTool):
    """日期时间工具：获取、格式化和计算日期时间"""
    
    @property
    def name(self) -> str:
        return "datetime"
    
    @property
    def description(self) -> str:
        return """获取和处理日期时间信息。

使用场景：
- 获取当前时间：日期、星期、时区
- 时间计算：加减天数、计算时间差
- 格式转换：ISO、时间戳、自定义格式
- 时区转换：UTC、本地时间、指定时区

常用时区：
- Asia/Shanghai (北京时间)
- UTC (协调世界时)
- America/New_York (纽约)
- Europe/London (伦敦)
"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["now", "format", "calc", "convert", "parse", "timestamp"],
                    "default": "now"
                },
                "timezone": {
                    "type": "string",
                    "description": "时区，如 Asia/Shanghai, UTC"
                },
                "format_str": {
                    "type": "string",
                    "description": "输出格式，如 %Y-%m-%d %H:%M:%S"
                },
                "days": {
                    "type": "integer",
                    "description": "天数（用于计算），正数为未来，负数为过去"
                },
                "timestamp": {
                    "type": "integer",
                    "description": "Unix 时间戳"
                },
                "date_str": {
                    "type": "string",
                    "description": "日期字符串（用于解析或转换）"
                }
            },
            "required": []
        }
    
    def execute(
        self,
        action: str = "now",
        timezone: Optional[str] = None,
        format_str: Optional[str] = None,
        days: Optional[int] = None,
        timestamp: Optional[int] = None,
        date_str: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """执行日期时间操作"""
        try:
            if action == "now":
                return self._get_now(timezone, format_str)
            elif action == "format":
                return self._format_time(timezone, format_str)
            elif action == "calc":
                return self._calc_days(days, timezone, format_str)
            elif action == "convert":
                return self._convert_timezone(date_str, timezone)
            elif action == "parse":
                return self._parse_date(date_str)
            elif action == "timestamp":
                return self._from_timestamp(timestamp, timezone, format_str)
            else:
                return ToolResult(success=False, output="", error=f"未知操作: {action}")
                
        except Exception as e:
            return ToolResult(success=False, output="", error=f"操作失败: {e}")
    
    def _get_now(self, tz_name: Optional[str], fmt: Optional[str]) -> ToolResult:
        """获取当前时间"""
        now = self._get_time(tz_name)
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekdays[now.weekday()]
        
        lines = [
            f"📅 日期：{now.year}年{now.month}月{now.day}日 {weekday}",
            f"🕐 时间：{now.strftime('%H:%M:%S')}",
            f"🌍 时区：{self._get_tz_name(now, tz_name)}",
            f"📝 ISO：{now.isoformat()}",
            f"🔢 时间戳：{int(now.timestamp())}",
        ]
        
        if fmt:
            lines.append(f"🎨 格式化：{now.strftime(fmt)}")
        
        return ToolResult(success=True, output="\n".join(lines))
    
    def _format_time(self, tz_name: Optional[str], fmt: str) -> ToolResult:
        """格式化当前时间"""
        now = self._get_time(tz_name)
        if not fmt:
            fmt = "%Y-%m-%d %H:%M:%S"
        
        return ToolResult(success=True, output=now.strftime(fmt))
    
    def _calc_days(self, days: Optional[int], tz_name: Optional[str], fmt: Optional[str]) -> ToolResult:
        """计算日期"""
        if days is None:
            days = 0
        
        now = self._get_time(tz_name)
        target = now + timedelta(days=days)
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        
        direction = "后" if days >= 0 else "前"
        abs_days = abs(days)
        
        lines = [
            f"📊 计算：{abs_days}天{direction}",
            f"📅 结果：{target.year}年{target.month}月{target.day}日 {weekdays[target.weekday()]}",
            f"📝 ISO：{target.isoformat()}",
        ]
        
        if fmt:
            lines.append(f"🎨 格式化：{target.strftime(fmt)}")
        
        return ToolResult(success=True, output="\n".join(lines))
    
    def _convert_timezone(self, date_str: Optional[str], target_tz: str) -> ToolResult:
        """时区转换"""
        if not target_tz:
            return ToolResult(success=False, output="", error="请指定目标时区")
        
        if date_str:
            # 解析日期字符串
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.now(timezone.utc)
        
        if HAS_ZONEINFO:
            target = dt.astimezone(ZoneInfo(target_tz))
        else:
            target = dt.astimezone()
        
        return ToolResult(
            success=True,
            output=f"时区转换结果：\n原始：{dt.isoformat()}\n目标：{target.isoformat()}"
        )
    
    def _parse_date(self, date_str: Optional[str]) -> ToolResult:
        """解析日期字符串"""
        if not date_str:
            return ToolResult(success=False, output="", error="请提供日期字符串")
        
        # 尝试多种格式
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y年%m月%d日",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                
                return ToolResult(
                    success=True,
                    output=f"解析成功：\n"
                           f"📅 日期：{dt.year}年{dt.month}月{dt.day}日 {weekdays[dt.weekday()]}\n"
                           f"🕐 时间：{dt.strftime('%H:%M:%S') if dt.hour or dt.minute or dt.second else '00:00:00'}\n"
                           f"📝 ISO：{dt.isoformat()}"
                )
            except ValueError:
                continue
        
        return ToolResult(success=False, output="", error=f"无法解析日期：{date_str}")
    
    def _from_timestamp(self, ts: Optional[int], tz_name: Optional[str], fmt: Optional[str]) -> ToolResult:
        """从时间戳转换"""
        if ts is None:
            # 返回当前时间戳
            now = datetime.now()
            return ToolResult(success=True, output=f"当前时间戳：{int(now.timestamp())}")
        
        dt = datetime.fromtimestamp(ts, tz=self._get_tz(tz_name))
        
        if not fmt:
            fmt = "%Y-%m-%d %H:%M:%S"
        
        return ToolResult(
            success=True,
            output=f"时间戳 {ts} 转换结果：\n"
                   f"📅 日期：{dt.strftime(fmt)}\n"
                   f"📝 ISO：{dt.isoformat()}"
        )
    
    def _get_time(self, tz_name: Optional[str] = None) -> datetime:
        """获取指定时区的当前时间"""
        if tz_name and HAS_ZONEINFO:
            try:
                return datetime.now(ZoneInfo(tz_name))
            except:
                pass
        return datetime.now()
    
    def _get_tz(self, tz_name: Optional[str] = None):
        """获取时区对象"""
        if tz_name and HAS_ZONEINFO:
            try:
                return ZoneInfo(tz_name)
            except:
                pass
        return None
    
    def _get_tz_name(self, dt: datetime, tz_name: Optional[str]) -> str:
        """获取时区名称"""
        if tz_name:
            return tz_name
        try:
            return dt.tzname() or "本地时区"
        except:
            return "本地时区"


# 保留旧名称兼容
class GetCurrentDateTool(DateTimeTool):
    """兼容旧版本"""
    @property
    def name(self) -> str:
        return "GetCurrentDateTool"
    
    def execute(self, format: str = "simple", **kwargs) -> ToolResult:
        if format == "detailed":
            return super().execute(action="now")
        else:
            now = self._get_time()
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            return ToolResult(
                success=True,
                output=f"今天是{now.year}年{now.month}月{now.day}日，{weekdays[now.weekday()]}."
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    DateTimeTool,
    tags=["date", "time", "datetime", "timezone"],
    description="获取和处理日期时间信息"
)
