"""
执行上下文 - 线程本地存储

用于在多层调用中传递运行时配置：
- output_dir: 输出目录
- sandbox_dir: 沙箱目录
- verbose: 详细输出
"""

import threading

# 全局执行上下文（线程本地存储）
# 所有模块都应该使用同一个 _execution_context
_execution_context = threading.local()


def set_output_dir(output_dir: str):
    """设置输出目录"""
    _execution_context.output_dir = output_dir


def get_output_dir() -> str:
    """获取输出目录"""
    return getattr(_execution_context, 'output_dir', None)


def set_sandbox_dir(sandbox_dir: str):
    """设置沙箱目录（沙箱根目录）"""
    _execution_context.sandbox_dir = sandbox_dir


def get_sandbox_dir() -> str:
    """获取沙箱目录"""
    return getattr(_execution_context, 'sandbox_dir', None)


def set_verbose(verbose: bool):
    """设置详细输出模式"""
    _execution_context.verbose = verbose


def get_verbose() -> bool:
    """获取详细输出模式"""
    return getattr(_execution_context, 'verbose', True)


def clear():
    """清理执行上下文（用于任务结束后的资源清理）"""
    if hasattr(_execution_context, 'output_dir'):
        delattr(_execution_context, 'output_dir')
    if hasattr(_execution_context, 'sandbox_dir'):
        delattr(_execution_context, 'sandbox_dir')
    if hasattr(_execution_context, 'verbose'):
        delattr(_execution_context, 'verbose')


# 保持向后兼容：直接导出 _execution_context
# 旧代码仍可使用 _execution_context 直接访问
__all__ = ['_execution_context', 'set_output_dir', 'get_output_dir',
           'set_sandbox_dir', 'get_sandbox_dir', 'set_verbose', 'get_verbose', 'clear']
