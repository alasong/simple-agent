"""
API Auth - API Key 认证

支持:
- API Key 生成和验证
- 速率限制
- IP 白名单
"""

import secrets
import hashlib
import time
from typing import Optional, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os


@dataclass
class APIKey:
    """API Key 数据结构"""
    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    rate_limit: int = 100  # 每分钟请求数
    rate_limit_window: int = 60  # 速率限制窗口（秒）
    ip_whitelist: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=lambda: {"read", "write"})
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    total_requests: int = 0


class RateLimiter:
    """滑动窗口速率限制器"""

    def __init__(self):
        # {api_key: [(timestamp, count)]}
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, api_key: str, limit: int, window: int) -> bool:
        """
        检查请求是否被允许

        Args:
            api_key: API Key
            limit: 窗口内最大请求数
            window: 时间窗口（秒）

        Returns:
            True 如果允许请求，False 如果超出限制
        """
        now = time.time()
        cutoff = now - window

        if api_key not in self._requests:
            self._requests[api_key] = []

        # 移除过期记录
        self._requests[api_key] = [
            ts for ts in self._requests[api_key] if ts > cutoff
        ]

        # 检查是否超出限制
        if len(self._requests[api_key]) >= limit:
            return False

        # 记录新请求
        self._requests[api_key].append(now)
        return True

    def get_remaining(self, api_key: str, limit: int, window: int) -> int:
        """获取剩余请求数"""
        now = time.time()
        cutoff = now - window

        if api_key not in self._requests:
            return limit

        current_count = len([
            ts for ts in self._requests[api_key] if ts > cutoff
        ])
        return max(0, limit - current_count)


class APIAuth:
    """API 认证管理器"""

    def __init__(self, storage_path: Optional[str] = None):
        self._keys: Dict[str, APIKey] = {}
        self._rate_limiter = RateLimiter()
        self._storage_path = storage_path or self._default_storage_path()
        self._load_keys()

    @property
    def _default_storage_path(self) -> str:
        """默认存储路径"""
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "config",
            "api_keys.json"
        )

    def _load_keys(self):
        """从文件加载 API Keys"""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r") as f:
                    data = json.load(f)
                    for key_data in data:
                        key = APIKey(
                            key=key_data["key"],
                            name=key_data["name"],
                            created_at=datetime.fromisoformat(key_data["created_at"]),
                            expires_at=(
                                datetime.fromisoformat(key_data["expires_at"])
                                if key_data.get("expires_at") else None
                            ),
                            rate_limit=key_data.get("rate_limit", 100),
                            rate_limit_window=key_data.get("rate_limit_window", 60),
                            ip_whitelist=set(key_data.get("ip_whitelist", [])),
                            permissions=set(key_data.get("permissions", ["read", "write"])),
                            is_active=key_data.get("is_active", True),
                            last_used_at=(
                                datetime.fromisoformat(key_data["last_used_at"])
                                if key_data.get("last_used_at") else None
                            ),
                            total_requests=key_data.get("total_requests", 0),
                        )
                        self._keys[key.key] = key
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[APIAuth] 警告：加载 API Keys 失败：{e}")

    def _save_keys(self):
        """保存 API Keys 到文件"""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        data = []
        for key in self._keys.values():
            data.append({
                "key": key.key,
                "name": key.name,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "rate_limit": key.rate_limit,
                "rate_limit_window": key.rate_limit_window,
                "ip_whitelist": list(key.ip_whitelist),
                "permissions": list(key.permissions),
                "is_active": key.is_active,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "total_requests": key.total_requests,
            })
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def generate_key(self, name: str, **kwargs) -> APIKey:
        """
        生成新的 API Key

        Args:
            name: Key 名称
            **kwargs: 其他配置参数

        Returns:
            APIKey 对象
        """
        key = "sk-" + secrets.token_urlsafe(24)
        api_key = APIKey(
            key=key,
            name=name,
            created_at=datetime.now(),
            **kwargs
        )
        self._keys[key] = api_key
        self._save_keys()
        return api_key

    def validate_key(self, api_key: str, client_ip: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        验证 API Key

        Args:
            api_key: API Key
            client_ip: 客户端 IP 地址

        Returns:
            (是否有效，错误消息)
        """
        if api_key not in self._keys:
            return False, "无效的 API Key"

        key_data = self._keys[api_key]

        # 检查是否激活
        if not key_data.is_active:
            return False, "API Key 已禁用"

        # 检查是否过期
        if key_data.expires_at and datetime.now() > key_data.expires_at:
            return False, "API Key 已过期"

        # 检查 IP 白名单
        if client_ip and key_data.ip_whitelist:
            if client_ip not in key_data.ip_whitelist:
                return False, f"IP 地址 {client_ip} 不在白名单中"

        # 检查速率限制
        if not self._rate_limiter.is_allowed(
            api_key,
            key_data.rate_limit,
            key_data.rate_limit_window
        ):
            return False, "请求速率超出限制"

        # 更新使用统计
        key_data.last_used_at = datetime.now()
        key_data.total_requests += 1
        self._save_keys()

        return True, None

    def get_key_info(self, api_key: str) -> Optional[APIKey]:
        """获取 API Key 信息"""
        return self._keys.get(api_key)

    def revoke_key(self, api_key: str) -> bool:
        """撤销 API Key"""
        if api_key in self._keys:
            self._keys[api_key].is_active = False
            self._save_keys()
            return True
        return False

    def get_remaining_requests(self, api_key: str) -> int:
        """获取剩余请求数"""
        if api_key not in self._keys:
            return 0
        key_data = self._keys[api_key]
        return self._rate_limiter.get_remaining(
            api_key,
            key_data.rate_limit,
            key_data.rate_limit_window
        )

    def list_keys(self) -> List[Dict]:
        """列出所有 API Key 信息（不暴露实际 key）"""
        result = []
        for key in self._keys.values():
            result.append({
                "name": key.name,
                "key_prefix": key.key[:8] + "...",
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "is_active": key.is_active,
                "rate_limit": key.rate_limit,
                "total_requests": key.total_requests,
            })
        return result


# 全局认证实例
_auth_instance: Optional[APIAuth] = None


def get_auth() -> APIAuth:
    """获取全局认证实例"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = APIAuth()
    return _auth_instance


def init_auth(storage_path: Optional[str] = None) -> APIAuth:
    """初始化认证实例"""
    global _auth_instance
    _auth_instance = APIAuth(storage_path)
    return _auth_instance
