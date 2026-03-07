# 深度防护 - Agent 能力的代码质量保障系统

## 快速开始

### 1. 静态分析（快速检查）

```bash
# 检查单个文件
python scripts/deep_protection.py core/agent.py --no-agent

# 检查整个项目
python scripts/deep_protection.py --all --no-agent
```

### 2. Agent 深度审查

```bash
# 审查单个文件
python scripts/agent_review.py core/agent.py

# 审查所有文件
python scripts/agent_review.py --all

# 输出报告
python scripts/agent_review.py core/ -o review.txt
```

### 3. CLI 中使用

```bash
python cli.py

# 审查文件
/review core/agent.py

# 审查所有 Python 文件
/review --all

# 使用增强型 Agent
/enhanced plan_reflect 审查这个项目的代码质量
```

## 功能特性

### 🔒 安全性检查
- 硬编码密钥/密码检测
- 代码注入风险（eval, exec）
- 命令注入风险（os.system, subprocess）
- 反序列化漏洞（pickle）
- 弱加密算法（MD5, SHA1）

### 📊 质量评估
- 代码复杂度分析
- 函数长度检查
- 文件大小验证
- 错误处理完整性
- 资源泄漏检测

### 🎨 风格验证
- PEP8 规范检查
- 缩进和格式
- 文档字符串
- 命名约定
- 导入规范

### 📈 复杂度分析
- 圈复杂度计算
- 嵌套深度
- 参数数量
- 返回值复杂度

## 输出示例

```
================================================================================
深度防护检查报告
================================================================================

📄 文件：core/agent.py
--------------------------------------------------------------------------------
  🟡 📈 行 235: 函数复杂度过高：13（建议 < 10）
      建议：简化逻辑或拆分为多个函数
  
  🔴 🔒 行 45: 发现硬编码的密钥或密码
      代码：api_key = "YOUR_API_KEY_HERE"
      建议：使用环境变量或配置文件

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

## 完整文档

- 📖 [DEEP_PROTECTION.md](./DEEP_PROTECTION.md) - 详细使用指南
- 📊 [DEEP_PROTECTION_SUMMARY.md](./DEEP_PROTECTION_SUMMARY.md) - 集成总结
- 🧪 [test_deep_protection.sh](./test_deep_protection.sh) - 测试脚本

## 集成到工作流

### Git Pre-commit Hook

```bash
#!/bin/bash
python scripts/deep_protection.py --no-agent
if [ $? -ne 0 ]; then
    echo "❌ 深度防护检查失败"
    exit 1
fi
echo "✅ 深度防护检查通过"
```

### CI/CD 配置

```yaml
- name: Code Quality
  run: |
    python scripts/deep_protection.py --all --no-agent
    python scripts/agent_review.py --all
```

## 核心优势

1. **双层防护** - 静态分析 + AI 智能审查
2. **全面覆盖** - 安全性、质量、风格、复杂度
3. **灵活使用** - CLI、脚本、Git Hooks
4. **可扩展** - 易于添加新规则

## 使用建议

### 提交前
```bash
# 快速检查（<1 秒）
python scripts/deep_protection.py core/ --no-agent
```

### 合并前
```bash
# 完整审查（10-30 秒）
python scripts/agent_review.py feature.py
```

### 定期审查
```bash
# 每周质量报告
python scripts/deep_protection.py --all --json > weekly_report.json
```

---

**深度防护系统** - 基于 Agent 能力的智能代码质量保障 🚀
