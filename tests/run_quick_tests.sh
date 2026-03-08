#!/bin/bash
# 快速测试脚本 (Quick Tests)
# 在 5 分钟内完成核心功能验证

set -e

echo "========================================"
echo "  Simple Agent - 快速测试 (5 分钟)"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查虚拟环境
if [ ! -d "./venv" ]; then
    echo -e "${RED}错误：未找到虚拟环境 ./venv${NC}"
    exit 1
fi

# 运行最快的核心测试
echo -e "${YELLOW}运行核心组件测试...${NC}"
./venv/bin/python -m pytest \
    tests/test_deep_core.py \
    -v \
    --tb=short \
    -x \
    -q

echo ""
echo "========================================"
echo -e "${GREEN}✓ 快速测试完成!${NC}"
echo "========================================"
