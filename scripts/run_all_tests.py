#!/usr/bin/env python3
"""
运行所有 Swarm 相关测试
"""
import subprocess
import sys


def run_test(script):
    """运行测试脚本"""
    print(f"\n{'='*70}")
    print(f"运行：{script}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(
        [sys.executable, script],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0


def main():
    print("\n" + "="*70)
    print(" " * 20 + "Swarm 测试套件")
    print("="*70)
    
    tests = [
        "tests/test_swarm.py",
        "tests/test_swarm_stage2.py",
        "tests/test_scaling.py",
    ]
    
    results = []
    for test in tests:
        success = run_test(test)
        results.append((test, success))
    
    # 汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    all_passed = True
    for test, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status}: {test}")
        if not success:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("所有测试通过！✓")
        return 0
    else:
        print("部分测试失败 ✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
