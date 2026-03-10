#!/usr/bin/env python3
"""
Agent 代码审查工具 - 快速使用 EnhancedAgent 进行代码审查

使用:
    python scripts/agent_review.py <文件路径>
    python scripts/agent_review.py --help
"""

import sys
import os
import asyncio
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import SkillLibrary, EnhancedMemory
from core.agent_enhanced import EnhancedAgent
from core.llm import OpenAILLM


class CodeReviewAgent:
    """代码审查 Agent"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = OpenAILLM()
        self.memory = EnhancedMemory()
        self.skill_library = SkillLibrary()
        
        # 创建增强型 Agent
        self.agent = EnhancedAgent(
            llm=self.llm,
            memory=self.memory,
            skill_library=self.skill_library
        )
        
        # 设置审查技能
        self._setup_review_skill()
    
    def _setup_review_skill(self):
        """设置代码审查技能"""
        from core.skill_learning import Skill
        
        review_skill = Skill(
            name="代码深度审查",
            description="深度审查代码质量和安全性",
            trigger_pattern=r"审查代码 | 代码分析 | 质量检查",
            prompt_template="""你是资深代码审查专家，拥有丰富的 Python 开发经验。

请从以下维度审查代码：

## 1. 安全性检查
- 硬编码密钥/密码
- SQL 注入风险
- 命令注入风险
- 不安全的反序列化
- 弱加密算法

## 2. 代码质量
- 函数复杂度
- 代码重复
- 错误处理
- 资源泄漏
- 类型安全

## 3. 最佳实践
- PEP8 规范
- 命名约定
- 文档完整性
- 测试覆盖
- 依赖管理

## 4. 性能优化
- 时间复杂度
- 空间复杂度
- 不必要的计算
- 缓存使用
- 并发处理

请按以下格式返回审查结果：

### 🔴 严重问题（必须修复）
[列出所有严重问题]

### 🟡 改进建议（建议修复）
[列出所有建议]

### 🔵 代码提示（可选优化）
[列出所有提示]

### 📊 总体评分
- 安全性：X/10
- 质量：X/10
- 可维护性：X/10
- 总体：X/10""",
            tools=["ReadFileTool", "WriteFileTool", "BashTool"],
            success_rate=0.9
        )
        
        # 添加到技能库
        self.skill_library.skills["代码深度审查"] = review_skill
    
    async def review_file(self, file_path: str) -> str:
        """审查文件"""
        if not os.path.exists(file_path):
            return f"❌ 文件不存在：{file_path}"
        
        if not file_path.endswith('.py'):
            return f"❌ 不是 Python 文件：{file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 限制代码长度
            max_length = 8000
            if len(code) > max_length:
                code = code[:max_length] + "\n# ... (代码过长，已截断)"
            
            # 构建审查请求
            prompt = f"""请审查以下 Python 代码：

```python
{code}
```

文件路径：{file_path}

请按照以下格式输出审查报告：

### 📋 文件信息
- 文件名：{os.path.basename(file_path)}
- 路径：{file_path}
- 大小：{os.path.getsize(file_path)} 字节

### 🔍 审查结果
[详细审查结果]

### 💡 总结
[总体评价和建议]"""
            
            if self.verbose:
                print(f"\n🤖 正在审查：{file_path}")
                print(f"   代码行数：{len(code.split(chr(10)))}")
                print(f"   使用策略：{self.agent.strategy}")
            
            # 执行审查
            result = await self.agent.run(prompt, verbose=self.verbose)
            return result
        
        except Exception as e:
            import traceback
            return f"❌ 审查失败：{str(e)}\n{traceback.format_exc()}"
    
    async def review_multiple_files(self, file_paths: List[str]) -> str:
        """审查多个文件"""
        if not file_paths:
            return "❌ 没有文件需要审查"
        
        results = []
        results.append("="*80)
        results.append("Agent 代码审查报告")
        results.append("="*80)
        results.append(f"文件数量：{len(file_paths)}")
        results.append("")
        
        for i, file_path in enumerate(file_paths, 1):
            if self.verbose:
                print(f"\n[{i}/{len(file_paths)}] 审查：{file_path}")
            
            result = await self.review_file(file_path)
            results.append(result)
            results.append("")
        
        return "\n".join(results)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 代码审查工具")
    parser.add_argument("files", nargs="*", help="要审查的文件路径")
    parser.add_argument("--all", action="store_true", help="审查当前目录下所有 Python 文件")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--output", "-o", help="输出报告到文件")
    
    args = parser.parse_args()
    
    # 创建审查 Agent
    reviewer = CodeReviewAgent(verbose=args.verbose)
    
    # 确定要审查的文件
    files_to_review = []
    
    if args.all:
        # 查找所有 Python 文件
        from glob import glob
        files_to_review = glob("**/*.py", recursive=True)
        # 排除虚拟环境等
        files_to_review = [
            f for f in files_to_review 
            if not any(ex in f for ex in ['.venv', 'venv', '__pycache__', '.git', 'node_modules'])
        ]
    elif args.files:
        files_to_review = args.files
    else:
        print("用法：python scripts/agent_review.py <文件路径>")
        print("      python scripts/agent_review.py --all  (审查所有 Python 文件)")
        print("\n示例:")
        print("  python scripts/agent_review.py core/agent.py")
        print("  python scripts/agent_review.py --all")
        print("  python scripts/agent_review.py file1.py file2.py file3.py")
        sys.exit(1)
    
    if not files_to_review:
        print("❌ 没有找到 Python 文件")
        sys.exit(1)
    
    if args.verbose:
        print(f"📋 找到 {len(files_to_review)} 个文件")
    
    # 执行审查
    if len(files_to_review) == 1:
        # 单个文件
        report = await reviewer.review_file(files_to_review[0])
    else:
        # 多个文件
        report = await reviewer.review_multiple_files(files_to_review)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ 报告已保存到：{args.output}")
    else:
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
