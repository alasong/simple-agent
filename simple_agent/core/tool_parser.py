"""
工具调用解析器
"""

import re
import json
from typing import Optional


class ToolCallParser:
    def parse(self, content: str) -> list[dict]:
        if not content:
            return []

        seen = set()
        tool_calls = []

        # 解析 JSON 格式
        for tc in self._parse_json(content) or []:
            key = tc["name"]
            if key not in seen:
                seen.add(key)
                tool_calls.append(tc)

        # 解析 Python 格式
        for tc in self._parse_python_like(content) or []:
            key = tc["name"]
            if key not in seen:
                seen.add(key)
                tool_calls.append(tc)

        # 解析 XML 格式
        for tc in self._parse_xml(content) or []:
            key = tc["name"]
            if key not in seen:
                seen.add(key)
                tool_calls.append(tc)

        return tool_calls

    def _extract_json_from_codeblock(self, content: str) -> list[str]:
        """从代码块中提取 JSON 内容"""
        json_blocks = []
        # 匹配 JSON 代码块: ```json ... ```
        pattern = r'```json(.*?)```'
        for m in re.finditer(pattern, content, re.DOTALL):
            block = m.group(1).strip()
            if block.startswith('{'):
                json_blocks.append(block)

        # 也匹配不带语言标识的代码块
        pattern2 = r'```(.*?)```'
        for m in re.finditer(pattern2, content, re.DOTALL):
            block = m.group(1).strip()
            if block.startswith('{') and block not in json_blocks:
                json_blocks.append(block)

        return json_blocks

    def _parse_json(self, content: str) -> Optional[list[dict]]:
        tool_calls = []

        # 首先尝试从代码块中提取 JSON
        json_blocks = self._extract_json_from_codeblock(content)
        for block_content in json_blocks:
            try:
                # 尝试解析 JSON 对象
                if block_content.strip().startswith('{'):
                    data = json.loads(block_content)
                    # 检查是否是工具调用格式
                    if 'name' in data or 'tool' in data:
                        tool_name = data.get('name') or data.get('tool')
                        args = data.get('arguments') or data.get('parameters', {})
                        tool_calls.append({
                            "id": f"call_{len(tool_calls)}",
                            "name": tool_name,
                            "arguments": args
                        })
            except:
                pass

        # 如果没有从代码块中提取到，尝试直接匹配
        if not tool_calls:
            # 匹配多行 JSON 工具调用格式
            # 支持：
            # 1. 单行: {"name":"tool_name","arguments":{...}}
            # 2. 多行: {"name": "tool_name", "arguments": {...}}
            # 3. 兼容格式: {"tool":"tool_name","parameters":{...}}
            # 4. 混合格式: {"tool":"tool_name","arguments":{...}}
            patterns = [
                # 多行格式（支持换行和空格）
                r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}',
                # 单行格式
                r'\{"name":"([^"]+)","arguments":(\{[^}]*\})\}',
                # 兼容格式: {"tool":"tool_name","parameters":{...}}
                r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"parameters"\s*:\s*(\{[^}]*\})\s*\}',
                # 兼容格式单行
                r'\{"tool":"([^"]+)","parameters":(\{[^}]*\})\}',
                # 混合格式: {"tool":"tool_name","arguments":{...}}
                r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}',
                # 混合格式单行
                r'\{"tool":"([^"]+)","arguments":(\{[^}]*\})\}',
            ]

            for pattern in patterns:
                for m in re.finditer(pattern, content, re.DOTALL):
                    try:
                        tool_name = m.group(1)
                        args_str = m.group(2)

                        args = json.loads(args_str)

                        tool_calls.append({
                            "id": f"call_{len(tool_calls)}",
                            "name": tool_name,
                            "arguments": args
                        })
                    except:
                        pass

            # 尝试解析 JSON 数组格式
            if not tool_calls:
                try:
                    # 尝试匹配整个 JSON 数组
                    array_match = re.search(r'\[\s*\{[^}]*"name"[^}]*\}\s*\]', content, re.DOTALL)
                    if array_match:
                        tools_list = json.loads(array_match.group(0))
                        for tool in tools_list:
                            tool_calls.append({
                                "id": f"call_{len(tool_calls)}",
                                "name": tool.get("name", ""),
                                "arguments": tool.get("arguments", {})
                            })
                except:
                    pass

        return tool_calls if tool_calls else None
    
    def _parse_python_like(self, content: str) -> Optional[list[dict]]:
        """解析 Python 风格的工具调用"""
        tool_calls = []

        # 模式 1: 分配语句格式 - variable = Tool().run()
        pattern1 = r'(\w+)\s*=\s*([A-Z][A-Za-z0-9_]*)\s*\(\s*\)\s*(?:\.run)?\s*\(\s*\)'
        for m in re.finditer(pattern1, content):
            try:
                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "name": m.group(2),
                    "arguments": {}
                })
            except:
                pass

        # 模式 2: 函数调用格式 - Tool(arg="value").run() 或 Tool(arg="value")()
        pattern2 = r'([A-Z][A-Za-z0-9_]*)\s*\(\s*([^)]*)\s*\)\s*(?:\.run)?\s*\(\s*\)'
        for m in re.finditer(pattern2, content):
            try:
                tool_name = m.group(1)
                args_str = m.group(2)
                args = {}
                # 解析参数
                for arg_match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']*)["\']', args_str):
                    args[arg_match.group(1)] = arg_match.group(2)

                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "name": tool_name,
                    "arguments": args
                })
            except:
                pass

        # 模式 3: 方括号格式 - [ToolName(arg="value")]
        pattern3 = r'\[([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\)\]'
        for m in re.finditer(pattern3, content):
            try:
                tool_name = m.group(1)
                args_str = m.group(2)
                args = {}
                for arg_match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']*)["\']', args_str):
                    args[arg_match.group(1)] = arg_match.group(2)

                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "name": tool_name,
                    "arguments": args
                })
            except:
                pass

        return tool_calls if tool_calls else None
    
    def _parse_xml(self, content: str) -> Optional[list[dict]]:
        tool_calls = []

        # 模式 1: 嵌套格式 <function_calls><invoke name="...">...</invoke></function_calls>
        xml_match = re.search(
            r'<function_calls>\s*<invoke\s+name="([^"]+)">(.*?)</invoke>\s*</function_calls>',
            content,
            re.DOTALL
        )
        if xml_match:
            try:
                tool_name = xml_match.group(1)
                params_str = xml_match.group(2)
                args = {}
                for param_match in re.finditer(r'<parameter\s+name="([^"]+)">\s*([^<]+)\s*', params_str):
                    args[param_match.group(1)] = param_match.group(2).strip()

                tool_calls.append({
                    "id": "call_0",
                    "name": tool_name,
                    "arguments": args
                })
            except:
                pass

        # 模式 2: 自闭合标签格式 <ToolName param="value" />
        if not tool_calls:
            pattern = r'<([A-Z][A-Za-z0-9_]*)\s+([^>]*?)\s*/?>'
            for m in re.finditer(pattern, content):
                try:
                    tool_name = m.group(1)
                    params_str = m.group(2)
                    args = {}

                    # 解析参数
                    for param_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', params_str):
                        args[param_match.group(1)] = param_match.group(2)

                    # 兼容 without quotes: <ToolName param=value />
                    for param_match in re.finditer(r'(\w+)\s*=\s*([^\s>]+)', params_str):
                        if param_match.group(1) not in args:  # 只接受未设置的参数
                            args[param_match.group(1)] = param_match.group(2)

                    tool_calls.append({
                        "id": f"call_{len(tool_calls)}",
                        "name": tool_name,
                        "arguments": args
                    })
                except:
                    pass

        return tool_calls if tool_calls else None
