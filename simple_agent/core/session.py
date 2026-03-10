"""
Session Manager - 会话持久化管理

用途:
- 将 Agent.memory 持久化到磁盘
- 支持多会话切换
- 不替代 Agent.memory，而是其存储后端

使用:
  from simple_agent.core.session import SessionManager
  
  sessions = SessionManager()
  sessions.load("default", agent)  # 加载会话到 agent
  sessions.save("default", agent)  # 保存 agent 记忆到会话
  sessions.switch("new_session")   # 切换会话
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


from simple_agent.core.config_loader import get_config

class SessionManager:
    """会话管理器 - 管理多个会话的持久化"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Args:
            storage_dir: 存储目录，默认从配置文件加载
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 从统一配置加载
            config = get_config()
            session_dir = config.get('directories.sessions', '')
            if session_dir:
                self.storage_dir = Path(session_dir)
            else:
                self.storage_dir = Path.home() / ".simple-agent" / "sessions"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[str] = None
    
    def _get_session_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{session_id}.json"
    
    def save(self, session_id: str, agent) -> bool:
        """
        保存 agent 的记忆到会话
        
        Args:
            session_id: 会话 ID
            agent: Agent 实例
        
        Returns:
            是否成功
        """
        try:
            # 从 agent.memory 提取消息
            messages = []
            if hasattr(agent.memory, 'get_messages'):
                for msg in agent.memory.get_messages():
                    if hasattr(msg, 'to_dict'):
                        messages.append(msg.to_dict())
                    elif isinstance(msg, dict):
                        messages.append(msg)
            
            # 系统提示词
            system_prompt = ""
            if hasattr(agent, 'system_prompt'):
                system_prompt = agent.system_prompt
            
            data = {
                "session_id": session_id,
                "agent_name": agent.name,
                "system_prompt": system_prompt,
                "messages": messages,
                "updated_at": datetime.now().isoformat()
            }
            
            path = self._get_session_path(session_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.current_session = session_id
            return True
            
        except Exception as e:
            print(f"[Session] 保存失败：{e}")
            return False
    
    def load(self, session_id: str, agent) -> bool:
        """
        从会话加载记忆到 agent
        
        Args:
            session_id: 会话 ID
            agent: Agent 实例
        
        Returns:
            是否成功
        """
        path = self._get_session_path(session_id)
        if not path.exists():
            # 新会话，直接设置当前会话
            self.current_session = session_id
            return True
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清空 agent 记忆
            if hasattr(agent.memory, 'clear'):
                agent.memory.clear()
            
            # 恢复系统提示词
            system_prompt = data.get("system_prompt", "")
            if system_prompt and hasattr(agent.memory, 'add_system'):
                agent.memory.add_system(system_prompt)
            
            # 恢复消息
            messages = data.get("messages", [])
            for msg_data in messages:
                role = msg_data.get("role", "user")
                content = msg_data.get("content", "")
                
                if hasattr(agent.memory, 'add_user') and hasattr(agent.memory, 'add_assistant'):
                    if role == "user":
                        agent.memory.add_user(content)
                    elif role == "assistant":
                        agent.memory.add_assistant(content)
                elif hasattr(agent.memory, 'add'):
                    agent.memory.add(role, content)
            
            self.current_session = session_id
            return True
            
        except Exception as e:
            print(f"[Session] 加载失败：{e}")
            return False
    
    def switch(self, session_id: str, agent) -> bool:
        """
        切换会话：先保存当前，再加载新的
        
        Args:
            session_id: 新会话 ID
            agent: Agent 实例
        
        Returns:
            是否成功
        """
        # 保存当前会话
        if self.current_session:
            self.save(self.current_session, agent)
        
        # 加载新会话
        return self.load(session_id, agent)
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        sessions = []
        if self.storage_dir.exists():
            for f in self.storage_dir.glob("*.json"):
                sessions.append(f.stem)
        return sorted(sessions)
    
    def delete(self, session_id: str) -> bool:
        """删除会话"""
        path = self._get_session_path(session_id)
        if path.exists():
            path.unlink()
            if self.current_session == session_id:
                self.current_session = None
            return True
        return False
    
    def get_current(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self.current_session
    
    def clear(self, session_id: Optional[str] = None):
        """
        清空会话
        
        Args:
            session_id: 会话 ID，None 则清空当前
        """
        if session_id is None:
            session_id = self.current_session
        
        if session_id:
            path = self._get_session_path(session_id)
            if path.exists():
                path.unlink()
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        path = self._get_session_path(session_id)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "session_id": session_id,
                "agent_name": data.get("agent_name", ""),
                "message_count": len(data.get("messages", [])),
                "updated_at": data.get("updated_at", "")
            }
        except Exception:
            return None


# 全局实例
_sessions = SessionManager()


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    return _sessions


def save_session(session_id: str, agent) -> bool:
    """保存会话"""
    return _sessions.save(session_id, agent)


def load_session(session_id: str, agent) -> bool:
    """加载会话"""
    return _sessions.load(session_id, agent)


def switch_session(session_id: str, agent) -> bool:
    """切换会话"""
    return _sessions.switch(session_id, agent)


def list_sessions() -> List[str]:
    """列出所有会话"""
    return _sessions.list_sessions()


def get_current_session() -> Optional[str]:
    """获取当前会话"""
    return _sessions.get_current()


def clear_session(session_id: Optional[str] = None):
    """清空会话"""
    _sessions.clear(session_id)


def get_session_info(session_id: str) -> Optional[Dict]:
    """获取会话信息"""
    return _sessions.get_session_info(session_id)
