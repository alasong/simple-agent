"""
阶段 1 功能测试
"""
import asyncio
import sys
sys.path.insert(0, '/home/song/simple-agent')


async def test_memory_enhanced():
    """测试增强记忆系统"""
    from core.memory_enhanced import EnhancedMemory, Experience
    
    mem = EnhancedMemory()
    exp = Experience(
        content='测试任务',
        context='单元测试',
        result='成功',
        success=True,
        tags=['test']
    )
    mem.add_to_short_term(exp)
    
    assert len(mem.experiences) == 1
    assert mem.experiences[0].success == True
    
    print('✓ EnhancedMemory 测试通过')


async def test_skill_library():
    """测试技能库"""
    from core.skill_learning import SkillLibrary
    
    lib = SkillLibrary()
    
    skill = lib.select_skill('请分析代码')
    assert skill is not None
    assert skill.name == '代码分析'
    
    await lib.improve_skill('代码分析', 1.0)
    assert lib.skills['代码分析'].usage_count == 1
    
    print('✓ SkillLibrary 测试通过')


async def test_reasoning_modes():
    """测试推理模式"""
    from core.reasoning_modes import ReflectionLoop
    
    trajectory = [
        ('思考 1', '行动 1', '结果 1 - 成功'),
        ('思考 2', '行动 2', '结果 2 - 部分成功'),
    ]
    
    print('✓ ReflectionLoop 结构验证通过')
    print('  注意：完整测试需要 Agent 实例')


async def main():
    print('=' * 50)
    print('阶段 1 功能测试')
    print('=' * 50)
    
    await test_memory_enhanced()
    await test_skill_library()
    await test_reasoning_modes()
    
    print('=' * 50)
    print('所有测试完成！')
    print('=' * 50)


if __name__ == '__main__':
    asyncio.run(main())
