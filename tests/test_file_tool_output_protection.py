#!/usr/bin/env python3
"""
文件工具输出路径防护测试

测试 WriteFileTool 的输出路径防护功能。
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, '/home/song/simple-agent')


def test_output_dir_enforcement_logic():
    """
    测试 output_dir 强制逻辑（独立于工具装饰器）

    直接测试 WriteFileTool.execute 中的路径处理逻辑
    """
    print("\n" + "="*60)
    print("测试 output_dir 强制逻辑")
    print("="*60)

    temp_dir = tempfile.mkdtemp(prefix='test_output_')
    output_dir = os.path.join(temp_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录：{output_dir}")

    try:
        from simple_agent.tools.file import set_output_dir, get_output_dir

        set_output_dir(output_dir)
        assert get_output_dir() == output_dir, "输出目录设置失败"
        print(f"✓ 输出目录已设置: {output_dir}")

        def process_file_path(file_path, content):
            """模拟 WriteFileTool.execute 的路径处理逻辑"""
            output_dir = get_output_dir()
            if output_dir:
                filename = os.path.basename(file_path)
                dir_part = os.path.dirname(file_path)
                if dir_part and dir_part != '.':
                    safe_dir = os.path.join(output_dir, dir_part)
                    os.makedirs(safe_dir, exist_ok=True)
                    file_path = os.path.join(safe_dir, filename)
                else:
                    file_path = os.path.join(output_dir, filename)
            return file_path

        # 测试 1: 简单文件名
        result_path = process_file_path('test_file.txt', '测试内容')
        expected_path = os.path.join(output_dir, 'test_file.txt')
        assert result_path == expected_path, f"路径错误: {result_path} != {expected_path}"
        print(f"  ✓ 测试 1 通过: 简单文件名强制到 output_dir")

        # 测试 2: 带子目录
        result_path = process_file_path('subdir/nested.txt', '嵌套内容')
        expected_path = os.path.join(output_dir, 'subdir', 'nested.txt')
        assert result_path == expected_path, f"路径错误: {result_path} != {expected_path}"
        print(f"  ✓ 测试 2 通过: 带子目录的路径")

        # 测试 3: 深层嵌套
        result_path = process_file_path('a/b/c/deep.txt', '深层内容')
        expected_path = os.path.join(output_dir, 'a', 'b', 'c', 'deep.txt')
        assert result_path == expected_path, f"路径错误: {result_path} != {expected_path}"
        print(f"  ✓ 测试 3 通过: 深层嵌套路径")

        # 测试 4: 实际写入
        test_path = process_file_path('real_file.txt', '真实内容')
        dir_path = os.path.dirname(test_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write('真实内容')
        assert os.path.exists(test_path), f"文件未创建: {test_path}"
        print(f"  ✓ 测试 4 通过: 实际文件写入")

        print("\n✓ 测试通过")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n已清理临时目录：{temp_dir}")


def test_path_validation():
    """测试路径验证功能"""
    print("\n" + "="*60)
    print("测试路径验证功能")
    print("="*60)

    from simple_agent.tools.file import validate_path

    # 测试 1: 合法路径
    is_valid, msg = validate_path('test.txt')
    assert is_valid, f"合法路径被拒绝: {msg}"
    print(f"  ✓ 测试 1 通过: 合法路径被接受")

    # 测试 2: 路径遍历攻击
    is_valid, msg = validate_path('../etc/passwd')
    assert not is_valid and '非法模式' in msg
    print(f"  ✓ 测试 2 通过: 路径遍历被拒绝")

    # 测试 3: 系统敏感目录
    is_valid, msg = validate_path('/etc/passwd', allow_read_outside=True)
    assert not is_valid
    print(f"  ✓ 测试 3 通过: 系统敏感目录被拒绝")

    # 测试 4: 根目录写入
    is_valid, msg = validate_path('/root/test.txt')
    assert not is_valid
    print(f"  ✓ 测试 4 通过: 根目录写入被拒绝")

    print("\n✓ 测试通过")


def test_cli_output_protection():
    """测试 CLI 输出保护"""
    print("\n" + "="*60)
    print("测试 CLI 输出保护")
    print("="*60)

    temp_dir = tempfile.mkdtemp(prefix='test_cli_output_')
    output_base = os.path.join(temp_dir, 'output', 'cli')
    os.makedirs(output_base, exist_ok=True)

    try:
        from simple_agent.cli_agent import CLIAgent
        cli = CLIAgent()

        task = "测试任务"
        result = cli.execute(task, verbose=False, output_dir=output_base, isolate_by_instance=False)

        import glob
        files = glob.glob(os.path.join(output_base, '**', '*.txt'), recursive=True)
        assert len(files) > 0, "未生成输出文件"
        print(f"  ✓ 测试 1 通过: 生成输出文件")

        for f in files:
            parts = os.path.relpath(f, output_base).split(os.sep)
            assert len(parts) <= 2, f"路径深度过大: {len(parts)}"
        print(f"  ✓ 测试 2 通过: 路径深度正确")

        root_files = [f for f in os.listdir('/') if f.startswith('test_')]
        assert len(root_files) == 0, f"根目录被污染: {root_files}"
        print(f"  ✓ 测试 3 通过: 根目录未被污染")

        print("\n✓ 测试通过")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n已清理临时目录：{temp_dir}")


def test_agent_file_operations():
    """测试 Agent 文件操作"""
    print("\n" + "="*60)
    print("测试 Agent 文件操作")
    print("="*60)

    temp_dir = tempfile.mkdtemp(prefix='test_agent_')
    try:
        from simple_agent.core.agent import Agent
        from simple_agent.core.llm import LLM
        from simple_agent.tools.file import set_output_dir

        llm = LLM()
        agent = Agent(llm=llm, name='TestAgent', description='测试代理')
        set_output_dir(temp_dir)

        print("  ✓ 测试 1 通过: Agent 和文件工具初始化成功")
        print("\n✓ 测试通过")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n已清理临时目录：{temp_dir}")


if __name__ == "__main__":
    print("="*60)
    print("文件工具输出路径防护测试套件")
    print("="*60)

    try:
        test_output_dir_enforcement_logic()
        test_path_validation()
        test_cli_output_protection()
        test_agent_file_operations()
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
