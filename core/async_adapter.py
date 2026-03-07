"""
Async Adapter - 异步适配器模式

使同步 Agent 能在异步环境中使用
"""

import asyncio
from typing import Any


class AsyncAgentAdapter:
    """
    异步 Agent 适配器
    
    将同步 Agent 包装为异步接口，使其能在 Swarm 等异步环境中使用
    
    示例:
        sync_agent = Agent(llm, tools)
        async_agent = AsyncAgentAdapter(sync_agent)
        
        # 在异步代码中使用
        result = await async_agent.run(task)
    """
    
    def __init__(self, sync_agent):
        """
        初始化适配器
        
        Args:
            sync_agent: 同步 Agent 实例
        """
        self.sync_agent = sync_agent
        self.name = sync_agent.name
        self.version = sync_agent.version
    
    async def run(self, task: str, verbose: bool = False) -> str:
        """
        异步执行任务
        
        在线程池中运行同步 Agent，避免阻塞事件循环
        
        Args:
            task: 任务描述
            verbose: 是否打印详细过程
        
        Returns:
            执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.sync_agent.run(task, verbose=verbose)
        )
    
    async def solve(self, task: str, verbose: bool = False) -> str:
        """
        解决复杂任务（别名方法）
        
        Args:
            task: 任务描述
            verbose: 是否打印详细过程
        
        Returns:
            执行结果
        """
        return await self.run(task, verbose)
    
    def __getattr__(self, name: str) -> Any:
        """代理其他属性访问到同步 agent"""
        return getattr(self.sync_agent, name)
