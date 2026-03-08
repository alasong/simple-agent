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
if [ ! -d "./venv" ]; then
    echo -e "${RED}错误：未找到虚拟环境 ./venv${NC}"
    exit 1
fi

# 运行核心深度测试
echo -e "${YELLOW}[1/3] 运行核心深度测试...${NC}"
./venv/bin/python -m pytest tests/test_deep_core.py -v --tb=short

# 运行工具测试
echo ""
echo -e "${YELLOW}[2/3] 运行工具执行测试...${NC}"
./venv/bin/python -m pytest tests/test_tool_execution.py -v --tb=short -x

# 运行领域测试
echo ""
echo -e "${YELLOW}[3/3] 运行领域测试...${NC}"
./venv/bin/python -m pytest tests/test_domains.py -v --tb=short -x

echo ""
echo "========================================"
echo -e "${GREEN}✓ 所有日常测试完成!${NC}"
echo "========================================"
