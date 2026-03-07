# 深度防护脚本使用指南

## 概述

基于 Agent 能力的深度防护系统，结合静态分析和智能审查，提供全面的代码质量检查。

## 工具列表

### 1. deep_protection.py - 深度防护主脚本

**功能**:
- 静态代码分析（AST 分析）
- Agent 智能审查
- 安全性检查
- 代码质量评估
- 复杂度分析
- 最佳实践验证

**使用**:
```bash
# 检查单个文件
python scripts/deep_protection.py core/agent.py

# 检查所有 Python 文件
python scripts/deep_protection.py --all

# 输出 JSON 报告
python scripts/deep_protection.py --all --json > report.json

# 详细模式
python scripts/deep_protection.py core/ -v

# 仅静态分析（不使用 Agent）
python scripts/deep_protection.py core/ --no-agent
```

**检查项目**:

#### 静态分析
- ✓ 文件大小检查（>500 行警告）
- ✓ 编码问题检查
- ✓ 圈复杂度分析（>10 警告）
- ✓ 函数长度检查（>50 行警告）
- ✓ 导入规范检查
- ✓ 文档字符串检查

#### 安全性检查
- 🔒 `eval()` / `exec()` 使用
- 🔒 `os.system()` 命令注入
- 🔒 `shell=True` 风险
- 🔒 `pickle.load()` 反序列化
- 🔒 弱哈希算法（MD5/SHA1）
- 🔒 硬编码密钥/密码

#### 代码异味
- 📝 超长行（>120 字符）
- 📝 TODO/FIXME 注释
- 📝 空函数
- 📝 未使用的导入

#### 风格检查
- 🎨 缩进规范（4 空格）
- 🎨 空行规范
- 🎨 命名约定

### 2. agent_review.py - Agent 代码审查工具

**功能**:
- 使用 EnhancedAgent 进行智能审查
- 深度代码质量分析
- 安全性评估
- 最佳实践建议
- 总体评分

**使用**:
```bash
# 审查单个文件
python scripts/agent_review.py core/agent.py

# 审查所有 Python 文件
python scripts/agent_review.py --all

# 输出报告到文件
python scripts/agent_review.py core/ -o review_report.txt

# 详细模式
python scripts/agent_review.py core/ -v
```

**输出示例**:
```
================================================================================
Agent 代码审查报告
================================================================================
文件数量：1

📋 文件信息
- 文件名：agent.py
- 路径：core/agent.py
- 大小：5234 字节

### 🔍 审查结果

🔴 严重问题（必须修复）
1. 第 45 行：发现硬编码的 API 密钥
   建议：使用环境变量存储敏感信息

🟡 改进建议（建议修复）
1. 第 78 行：函数过长（65 行）
   建议：拆分为多个小函数
2. 第 120 行：缺少文档字符串
   建议：添加函数说明

### 📊 总体评分
- 安全性：8/10
- 质量：7/10
- 可维护性：8/10
- 总体：7.7/10
```

### 3. CLI 集成命令

**在 CLI 中使用**:
```bash
python cli.py

# 审查单个文件
[CLI Agent] 你：/review core/agent.py

# 审查所有 Python 文件
[CLI Agent] 你：/review --all

# 使用增强型 Agent 审查
[CLI Agent] 你：/enhanced plan_reflect 审查这个项目的代码质量
```

## 检查维度

### 1. 安全性 (Security)

| 检查项 | 严重程度 | 说明 |
|--------|---------|------|
| 硬编码密钥 | 🔴 Critical | 密码、API 密钥等敏感信息 |
| 代码注入 | 🔴 Critical | eval(), exec(), os.system() |
| 命令注入 | 🔴 Critical | subprocess shell=True |
| 反序列化 | 🔴 Critical | pickle.load() |
| 弱加密 | 🟡 Warning | MD5, SHA1 |
| 随机数 | 🟡 Warning | random vs secrets |

### 2. 代码质量 (Quality)

| 检查项 | 严重程度 | 说明 |
|--------|---------|------|
| 语法错误 | 🔴 Critical | Python 语法问题 |
| 圈复杂度 | 🟡 Warning | >10 表示复杂度过高 |
| 函数长度 | 🟡 Warning | >50 行建议拆分 |
| 文件长度 | 🟡 Warning | >500 行建议拆分 |
| 错误处理 | 🟡 Warning | 缺少异常处理 |

### 3. 代码风格 (Style)

| 检查项 | 严重程度 | 说明 |
|--------|---------|------|
| 缩进 | 🔵 Info | 应该使用 4 空格 |
| 行长 | 🔵 Info | 建议 <120 字符 |
| 文档 | 🔵 Info | 缺少 docstring |
| 导入 | 🔵 Info | 使用 * 导入 |

### 4. 复杂度 (Complexity)

| 检查项 | 说明 |
|--------|------|
| 圈复杂度 | 控制流复杂度 |
| 嵌套深度 | 代码嵌套层数 |
| 参数数量 | 函数参数个数 |
| 返回复杂度 | 返回值复杂度 |

## 集成到 Git Hooks

### Pre-commit Hook 集成

编辑 `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "🔒 [Pre-commit] 运行深度防护检查..."

# 运行静态分析
python scripts/deep_protection.py --no-agent

# 如果有严重问题，阻止提交
if [ $? -ne 0 ]; then
    echo "❌ 深度防护检查失败"
    exit 1
fi

echo "✅ 深度防护检查通过"
```

### Pre-push Hook 集成

编辑 `.git/hooks/pre-push`:

```bash
#!/bin/bash
set -e

echo "🔒 [Pre-push] 运行完整代码审查..."

# 运行 Agent 审查（仅检查修改的文件）
python scripts/agent_review.py $(git diff --name-only HEAD^ HEAD | grep '\.py$')

echo "✅ 代码审查通过"
```

## 使用场景

### 场景 1: 提交前检查

```bash
# 快速检查（静态分析）
python scripts/deep_protection.py core/ --no-agent

# 或使用 CLI
python cli.py
/review core/
```

### 场景 2: Code Review

```bash
# 完整审查（包含 Agent 分析）
python scripts/agent_review.py feature.py -v

# 生成报告
python scripts/agent_review.py feature.py -o review.txt
```

### 场景 3: 项目质量评估

```bash
# 检查整个项目
python scripts/deep_protection.py --all --json > quality_report.json

# 分析结果
python -c "
import json
with open('quality_report.json') as f:
    data = json.load(f)
    print(f'文件数：{data[\"summary\"][\"total_files\"]}')
    print(f'严重问题：{data[\"summary\"][\"critical\"]}')
    print(f'警告：{data[\"summary\"][\"warning\"]}')
"
```

### 场景 4: 持续集成

```yaml
# .github/workflows/code_quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run deep protection
        run: python scripts/deep_protection.py --all --no-agent
      
      - name: Agent review
        run: python scripts/agent_review.py --all
```

## 配置选项

### 深度防护配置

创建 `.deep_protection.json`:

```json
{
  "exclude": [".venv", "venv", "__pycache__", "tests"],
  "max_line_length": 120,
  "max_function_length": 50,
  "max_complexity": 10,
  "max_file_size": 500,
  "enable_agent_review": true,
  "output_format": "text"
}
```

### Agent 配置

在 `config.json` 中添加:

```json
{
  "code_review": {
    "model": "qwen3.5-plus",
    "temperature": 0.3,
    "max_tokens": 4000,
    "focus_areas": ["security", "quality", "performance"]
  }
}
```

## 输出格式

### 文本格式（默认）

```
================================================================================
深度防护检查报告
================================================================================

📄 文件：core/agent.py
--------------------------------------------------------------------------------
  🔴 🔒  行 45: 发现硬编码的密钥或密码
      代码：api_key = "YOUR_API_KEY_HERE"
      建议：使用环境变量或配置文件

  🟡 📊  行 78: 函数 'process_data' 复杂度过高：15（建议 < 10）
      建议：简化逻辑或拆分为多个函数

================================================================================
总结
================================================================================
检查文件数：5
总问题数：12
  🔴 严重：2
  🟡 警告：7
  🔵 提示：3
================================================================================

⚠️  检查通过：存在警告
```

### JSON 格式

```json
{
  "files": [
    {
      "file": "core/agent.py",
      "success": false,
      "metrics": {
        "lines": 234,
        "functions": 12,
        "classes": 3
      },
      "issues": [
        {
          "line": 45,
          "severity": "critical",
          "category": "security",
          "message": "发现硬编码的密钥或密码",
          "suggestion": "使用环境变量或配置文件"
        }
      ]
    }
  ],
  "summary": {
    "total_files": 5,
    "total_issues": 12,
    "critical": 2,
    "warning": 7,
    "info": 3
  }
}
```

## 最佳实践

### 1. 定期审查

```bash
# 每周运行一次完整审查
0 0 * * 0 python scripts/deep_protection.py --all --json > weekly_report.json
```

### 2. 渐进式改进

1. **第一阶段**: 修复所有 🔴 严重问题
2. **第二阶段**: 减少 🟡 警告数量
3. **第三阶段**: 优化 🔵 提示信息

### 3. 团队规范

- 新代码必须通过深度防护检查
- 严重问题必须修复才能合并
- 警告问题应该有改进计划

### 4. 持续监控

```bash
# 生成趋势报告
python scripts/generate_trend.py
```

## 故障排除

### 问题 1: Agent 审查失败

**错误**: `ConnectionError`

**解决**: 
- 检查网络连接
- 检查 LLM 配置
- 使用 `--no-agent` 仅进行静态分析

### 问题 2: 内存不足

**错误**: `MemoryError`

**解决**:
- 减少检查的文件数量
- 增加系统内存
- 分批检查

### 问题 3: 误报

**解决**:
- 在配置中添加排除规则
- 使用 `# noqa` 注释标记
- 向 Agent 提供更详细的上下文

## 性能优化

### 加速建议

1. **缓存结果**
   ```bash
   python scripts/deep_protection.py --cache
   ```

2. **并行处理**
   ```bash
   python scripts/deep_protection.py --parallel 4
   ```

3. **增量检查**
   ```bash
   python scripts/deep_protection.py --incremental
   ```

## 扩展开发

### 添加自定义检查

```python
from deep_protection import CodeAnalyzer, Issue

class CustomAnalyzer(CodeAnalyzer):
    def _check_custom(self, report, content, lines):
        # 添加自定义检查逻辑
        if 'bad_pattern' in content:
            report.add_issue(Issue(
                file=report.file,
                line=0,
                severity="warning",
                category="quality",
                message="发现不良模式"
            ))
```

### 添加新的 Agent 技能

```python
from core.skill_learning import Skill

custom_skill = Skill(
    name="性能分析",
    description="分析代码性能问题",
    trigger_pattern=r"性能 | 优化 | 效率",
    prompt_template="你是性能优化专家...",
    success_rate=0.85
)
skill_library.skills["性能分析"] = custom_skill
```

## 总结

深度防护系统提供了多层次的代码质量保障：

1. **静态分析** - 快速、准确的语法和风格检查
2. **Agent 审查** - 智能、深度的质量和安全检查
3. **CLI 集成** - 方便的交互式审查
4. **Git Hooks** - 自动化的提交防护

通过结合使用这些工具，可以显著提升代码质量和安全性。
