"""
CalculatorTool - 数学计算工具

执行数学运算，支持基础运算和常用函数
"""

import math
import re
from typing import Union
from core.tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """数学计算工具：执行数学运算并返回结果"""
    
    @property
    def name(self) -> str:
        return "math"
    
    @property
    def description(self) -> str:
        return """执行数学计算。

使用场景：
- 基础运算：加减乘除、幂运算、取余
- 数学函数：sin, cos, tan, log, sqrt, abs
- 统计计算：平均值、百分比、比例
- 单位换算：温度、长度、重量等

支持的操作符：
- 算术：+ - * / // % **
- 比较：> < >= <= == !=
- 数学函数：sin, cos, tan, log, log10, sqrt, abs, round, floor, ceil
- 常量：pi, e

示例：
- "2 + 3 * 4" → 14
- "sqrt(16)" → 4.0
- "2 ** 10" → 1024
- "sin(pi/2)" → 1.0
"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'"
                },
                "precision": {
                    "type": "integer",
                    "description": "结果精度（小数位数），默认 4",
                    "default": 4
                }
            },
            "required": ["expression"]
        }
    
    # 允许的安全名称
    SAFE_NAMES = {
        # 数学常量
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        
        # 数学函数
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        
        "sqrt": math.sqrt,
        "pow": pow,
        "floor": math.floor,
        "ceil": math.ceil,
        
        "degrees": math.degrees,
        "radians": math.radians,
        
        "factorial": math.factorial,
        "gcd": math.gcd,
    }
    
    def execute(
        self,
        expression: str,
        precision: int = 4,
        **kwargs
    ) -> ToolResult:
        """执行数学计算"""
        try:
            # 预处理表达式
            expr = expression.strip()
            
            # 安全检查：只允许数字、运算符和安全名称
            allowed_pattern = r'^[\d\s\+\-\*\/\%\(\)\.\,\^]+$'
            temp_expr = expr
            
            # 移除安全名称后检查
            for name in self.SAFE_NAMES:
                temp_expr = temp_expr.replace(name, "")
            
            # 检查是否有非法字符
            if not re.match(allowed_pattern, temp_expr):
                # 可能有函数名，进一步检查
                for word in re.findall(r'[a-zA-Z_]+', expr):
                    if word not in self.SAFE_NAMES:
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"不允许的名称: {word}"
                        )
            
            # 替换 ^ 为 **
            expr = expr.replace("^", "**")
            
            # 创建安全的计算环境
            safe_env = dict(self.SAFE_NAMES)
            
            # 执行计算
            result = eval(expr, {"__builtins__": {}}, safe_env)
            
            # 格式化结果
            if isinstance(result, float):
                # 处理精度
                result = round(result, precision)
                # 移除末尾的 0
                if result == int(result):
                    result = int(result)
            
            return ToolResult(
                success=True,
                output=f"{expression} = {result}"
            )
            
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                output="",
                error="除零错误：不能除以零"
            )
        except ValueError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"数值错误: {e}"
            )
        except SyntaxError:
            return ToolResult(
                success=False,
                output="",
                error=f"语法错误：表达式格式不正确"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"计算失败: {e}"
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    CalculatorTool,
    tags=["math", "calculate", "number"],
    description="执行数学计算"
)