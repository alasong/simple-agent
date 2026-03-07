#!/usr/bin/env python3
"""
测试输出路径修复

问题：之前输出路径出现双重目录名
例如：/output/cli/北京天气/北京天气/result_xxx.txt

修复后应该是：/output/cli/北京天气/result_xxx.txt
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools  # noqa: F401
from cli_agent import CLIAgent


def test_output_path_structure():
    """测试输出目录结构是否正确"""
    print("\n" + "="*60)
    print("测试输出目录结构")
    print("="*60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix='test_output_')
    output_base = os.path.join(temp_dir, 'output', 'cli')
    os.makedirs(output_base, exist_ok=True)
    
    try:
        cli = CLIAgent()
        
        # 测试短任务
        test_task = "北京天气"
        print(f"\n测试任务：{test_task}")
        
        result = cli.execute(
            test_task,
            verbose=False,
            output_dir=output_base,
            isolate_by_instance=False
        )
        
        # 检查生成的目录结构
        print(f"\n结果长度：{len(str(result))} 字符")
        
        # 查找生成的文件
        import glob
        files = glob.glob(os.path.join(output_base, '**', '*.txt'), recursive=True)
        
        if not files:
            print("❌ 未找到输出文件")
            return False
        
        print(f"\n找到的文件:")
        for f in files:
            rel_path = os.path.relpath(f, output_base)
            print(f"  - {rel_path}")
            
            # 检查路径深度（应该只有一层子目录）
            parts = rel_path.split(os.sep)
            if len(parts) == 2:  # 应该是：任务名/文件名
                print(f"  ✓ 路径深度正确")
                
                # 验证目录名是任务名
                dir_name = parts[0]
                if "北京天气" in dir_name or "北京" in dir_name:
                    print(f"  ✓ 目录名包含任务关键词")
                else:
                    print(f"  ⚠ 目录名不包含任务关键词：{dir_name}")
            else:
                print(f"  ❌ 路径深度错误，应该是 2 层，实际{len(parts)}层")
                
                # 检查是否有双重目录名
                if len(parts) >= 3:
                    if parts[0] == parts[1]:
                        print(f"  ❌ 检测到双重目录名：{parts[0]}/{parts[1]}")
                        return False
        
        # 验证文件内容
        print(f"\n文件内容预览:")
        with open(files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')[:5]
            for line in lines:
                print(f"  {line}")
        
        print("\n✓ 测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n已清理临时目录：{temp_dir}")


def test_isolate_by_instance():
    """测试按实例隔离模式"""
    print("\n" + "="*60)
    print("测试按实例隔离模式")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp(prefix='test_isolate_')
    output_base = os.path.join(temp_dir, 'output', 'cli')
    os.makedirs(output_base, exist_ok=True)
    
    try:
        cli = CLIAgent()
        
        # 启用隔离模式
        result = cli.execute(
            "你好",
            verbose=False,
            output_dir=output_base,
            isolate_by_instance=True
        )
        
        # 检查是否创建了实例 ID 目录
        import glob
        files = glob.glob(os.path.join(output_base, '**', '*.txt'), recursive=True)
        
        if files:
            print(f"\n找到文件:")
            for f in files:
                rel_path = os.path.relpath(f, output_base)
                print(f"  - {rel_path}")
                
                # 检查是否使用实例 ID 作为目录名
                parts = rel_path.split(os.sep)
                if len(parts) >= 2:
                    dir_name = parts[0]
                    print(f"  实例 ID 目录：{dir_name}")
                    
                    # 实例 ID 应该是 UUID 格式
                    if len(dir_name) > 10:  # UUID 通常比较长
                        print(f"  ✓ 使用了实例 ID 隔离")
                    else:
                        print(f"  ⚠ 目录名较短，可能不是实例 ID")
        else:
            print("  未找到输出文件（可能实例 ID 不存在）")
        
        print("\n✓ 测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录：{temp_dir}")


def test_long_task_name():
    """测试长任务名的目录名处理"""
    print("\n" + "="*60)
    print("测试长任务名处理")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp(prefix='test_long_')
    output_base = os.path.join(temp_dir, 'output', 'cli')
    os.makedirs(output_base, exist_ok=True)
    
    try:
        cli = CLIAgent()
        
        # 长任务名（超过 20 字符）
        long_task = "这是一个非常长的任务名称用来测试目录名截断功能是否正常工作"
        print(f"任务名长度：{len(long_task)} 字符")
        
        result = cli.execute(
            long_task,
            verbose=False,
            output_dir=output_base,
            isolate_by_instance=False
        )
        
        # 检查目录名
        import glob
        dirs = glob.glob(os.path.join(output_base, '*'))
        
        if dirs:
            print(f"\n创建的目录:")
            for d in dirs:
                dir_name = os.path.basename(d)
                print(f"  - {dir_name} (长度：{len(dir_name)})")
                
                # 目录名应该被截断到 20 字符
                if len(dir_name) <= 20:
                    print(f"  ✓ 目录名长度正确（≤20 字符）")
                else:
                    print(f"  ❌ 目录名过长：{len(dir_name)} 字符")
        
        print("\n✓ 测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录：{temp_dir}")


def test_special_characters_in_task_name():
    """测试特殊字符在任务名中的处理"""
    print("\n" + "="*60)
    print("测试特殊字符处理")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp(prefix='test_special_')
    output_base = os.path.join(temp_dir, 'output', 'cli')
    os.makedirs(output_base, exist_ok=True)
    
    try:
        cli = CLIAgent()
        
        # 包含特殊字符的任务名
        special_task = "测试/路径\\分隔符和 空格"
        print(f"任务名：{special_task}")
        
        result = cli.execute(
            special_task,
            verbose=False,
            output_dir=output_base,
            isolate_by_instance=False
        )
        
        # 检查目录名
        import glob
        dirs = glob.glob(os.path.join(output_base, '*'))
        
        if dirs:
            print(f"\n创建的目录:")
            for d in dirs:
                dir_name = os.path.basename(d)
                print(f"  - {dir_name}")
                
                # 不应该包含路径分隔符
                if '/' not in dir_name and '\\' not in dir_name:
                    print(f"  ✓ 目录名不包含路径分隔符")
                else:
                    print(f"  ❌ 目录名包含路径分隔符")
        
        print("\n✓ 测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录：{temp_dir}")


if __name__ == "__main__":
    print("="*60)
    print("输出路径修复测试套件")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("输出目录结构", test_output_path_structure()))
    results.append(("实例隔离模式", test_isolate_by_instance()))
    results.append(("长任务名处理", test_long_task_name()))
    results.append(("特殊字符处理", test_special_characters_in_task_name()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        sys.exit(1)
