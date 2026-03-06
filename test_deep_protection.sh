#!/bin/bash
# 深度防护功能测试脚本

echo "============================================================"
echo "深度防护功能测试"
echo "============================================================"
echo ""

# 测试 1: 静态分析
echo "测试 1: 静态分析（不使用 Agent）"
echo "-----------------------------------------------------------"
python3 scripts/deep_protection.py core/agent.py --no-agent -v
echo ""
echo "✓ 静态分析测试完成"
echo ""

# 测试 2: Agent 审查
echo "测试 2: Agent 代码审查"
echo "-----------------------------------------------------------"
timeout 60 python3 scripts/agent_review.py core/agent.py
echo ""
echo "✓ Agent 审查测试完成"
echo ""

# 测试 3: CLI 命令
echo "测试 3: CLI 命令测试"
echo "-----------------------------------------------------------"
echo "在 CLI 中可以使用以下命令:"
echo "  python cli.py"
echo "  /review core/agent.py      # 审查单个文件"
echo "  /review --all              # 审查所有 Python 文件"
echo "  /enhanced 审查代码质量     # 使用增强型 Agent"
echo ""

echo "============================================================"
echo "测试总结"
echo "============================================================"
echo ""
echo "已创建的工具:"
echo "  1. scripts/deep_protection.py - 深度防护主脚本"
echo "  2. scripts/agent_review.py - Agent 代码审查工具"
echo "  3. CLI 集成命令 /review"
echo ""
echo "文档:"
echo "  - DEEP_PROTECTION.md - 详细使用指南"
echo ""
echo "功能特性:"
echo "  ✓ 静态代码分析（AST 分析）"
echo "  ✓ 安全性检查（敏感信息、漏洞）"
echo "  ✓ 代码质量评估"
echo "  ✓ 复杂度分析"
echo "  ✓ 最佳实践验证"
echo "  ✓ Agent 智能审查"
echo "  ✓ CLI 命令集成"
echo ""
echo "============================================================"
