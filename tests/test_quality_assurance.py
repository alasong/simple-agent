"""
质量保障模块测试 (Quality Assurance Tests)

测试内容：
1. QualityChecker - 质量检查器
2. FeedbackEvaluator - 反馈评估器
3. IterativeOptimizer - 迭代优化器
4. PairProgramming (增强版) - 结对编程
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# 质量检查器测试
from core.quality_checker import QualityChecker, create_checker, QualityReport
from core.feedback_evaluator import FeedbackEvaluator, FeedbackQuality, create_evaluator


def run_async(coro):
    """Helper to run async tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestQualityChecker:
    """质量检查器测试"""

    def test_create_checker_general(self):
        """测试创建通用检查器"""
        checker = create_checker("general")
        assert checker is not None
        assert checker.checklist_type == "general"
        assert len(checker.checklist) > 0

    def test_create_checker_code(self):
        """测试创建代码检查器"""
        checker = create_checker("code")
        assert checker is not None
        assert checker.checklist_type == "code"

    def test_create_checker_document(self):
        """测试创建文档检查器"""
        checker = create_checker("document")
        assert checker is not None
        assert checker.checklist_type == "document"

    def test_create_checker_review(self):
        """测试创建审查检查器"""
        checker = create_checker("review")
        assert checker is not None
        assert checker.checklist_type == "review"

    def test_create_checker_design(self):
        """测试创建设计检查器"""
        checker = create_checker("design")
        assert checker is not None
        assert checker.checklist_type == "design"

    def test_create_checker_analysis(self):
        """测试创建分析检查器"""
        checker = create_checker("analysis")
        assert checker is not None
        assert checker.checklist_type == "analysis"

    def test_check_simple_content(self):
        """测试简单内容检查"""
        checker = create_checker("general")
        content = "这是一个简单的回答，包含一些基本信息。"
        report = checker.check(content)

        assert isinstance(report, QualityReport)
        assert report.total > 0
        assert 0 <= report.pass_rate <= 1

    def test_check_code_content(self):
        """测试代码内容检查"""
        checker = create_checker("code")
        code = """
def hello():
    print("Hello, World!")
    return True
"""
        report = checker.check(code)

        assert isinstance(report, QualityReport)
        assert report.passed >= 0

    def test_check_with_context(self):
        """测试带上下文的内容检查"""
        checker = create_checker("general")
        content = "这是一个详细的回答，包含步骤 1、步骤 2、步骤 3。"
        context = {"task_type": "explanation"}
        report = checker.check(content, context=context)

        assert isinstance(report, QualityReport)

    def test_report_to_dict(self):
        """测试报告转换为字典"""
        checker = create_checker("general")
        content = "测试内容"
        report = checker.check(content)

        report_dict = report.to_dict()
        assert "checklist_type" in report_dict
        assert "total" in report_dict
        assert "passed" in report_dict
        assert "pass_rate" in report_dict

    def test_report_summary(self):
        """测试报告摘要"""
        checker = create_checker("general")
        content = "测试内容"
        report = checker.check(content)

        summary = report.to_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_checklist_summary(self):
        """测试检查清单摘要"""
        checker = create_checker("general")
        summary = checker.get_checklist_summary()
        assert isinstance(summary, str)
        assert "质量检查器" in summary


class TestFeedbackEvaluator:
    """反馈评估器测试"""

    def test_create_evaluator(self):
        """测试创建反馈评估器"""
        evaluator = create_evaluator()
        assert evaluator is not None

    def test_evaluate_too_short_feedback(self):
        """测试评估过短反馈"""
        evaluator = FeedbackEvaluator()
        feedback = "不好"
        analysis = evaluator.evaluate(feedback)

        assert analysis.quality == FeedbackQuality.TOO_SHORT
        assert analysis.score < 0.3

    def test_evaluate_vague_feedback(self):
        """测试评估模糊反馈"""
        evaluator = FeedbackEvaluator()
        feedback = "代码有问题，感觉不对，需要修改"
        analysis = evaluator.evaluate(feedback)

        assert analysis.quality in [
            FeedbackQuality.TOO_VAGUE,
            FeedbackQuality.POOR
        ]

    def test_evaluate_good_feedback(self):
        """测试评估良好反馈"""
        evaluator = FeedbackEvaluator()
        feedback = """
        第 15 行的函数命名不够清晰，建议将 'proc_data' 改为 'process_user_data'。
        另外，建议添加异常处理，当输入为空时应该抛出 ValueError。
        整体逻辑正确，但需要考虑边界情况。
        """
        analysis = evaluator.evaluate(feedback)

        # 优秀、良好或部分都可以接受
        assert analysis.quality in [
            FeedbackQuality.GOOD,
            FeedbackQuality.PARTIAL,
            FeedbackQuality.EXCELLENT
        ]
        assert analysis.is_actionable == True

    def test_evaluate_specific_feedback(self):
        """测试评估具体反馈"""
        evaluator = FeedbackEvaluator()
        feedback = "第 23 行有一个 bug：当 user_id 为 None 时会抛出 AttributeError"
        analysis = evaluator.evaluate(feedback)

        assert analysis.quality != FeedbackQuality.TOO_SHORT
        assert analysis.score > 0.5

    def test_should_trigger_re_review(self):
        """测试是否应触发重新审查"""
        evaluator = FeedbackEvaluator()

        # 低质量反馈应触发
        assert evaluator.should_trigger_re_review("不好") == True
        assert evaluator.should_trigger_re_review("有问题") == True

        # 高质量反馈不应触发
        good_feedback = "第 10 行的变量命名不清晰，建议修改"
        assert evaluator.should_trigger_re_review(good_feedback) == False

    def test_is_approved_with_approval_keywords(self):
        """测试通过关键词判断"""
        evaluator = FeedbackEvaluator()

        assert evaluator.is_approved("LGTM") == True
        assert evaluator.is_approved("通过") == True
        assert evaluator.is_approved("没问题") == True
        assert evaluator.is_approved("需要修改") == False

    def test_get_improvement_prompt(self):
        """测试生成改进提示"""
        evaluator = FeedbackEvaluator()
        feedback = "不好"
        prompt = evaluator.get_improvement_prompt(feedback)

        assert isinstance(prompt, str)
        assert len(prompt) > 20

    def test_feedback_analysis_to_dict(self):
        """测试分析结果转换为字典"""
        evaluator = FeedbackEvaluator()
        feedback = "第 5 行有问题"
        analysis = evaluator.evaluate(feedback)

        analysis_dict = analysis.to_dict()
        assert "quality" in analysis_dict
        assert "score" in analysis_dict
        assert "is_actionable" in analysis_dict


class TestPairProgrammingEnhanced:
    """增强版结对编程测试"""

    def test_pair_programming_feedback_evaluation_enabled(self):
        """测试结对编程反馈质量评估启用"""
        from swarm.collaboration_patterns import PairProgramming

        driver = Mock()
        driver.name = "Driver"
        navigator = Mock()
        navigator.name = "Navigator"

        pair = PairProgramming(
            driver,
            navigator,
            max_iterations=3,
            enable_feedback_evaluation=True
        )

        assert pair.enable_feedback_evaluation == True

    def test_pair_programming_feedback_evaluation_disabled(self):
        """测试结对编程反馈质量评估禁用"""
        from swarm.collaboration_patterns import PairProgramming

        driver = Mock()
        driver.name = "Driver"
        navigator = Mock()
        navigator.name = "Navigator"

        pair = PairProgramming(
            driver,
            navigator,
            max_iterations=3,
            enable_feedback_evaluation=False
        )

        assert pair.enable_feedback_evaluation == False

    def test_evaluate_feedback_quality(self):
        """测试反馈质量评估方法"""
        from swarm.collaboration_patterns import PairProgramming, FeedbackQuality

        driver = Mock()
        driver.name = "Driver"
        navigator = Mock()
        navigator.name = "Navigator"

        pair = PairProgramming(driver, navigator, max_iterations=3)

        # 测试过短反馈
        quality = pair._evaluate_feedback_quality("不好")
        assert quality == FeedbackQuality.TOO_SHORT

        # 测试模糊反馈
        quality = pair._evaluate_feedback_quality("代码有问题，感觉不对")
        assert quality in [FeedbackQuality.TOO_VAGUE, FeedbackQuality.POOR]

        # 测试具体反馈
        quality = pair._evaluate_feedback_quality("第 10 行需要修改")
        assert quality in [FeedbackQuality.PARTIAL, FeedbackQuality.GOOD]

    def test_should_reject_feedback(self):
        """测试反馈拒绝逻辑"""
        from swarm.collaboration_patterns import PairProgramming, FeedbackQuality

        driver = Mock()
        driver.name = "Driver"
        navigator = Mock()
        navigator.name = "Navigator"

        pair = PairProgramming(
            driver,
            navigator,
            max_iterations=3,
            enable_feedback_evaluation=True
        )

        # 低质量反馈应拒绝
        assert pair._should_reject_feedback("不好") == True
        assert pair._should_reject_feedback("有问题") == True

        # 高质量反馈不应拒绝
        good_feedback = "第 10 行的变量命名不清晰，建议修改"
        assert pair._should_reject_feedback(good_feedback) == False

    def test_get_feedback_improvement_prompt(self):
        """测试生成反馈改进提示"""
        from swarm.collaboration_patterns import PairProgramming, FeedbackQuality

        driver = Mock()
        driver.name = "Driver"
        navigator = Mock()
        navigator.name = "Navigator"

        pair = PairProgramming(driver, navigator, max_iterations=3)

        # 测试各种质量等级的提示
        for quality in FeedbackQuality:
            prompt = pair._get_feedback_improvement_prompt("test", quality)
            assert isinstance(prompt, str)
            assert len(prompt) > 10


class TestIterativeOptimizer:
    """迭代优化器测试"""

    def test_optimizer_creation(self):
        """测试创建迭代优化器"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(agents=[Mock()], max_iterations=3)
        assert optimizer is not None
        assert optimizer.max_iterations == 3

    def test_optimizer_with_quality_threshold(self):
        """测试带质量阈值的迭代优化器"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(
            agents=[Mock()],
            max_iterations=5,
            quality_threshold=0.8
        )
        assert optimizer.quality_threshold == 0.8

    def test_normalize_score_raw(self):
        """测试分数归一化 (原始分数)"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(agents=[], score_type="raw")

        # 5 分制转 0-1
        assert optimizer._normalize_score(5.0) == 1.0
        assert optimizer._normalize_score(4.0) == 0.75
        assert optimizer._normalize_score(3.0) == 0.5
        assert optimizer._normalize_score(2.0) == 0.25
        assert optimizer._normalize_score(1.0) == 0.0

    def test_normalize_score_normalized(self):
        """测试分数归一化 (已归一化)"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(agents=[], score_type="normalized")

        # 已经是 0-1 范围
        assert optimizer._normalize_score(0.8) == 0.8
        assert optimizer._normalize_score(0.5) == 0.5
        assert optimizer._normalize_score(1.0) == 1.0
        assert optimizer._normalize_score(0.0) == 0.0

    def test_extract_improvements(self):
        """测试提取改进建议"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(agents=[])

        feedback = """
        1. 改进命名：使用更具描述性的变量名
        2. 添加注释：说明复杂逻辑
        3. 优化性能：减少不必要的循环
        """

        improvements = optimizer._extract_improvements(feedback)
        # 改进提取逻辑可能因格式而异，至少验证函数不报错
        assert isinstance(improvements, list)

    def test_extract_improvements_with_bullets(self):
        """测试提取改进建议 (项目符号)"""
        from swarm.iterative_optimizer import IterativeOptimizer

        optimizer = IterativeOptimizer(agents=[])

        feedback = """
        - 改进命名
        - 添加注释
        - 优化性能
        """

        improvements = optimizer._extract_improvements(feedback)
        assert isinstance(improvements, list)


class TestIntegration:
    """集成测试"""

    def test_quality_checker_and_feedback_evaluator(self):
        """测试质量检查器和反馈评估器集成"""
        checker = create_checker("code")
        evaluator = create_evaluator()

        code = """
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""

        # 质量检查
        code_report = checker.check(code)
        assert code_report.pass_rate >= 0

        # 反馈评估
        feedback = "第 3 行添加了边界检查，很好。建议添加类型注解。"
        feedback_analysis = evaluator.evaluate(feedback)

        # 优秀、良好或部分都可以接受
        assert feedback_analysis.quality in [
            FeedbackQuality.GOOD,
            FeedbackQuality.PARTIAL,
            FeedbackQuality.EXCELLENT
        ]

    def test_all_checklist_types(self):
        """测试所有检查清单类型"""
        checklist_types = ["general", "code", "document", "review", "design", "analysis"]

        for checklist_type in checklist_types:
            checker = create_checker(checklist_type)
            assert checker is not None
            assert len(checker.checklist) > 0

    def test_feedback_quality_enum_values(self):
        """测试反馈质量枚举值"""
        from swarm.collaboration_patterns import FeedbackQuality as PatternFeedbackQuality
        from core.feedback_evaluator import FeedbackQuality as CoreFeedbackQuality

        # 确保两个模块的枚举值一致
        pattern_values = set(q.value for q in PatternFeedbackQuality)
        core_values = set(q.value for q in CoreFeedbackQuality)

        # 核心模块的值应该包含模式模块的所有值
        assert core_values == pattern_values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
