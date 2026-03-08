"""
验证 CLI 并行执行功能
"""

import asyncio
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List


class MockAgent:
    """模拟 Agent 用于测试"""

    def __init__(self, name: str, delay: float = 0.1):
        self.name = name
        self.delay = delay
        self.call_time = None

    def run(self, task_input: str, verbose: bool = True) -> str:
        if verbose:
            print(f"[{self.name}] 开始执行...")
        time.sleep(self.delay)
        self.call_time = time.time()
        if verbose:
            print(f"[{self.name}] 完成 (耗时：{self.delay}s)")
        return f"[{self.name}] 结果：{task_input[:30]}"


async def test_parallel_workflow():
    """测试并行工作流"""
    from core.workflow import create_parallel_workflow

    # 创建 3 个 Agent，每个耗时 0.5 秒
    agents = [
        MockAgent("Agent-A", delay=0.5),
        MockAgent("Agent-B", delay=0.5),
        MockAgent("Agent-C", delay=0.5),
    ]

    # 创建并行工作流
    workflow = create_parallel_workflow(max_concurrent=5, default_timeout=30.0)

    # 添加任务
    for i, agent in enumerate(agents):
        workflow.add_task(f"task{i}", agent, instance_id=agent.name)

    print("\n" + "="*60)
    print("开始并行执行 3 个任务 (每个耗时 0.5 秒)")
    print("="*60 + "\n")

    start = time.time()
    results = await workflow.execute("并行测试", verbose=True)
    elapsed = time.time() - start

    print("\n" + "="*60)
    print(f"执行完成！总耗时：{elapsed:.2f}秒")
    print(f"理论串行时间：1.5 秒 (3 x 0.5)")
    print(f"并行效率：{1.5/elapsed:.2f}x")
    print("="*60)

    # 验证
    assert elapsed < 1.0, f"并行执行失败，耗时过长：{elapsed}秒"
    success_count = sum(1 for r in results.values() if r.success)
    assert success_count == 3, f"应有 3 个成功任务，实际：{success_count}"

    print("\n✓ 并行执行验证通过！")


if __name__ == "__main__":
    asyncio.run(test_parallel_workflow())
