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
        
        tool_calls = self._parse_json(content)
        if tool_calls:
            return tool_calls
        
        tool_calls = self._parse_python_like(content)
        if tool_calls:
            return tool_calls
        
        tool_calls = self._parse_xml(content)
        if tool_calls:
            return tool_calls
        
        return []
    
    def _parse_json(self, content: str) -> Optional[list[dict]]:
        tool_calls = []
        for m in re.finditer(r'\{"name":"([^"]+)","arguments":(\{[^}]*\})\}', content):
            try:
                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "name": m.group(1),
                    "arguments": json.loads(m.group(2))
                })
            except:
                pass
        return tool_calls if tool_calls else None
    
    def _parse_python_like(self, content: str) -> Optional[list[dict]]:
        tool_calls = []
        for m in re.finditer(r'\[([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\)\]', content):
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
        return tool_calls if tool_calls else None
