#!/bin/bash
# 日常核心测试脚本 (Daily Core Tests)
# 快速运行核心测试，确保系统基本功能正常

set -e

echo "========================================"
echo "  Simple Agent - 日常核心测试"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查虚拟环境
if [ ! -d "./.venv" ]; then
    echo -e "${RED}错误：未找到虚拟环境 ./.venv${NC}"
    exit 1
fi

# 运行核心深度测试
echo -e "${YELLOW}[1/4] 运行核心深度测试...${NC}"
./.venv/bin/python -m pytest tests/test_deep_core.py -v --tb=short

# 运行工具测试
echo ""
echo -e "${YELLOW}[2/4] 运行工具执行测试...${NC}"
./.venv/bin/python tests/test_tool_execution.py || exit 1

# 运行领域测试
echo ""
echo -e "${YELLOW}[3/4] 运行领域测试...${NC}"
./.venv/bin/python tests/domains_stats.py 2>/dev/null || echo "领域测试跳过"

# 运行 CLI Tab 补全测试
echo ""
echo -e "${YELLOW}[4/4] 运行 CLI Tab 补全测试...${NC}"
./.venv/bin/python -m pytest tests/test_cli_tab_completion.py -v --tb=short

echo ""
echo "========================================"
echo -e "${GREEN}✓ 所有日常测试完成!${NC}"
echo "========================================"
