"""
Tool Registry - 工具注册表（插件型按需加载）

设计理念:
- 自动发现：扫描 tools/ 目录自动发现所有工具
- 按需加载：只在首次使用时实例化
- 向后兼容：保留 tools/__init__.py 的导出接口

使用示例:
    from core.tool_registry import ToolRegistry

    # 获取工具实例（首次使用时自动加载）
    tool = ToolRegistry.get_tool("BashTool")

    # 获取所有已发现的工具
    tools = ToolRegistry.get_all_tools()
"""

import importlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Type, Any

from .tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表 - 单例模式

    功能:
    - 自动发现 tools/ 目录下的所有工具类
    - 懒加载：首次使用时才实例化
    - 支持按标签筛选工具
    """

    _instance: Optional['ToolRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        # 工具类注册表：name -> tool_class
        self._tool_classes: Dict[str, Type[BaseTool]] = {}

        # 工具实例缓存：name -> tool_instance
        self._tool_instances: Dict[str, BaseTool] = {}

        # 工具标签索引：tag -> [tool_names]
        self._tool_tags: Dict[str, List[str]] = {}

        # 是否已扫描
        self._discovered = False

    def discover_tools(self, package: str = "tools") -> int:
        """
        自动发现工具包中的所有工具类

        Args:
            package: 工具包名称，默认 "tools"

        Returns:
            发现的工具数量
        """
        if self._discovered:
            return len(self._tool_classes)

        count = 0

        try:
            # 获取包路径
            pkg_path = Path(__file__).parent.parent / package

            if not pkg_path.exists():
                logger.warning(f"工具目录不存在：{pkg_path}")
                return 0

            # 扫描所有 Python 文件
            for file in pkg_path.glob("*.py"):
                # 跳过私有文件
                if file.name.startswith("_"):
                    continue

                module_name = f"{package}.{file.stem}"

                try:
                    # 延迟导入模块
                    module = importlib.import_module(module_name)

                    # 扫描模块中继承 BaseTool 的类
                    for name, obj in vars(module).items():
                        if (isinstance(obj, type) and
                            issubclass(obj, BaseTool) and
                            obj != BaseTool):

                            tool_name = obj.__name__
                            if tool_name not in self._tool_classes:
                                self._tool_classes[tool_name] = obj
                                count += 1
                                logger.debug(f"发现工具：{tool_name}")

                except Exception as e:
                    logger.warning(f"加载工具模块 {module_name} 失败：{e}")

            self._discovered = True
            logger.info(f"共发现 {count} 个工具")

        except Exception as e:
            logger.error(f"扫描工具失败：{e}")

        return count

    def get_tool(self, name: str) -> BaseTool:
        """
        获取工具实例（懒加载）

        Args:
            name: 工具名称（类名）

        Returns:
            工具实例

        Raises:
            KeyError: 工具不存在
        """
        # 确保已扫描
        if not self._discovered:
            self.discover_tools()

        # 检查是否存在
        if name not in self._tool_classes:
            # 尝试动态导入
            self._try_lazy_import(name)

        if name not in self._tool_classes:
            raise KeyError(f"未知工具：{name}")

        # 懒加载实例化
        if name not in self._tool_instances:
            try:
                self._tool_instances[name] = self._tool_classes[name]()
                logger.debug(f"实例化工具：{name}")
            except Exception as e:
                raise RuntimeError(f"实例化工具 {name} 失败：{e}")

        return self._tool_instances[name]

    def _try_lazy_import(self, name: str):
        """
        尝试动态导入指定工具

        用于按需加载场景，只导入需要的工具模块
        """
        # 可能的模块名映射
        name_lower = name.lower()

        # 常见工具模块映射
        module_mappings = {
            "bashtool": "tools.bash_tool",
            "readfiletool": "tools.file",
            "writefiletool": "tools.file",
            "websearchtool": "tools.web_search_tool",
            "httptool": "tools.http_tool",
            "invokeagenttool": "tools.agent_tools",
            "createworkflowtool": "tools.agent_tools",
            "listagentstool": "tools.agent_tools",
            "supplementtool": "tools.supplement",
            "explainreasontool": "tools.supplement",
            # 推理工具
            "treeofthoughttool": "tools.reasoning_tools_wrappers",
            "iterativeoptimizertool": "tools.reasoning_tools_wrappers",
            "swarmvotingtool": "tools.reasoning_tools_wrappers",
            "multipathoptimizertool": "tools.reasoning_tools_wrappers",
            # 数据工具
            "stockmarkettool": "tools.stock_market_tool",
        }

        module_name = module_mappings.get(name_lower)
        if module_name:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, name):
                    self._tool_classes[name] = getattr(module, name)
            except Exception as e:
                logger.debug(f"懒加载工具 {name} 失败：{e}")

    def get_tools(self, names: List[str]) -> List[BaseTool]:
        """
        批量获取工具实例

        Args:
            names: 工具名称列表

        Returns:
            工具实例列表
        """
        return [self.get_tool(name) for name in names]

    def get_tools_by_tags(self, tags: List[str]) -> List[BaseTool]:
        """
        按标签获取工具

        Args:
            tags: 标签列表

        Returns:
            工具实例列表
        """
        tool_names = set()
        for tag in tags:
            if tag in self._tool_tags:
                tool_names.update(self._tool_tags[tag])

        return self.get_tools(list(tool_names))

    def register_tool(
        self,
        tool_class: Type[BaseTool],
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> Type[BaseTool]:
        """
        注册工具（用于动态注册或装饰器）

        Args:
            tool_class: 工具类
            tags: 标签列表
            description: 描述

        Returns:
            工具类
        """
        name = tool_class.__name__
        self._tool_classes[name] = tool_class

        # 建立标签索引
        for tag in (tags or []):
            if tag not in self._tool_tags:
                self._tool_tags[tag] = []
            if name not in self._tool_tags[tag]:
                self._tool_tags[tag].append(name)

        logger.debug(f"注册工具：{name}")
        return tool_class

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具实例"""
        if not self._discovered:
            self.discover_tools()

        return list(self._tool_instances.values())

    def get_available_tools(self) -> Dict[str, str]:
        """
        获取可用工具信息

        Returns:
            {工具名：描述} 字典
        """
        if not self._discovered:
            self.discover_tools()

        result = {}
        for name, cls in self._tool_classes.items():
            desc = cls.__doc__ or ""
            # 提取第一行作为简短描述
            desc = desc.strip().split('\n')[0] if desc else name
            result[name] = desc

        return result

    def list_tools(self) -> List[str]:
        """列出所有可用工具名称"""
        if not self._discovered:
            self.discover_tools()
        return list(self._tool_classes.keys())

    def clear_cache(self):
        """清除工具实例缓存（用于测试或重新加载）"""
        self._tool_instances.clear()
        self._discovered = False


# ============================================================================
# 全局工具函数
# ============================================================================

# 全局注册表实例
_registry_instance: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """获取全局注册表实例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


def get_tool(name: str) -> BaseTool:
    """便捷函数：获取工具实例"""
    return get_registry().get_tool(name)


def get_tools(names: List[str]) -> List[BaseTool]:
    """便捷函数：批量获取工具实例"""
    return get_registry().get_tools(names)


def discover_tools() -> int:
    """便捷函数：扫描工具"""
    return get_registry().discover_tools()


def register_tool(
    tool_class: Type[BaseTool],
    tags: Optional[List[str]] = None
) -> Type[BaseTool]:
    """
    装饰器：注册工具

    使用示例:
        @register_tool(tags=["file", "io"])
        class MyTool(BaseTool):
            ...
    """
    registry = get_registry()
    registry.register_tool(tool_class, tags)
    return tool_class
