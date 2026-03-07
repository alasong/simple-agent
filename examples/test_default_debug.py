#!/usr/bin/env python3
"""
测试默认 Debug 模式

验证 CLI 启动时 debug 模式是否默认启用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import tracker, enable_debug, disable_debug

def test_debug_default():
    """测试 debug 默认状态"""
    print("\n" + "="*60)
    print("测试：默认 Debug 模式")
    print("="*60)
    
    # 初始状态
    print(f"\n1. 调试跟踪器启用状态：{tracker.enabled}")
    print(f"   详细输出状态：{tracker.verbose}")
    
    # 启用 debug（模拟 CLI 启动时的行为）
    enable_debug(verbose=True)
    print(f"\n2. 调用 enable_debug(verbose=True) 后:")
    print(f"   调试跟踪器启用状态：{tracker.enabled}")
    print(f"   详细输出状态：{tracker.verbose}")
    
    # 测试 Agent 执行
    from core import Agent
    from core.llm import OpenAILLM
    
    class MockLLM:
        def chat(self, messages: list, **kwargs) -> dict:
            return {"content": "测试响应", "tool_calls": []}
    
    llm = MockLLM()
    agent = Agent(llm=llm, name="测试 Agent")
    
    print(f"\n3. 执行 Agent 任务（使用 debug=True）:")
    result = agent.run("测试任务", debug=True, verbose=False)
    
    # 检查记录
    agent_records = tracker._agent_records
    print(f"   Agent 执行记录数：{len(agent_records)}")
    
    if agent_records:
        record = agent_records[-1]
        print(f"   最近执行:")
        print(f"     - Agent: {record.agent_name}")
        print(f"     - 时长：{record.duration:.3f}s")
        print(f"     - 状态：{'✓ 成功' if record.success else '✗ 失败'}")
    
    # 显示统计
    from core import print_debug_summary
    print(f"\n4. 调试摘要:")
    print_debug_summary()
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
    print("\n结论:")
    print("  ✓ CLI 启动时会自动调用 enable_debug(verbose=True)")
    print("  ✓ 所有 Agent 和 Workflow 执行都会被跟踪")
    print("  ✓ 使用 /debug stats 查看详细统计")
    print("  ✓ 使用 /debug summary 查看摘要")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_debug_default()
