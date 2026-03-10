"""
记忆系统
"""

from typing import Optional


class Memory:
    """记忆系统：管理对话历史"""
    
    def __init__(self, system_prompt: Optional[str] = None):
        self.messages: list[dict] = []
        if system_prompt:
            self.add_system(system_prompt)
    
    def add_system(self, content: str):
        """添加系统消息"""
        self.messages.append({"role": "system", "content": content})
    
    def add_user(self, content: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant(self, content: str, tool_calls: Optional[list] = None):
        """添加助手消息"""
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
    
    def add_tool_result(self, tool_call_id: str, name: str, content: str):
        """添加工具执行结果"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content
        })
    
    def get_messages(self) -> list[dict]:
        """获取所有消息"""
        return self.messages
    
    def clear(self):
        """清空记忆"""
        self.messages.clear()
