"""
LLM - OpenAI 兼容的 LLM 客户端

支持任何 OpenAI 兼容的 API：
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- 本地部署 (vLLM, Ollama 等)
- 其他兼容服务

使用方式:
    llm = LLM()  # 从环境变量获取配置
    response = llm.chat(messages=[...], tools=[...])

环境变量:
    OPENAI_API_KEY: API 密钥（必需）
    OPENAI_MODEL: 模型名称（默认：gpt-4o-mini）
    OPENAI_BASE_URL: API 基础 URL（可选）
"""

import json
import os
from typing import Optional


class LLM:
    """
    OpenAI 兼容的 LLM 客户端

    调用 OpenAI 或兼容 API 提供聊天和工具调用能力
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化 LLM

        Args:
            api_key: API 密钥（默认从 OPENAI_API_KEY 环境变量获取）
            model: 模型名称（默认从 OPENAI_MODEL 环境变量获取，或 gpt-4o-mini）
            base_url: API 基础 URL（默认从 OPENAI_BASE_URL 环境变量获取）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")

    def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        """
        调用 LLM 聊天接口

        Args:
            messages: 对话历史，格式为 [{"role": "user|assistant|system", "content": "..."}]
            tools: 可用工具列表（OpenAI 工具格式）

        Returns:
            {
                "content": str,           # 回复内容
                "tool_calls": list | None, # 工具调用列表
                "finish_reason": str       # 结束原因
            }
        """
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


# 向后兼容别名
OpenAILLM = LLM
LLMInterface = LLM  # 保持接口兼容
