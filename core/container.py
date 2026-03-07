"""
Dependency Injection Container

解耦组件依赖，避免循环导入
"""

from typing import Any, Optional, Type, Dict, Callable
from dataclasses import dataclass, field


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    interface: Type
    implementation: Any
    is_singleton: bool = True
    instance: Optional[Any] = None


class DIContainer:
    """
    依赖注入容器
    
    用途:
    - 统一管理组件依赖
    - 消除循环导入
    - 支持测试时注入 Mock
    
    示例:
        container = DIContainer()
        container.register(LLMInterface, OpenAILLM)
        container.register(Agent, lambda: Agent(container.get(LLMInterface)))
        
        agent = container.get(Agent)
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._factories: Dict[str, Callable] = {}
    
    def _get_key(self, interface: Type) -> str:
        """获取接口键"""
        return interface.__name__
    
    def register(
        self, 
        interface: Type, 
        implementation: Any,
        is_singleton: bool = True
    ) -> "DIContainer":
        """
        注册服务
        
        Args:
            interface: 接口类型
            implementation: 实现类或实例
            is_singleton: 是否单例
        
        Returns:
            容器自身，支持链式调用
        """
        key = self._get_key(interface)
        
        if isinstance(implementation, type):
            # 注册的是类
            self._services[key] = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                is_singleton=is_singleton
            )
        else:
            # 注册的是实例
            self._services[key] = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                is_singleton=True,
                instance=implementation
            )
        
        return self
    
    def register_factory(
        self, 
        interface: Type, 
        factory: Callable[[], Any]
    ) -> "DIContainer":
        """
        注册工厂函数
        
        Args:
            interface: 接口类型
            factory: 工厂函数
        
        Returns:
            容器自身，支持链式调用
        """
        key = self._get_key(interface)
        self._factories[key] = factory
        return self
    
    def get(self, interface: Type) -> Any:
        """
        获取服务实例
        
        Args:
            interface: 接口类型
        
        Returns:
            服务实例
        """
        key = self._get_key(interface)
        
        # 检查是否有工厂函数
        if key in self._factories:
            return self._factories[key]()
        
        # 检查是否有注册的服务
        if key not in self._services:
            raise KeyError(f"Service {key} not registered")
        
        descriptor = self._services[key]
        
        # 如果是单例且已创建实例，直接返回
        if descriptor.is_singleton and descriptor.instance is not None:
            return descriptor.instance
        
        # 创建实例
        if isinstance(descriptor.implementation, type):
            instance = descriptor.implementation()
        else:
            instance = descriptor.implementation
        
        # 单例则保存实例
        if descriptor.is_singleton:
            descriptor.instance = instance
        
        return instance
    
    def get_optional(self, interface: Type, default: Any = None) -> Any:
        """
        获取服务实例（可选）
        
        Args:
            interface: 接口类型
            default: 默认值
        
        Returns:
            服务实例或默认值
        """
        try:
            return self.get(interface)
        except KeyError:
            return default
    
    def has(self, interface: Type) -> bool:
        """检查服务是否已注册"""
        key = self._get_key(interface)
        return key in self._services or key in self._factories
    
    def clear(self):
        """清空所有注册"""
        self._services.clear()
        self._factories.clear()


# 全局容器实例
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container():
    """重置全局容器（用于测试）"""
    global _container
    _container = None
