"""
LLM 接口
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional


class LLMInterface(ABC):
    """LLM 接口抽象 - 可扩展支持不同 LLM 提供商"""
    
    @abstractmethod
    def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        """
        调用 LLM
        
        Args:
            messages: 对话历史
            tools: 可用工具列表 (OpenAI 格式)
        
        Returns:
            {
                "content": str,           # 回复内容
                "tool_calls": list | None, # 工具调用
                "finish_reason": str       # 结束原因
            }
        """
        pass


class OpenAILLM(LLMInterface):
    """OpenAI 兼容的 LLM 实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")
    
    def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
        
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        kwargs = {
            "model": self.model,
            "messages": messages
        }
        if tools:
            kwargs["tools"] = tools
        
        response = client.chat.completions.create(**kwargs)
        
        message = response.choices[0].message
        
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                }
                for tc in message.tool_calls
            ]
        
        return {
            "content": message.content or "",
            "tool_calls": tool_calls,
            "finish_reason": response.choices[0].finish_reason
        }
