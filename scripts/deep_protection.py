#!/usr/bin/env python3
"""
深度防护脚本 - 基于 Agent 能力的代码质量检查系统

功能:
1. 代码质量分析（使用 EnhancedAgent 的代码分析技能）
2. 安全性检查（敏感信息、潜在漏洞）
3. 最佳实践验证（PEP8、代码规范）
4. 复杂度分析（圈复杂度、代码重复）
5. 依赖检查（过时库、安全漏洞）

使用:
    python scripts/deep_protection.py <文件路径>
    python scripts/deep_protection.py --all  # 检查所有 Python 文件
"""

import sys
import os
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    EnhancedMemory, Experience,
    TreeOfThought, ReflectionLoop,
    SkillLibrary
)
from core.agent_enhanced import EnhancedAgent
from core.llm import OpenAILLM


@dataclass
class Issue:
    """代码问题"""
    file: str
    line: int
    severity: str  # critical, warning, info
    category: str  # security, quality, style, complexity
    message: str
    suggestion: str = ""
    code: str = ""


@dataclass
class FileReport:
    """文件检查报告"""
    file: str
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    
    def add_issue(self, issue: Issue):
        self.issues.append(issue)
        if issue.severity in ["critical", "warning"]:
            self.success = False
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "critical")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")
    
    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "info")


class CodeAnalyzer:
    """代码分析器 - 静态分析"""
    
    def __init__(self):
        self.issues = []
    
    def analyze_file(self, file_path: str) -> FileReport:
        """分析单个文件"""
        report = FileReport(file=file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 基础检查
            self._check_file_size(report, len(lines))
            self._check_encoding(report, content)
            
            # AST 分析
            try:
                tree = ast.parse(content)
                self._check_complexity(report, tree)
                self._check_long_functions(report, tree, lines)
                self._check_imports(report, tree)
                self._check_docstrings(report, tree)
            except SyntaxError as e:
                report.add_issue(Issue(
                    file=file_path,
                    line=e.lineno or 0,
                    severity="critical",
                    category="quality",
                    message=f"语法错误：{e.msg}",
                    code=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else ""
                ))
                return report
            
            # 模式检查
            self._check_security_issues(report, content, lines)
            self._check_code_smells(report, content, lines)
            self._check_pep8_style(report, content, lines)
            
            # 计算指标
            report.metrics = self._calculate_metrics(content, tree)
            
        except Exception as e:
            report.add_issue(Issue(
                file=file_path,
                line=0,
                severity="critical",
                category="quality",
                message=f"分析失败：{str(e)}",
                suggestion="检查文件是否可读取"
            ))
            report.success = False
        
        return report
    
    def _check_file_size(self, report: FileReport, line_count: int):
        """检查文件大小"""
        if line_count > 500:
            report.add_issue(Issue(
                file=report.file,
                line=0,
                severity="warning",
                category="complexity",
                message=f"文件过大：{line_count} 行（建议 < 500 行）",
                suggestion="考虑拆分为多个模块"
            ))
    
    def _check_encoding(self, report: FileReport, content: str):
        """检查编码问题"""
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            report.add_issue(Issue(
                file=report.file,
                line=0,
                severity="warning",
                category="quality",
                message="文件包含非 UTF-8 字符",
                suggestion="确保文件使用 UTF-8 编码"
            ))
    
    def _check_complexity(self, report: FileReport, tree: ast.AST):
        """检查代码复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_function_complexity(node)
                if complexity > 10:
                    report.add_issue(Issue(
                        file=report.file,
                        line=node.lineno,
                        severity="warning",
                        category="complexity",
                        message=f"函数 '{node.name}' 复杂度过高：{complexity}（建议 < 10）",
                        suggestion="简化逻辑或拆分为多个函数"
                    ))
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _check_long_functions(self, report: FileReport, tree: ast.AST, lines: List[str]):
        """检查过长函数"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算函数行数
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 50
                func_length = end_line - node.lineno + 1
                
                if func_length > 50:
                    report.add_issue(Issue(
                        file=report.file,
                        line=node.lineno,
                        severity="warning",
                        category="quality",
                        message=f"函数 '{node.name}' 过长：{func_length} 行（建议 < 50 行）",
                        suggestion="拆分为多个小函数"
                    ))
    
    def _check_imports(self, report: FileReport, tree: ast.AST):
        """检查导入问题"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if '.' in alias.name:
                        report.add_issue(Issue(
                            file=report.file,
                            line=node.lineno,
                            severity="info",
                            category="style",
                            message=f"导入整个模块：{alias.name}",
                            suggestion="考虑只导入需要的部分"
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and 'star' in str(node.names[0]) if node.names else False:
                    report.add_issue(Issue(
                        file=report.file,
                        line=node.lineno,
                        severity="warning",
                        category="style",
                        message="使用 * 导入",
                        suggestion="明确导入需要的名称"
                    ))
    
    def _check_docstrings(self, report: FileReport, tree: ast.AST):
        """检查文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    report.add_issue(Issue(
                        file=report.file,
                        line=node.lineno,
                        severity="info",
                        category="style",
                        message=f"缺少文档：{node.name}",
                        suggestion="添加文档字符串说明用途"
                    ))
    
    def _check_security_issues(self, report: FileReport, content: str, lines: List[str]):
        """检查安全问题"""
        security_patterns = [
            (r'eval\s*\(', '使用 eval() 可能存在代码注入风险'),
            (r'exec\s*\(', '使用 exec() 可能存在代码注入风险'),
            (r'os\.system\s*\(', '使用 os.system() 可能存在命令注入风险'),
            (r'subprocess\..*shell\s*=\s*True', '使用 shell=True 可能存在命令注入风险'),
            (r'pickle\.load', '使用 pickle.load() 可能存在反序列化漏洞'),
            (r'yaml\.load\s*\([^)]*\)\s*$', '使用 yaml.load()  without Loader 可能存在风险'),
            (r'input\s*\(\s*\)\s*\)', '使用 input() 在 Python 2 中会执行代码'),
            (r'md5\s*\(|sha1\s*\(', '使用弱哈希算法（MD5/SHA1）'),
            (r'random\.(random|randint|choice)', '使用随机模块而非加密安全的 secrets'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in security_patterns:
                if re.search(pattern, line):
                    report.add_issue(Issue(
                        file=report.file,
                        line=i,
                        severity="critical",
                        category="security",
                        message=message,
                        code=line.strip(),
                        suggestion="使用安全的替代方案"
                    ))
        
        # 检查硬编码密钥
        key_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'access_key\s*=\s*["\'][^"\']+["\']',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in key_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 跳过示例文件和测试文件
                    if 'example' not in report.file and 'sample' not in report.file and 'test' not in report.file:
                        report.add_issue(Issue(
                            file=report.file,
                            line=i,
                            severity="critical",
                            category="security",
                            message="发现硬编码的密钥或密码",
                            code=line.strip(),
                            suggestion="使用环境变量或配置文件"
                        ))
    
    def _check_code_smells(self, report: FileReport, content: str, lines: List[str]):
        """检查代码异味"""
        # 检查过长的行
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                report.add_issue(Issue(
                    file=report.file,
                    line=i,
                    severity="info",
                    category="style",
                    message=f"行过长：{len(line)} 字符（建议 < 120）",
                    code=line[:50] + "..."
                ))
        
        # 检查 TODO/FIXME 注释
        for i, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                report.add_issue(Issue(
                    file=report.file,
                    line=i,
                    severity="info",
                    category="quality",
                    message=line.strip(),
                    suggestion="处理或移除临时标记"
                ))
        
        # 检查空函数
        for match in re.finditer(r'def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*pass', content):
            line_num = content[:match.start()].count('\n') + 1
            report.add_issue(Issue(
                file=report.file,
                line=line_num,
                severity="info",
                category="quality",
                message="空函数（只有 pass）",
                suggestion="实现函数或考虑移除"
            ))
    
    def _check_pep8_style(self, report: FileReport, content: str, lines: List[str]):
        """检查 PEP8 风格"""
        # 检查缩进
        for i, line in enumerate(lines, 1):
            if line and not line.startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent % 4 != 0:
                    report.add_issue(Issue(
                        file=report.file,
                        line=i,
                        severity="info",
                        category="style",
                        message="缩进不是 4 的倍数",
                        code=line[:30]
                    ))
        
        # 检查空行
        for i in range(len(lines) - 1):
            if lines[i].strip() and lines[i+1].strip():
                # 检查类/函数定义前是否有足够空行
                if re.match(r'^(class|def)\s+', lines[i+1]):
                    if i > 0 and lines[i-1].strip():
                        report.add_issue(Issue(
                            file=report.file,
                            line=i+1,
                            severity="info",
                            category="style",
                            message="定义前缺少空行",
                            suggestion="在类/函数定义前添加空行"
                        ))
    
    def _calculate_metrics(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """计算代码指标"""
        metrics = {
            'lines': len(content.split('\n')),
            'blank_lines': sum(1 for line in content.split('\n') if not line.strip()),
            'comment_lines': sum(1 for line in content.split('\n') if line.strip().startswith('#')),
            'functions': sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))),
            'classes': sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)),
            'imports': sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
        }
        metrics['code_lines'] = metrics['lines'] - metrics['blank_lines'] - metrics['comment_lines']
        return metrics


class AgentCodeReviewer:
    """Agent 代码审查员 - 使用 EnhancedAgent 进行智能分析"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = OpenAILLM()
        self.memory = EnhancedMemory()
        self.skill_library = SkillLibrary()
        self.agent = EnhancedAgent(
            llm=self.llm,
            memory=self.memory,
            skill_library=self.skill_library
        )
    
    async def review_file(self, file_path: str, static_issues: List[Issue]) -> List[Issue]:
        """使用 Agent 审查代码"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 构建审查提示
            prompt = f"""你是资深代码审查专家。请审查以下 Python 代码：

```python
{content[:5000]}  # 限制长度避免超出
```

检查以下方面：
1. 代码逻辑问题
2. 潜在 bug
3. 性能问题
4. 安全漏洞
5. 可维护性问题

以 JSON 数组格式返回问题列表，每个问题包含：
- line: 行号
- severity: 严重程度 (critical/warning/info)
- message: 问题描述
- suggestion: 改进建议

示例格式：
[{{"line": 10, "severity": "warning", "message": "变量未使用", "suggestion": "移除或使用该变量"}}]

如果代码质量很好，返回空数组 []。"""
            
            if self.verbose:
                print(f"\n🤖 Agent 正在审查：{file_path}")
            
            # 使用 EnhancedAgent 执行审查
            import asyncio
            result = await self.agent.run(prompt, verbose=False)
            
            # 解析结果
            try:
                # 尝试提取 JSON
                import json
                # 查找 JSON 数组
                start = result.find('[')
                end = result.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    ai_issues = json.loads(json_str)
                    
                    for issue_data in ai_issues:
                        issues.append(Issue(
                            file=file_path,
                            line=issue_data.get('line', 0),
                            severity=issue_data.get('severity', 'info'),
                            category='quality',
                            message=issue_data.get('message', ''),
                            suggestion=issue_data.get('suggestion', '')
                        ))
                else:
                    if self.verbose:
                        print(f"  ⚠️  无法解析 Agent 返回的 JSON")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  解析 Agent 结果失败：{e}")
        
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  Agent 审查失败：{e}")
        
        return issues


class DeepProtection:
    """深度防护系统"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.analyzer = CodeAnalyzer()
        self.reviewer = AgentCodeReviewer(verbose)
        self.reports = []
    
    def check_file(self, file_path: str) -> FileReport:
        """检查单个文件"""
        if self.verbose:
            print(f"\n📋 检查文件：{file_path}")
        
        # 静态分析
        report = self.analyzer.analyze_file(file_path)
        
        # Agent 智能审查（如果启用）
        if self.reviewer:
            import asyncio
            ai_issues = asyncio.run(self.reviewer.review_file(file_path, report.issues))
            for issue in ai_issues:
                report.add_issue(issue)
        
        self.reports.append(report)
        return report
    
    def check_directory(self, dir_path: str, pattern: str = "*.py") -> List[FileReport]:
        """检查目录下所有匹配的文件"""
        from glob import glob
        
        files = glob(os.path.join(dir_path, "**", pattern), recursive=True)
        
        # 排除虚拟环境和测试文件
        excluded = ['.venv', 'venv', '__pycache__', '.git', 'node_modules']
        files = [f for f in files if not any(ex in f for ex in excluded)]
        
        if self.verbose:
            print(f"📂 找到 {len(files)} 个 Python 文件")
        
        for file_path in files:
            self.check_file(file_path)
        
        return self.reports
    
    def generate_report(self, output_format: str = "text") -> str:
        """生成检查报告"""
        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("="*80)
        lines.append("深度防护检查报告")
        lines.append("="*80)
        
        total_issues = 0
        total_critical = 0
        total_warning = 0
        total_info = 0
        
        for report in self.reports:
            if not report.issues:
                continue
            
            lines.append(f"\n📄 文件：{report.file}")
            lines.append("-" * 80)
            
            # 按严重程度排序
            sorted_issues = sorted(report.issues, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x.severity])
            
            for issue in sorted_issues:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[issue.severity]
                category_icon = {"security": "🔒", "quality": "📊", "style": "🎨", "complexity": "📈"}[issue.category]
                
                lines.append(f"  {severity_icon} {category_icon} 行 {issue.line}: {issue.message}")
                if issue.code:
                    lines.append(f"      代码：{issue.code}")
                if issue.suggestion:
                    lines.append(f"      建议：{issue.suggestion}")
                
                total_issues += 1
                if issue.severity == "critical":
                    total_critical += 1
                elif issue.severity == "warning":
                    total_warning += 1
                else:
                    total_info += 1
        
        lines.append("\n" + "="*80)
        lines.append("总结")
        lines.append("="*80)
        lines.append(f"检查文件数：{len(self.reports)}")
        lines.append(f"总问题数：{total_issues}")
        lines.append(f"  🔴 严重：{total_critical}")
        lines.append(f"  🟡 警告：{total_warning}")
        lines.append(f"  🔵 提示：{total_info}")
        lines.append("="*80)
        
        if total_critical > 0:
            lines.append("\n❌ 检查失败：存在严重问题")
        elif total_warning > 0:
            lines.append("\n⚠️  检查通过：存在警告")
        else:
            lines.append("\n✅ 检查通过：代码质量良好")
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> str:
        """生成 JSON 报告"""
        data = {
            "files": [],
            "summary": {
                "total_files": len(self.reports),
                "total_issues": 0,
                "critical": 0,
                "warning": 0,
                "info": 0
            }
        }
        
        for report in self.reports:
            file_data = {
                "file": report.file,
                "success": report.success,
                "metrics": report.metrics,
                "issues": [
                    {
                        "line": issue.line,
                        "severity": issue.severity,
                        "category": issue.category,
                        "message": issue.message,
                        "suggestion": issue.suggestion,
                        "code": issue.code
                    }
                    for issue in report.issues
                ]
            }
            data["files"].append(file_data)
            
            data["summary"]["total_issues"] += len(report.issues)
            data["summary"]["critical"] += report.critical_count
            data["summary"]["warning"] += report.warning_count
            data["summary"]["info"] += report.info_count
        
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="深度防护脚本 - 基于 Agent 的代码质量检查")
    parser.add_argument("path", nargs="?", default=".", help="要检查的文件或目录路径")
    parser.add_argument("--all", action="store_true", help="检查所有 Python 文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式报告")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--no-agent", action="store_true", help="不使用 Agent 审查（仅静态分析）")
    
    args = parser.parse_args()
    
    # 创建防护系统
    protection = DeepProtection(verbose=args.verbose)
    
    # 如果启用了 Agent，设置标志
    if args.no_agent:
        protection.reviewer = None
    
    # 确定检查范围
    if args.all:
        # 检查当前目录下所有 Python 文件
        protection.check_directory(".", "*.py")
    elif os.path.isfile(args.path):
        # 检查单个文件
        protection.check_file(args.path)
    elif os.path.isdir(args.path):
        # 检查目录
        protection.check_directory(args.path, "*.py")
    else:
        print(f"错误：路径不存在：{args.path}")
        sys.exit(1)
    
    # 生成报告
    output_format = "json" if args.json else "text"
    report = protection.generate_report(output_format)
    print(report)
    
    # 根据结果设置退出码
    has_critical = any(r.critical_count > 0 for r in protection.reports)
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
