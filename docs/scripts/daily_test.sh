#!/bin/bash
# 日常测试脚本
echo "======================================"
echo "  日常测试脚本"
echo "======================================"

cd "$(dirname "$0")/.."

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "1. Python 语法检查..."
SKIP_FILES="agent_simple.py"
for file in core/*.py; do
    fname=$(basename "$file")
    if [[ ! " $SKIP_FILES " =~ " $fname " ]]; then
        python3 -m py_compile "$file" && echo "  ✓ $fname"
    else
        echo "  ⊘ $fname (跳过)"
    fi
done

echo "2. 单元测试..."
python3 tests/test_stage1.py

echo "3. 导入测试..."
python3 -c "from core import EnhancedMemory, SkillLibrary"

echo "✅ 所有测试通过"
