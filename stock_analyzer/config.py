"""
股市热点分析工具配置文件
配置已移至 config/sectors.yaml 和 config/settings.yaml
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# 导入统一配置加载器
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config_loader import get_config

config = get_config()


@dataclass
class SectorConfig:
    """行业配置"""
    name: str
    keywords: List[str]
    related_stocks: List[str]
    api_endpoints: List[str]

    @classmethod
    def from_dict(cls, data: Dict) -> 'SectorConfig':
        """从字典创建配置"""
        return cls(
            name=data.get('name', ''),
            keywords=data.get('keywords', []),
            related_stocks=data.get('related_stocks', []),
            api_endpoints=data.get('api_endpoints', [])
        )


def get_sector_configs() -> Dict[str, SectorConfig]:
    """获取行业配置（从外部配置文件加载）"""
    sectors_config = config.sectors.get('sectors', {})
    return {
        key: SectorConfig.from_dict(value)
        for key, value in sectors_config.items()
    }


# 延迟加载的行业配置
SECTOR_CONFIGS: Optional[Dict[str, SectorConfig]] = None


def get_sector(name: str) -> Optional[SectorConfig]:
    """获取单个行业配置"""
    global SECTOR_CONFIGS
    if SECTOR_CONFIGS is None:
        SECTOR_CONFIGS = get_sector_configs()
    return SECTOR_CONFIGS.get(name)


def list_sectors() -> List[str]:
    """列出所有行业名称"""
    global SECTOR_CONFIGS
    if SECTOR_CONFIGS is None:
        SECTOR_CONFIGS = get_sector_configs()
    return list(SECTOR_CONFIGS.keys())


# API配置 - 必须通过环境变量设置，无默认值
def _get_required_env(name: str) -> str:
    """获取必需的环境变量"""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"环境变量 {name} 必须设置。请在 .env 文件或环境中配置。")
    return value


def get_alpha_vantage_api_key() -> str:
    """获取 Alpha Vantage API Key"""
    return _get_required_env("ALPHA_VANTAGE_API_KEY")


def get_news_api_key() -> str:
    """获取 News API Key"""
    return _get_required_env("NEWS_API_KEY")


# 向后兼容的属性（延迟加载，会在访问时检查环境变量）
def __getattr__(name: str):
    """延迟加载配置属性"""
    if name == "ALPHA_VANTAGE_API_KEY":
        return get_alpha_vantage_api_key()
    elif name == "NEWS_API_KEY":
        return get_news_api_key()
    elif name == "SECTOR_CONFIGS":
        global SECTOR_CONFIGS
        if SECTOR_CONFIGS is None:
            SECTOR_CONFIGS = get_sector_configs()
        return SECTOR_CONFIGS
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
