#!/bin/bash
# 完整测试套件脚本 (Full Test Suite)
# 运行所有测试，包含深度测试和集成测试

set -e

echo "========================================"
echo "  Simple Agent - 完整测试套件"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查虚拟环境
if [ ! -d "./venv" ]; then
    echo -e "${RED}错误：未找到虚拟环境 ./venv${NC}"
    exit 1
fi

# 统计
TOTAL_START=$(date +%s)
PASSED=0
FAILED=0
SKIPPED=0

# 测试函数
run_test_suite() {
    local suite_name=$1
    local test_pattern=$2

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  运行：${suite_name}${NC}"
    echo -e "${BLUE}========================================${NC}"

    set +e
    OUTPUT=$(./venv/bin/python -m pytest $test_pattern -v --tb=short 2>&1)
    EXIT_CODE=$?
    set -e

    echo "$OUTPUT" | tail -20

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ ${suite_name} 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ ${suite_name} 失败${NC}"
        ((FAILED++))
    fi
}

# 核心测试
run_test_suite "核心深度测试" "tests/test_deep_core.py"
run_test_suite "动态调度器测试" "tests/test_dynamic_scheduler.py"
run_test_suite "并行工作流测试" "tests/test_workflow_parallel.py"
run_test_suite "Swarm 集成测试" "tests/test_swarm_integration.py"

# 工具测试
run_test_suite "工具执行测试" "tests/test_tool_execution.py"
run_test_suite "领域测试" "tests/test_domains.py"
run_test_suite "Agent 测试" "tests/test_agents.py"

# 集成测试
run_test_suite "工作流集成测试" "tests/test_workflow_integration.py"
run_test_suite "Swarm 并发测试" "tests/test_swarm_concurrent.py"

# 汇总
TOTAL_END=$(date +%s)
DURATION=$((TOTAL_END - TOTAL_START))

echo ""
echo "========================================"
echo "  测试汇总"
echo "========================================"
echo -e "  通过：${GREEN}${PASSED}${NC}"
echo -e "  失败：${RED}${FAILED}${NC}"
echo "  耗时：${DURATION}秒"
echo "========================================"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}部分测试失败，请检查上方输出${NC}"
    exit 1
else
    echo -e "${GREEN}所有测试通过!${NC}"
    exit 0
fi
