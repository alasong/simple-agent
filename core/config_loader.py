"""
配置加载器
统一管理所有外部配置文件
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigLoader:
    """配置加载器，支持环境变量替换"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.getenv("CONFIG_DIR", "./config"))
        self._settings: Optional[Dict] = None
        self._sectors: Optional[Dict] = None
        self._apis: Optional[Dict] = None

    def _expand_env_vars(self, value: Any) -> Any:
        """递归替换环境变量

        支持格式:
        - ${VAR} - 从环境变量获取，无默认值
        - ${VAR:default} - 有默认值
        - 特殊变量 HOME 直接使用 os.environ['HOME']
        """
        if isinstance(value, str):
            # 匹配 ${VAR} 或 ${VAR:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replace_var(match):
                var_name = match.group(1)
                default = match.group(2)
                
                # 特殊处理 HOME 变量
                if var_name == 'HOME':
                    return os.environ.get('HOME', '/tmp')
                
                env_value = os.getenv(var_name)

                if env_value is not None:
                    return env_value
                elif default is not None:
                    # 处理嵌套的环境变量 (如 ${HOME})
                    if default.startswith('${'):
                        return self._expand_env_vars(default)
                    return default
                else:
                    # 无默认值，返回变量名本身（保持原样）
                    return match.group(0)

            return re.sub(pattern, replace_var, value)
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        return value

    def _load_yaml(self, filename: str) -> Dict:
        """加载 YAML 配置文件"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        return self._expand_env_vars(config)

    @property
    def settings(self) -> Dict:
        """通用设置"""
        if self._settings is None:
            self._settings = self._load_yaml('settings.yaml')
        return self._settings

    @property
    def sectors(self) -> Dict:
        """行业配置"""
        if self._sectors is None:
            self._sectors = self._load_yaml('sectors.yaml')
        return self._sectors

    @property
    def apis(self) -> Dict:
        """API 端点配置"""
        if self._apis is None:
            self._apis = self._load_yaml('apis.yaml')
        return self._apis

    def get(self, path: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔路径

        Args:
            path: 配置路径，如 "directories.agents"
            default: 默认值

        Returns:
            配置值
        """
        keys = path.split('.')
        value = self.settings

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload(self):
        """重新加载所有配置"""
        self._settings = None
        self._sectors = None
        self._apis = None


# 全局配置实例
config = ConfigLoader()


def get_config() -> ConfigLoader:
    """获取全局配置实例"""
    return config
