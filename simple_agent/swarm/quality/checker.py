"""
质量检查器 (Quality Checker)

基于检查清单执行质量检查，生成质量报告。

功能：
- 加载检查清单配置
- 执行质量检查
- 生成质量报告
- 支持自定义检查清单
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    """单项检查结果"""
    item: str
    passed: bool
    confidence: float = 1.0  # 置信度
    reason: str = ""  # 判定理由

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "passed": self.passed,
            "confidence": round(self.confidence, 2),
            "reason": self.reason
        }


@dataclass
class QualityReport:
    """质量检查报告"""
    checklist_type: str
    total: int
    passed: int
    results: List[CheckResult]
    pass_rate: float
    overall_passed: bool
    details: str = ""
    suggestions: List[str] = field(default_factory=list)

    @property
    def failed_count(self) -> int:
        return self.total - self.passed

    @property
    def failed_items(self) -> List[str]:
        return [r.item for r in self.results if not r.passed]

    def to_dict(self) -> dict:
        return {
            "checklist_type": self.checklist_type,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed_count,
            "pass_rate": round(self.pass_rate, 2),
            "overall_passed": self.overall_passed,
            "failed_items": self.failed_items,
            "suggestions": self.suggestions
        }

    def to_summary(self) -> str:
        """生成摘要文本"""
        status = "通过" if self.overall_passed else "未通过"
        summary = f"质量检查{status}：{self.passed}/{self.total} 项通过 ({self.pass_rate:.1%})"
        if self.failed_items:
            summary += f"\n未通过项：{', '.join(self.failed_items[:5])}"
        if self.suggestions:
            summary += f"\n建议：{self.suggestions[0]}"
        return summary


class QualityChecker:
    """质量检查器 - 基于检查清单"""

    # 检查清单类型映射
    CHECKLIST_TYPES = {
        "general": "general_checklist",
        "code": "code_checklist",
        "document": "document_checklist",
        "review": "review_checklist",
        "design": "design_checklist",
        "analysis": "analysis_checklist"
    }

    def __init__(
        self,
        checklist_type: str = "general",
        config_path: Optional[str] = None,
        llm_client: Optional[Any] = None
    ):
        """
        初始化质量检查器

        Args:
            checklist_type: 检查清单类型 (general/code/document/review/design/analysis)
            config_path: 配置文件路径，默认使用 configs/quality_checklist.yaml
            llm_client: 可选的 LLM 客户端，用于智能评估
        """
        self.checklist_type = checklist_type
        self.config_path = config_path or self._default_config_path()
        self.llm_client = llm_client
        self.checklist = self._load_checklist()
        self.thresholds = self._load_thresholds()

    def _default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的位置
        possible_paths = [
            Path(__file__).parent.parent / "configs" / "quality_checklist.yaml",
            Path.cwd() / "configs" / "quality_checklist.yaml",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        return str(possible_paths[0])  # 返回默认路径

    def _load_checklist(self) -> List[str]:
        """加载检查清单"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            checklist_key = self.CHECKLIST_TYPES.get(
                self.checklist_type,
                "general_checklist"
            )

            checklist_data = config.get(checklist_key, {})
            return checklist_data.get("items", [])
        except Exception as e:
            # 加载失败时返回默认清单
            return self._get_default_checklist()

    def _load_thresholds(self) -> Dict:
        """加载通过阈值"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get("thresholds", {}).get(self.checklist_type, {})
        except Exception:
            return {}

    def _get_default_checklist(self) -> List[str]:
        """获取默认检查清单"""
        defaults = {
            "general": [
                "回答是否直接解决了用户问题",
                "是否提供了具体的步骤或示例",
                "是否有清晰的结论或总结"
            ],
            "code": [
                "代码是否可运行，无语法错误",
                "是否包含必要的错误处理",
                "命名是否清晰，符合规范"
            ],
            "document": [
                "结构是否清晰，层次分明",
                "是否使用了恰当的标题和分段",
                "内容是否准确，无事实错误"
            ],
            "review": [
                "问题描述是否清晰具体",
                "是否提供了风险等级评估",
                "改进建议是否可执行"
            ]
        }
        return defaults.get(self.checklist_type, defaults["general"])

    def check(
        self,
        content: str,
        context: Optional[Dict] = None,
        use_llm: bool = False
    ) -> QualityReport:
        """
        执行质量检查

        Args:
            content: 待检查的内容
            context: 上下文信息（可选）
            use_llm: 是否使用 LLM 进行智能评估

        Returns:
            QualityReport: 质量检查报告
        """
        if use_llm and self.llm_client:
            return self._check_with_llm(content, context)
        else:
            return self._check_simple(content, context)

    def _check_simple(
        self,
        content: str,
        context: Optional[Dict] = None
    ) -> QualityReport:
        """简单检查 - 基于关键词匹配"""
        results = []
        content_lower = content.lower()

        for item in self.checklist:
            passed, confidence, reason = self._evaluate_item_simple(
                content_lower, item, context
            )
            results.append(CheckResult(
                item=item,
                passed=passed,
                confidence=confidence,
                reason=reason
            ))

        passed_count = sum(1 for r in results if r.passed)
        pass_rate = passed_count / len(results) if results else 0

        # 判断是否通过
        threshold = self.thresholds.get("pass_rate", 0.7)
        overall_passed = pass_rate >= threshold

        # 生成建议
        suggestions = self._generate_suggestions(results)

        return QualityReport(
            checklist_type=self.checklist_type,
            total=len(results),
            passed=passed_count,
            results=results,
            pass_rate=pass_rate,
            overall_passed=overall_passed,
            suggestions=suggestions
        )

    def _evaluate_item_simple(
        self,
        content: str,
        item: str,
        context: Optional[Dict] = None
    ) -> tuple:
        """
        简单评估检查项

        Returns:
            (passed, confidence, reason)
        """
        # 基于关键词的简单判断逻辑
        item_keywords = {
            "可运行": ["def ", "class ", "import ", "return ", "if ", "for "],
            "语法错误": ["error", "错误", "syntax"],
            "错误处理": ["try", "except", "catch", "if ", "validate", "检查"],
            "命名": ["def ", "class ", "=", "变量", "函数"],
            "注释": ["#", "//", "/*", "注", "comment"],
            "清晰": ["首先", "其次", "然后", "步骤", "1.", "2."],
            "具体": ["例如", "比如", "示例", "code", "```"],
            "结论": ["总结", "综上", "因此", "结论", "建议"],
            "步骤": ["步骤", "第一步", "然后", "接着", "最后"],
            "示例": ["例如", "比如", "示例", "code", "```"],
        }

        # 检查是否包含相关关键词
        for keyword, patterns in item_keywords.items():
            if keyword in item:
                match_count = sum(1 for p in patterns if p in content)
                if match_count >= 1:
                    return (True, 0.8, f"检测到 {match_count} 个相关特征")
                else:
                    return (False, 0.6, f"未检测到足够的相关特征")

        # 默认通过（无法判断时）
        return (True, 0.5, "默认通过")

    def _check_with_llm(
        self,
        content: str,
        context: Optional[Dict] = None
    ) -> QualityReport:
        """使用 LLM 进行智能检查"""
        if not self.llm_client:
            return self._check_simple(content, context)

        # 构建评估提示
        checklist_text = "\n".join([f"- {item}" for item in self.checklist])

        prompt = f"""请对以下内容进行质量检查：

检查清单：
{checklist_text}

待检查内容：
{content}

请逐项评估检查清单中的每一项，判断是否通过。

返回 JSON 格式：
{{
    "results": [
        {{"item": "检查项", "passed": true/false, "reason": "理由"}}
    ],
    "suggestions": ["改进建议 1", "改进建议 2"]
}}
"""

        try:
            # 调用 LLM
            response = self.llm_client.generate(prompt)
            # 解析响应（简化处理）
            import json
            result_data = json.loads(response)

            results = [
                CheckResult(
                    item=r["item"],
                    passed=r["passed"],
                    reason=r.get("reason", "")
                )
                for r in result_data.get("results", [])
            ]

            passed_count = sum(1 for r in results if r.passed)
            pass_rate = passed_count / len(results) if results else 0

            threshold = self.thresholds.get("pass_rate", 0.7)
            overall_passed = pass_rate >= threshold

            return QualityReport(
                checklist_type=self.checklist_type,
                total=len(results),
                passed=passed_count,
                results=results,
                pass_rate=pass_rate,
                overall_passed=overall_passed,
                suggestions=result_data.get("suggestions", [])
            )
        except Exception as e:
            # LLM 检查失败，降级到简单检查
            return self._check_simple(content, context)

    def _generate_suggestions(self, results: List[CheckResult]) -> List[str]:
        """基于检查结果生成建议"""
        suggestions = []
        failed_items = [r.item for r in results if not r.passed]

        if not failed_items:
            return ["内容质量良好，无需改进"]

        # 根据未通过的项生成建议
        suggestion_map = {
            "可运行": "建议提供完整的代码示例",
            "错误处理": "建议添加异常处理和边界条件检查",
            "命名": "建议使用更具描述性的变量和函数名",
            "注释": "建议添加必要的注释说明复杂逻辑",
            "清晰": "建议优化结构，使用分点和标题",
            "具体": "建议提供具体的示例或代码",
            "结论": "建议在末尾添加总结或结论",
            "步骤": "建议分步骤说明，使流程更清晰",
            "示例": "建议添加示例帮助理解"
        }

        for item in failed_items[:3]:  # 最多 3 条建议
            for key, suggestion in suggestion_map.items():
                if key in item:
                    suggestions.append(suggestion)
                    break

        return suggestions if suggestions else ["请根据检查清单改进内容"]

    def get_checklist_summary(self) -> str:
        """获取检查清单摘要"""
        return f"质量检查器 ({self.checklist_type}): {len(self.checklist)} 项检查"


def create_checker(
    checklist_type: str = "general",
    **kwargs
) -> QualityChecker:
    """工厂函数：创建质量检查器"""
    return QualityChecker(checklist_type=checklist_type, **kwargs)
