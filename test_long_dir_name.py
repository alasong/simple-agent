#!/usr/bin/env python3
"""
测试超长目录名截断功能
"""

import os
import sys
import tempfile
from pathlib import Path


def create_directory_with_long_name(base_path, long_name):
    """
    创建带有超长名称的目录
    
    Args:
        base_path (str): 基础路径
        long_name (str): 超长目录名称
    
    Returns:
        tuple: (成功状态, 目录路径, 实际创建的名称)
    """
    try:
        full_path = os.path.join(base_path, long_name)
        
        # 尝试创建目录
        os.makedirs(full_path, exist_ok=True)
        
        # 检查目录是否实际存在
        if os.path.exists(full_path):
            return True, full_path, os.path.basename(full_path)
        else:
            # 如果目录不存在，可能是因为名称被截断了
            parent_dir = os.path.dirname(full_path)
            all_dirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
            
            # 查找最相似的目录名
            for dir_name in all_dirs:
                if long_name[:min(len(long_name), len(dir_name))] in dir_name or \
                   dir_name[:min(len(long_name), len(dir_name))] in long_name:
                    return True, os.path.join(parent_dir, dir_name), dir_name
            
            return False, full_path, None
            
    except OSError as e:
        print(f"创建目录失败: {e}")
        return False, full_path, None


def get_file_system_info(path):
    """
    获取文件系统的相关信息
    """
    try:
        # 获取文件系统类型和限制信息
        statvfs_result = os.statvfs(path)
        max_filename_length = statvfs_result.f_namemax
        
        return {
            'max_filename_length': max_filename_length,
            'block_size': statvfs_result.f_bsize
        }
    except Exception as e:
        print(f"无法获取文件系统信息: {e}")
        return {}


def main():
    # 要测试的超长目录名
    long_dir_name = '这是一个非常长的任务名称用来测试目录名截断功能是否正常工作'
    
    print(f"原始目录名长度: {len(long_dir_name)} 字符")
    print(f"原始目录名: {long_dir_name}")
    
    # 获取当前工作目录作为基础路径
    base_path = os.getcwd()
    
    # 或者使用临时目录进行测试（更安全）
    base_path = tempfile.gettempdir()
    print(f"在基础路径下创建目录: {base_path}")
    
    # 获取文件系统信息
    fs_info = get_file_system_info(base_path)
    if fs_info:
        print(f"文件系统最大文件名长度: {fs_info['max_filename_length']} 字节")
    
    # 创建带长名称的目录
    success, created_path, actual_name = create_directory_with_long_name(base_path, long_dir_name)
    
    if success:
        print(f"✓ 目录创建成功")
        print(f"  完整路径: {created_path}")
        print(f"  实际目录名: {actual_name}")
        print(f"  实际目录名长度: {len(actual_name)} 字符")
        
        if actual_name != long_dir_name:
            print("  注意: 目录名与原始名称不匹配，可能发生了截断或转换")
            print(f"  原始名称: {long_dir_name}")
            print(f"  实际名称: {actual_name}")
            
            # 比较两个名称的差异
            if len(actual_name) < len(long_dir_name):
                print("  确认发生了截断")
            else:
                print("  可能发生了字符编码转换")
        else:
            print("  目录名与原始名称完全一致")
    else:
        print("✗ 目录创建失败")
    
    # 清理 - 删除创建的目录
    if success and os.path.exists(created_path):
        try:
            # 先检查目录是否为空，如果非空则清空
            if os.listdir(created_path):
                print("目录非空，正在清空...")
                for item in os.listdir(created_path):
                    item_path = os.path.join(created_path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
            
            os.rmdir(created_path)
            print(f"已清理测试目录: {created_path}")
        except Exception as e:
            print(f"清理目录时出错: {e}")
    
    print("\n测试完成")


if __name__ == "__main__":
    main()