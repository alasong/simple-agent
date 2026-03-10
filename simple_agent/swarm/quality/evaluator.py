"""
反馈评估器 (Feedback Evaluator)

评估反馈的质量，判断是否需要重新审查。

功能：
- 反馈质量评估
- 低质量反馈检测
- 建设性反馈判断
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class FeedbackQuality(Enum):
    """反馈质量等级"""
    TOO_SHORT = "too_short"      # 过于简短
    TOO_VAGUE = "too_vague"      # 过于模糊
    POOR = "poor"                # 缺乏具体内容
    PARTIAL = "partial"          # 有部分价值
    GOOD = "good"                # 良好的反馈
    EXCELLENT = "excellent"      # 优秀的反馈


@dataclass
class FeedbackAnalysis:
    """反馈分析结果"""
    quality: FeedbackQuality
    score: float  # 0-1 之间的质量分数
    is_actionable: bool  # 是否可执行
    is_constructive: bool  # 是否建设性
    issues: List[str]  # 发现的问题
    suggestions: List[str]  # 提取的建议
    reason: str  # 判定理由

    def to_dict(self) -> dict:
        return {
            "quality": self.quality.value,
            "score": round(self.score, 2),
            "is_actionable": self.is_actionable,
            "is_constructive": self.is_constructive,
            "issues_count": len(self.issues),
            "suggestions_count": len(self.suggestions),
            "reason": self.reason
        }


class FeedbackEvaluator:
    """反馈质量评估器"""

    # 低质量反馈特征词
    VAGUE_PATTERNS = [
        "不好", "有问题", "不太行", "感觉不对", "好像错了",
        "bad", "wrong", "not good", "doesn't work"
    ]

    # 建设性反馈特征词
    CONSTRUCTIVE_PATTERNS = [
        "建议", "可以改为", "应该", "需要", "问题是",
        "suggestion", "recommend", "should", "because",
        "具体来说", "例如", "比如", "原因是"
    ]

    # 具体问题描述词
    SPECIFIC_PATTERNS = [
        "第", "行", "函数", "方法", "变量", "参数",
        "line", "function", "method", "parameter",
        "错误", "异常", "bug", "问题", "漏洞"
    ]

    # 改进建议词
    IMPROVEMENT_PATTERNS = [
        "改为", "修改为", "使用", "采用", "添加", "删除",
        "change to", "use", "add", "remove", "fix"
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化反馈评估器

        Args:
            config: 可选的配置字典
        """
        self.config = config or {}
        self.min_good_length = self.config.get("min_good_length", 20)
        self.specific_threshold = self.config.get("specific_threshold", 1)

    def evaluate(self, feedback: str) -> FeedbackAnalysis:
        """
        评估反馈质量

        Args:
            feedback: 反馈文本

        Returns:
            FeedbackAnalysis: 反馈分析结果
        """
        feedback_stripped = feedback.strip()
        feedback_lower = feedback_stripped.lower()

        # 1. 检查长度
        if len(feedback_stripped) < 10:
            return FeedbackAnalysis(
                quality=FeedbackQuality.TOO_SHORT,
                score=0.1,
                is_actionable=False,
                is_constructive=False,
                issues=[],
                suggestions=[],
                reason="反馈过于简短，无法提供有效信息"
            )

        # 2. 检查是否过于模糊
        vague_count = sum(1 for p in self.VAGUE_PATTERNS if p in feedback_lower)
        specific_count = sum(1 for p in self.SPECIFIC_PATTERNS if p in feedback_lower)

        if vague_count > specific_count and vague_count >= 2:
            return FeedbackAnalysis(
                quality=FeedbackQuality.TOO_VAGUE,
                score=0.3,
                is_actionable=False,
                is_constructive=False,
                issues=[],
                suggestions=[],
                reason="反馈过于模糊，缺乏具体内容"
            )

        # 3. 检查是否包含具体问题
        has_specific_issue = (
            specific_count >= self.specific_threshold or
            any(kw in feedback_lower for kw in ["问题", "错误", "bug", "应该", "需要", "原因"])
        )

        # 4. 检查是否包含改进建议
        has_suggestion = (
            sum(1 for p in self.CONSTRUCTIVE_PATTERNS if p in feedback_lower) >= 1 or
            sum(1 for p in self.IMPROVEMENT_PATTERNS if p in feedback_lower) >= 1
        )

        # 5. 检查是否包含代码示例或具体引用
        has_example = (
            "```" in feedback or
            "`" in feedback or
            "第" in feedback or
            "line" in feedback
        )

        # 6. 综合评分
        score = 0.5  # 基础分

        if has_specific_issue:
            score += 0.2
        if has_suggestion:
            score += 0.2
        if has_example:
            score += 0.1

        # 长度奖励
        if len(feedback_stripped) > 100:
            score += 0.1
        if len(feedback_stripped) > 300:
            score += 0.1

        # 限制在 0-1 范围
        score = min(1.0, max(0.0, score))

        # 7. 判定质量等级
        if has_specific_issue and has_suggestion and score >= 0.8:
            quality = FeedbackQuality.EXCELLENT
        elif has_specific_issue and has_suggestion:
            quality = FeedbackQuality.GOOD
        elif has_specific_issue or has_suggestion:
            quality = FeedbackQuality.PARTIAL
        elif score >= 0.5:
            quality = FeedbackQuality.PARTIAL
        else:
            quality = FeedbackQuality.POOR

        # 8. 提取问题和建议
        issues = self._extract_issues(feedback)
        suggestions = self._extract_suggestions(feedback)

        # 9. 判断是否可执行和建设性
        is_actionable = len(suggestions) > 0 or has_specific_issue
        is_constructive = has_suggestion or quality in [
            FeedbackQuality.GOOD, FeedbackQuality.EXCELLENT
        ]

        # 10. 生成判定理由
        reason_parts = []
        if has_specific_issue:
            reason_parts.append("包含具体问题")
        if has_suggestion:
            reason_parts.append("包含改进建议")
        if has_example:
            reason_parts.append("包含示例/引用")
        if not has_specific_issue and not has_suggestion:
            reason_parts.append("缺乏具体内容")

        reason = "；".join(reason_parts) if reason_parts else "一般反馈"

        return FeedbackAnalysis(
            quality=quality,
            score=score,
            is_actionable=is_actionable,
            is_constructive=is_constructive,
            issues=issues,
            suggestions=suggestions,
            reason=reason
        )

    def _extract_issues(self, feedback: str) -> List[str]:
        """从反馈中提取问题"""
        issues = []
        feedback_lower = feedback.lower()

        # 简单的问题提取逻辑
        if any(kw in feedback_lower for kw in ["问题", "错误", "bug", "不对", "错了"]):
            # 尝试提取问题描述
            for kw in ["问题", "错误", "bug"]:
                if kw in feedback_lower:
                    idx = feedback_lower.find(kw)
                    # 提取前后各 20 个字符
                    start = max(0, idx - 10)
                    end = min(len(feedback), idx + len(kw) + 30)
                    issue_text = feedback[start:end].strip()
                    if issue_text and len(issue_text) > 5:
                        issues.append(issue_text)

        return issues[:3]  # 最多 3 个问题

    def _extract_suggestions(self, feedback: str) -> List[str]:
        """从反馈中提取建议"""
        suggestions = []
        feedback_lower = feedback.lower()

        # 简单的建议提取逻辑
        suggestion_markers = ["建议", "可以", "应该", "改为", "suggestion", "should"]
        for marker in suggestion_markers:
            if marker in feedback_lower:
                idx = feedback_lower.find(marker)
                # 提取后面的内容
                start = idx
                end = feedback.find("。", idx)
                if end == -1:
                    end = min(len(feedback), idx + 50)
                suggestion_text = feedback[start:end].strip()
                if suggestion_text and len(suggestion_text) > 5:
                    suggestions.append(suggestion_text)

        return suggestions[:3]  # 最多 3 条建议

    def is_approved(self, feedback: str) -> bool:
        """
        判断反馈是否通过审查（即是否需要修改）

        注意：这里的逻辑是：
        - 如果反馈包含"通过"、"LGTM"等词，说明代码已批准，无需修改
        - 否则需要修改

        Args:
            feedback: 反馈文本

        Returns:
            bool: True 表示通过（无需修改），False 表示需要修改
        """
        from configs.common_keywords import CommonKeywordsConfig
        approval_keywords = CommonKeywordsConfig.get_approval_keywords()
        feedback_lower = feedback.lower()
        return any(kw in feedback_lower for kw in approval_keywords)

    def should_trigger_re_review(self, feedback: str) -> bool:
        """
        判断是否应触发重新审查

        低质量反馈应触发重新审查，因为：
        1. 模糊的反馈无法指导改进
        2. 过于简短的反馈缺乏价值
        3. 无建设性的反馈可能导致无效循环

        Args:
            feedback: 反馈文本

        Returns:
            bool: True 表示应触发重新审查
        """
        analysis = self.evaluate(feedback)

        # 低质量反馈触发重新审查
        if analysis.quality in [
            FeedbackQuality.TOO_SHORT,
            FeedbackQuality.TOO_VAGUE,
            FeedbackQuality.POOR
        ]:
            return True

        # 非建设性反馈也可能需要重新审查
        if not analysis.is_constructive and not analysis.is_actionable:
            return True

        return False

    def get_improvement_prompt(self, feedback: str) -> str:
        """
        生成改进反馈的提示

        Args:
            feedback: 原始反馈

        Returns:
            str: 改进提示
        """
        analysis = self.evaluate(feedback)

        prompt_parts = ["请提供更具体、更有建设性的反馈："]

        if analysis.quality == FeedbackQuality.TOO_SHORT:
            prompt_parts.append("- 反馈过于简短，请详细说明问题")

        if analysis.quality == FeedbackQuality.TOO_VAGUE:
            prompt_parts.append("- 避免模糊表述，请指出具体问题所在")

        if not analysis.is_actionable:
            prompt_parts.append("- 请提供可执行的改进建议")

        if not analysis.is_constructive:
            prompt_parts.append("- 请以建设性的方式表达意见")

        if not analysis.issues:
            prompt_parts.append("- 请明确指出发现的问题")

        if not analysis.suggestions:
            prompt_parts.append("- 请提供具体的改进建议或代码示例")

        return "\n".join(prompt_parts)


def create_evaluator(config: Optional[Dict] = None) -> FeedbackEvaluator:
    """工厂函数：创建反馈评估器"""
    return FeedbackEvaluator(config=config)
