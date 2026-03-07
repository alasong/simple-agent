"""
Agent Error Enhancer - 错误增强逻辑

负责为工具执行错误提供智能应对建议
"""

from typing import Dict


class AgentErrorEnhancer:
    """
    Agent 错误增强器
    
    职责:
    - 为工具执行错误提供智能应对建议
    - 帮助 LLM 理解失败原因并采取替代方案
    """
    
    @staticmethod
    def enhance_with_suggestions(tool_name: str, arguments: Dict, error: str) -> str:
        """
        增强错误信息，提供智能应对建议
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            error: 原始错误信息
        
        Returns:
            增强后的错误信息，包含替代方案建议
        """
        enhanced = f"错误：{error}\n\n"
        enhanced += "⚠️ **重要提示**：不要重复调用同一个工具！这个错误是持久性的，重试不会成功。\n\n"
        
        # 针对 WebSearchTool 的特殊处理
        if tool_name == "WebSearchTool":
            enhanced += AgentErrorEnhancer._enhance_web_search_error(arguments, error)
        
        # 针对 GetCurrentDateTool
        elif tool_name == "GetCurrentDateTool":
            enhanced += "💡 应对建议：\n"
            enhanced += "1. 如果日期工具失败，可以直接使用系统日期或用户提供的时间\n"
            enhanced += "2. 对于日期相关的查询，可以基于相对时间（如'今天'、'明天'）来回答\n"
        
        # 通用工具失败处理
        else:
            enhanced += "💡 通用应对策略：\n"
            enhanced += "1. 尝试使用其他可用工具完成类似任务\n"
            enhanced += "2. 基于你的知识库提供帮助\n"
            enhanced += "3. 如果任务可以分解，尝试分步骤完成\n"
            enhanced += "4. 诚实地告诉用户限制，并提供替代方案\n"
        
        return enhanced
    
    @staticmethod
    def _enhance_web_search_error(arguments: Dict, error: str) -> str:
        """增强 WebSearchTool 错误信息"""
        query = arguments.get("query", "")
        
        enhanced = "💡 智能应对建议：\n"
        
        if "timeout" in error.lower() or "超时" in error or "timed out" in error.lower():
            enhanced += "1. **网络超时** → 立即采取以下替代方案（不要重试）：\n"
            enhanced += "   - **先获取日期**：使用 GetCurrentDateTool 确定今天的日期\n"
            enhanced += "   - 换一个搜索词或更具体的网站\n"
            enhanced += "   - 使用 fetch_content=false 先获取搜索结果列表\n"
            enhanced += "   - 换一个信息源（如直接访问目标网站）\n"
            enhanced += "   - 基于你的知识提供背景信息\n"
        elif "connection" in error.lower() or "连接" in error:
            enhanced += "1. **连接失败** → 尝试：\n"
            enhanced += "   - 换一个网站或搜索引擎\n"
            enhanced += "   - 使用你已有的知识库回答\n"
            enhanced += "   - 建议用户通过其他渠道获取\n"
        else:
            enhanced += "1. **搜索失败** → 尝试：\n"
            enhanced += "   - 换一种搜索方式或关键词\n"
            enhanced += "   - 直接访问相关专业网站\n"
            enhanced += "   - 基于已有知识提供帮助\n"
        
        enhanced += f"\n2. **替代方案示例**：\n"
        enhanced += f"   - 如果查询'{query}'失败，可以尝试：\n"
        
        # 根据查询类型提供具体建议
        if "天气" in query:
            enhanced += "     * 换一个天气网站（中国天气网、AccuWeather）\n"
            enhanced += "     * 先搜索'中国天气网 北京'找到 URL，再提取内容\n"
            enhanced += "     * 提供北京气候的一般知识\n"
        elif "新闻" in query or "最新" in query:
            enhanced += "     * 换搜索引擎或平台（微博、知乎、头条）\n"
            enhanced += "     * 搜索相关话题的历史背景\n"
            enhanced += "     * 解释如何追踪这类信息\n"
        elif "股价" in query or "股票" in query:
            enhanced += "     * 换财经网站（新浪财经、东方财富、雪球）\n"
            enhanced += "     * 提供股票分析方法\n"
            enhanced += "     * 解释基本面分析框架\n"
        else:
            enhanced += "     * 换一种表述或更具体的关键词\n"
            enhanced += "     * 访问相关领域的专业网站\n"
            enhanced += "     * 基于你的知识库提供相关信息\n"
        
        enhanced += "\n3. **最后的选择**：如果所有尝试都失败，诚实地告诉用户，并提供：\n"
        enhanced += "   - 你无法获取实时数据的原因\n"
        enhanced += "   - 用户可以自行访问的可靠来源\n"
        enhanced += "   - 你能够提供的背景知识或分析框架\n"
        
        return enhanced
