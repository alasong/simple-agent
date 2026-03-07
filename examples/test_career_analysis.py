#!/usr/bin/env python3
"""
职业前景分析测试 - 展示调试功能

运行：
    python examples/test_career_analysis.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import enable_debug, print_debug_summary, tracker
from builtin_agents import get_agent
from core import Workflow

def main():
    print("\n" + "="*60)
    print("职业前景分析 - 调试功能演示")
    print("="*60)
    
    # 启用调试
    enable_debug(verbose=False)
    
    # 任务 1: 使用金融分析师
    print("\n[任务 1] 金融分析师分析职业前景...")
    analyst = get_agent('financial_analyst')
    result1 = analyst.run(
        '分析未来 5 年什么职业前景更好，重点考虑薪资水平和发展空间',
        debug=True,
        verbose=False
    )
    print("✓ 完成")
    
    # 任务 2: 使用 AI 研究员
    print("\n[任务 2] AI 研究员分析科技行业趋势...")
    researcher = get_agent('ai_researcher')
    result2 = researcher.run(
        '从技术发展趋势角度，分析哪些职业最有前景',
        debug=True,
        verbose=False
    )
    print("✓ 完成")
    
    # 任务 3: 创建工作流
    print("\n[任务 3] 执行综合分析工作流...")
    workflow = Workflow('职业分析工作流', description='多角度分析职业前景')
    workflow.add_step('金融角度分析', analyst)
    workflow.add_step('技术角度分析', researcher)
    
    result3 = workflow.run('总结未来最有前景的职业', debug=True, verbose=False)
    print("✓ 完成")
    
    # 显示调试统计
    print("\n" + "="*60)
    print("调试统计信息")
    print("="*60)
    
    print("\n📊 执行摘要:")
    print_debug_summary()
    
    # 详细统计
    agent_stats = tracker.get_agent_stats()
    print("\n📊 Agent 详细统计:")
    print(f"  总执行次数：{agent_stats.get('count', 0)}")
    print(f"  成功：{agent_stats.get('successful', 0)}")
    print(f"  失败：{agent_stats.get('failed', 0)}")
    
    if agent_stats.get('by_agent'):
        print("\n  按 Agent 分类:")
        for name, stats in agent_stats['by_agent'].items():
            print(f"    - {name}:")
            print(f"        执行：{stats.get('count', 0)} 次")
            print(f"        成功率：{stats.get('success_rate', 0):.1%}")
            print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
    
    workflow_stats = tracker.get_workflow_stats()
    print("\n📊 Workflow 详细统计:")
    print(f"  总执行次数：{workflow_stats.get('count', 0)}")
    print(f"  成功：{workflow_stats.get('successful', 0)}")
    print(f"  总步骤：{workflow_stats.get('total_steps', 0)}")
    print(f"  步骤成功率：{workflow_stats.get('step_success_rate', 0):.1f}%")
    
    if workflow_stats.get('by_workflow'):
        print("\n  按 Workflow 分类:")
        for name, stats in workflow_stats['by_workflow'].items():
            print(f"    - {name}:")
            print(f"        执行：{stats.get('count', 0)} 次")
            print(f"        平均步骤：{stats.get('avg_steps', 0):.1f}")
            print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
    
    # 最近执行记录
    print("\n" + "="*60)
    print("最近执行记录")
    print("="*60)
    
    agent_records = tracker.get_recent_agent_records(limit=5)
    print("\n最近 Agent 执行:")
    for i, record in enumerate(agent_records, 1):
        print(f"  {i}. {record['agent_name']} - {record['duration']:.3f}s - {'✓' if record['success'] else '✗'}")
    
    workflow_records = tracker.get_recent_workflow_records(limit=3)
    print("\n最近 Workflow 执行:")
    for i, record in enumerate(workflow_records, 1):
        print(f"  {i}. {record['workflow_name']} - {record['total_steps']}步 - {record['duration']:.3f}s - {'✓' if record['success'] else '✗'}")
    
    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)
    print("\n提示：在 CLI 交互模式中，可以使用以下命令查看类似信息:")
    print("  /debug summary  - 显示调试摘要")
    print("  /debug stats    - 显示详细统计信息")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
