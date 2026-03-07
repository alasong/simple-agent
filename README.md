# 长目录名截断功能测试

此项目用于测试操作系统对长目录名的处理能力，包括：

- 创建超长目录名
- 嵌套长目录结构
- 系统路径长度限制检测

## 文件说明

- `test_long_directory_names.py` - 主测试脚本
- `run_tests.py` - 运行测试的辅助脚本

## 功能特性

1. 测试不同长度的目录名创建
2. 验证在长目录中创建和访问文件的能力
3. 测试嵌套长目录结构
4. 检测系统的路径长度限制

## 使用方法

```bash
python test_long_directory_names.py
```

或者

```bash
python run_tests.py
```