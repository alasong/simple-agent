"""
补充工具 - 对已有结果进行补充说明
"""
from typing import Optional
from core import tool, BaseTool, ToolResult


@tool(tags=["analysis", "supplement"], description="对已有结果进行补充说明")
class SupplementTool(BaseTool):
    """补充工具 - 对之前的结果添加补充说明"""
    
    @property
    def name(self) -> str:
        return "SupplementTool"
    
    @property
    def description(self) -> str:
        return """对已有的分析结果或结论进行补充说明。
适用于：
1. 补充详细原因（如：说明为什么得出某个结论）
2. 添加遗漏的信息
3. 提供更多背景说明
4. 补充数据来源或依据"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "要补充的内容目标，如：某个结论、某个预测、某个建议"
                },
                "supplement_type": {
                    "type": "string",
                    "enum": ["reason", "evidence", "background", "source", "detail"],
                    "description": "补充类型：reason=原因说明, evidence=证据支持, background=背景信息, source=数据来源, detail=详细说明"
                },
                "content": {
                    "type": "string",
                    "description": "补充的具体内容"
                }
            },
            "required": ["target", "content"]
        }
    
    def execute(
        self,
        target: str,
        content: str,
        supplement_type: str = "detail",
        **kwargs
    ) -> ToolResult:
        """
        执行补充操作
        
        Args:
            target: 要补充的目标内容
            supplement_type: 补充类型
            content: 补充内容
        """
        type_labels = {
            "reason": "原因说明",
            "evidence": "证据支持",
            "background": "背景信息",
            "source": "数据来源",
            "detail": "详细说明"
        }
        
        label = type_labels.get(supplement_type, "补充说明")
        
        # 格式化输出
        output = f"""## {label}

**针对**: {target}

{content}
"""
        
        return ToolResult(
            success=True,
            output=output
        )


@tool(tags=["analysis", "explanation"], description="解释某个结论的详细原因")
class ExplainReasonTool(BaseTool):
    """解释原因工具 - 专门用于补充详细原因"""
    
    @property
    def name(self) -> str:
        return "ExplainReasonTool"
    
    @property
    def description(self) -> str:
        return """解释某个结论或预测的详细原因。
当用户要求"说明原因"、"为什么"、"解释理由"时使用此工具。
会结合上下文和历史信息提供全面的原因分析。"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "conclusion": {
                    "type": "string",
                    "description": "需要解释原因的结论或预测"
                },
                "context": {
                    "type": "string",
                    "description": "相关的上下文或背景信息（可选）"
                }
            },
            "required": ["conclusion"]
        }
    
    def execute(
        self,
        conclusion: str,
        context: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        执行原因解释
        
        注意：这个工具返回一个提示，让 Agent 基于其内部知识和上下文生成原因
        """
        prompt = f"""请详细解释以下结论的原因：

**结论**: {conclusion}
"""

        if context:
            prompt += f"""
**相关背景**: {context}
"""

        prompt += """
请从以下几个维度进行说明：
1. **直接原因** - 导致该结论的最直接因素
2. **根本原因** - 深层次的、根本性的因素
3. **支撑证据** - 支持该结论的具体事实或数据
4. **推理过程** - 从原因到结论的逻辑链条
5. **潜在变量** - 可能影响结论的其他因素
"""
        
        return ToolResult(
            success=True,
            output=prompt
        )


# 注册工具
def register_supplement_tools():
    """注册补充相关工具"""
    from core.resource import repo
    
    repo.register_tool("SupplementTool", SupplementTool)
    repo.register_tool("ExplainReasonTool", ExplainReasonTool)
