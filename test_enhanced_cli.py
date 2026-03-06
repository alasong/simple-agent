#!/usr/bin/env python3
"""
测试阶段 1 功能集成到 CLI
"""
import asyncio
import sys
sys.path.insert(0, '.')

from core import (
    EnhancedMemory, Experience,
    TreeOfThought, ReflectionLoop,
    SkillLibrary
)
from core.agent_enhanced import EnhancedAgent
from core.llm import OpenAILLM


async def test_enhanced_agent():
    """测试增强型 Agent"""
    print("="*60)
    print("测试增强型 Agent")
    print("="*60)
    
    # 创建增强型 Agent
    llm = OpenAILLM()
    memory = EnhancedMemory()
    skill_library = SkillLibrary()
    agent = EnhancedAgent(llm=llm, memory=memory, skill_library=skill_library)
    
    print(f"\n✓ 增强型 Agent 创建成功")
    print(f"  - 默认策略：{agent.strategy}")
    print(f"  - 技能数量：{len(skill_library.skills)}")
    print(f"  - 记忆对象：{type(memory).__name__}")
    
    # 测试技能库
    print("\n技能库内容:")
    for name, skill in skill_library.skills.items():
        print(f"  - {name}: {skill.description} (成功率：{skill.success_rate:.0%})")
    
    # 测试策略选择
    print("\n策略选择测试:")
    test_tasks = [
        "分析这段代码",
        "设计一个完整的系统架构",
        "写个简单的函数"
    ]
    
    for task in test_tasks:
        strategy = await agent._select_strategy(task, [])
        complexity = await agent._estimate_complexity(task)
        print(f"  任务：{task[:20]}...")
        print(f"    复杂度：{complexity:.2f}, 策略：{strategy}")
    
    return agent


async def test_memory():
    """测试增强型记忆"""
    print("\n" + "="*60)
    print("测试增强型记忆")
    print("="*60)
    
    memory = EnhancedMemory()
    
    # 添加工作记忆
    memory.add_to_working("用户询问代码分析")
    memory.add_to_working("正在分析 Python 文件")
    
    # 添加经验到短期记忆
    exp1 = Experience(
        content="分析代码结构",
        context="用户提供了一个 Python 文件",
        result="成功识别了所有函数和类",
        success=True,
        tags=["代码分析", "Python"]
    )
    exp2 = Experience(
        content="生成测试代码",
        context="用户需要单元测试",
        result="生成了 pytest 测试框架代码",
        success=True,
        tags=["测试生成", "pytest"]
    )
    
    memory.add_to_short_term(exp1)
    memory.add_to_short_term(exp2)
    
    print(f"\n✓ 记忆状态:")
    print(f"  - 工作记忆：{len(memory.working_memory)} 条")
    print(f"  - 短期记忆：{len(memory.short_term)} 条")
    print(f"  - 经验记录：{len(memory.experiences)} 条")
    
    # 测试反思
    reflection = memory.reflect()
    print(f"\n✓ 反思总结:")
    print(f"  {reflection}")
    
    return memory


async def test_reasoning_modes():
    """测试推理模式"""
    print("\n" + "="*60)
    print("测试推理模式")
    print("="*60)
    
    llm = OpenAILLM()
    memory = EnhancedMemory()
    agent = EnhancedAgent(llm=llm, memory=memory)
    
    # 测试 TreeOfThought
    print("\n✓ TreeOfThought 已就绪")
    tot = TreeOfThought(agent, breadth=2, depth=2)
    print(f"  - 分支数：{tot.breadth}")
    print(f"  - 深度：{tot.depth}")
    
    # 测试 ReflectionLoop
    print("\n✓ ReflectionLoop 已就绪")
    reflection = ReflectionLoop(agent)
    print(f"  - 可用于分析执行轨迹并反思改进")
    
    return True


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("阶段 1 功能集成测试")
    print("="*60)
    
    try:
        # 测试各个组件
        agent = await test_enhanced_agent()
        memory = await test_memory()
        await test_reasoning_modes()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过!")
        print("="*60)
        print("\n阶段 1 功能已成功集成:")
        print("  1. EnhancedMemory - 增强型记忆系统")
        print("  2. TreeOfThought - 思维树推理")
        print("  3. ReflectionLoop - 反思循环")
        print("  4. SkillLibrary - 技能学习系统")
        print("  5. EnhancedAgent - 增强型 Agent")
        print("\nCLI 命令:")
        print("  /enhanced [策略] <任务> - 使用增强型 Agent")
        print("  /memory - 查看记忆状态")
        print("  /skills - 查看技能库")
        print("  /reasoning <模式> - 选择推理模式")
        
    except Exception as e:
        print(f"\n✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
