"""
GetCurrentDateTool - 获取当前日期工具

直接返回系统当前日期，无需网络搜索
"""

from datetime import datetime
from core.tool import BaseTool, ToolResult


class GetCurrentDateTool(BaseTool):
    """获取当前日期工具：返回系统当前日期和时间信息"""
    
    @property
    def name(self) -> str:
        return "GetCurrentDateTool"
    
    @property
    def description(self) -> str:
        return "获取当前系统日期和时间信息。适用于查询今天日期、星期、农历等基础时间信息。"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "日期格式：simple(简单), detailed(详细), 默认 simple",
                    "enum": ["simple", "detailed"]
                }
            },
            "required": []
        }
    
    def execute(
        self,
        format: str = "simple",
        **kwargs
    ) -> ToolResult:
        """获取当前日期"""
        try:
            now = datetime.now()
            
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = weekdays[now.weekday()]
            
            if format == "detailed":
                output = f"""当前日期时间信息：
- 公历：{now.year}年{now.month}月{now.day}日 {weekday}
- 时间：{now.strftime('%H:%M:%S')}
- 时区：{now.astimezone().tzname()}
- ISO 格式：{now.isoformat()}"""
            else:
                output = f"今天是{now.year}年{now.month}月{now.day}日，{weekday}。"
            
            return ToolResult(
                success=True,
                output=output
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"获取日期失败：{e}"
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    GetCurrentDateTool,
    tags=["date", "time", "current"],
    description="获取当前系统日期和时间信息"
)
