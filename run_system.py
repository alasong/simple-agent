#!/usr/bin/env python3
"""
运行AI驱动股市热点分析系统
"""

import subprocess
import sys
import os


def run_system():
    """运行系统"""
    print("🚀 启动AI驱动股市热点分析系统...")
    print("-" * 50)
    
    try:
        # 运行主程序
        result = subprocess.run([
            sys.executable, 'app.py', 
            '--output-dir', '.', 
            '--sectors', '固态电池', '半导体设备', 'AI算力',
            '--verbose'
        ], check=True, capture_output=True, text=True)
        
        print("✅ 系统运行成功！")
        print("\n📋 运行输出:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ 系统警告/错误信息:")
            print(result.stderr)
            
        # 检查输出文件是否存在
        print("\n📄 生成的文件:")
        files_to_check = ['report.html', 'report.json', 'visualization.png']
        for file in files_to_check:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"  ✅ {file} ({size} bytes)")
            else:
                print(f"  ❌ {file} (未找到)")
                
    except subprocess.CalledProcessError as e:
        print(f"❌ 系统运行失败: {e}")
        print(f"输出: {e.output}")
        print(f"错误: {e.stderr}")
    except FileNotFoundError:
        print("❌ 找不到Python解释器或app.py文件")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    run_system()