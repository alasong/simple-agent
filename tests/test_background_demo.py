#!/usr/bin/env python3
"""
后台任务功能演示
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_agent import CLIAgent
from core.rich_output import print_header, print_success, print_info


async def demo_background_tasks():
    """演示后台任务功能"""
    
    print_header("后台任务功能演示", "同时提交多个任务，UI 不会阻塞")
    
    # 创建 CLI Agent
    cli_agent = CLIAgent(max_concurrent=3)
    
    # 启动任务队列
    await cli_agent.task_queue.start()
    
    print("\n[演示 1] 提交 3 个后台任务")
    print("-" * 60)
    
    # 提交 3 个任务
    tasks = [
        "今天是几号？",
        "2+2 等于多少？",
        "介绍一下你自己"
    ]
    
    handles = []
    for i, task in enumerate(tasks, 1):
        handle = await cli_agent.execute_async(task, verbose=False)
        handles.append(handle)
        print(f"✓ 提交任务 {i}: {handle.id}")
    
    print("\n[演示 2] 查看所有任务状态")
    print("-" * 60)
    
    # 等待一小段时间让任务开始执行
    await asyncio.sleep(0.5)
    
    # 查看任务列表
    all_tasks = await cli_agent.task_queue.list_tasks()
    
    print(f"\n任务列表 (共{len(all_tasks)}个):")
    for t in all_tasks:
        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '⚠️'
        }.get(t.status.value, '?')
        
        elapsed = t.get_elapsed_time() if hasattr(t, 'get_elapsed_time') else 0
        print(f"  {status_icon} [{t.status.value:10}] {t.id:35} | {t.input[:30]} | {elapsed:.2f}s")
    
    print("\n[演示 3] 查看任务统计")
    print("-" * 60)
    
    stats = cli_agent.task_queue.get_stats()
    print(f"""
统计信息:
  总任务数：{stats['total']}
  - 等待中：{stats['pending']}
  - 运行中：{stats['running']}
  - 已完成：{stats['completed']}
  - 已失败：{stats['failed']}
  - 已取消：{stats['cancelled']}
  
  最大并发：{stats['max_concurrent']}
  队列大小：{stats['queue_size']}
""")
    
    print("\n[演示 4] 等待并获取任务结果")
    print("-" * 60)
    
    # 获取第一个任务的结果
    if handles:
        first_handle = handles[0]
        print(f"等待任务 {first_handle.id} 完成...")
        
        try:
            result = await first_handle.result(timeout=10)
            print_success(f"✓ 任务完成，结果：{str(result)[:100]}...")
        except asyncio.TimeoutError:
            print_info("⏱ 任务超时，可能仍在执行中")
        except Exception as e:
            print(f"✗ 任务失败：{e}")
    
    print("\n[演示 5] 任务并发执行验证")
    print("-" * 60)
    
    # 提交 5 个任务，验证并发执行
    import time
    start_time = time.time()
    
    async def timing_task(task_id):
        await asyncio.sleep(0.3)  # 每个任务耗时 0.3 秒
        return f"任务{task_id}完成"
    
    # 提交 5 个任务（最大并发 3 个）
    timing_handles = []
    for i in range(5):
        handle = await cli_agent.task_queue.submit(
            input_text=f"计时任务{i}",
            coro=timing_task(i)
        )
        timing_handles.append(handle)
    
    # 等待所有任务完成
    await asyncio.sleep(1.0)
    
    elapsed = time.time() - start_time
    print(f"5 个任务（每个 0.3 秒），最大并发 3 个")
    print(f"实际耗时：{elapsed:.2f}秒")
    print(f"理论串行：1.5 秒，理论并行（3 并发）：~0.6 秒")
    
    if elapsed < 1.0:
        print_success(f"✓ 并发执行成功！节省了{((1.5 - elapsed) / 1.5 * 100):.1f}%时间")
    else:
        print_info("⚠ 并发执行效果不明显")
    
    # 停止任务队列
    await cli_agent.task_queue.stop()
    
    print("\n" + "="*60)
    print("✓ 演示完成")
    print("="*60)
    print("\n提示：在 CLI 中使用以下命令体验后台任务功能：")
    print("  /bg <任务>       - 后台执行任务")
    print("  /tasks           - 查看所有任务")
    print("  /result <task_id> - 查看任务结果")
    print("  /cancel <task_id> - 取消任务")
    print("  /task_stats      - 查看任务统计")


if __name__ == "__main__":
    asyncio.run(demo_background_tasks())
