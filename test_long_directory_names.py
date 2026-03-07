#!/usr/bin/env python3
"""
测试长目录名截断功能
创建具有超长名称的目录结构，验证系统如何处理长目录名
"""

import os
import shutil
import tempfile
import sys
from pathlib import Path


def create_long_directory_path(base_path, length=300):
    """
    创建一个具有指定长度名称的目录路径
    
    Args:
        base_path (str): 基础路径
        length (int): 目录名总长度
    
    Returns:
        str: 创建的目录路径
    """
    # 计算需要的字符数量
    if len(base_path) >= length:
        raise ValueError(f"Base path already longer than {length} characters")
    
    remaining_length = length - len(base_path) - 6  # 减去 "/dir_" 和一些额外空间
    long_part = "very_long_directory_name_part_" * ((remaining_length // 30) + 1)
    long_part = long_part[:remaining_length]
    
    full_path = os.path.join(base_path, f"dir_{long_part}")
    return full_path


def test_long_directory_creation():
    """测试创建长目录名的功能"""
    print("开始测试长目录名创建...")
    
    # 在临时目录中进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时目录: {temp_dir}")
        
        # 测试不同长度的目录名
        test_lengths = [100, 200, 255, 260, 300, 400]
        
        for length in test_lengths:
            print(f"\n--- 测试长度: {length} ---")
            
            try:
                # 创建长目录路径
                long_dir_path = create_long_directory_path(temp_dir, length)
                print(f"目标路径长度: {len(long_dir_path)}")
                
                # 尝试创建目录
                os.makedirs(long_dir_path, exist_ok=True)
                print(f"✓ 成功创建长目录: {long_dir_path[:100]}...")
                
                # 验证目录是否存在
                if os.path.exists(long_dir_path):
                    print("✓ 目录存在验证通过")
                    
                    # 测试在长目录中创建文件
                    test_file = os.path.join(long_dir_path, "test_file.txt")
                    with open(test_file, 'w') as f:
                        f.write("测试内容")
                    print("✓ 在长目录中创建文件成功")
                    
                    # 检查文件是否确实被创建
                    if os.path.exists(test_file):
                        print("✓ 文件存在验证通过")
                    
                    # 清理测试文件
                    os.remove(test_file)
                    
                else:
                    print(f"✗ 目录不存在")
                
                # 清理目录
                shutil.rmtree(long_dir_path)
                
            except OSError as e:
                print(f"✗ OS错误 (长度{length}): {e}")
            except Exception as e:
                print(f"✗ 其他错误 (长度{length}): {e}")


def test_nested_long_directories():
    """测试嵌套的长目录结构"""
    print("\n\n开始测试嵌套长目录结构...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时目录: {temp_dir}")
        
        # 创建多层嵌套的长目录
        try:
            base_path = temp_dir
            for i in range(5):
                # 每层都使用相对较长的名称
                layer_name = f"layer_{i}_{'x' * 30}"
                layer_path = os.path.join(base_path, layer_name)
                
                print(f"创建第{i+1}层目录: {layer_path}")
                os.makedirs(layer_path, exist_ok=True)
                
                # 创建一个测试文件来验证这一层
                test_file = os.path.join(layer_path, f"test_file_{i}.txt")
                with open(test_file, 'w') as f:
                    f.write(f"Layer {i} test content")
                
                base_path = layer_path
            
            print("✓ 成功创建5层嵌套长目录")
            
            # 验证最深层目录中的文件
            deepest_file = os.path.join(base_path, "deepest_test.txt")
            with open(deepest_file, 'w') as f:
                f.write("Deepest level test")
            
            if os.path.exists(deepest_file):
                print("✓ 最深层目录访问成功")
            
            # 清理整个嵌套结构
            root_layer_path = os.path.join(temp_dir, "layer_0_*")
            shutil.rmtree(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
            
        except OSError as e:
            print(f"✗ 嵌套目录创建失败: {e}")
        except Exception as e:
            print(f"✗ 其他错误: {e}")


def check_system_limits():
    """检查系统的路径长度限制"""
    print("\n\n检查系统路径长度限制...")
    
    # 不同操作系统的典型限制
    limits_info = {
        "Linux": {"PATH_MAX": 4096, "FILENAME_MAX": 255},
        "Windows": {"PATH_MAX": 260, "FILENAME_MAX": 255, "Extended": "Up to 32767 with long path enabled"},
        "macOS": {"PATH_MAX": 1024, "FILENAME_MAX": 255}
    }
    
    import platform
    system = platform.system()
    print(f"当前系统: {system}")
    
    if system in limits_info:
        print(f"{system} 路径长度限制:")
        for key, value in limits_info[system].items():
            print(f"  {key}: {value}")
    else:
        print("未知系统类型")
    
    # 尝试确定实际限制
    print("\n尝试确定实际路径长度限制...")
    with tempfile.TemporaryDirectory() as temp_dir:
        max_success = 0
        max_test = 500
        
        for length in range(100, max_test, 50):
            try:
                long_dir_path = create_long_directory_path(temp_dir, length)
                os.makedirs(long_dir_path, exist_ok=True)
                max_success = length
                
                # 清理
                shutil.rmtree(long_dir_path)
                
                print(f"✓ 长度 {length}: 成功")
            except OSError:
                print(f"✗ 长度 {length}: 失败")
                break
        
        print(f"最大成功创建的路径长度约为: {max_success}")


def main():
    """主函数"""
    print("="*60)
    print("长目录名截断功能测试")
    print("="*60)
    
    try:
        test_long_directory_creation()
        test_nested_long_directories()
        check_system_limits()
        
        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()