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
    OPENAI_TIMEOUT: API 超时时间（秒，默认30）
    OPENAI_MAX_RETRIES: 最大重试次数（默认3）
"""

import json
import os
import time
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
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        """
        初始化 LLM

        Args:
            api_key: API 密钥（默认从 OPENAI_API_KEY 环境变量获取）
            model: 模型名称（默认从 OPENAI_MODEL 环境变量获取，或 gpt-4o-mini）
            base_url: API 基础 URL（默认从 OPENAI_BASE_URL 环境变量获取）
            timeout: API 超时时间（秒，默认从 OPENAI_TIMEOUT 获取，或 30）
            max_retries: 最大重试次数（默认从 OPENAI_MAX_RETRIES 获取，或 3）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.timeout = timeout or float(os.getenv("OPENAI_TIMEOUT", "30"))
        self.max_retries = max_retries or int(os.getenv("OPENAI_MAX_RETRIES", "3"))

        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")

    def _create_client(self):
        """创建 OpenAI 客户端（带超时设置）"""
        from openai import OpenAI
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def _chat_with_retry(self, messages: list, tools: Optional[list] = None) -> dict:
        """带重试机制的 LLM 调用"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                client = self._create_client()

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
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model
                }

            except Exception as e:
                last_error = e
                # 网络错误或 rate limit 错误才重试
                error_str = str(e).lower()
                if "network" in error_str or "timeout" in error_str or "rate" in error_str:
                    if attempt < self.max_retries - 1:
                        # 指数退避
                        wait_time = min(1.5 ** attempt, 10)
                        time.sleep(wait_time)
                        continue
                # 非网络错误不重试
                break

        raise RuntimeError(f"LLM 调用失败（{self.max_retries}次重试）: {last_error}")

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
            return self._chat_with_retry(messages, tools)
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}")

    def __repr__(self) -> str:
        return f"<LLM model={self.model}>"


# 向后兼容别名
OpenAILLM = LLM
LLMInterface = LLM  # 保持接口兼容
