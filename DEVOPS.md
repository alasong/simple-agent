# Simple Agent DevOps 防护系统

## 概述

本项目已配置完整的 DevOps 防护系统，包括：

- **Pre-commit Hook**: Commit 时自动检查
- **Pre-push Hook**: Push 前运行测试
- **Daily Test Script**: 日常测试脚本

## 安装

Hook 已自动安装到 `.git/hooks/` 目录，无需额外配置。

如需手动安装：

```bash
# 复制 hook 文件
cp .git/hooks/pre-commit .git/hooks/pre-commit.local
cp .git/hooks/pre-push .git/hooks/pre-push.local
```

## Pre-commit Hook 功能

### 1. 敏感信息检测
检测以下模式：
- 密码 (`password=...`)
- 密钥 (`secret=...`, `api_key=...`, `token=...`)
- AWS Access Key

### 2. Python 语法检查
编译检查所有 Python 文件

### 3. 文件大小检查
警告超过 1MB 的文件

### 4. TODO 标记统计
统计代码中的 TODO/FIXME 数量

## Pre-push Hook 功能

### 1. 分支保护
对 main/master/production 分支发出警告

### 2. 单元测试
运行 `tests/test_stage1.py`

### 3. 未提交更改检查
提示有未提交的更改

## 日常测试脚本

```bash
# 运行日常测试
./scripts/daily_test.sh

# 或
bash scripts/daily_test.sh
```

测试项目：
1. Python 语法检查（排除已知问题文件）
2. 阶段 1 单元测试
3. 核心模块导入测试

## 输出示例

```
======================================
  日常测试脚本
======================================
1. Python 语法检查...
  ✓ __init__.py
  ✓ agent.py
  ✓ agent_enhanced.py
  ...
2. 单元测试...
✓ EnhancedMemory 测试通过
✓ SkillLibrary 测试通过
✓ ReflectionLoop 结构验证通过
3. 导入测试...
✅ 所有测试通过
```

## 自定义配置

### 修改敏感信息检测模式

编辑 `.git/hooks/pre-commit`，修改 `SENSITIVE_PATTERNS` 数组。

### 修改保护分支

编辑 `.git/hooks/pre-push`，修改 `PROTECTED_BRANCHES` 数组。

### 添加新的测试项目

编辑 `scripts/daily_test.sh`，添加新的测试步骤。

## 故障排除

### Hook 不执行

检查执行权限：
```bash
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push
```

### 测试失败

查看详细错误信息：
```bash
python3 tests/test_stage1.py
```

### 跳过 Hook

紧急情况可跳过 Hook（不推荐）：
```bash
git commit -m "message" --no-verify
git push --no-verify
```

## 最佳实践

1. **每次提交前**: 确保能通过 pre-commit 检查
2. **每天运行**: 使用 `daily_test.sh` 进行日常测试
3. **代码审查**: 保护分支的提交需要人工审查
4. **定期更新**: 根据项目需求更新检查规则

## 文件结构

```
.git/hooks/
├── pre-commit          # Commit 防护
└── pre-push            # Push 防护

scripts/
└── daily_test.sh       # 日常测试

tests/
└── test_stage1.py      # 单元测试
```
