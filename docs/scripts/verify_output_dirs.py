#!/usr/bin/env python3
"""
验证输出目录配置
确保所有输出都保存到 output/ 目录，不会污染根目录
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import get_config


def check_output_dirs():
    """检查输出目录配置"""
    print("="*60)
    print("输出目录配置检查")
    print("="*60)
    
    config = get_config()
    
    # 检查关键配置
    dirs = {
        'output': config.get('directories.output', '未设置'),
        'output_root': config.get('directories.output_root', '未设置'),
        'cli_output': config.get('directories.cli_output', '未设置'),
        'swarm_output': config.get('directories.swarm_output', '未设置'),
        'generated_code': config.get('directories.generated_code', '未设置'),
        'reports': config.get('directories.reports', '未设置'),
    }
    
    print("\n📁 输出目录配置:")
    for name, path in dirs.items():
        exists = "✅" if Path(path).exists() or Path(path).parent.exists() else "❌"
        print(f"  {exists} {name:20} = {path}")
    
    # 检查根目录的整洁性
    print("\n🧹 根目录检查:")
    root_files = []
    for f in Path('.').glob('*'):
        if f.is_file() and f.suffix in ['.py', '.md', '.txt', '.log']:
            if 'README' not in str(f) and 'LICENSE' not in str(f):
                root_files.append(str(f))
    
    if root_files:
        print(f"  ⚠️  发现 {len(root_files)} 个文件（可能污染根目录）:")
        for f in root_files[:5]:
            print(f"     - {f}")
        if len(root_files) > 5:
            print(f"     ... 还有 {len(root_files) - 5} 个文件")
    else:
        print(f"  ✅ 根目录保持整洁")
    
    # 检查 output 目录
    print("\n📂 Output 目录结构:")
    output_dirs = ['output/cli', 'output/swarm', 'output/generated', 'output/reports']
    for dir_path in output_dirs:
        exists = "✅" if Path(dir_path).exists() else "❌"
        print(f"  {exists} {dir_path}")
    
    print("\n" + "="*60)
    print("✅ 配置检查完成！")
    print("="*60)


def test_cli_output():
    """测试 CLI 输出目录"""
    print("\n🧪 测试 CLI 输出目录...")
    
    # 导入 CLI 模块
    import cli
    print(f"  CLI OUTPUT_DIR: {cli.OUTPUT_DIR}")
    print(f"  CLI OUTPUT_ROOT: {cli.OUTPUT_ROOT}")
    
    # 检查目录是否存在
    if cli.OUTPUT_DIR:
        os.makedirs(cli.OUTPUT_DIR, exist_ok=True)
        print(f"  ✅ 已创建目录：{cli.OUTPUT_DIR}")


if __name__ == "__main__":
    check_output_dirs()
    test_cli_output()
    
    print("\n💡 提示:")
    print("  - 所有生成的文件都会保存到 output/ 目录")
    print("  - 使用 output_manager.py 可以管理输出文件")
    print("  - 查看 docs/OUTPUT_DIRECTORY.md 了解更多详情")
