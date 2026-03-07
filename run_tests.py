#!/usr/bin/env python3
"""
运行长目录名截断功能测试
"""

import subprocess
import sys

def run_test_script():
    """运行测试脚本"""
    try:
        print("正在运行长目录名截断功能测试...")
        result = subprocess.run([sys.executable, 'test_long_directory_names.py'], 
                              capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"返回码: {result.returncode}")
        
    except Exception as e:
        print(f"运行测试时出错: {e}")

if __name__ == "__main__":
    run_test_script()