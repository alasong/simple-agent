"""
Stock Market Tool Wrapper - 股市数据查询工具（封装为 BaseTool）

继承 BaseTool，使 ToolRegistry 能自动发现
"""

from typing import Optional
from simple_agent.core.tool import BaseTool, ToolResult


class StockMarketTool(BaseTool):
    """
    股市数据查询工具

    从真实 API 源（新浪财经）获取股市行情数据，禁止编造。

    数据源：
    - A 股：新浪财经 API (hq.sinajs.cn)
    - 港股：新浪财经 API
    - 美股：新浪财经 API

    输出格式：
    - 包含数据来源和更新时间
    - 每个指数标注数据可信度
    """

    @property
    def name(self) -> str:
        return "StockMarketTool"

    @property
    def description(self) -> str:
        return "查询真实股市数据（A 股/港股/美股），从新浪财经 API 获取实时行情。必须用于涉及股市数据的查询，禁止编造数值。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "市场类型：A（A 股）/HK（港股）/US（美股）",
                    "default": "A"
                },
                "include_sectors": {
                    "type": "boolean",
                    "description": "是否包含板块数据（可选，默认 false）",
                    "default": False
                }
            },
            "required": ["market"]
        }

    def execute(
        self,
        market: str = "A",
        include_sectors: bool = False,
        **kwargs
    ) -> ToolResult:
        """执行股市数据查询"""
        try:
            from simple_agent.tools.stock_data import query_stock_data, format_stock_report

            # 获取数据
            data = query_stock_data(market=market.upper())

            # 验证数据质量
            if not data.get("indices"):
                return ToolResult(
                    success=False,
                    output="无法获取股市数据，请稍后重试"
                )

            # 检查是否有有效数据
            valid_count = sum(
                1 for idx in data["indices"]
                if "新浪财经" in idx.get("source", "") and idx.get("current", 0) > 0
            )

            if valid_count == 0:
                return ToolResult(
                    success=False,
                    output="数据源暂时不可用，请稍后重试"
                )

            # 格式化报告
            report = format_stock_report(data)

            # 添加数据验证说明
            verification_note = (
                f"\n\n---\n**数据验证**: {valid_count}/{len(data['indices'])} 个指数已验证 ✓\n"
                f"**数据来源**: 新浪财经 API（实时）\n"
                f"**更新时问**: {data.get('timestamp', 'N/A')}\n"
            )

            return ToolResult(
                success=True,
                output=report + verification_note
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"获取股市数据失败：{str(e)}",
                error=str(e)
            )


__all__ = ["StockMarketTool"]
