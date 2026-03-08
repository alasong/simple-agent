"""
EnvTool - 环境变量工具

获取和管理系统环境变量
"""

import os
from typing import Optional, Union
from core.tool import BaseTool, ToolResult


class EnvTool(BaseTool):
    """环境变量工具：获取和列出系统环境变量"""
    
    @property
    def name(self) -> str:
        return "env"
    
    @property
    def description(self) -> str:
        return """获取系统环境变量。

使用场景：
- 获取配置：读取应用配置、API密钥路径等
- 系统信息：PATH, HOME, USER, SHELL 等
- 调试：检查环境配置是否正确
- 跨平台：获取平台特定信息（OS, PWD 等）

常用环境变量：
- PATH: 可执行文件搜索路径
- HOME: 用户主目录
- USER: 当前用户名
- PWD: 当前工作目录
- SHELL: 当前 shell
- LANG: 系统语言设置
- TERM: 终端类型
"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "环境变量名，不指定则列出所有"
                },
                "default": {
                    "type": "string",
                    "description": "变量不存在时的默认返回值"
                },
                "type": {
                    "type": "string",
                    "description": "返回值类型转换：string(默认), int, float, bool, list(按:分割)",
                    "enum": ["string", "int", "float", "bool", "list"]
                }
            },
            "required": []
        }
    
    def execute(
        self,
        name: Optional[str] = None,
        default: Optional[str] = None,
        type: str = "string",
        **kwargs
    ) -> ToolResult:
        """获取环境变量"""
        try:
            # 列出所有环境变量
            if name is None:
                env_vars = dict(os.environ)
                
                # 按类别分组
                categories = {
                    "系统信息": ["HOME", "USER", "HOSTNAME", "SHELL", "PWD", "LANG"],
                    "路径配置": ["PATH", "PYTHONPATH", "LD_LIBRARY_PATH"],
                    "终端": ["TERM", "COLORTERM", "DISPLAY"],
                    "编辑器": ["EDITOR", "VISUAL"],
                    "其他": []
                }
                
                lines = ["系统环境变量：\n"]
                
                for category, keys in categories.items():
                    found = []
                    for key in keys:
                        if key in env_vars:
                            value = env_vars.pop(key)
                            # 截断过长的值
                            if len(value) > 80:
                                value = value[:77] + "..."
                            found.append(f"  {key}={value}")
                    
                    if found:
                        lines.append(f"【{category}】")
                        lines.extend(found)
                        lines.append("")
                
                # 其他变量
                if env_vars:
                    lines.append("【其他变量】")
                    for key, value in sorted(env_vars.items()):
                        if len(value) > 80:
                            value = value[:77] + "..."
                        lines.append(f"  {key}={value}")
                
                return ToolResult(
                    success=True,
                    output="\n".join(lines)
                )
            
            # 获取指定环境变量
            value = os.environ.get(name)
            
            if value is None:
                if default is not None:
                    value = default
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"环境变量 '{name}' 不存在"
                    )
            
            # 类型转换
            try:
                if type == "int":
                    value = str(int(value))
                elif type == "float":
                    value = str(float(value))
                elif type == "bool":
                    value = str(bool(value.lower() in ("true", "1", "yes", "on")))
                elif type == "list":
                    value = "\n".join(value.split(os.pathsep))
            except (ValueError, TypeError) as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"类型转换失败 '{type}': {e}"
                )
            
            return ToolResult(
                success=True,
                output=f"{name}={value}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"获取环境变量失败：{e}"
            )


# 注册工具到资源仓库
from core.resource import repo
repo.register_tool(
    EnvTool,
    tags=["system", "environment", "config"],
    description="获取和管理系统环境变量"
)