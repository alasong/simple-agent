#!/usr/bin/env python3
"""
反思学习系统演示

展示反思学习如何分析 workflow 执行并生成优化建议
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.reflection_learning import (
    ReflectionLearningCoordinator,
    ExecutionRecord,
    StepMetrics,
    PerformanceAnalyzer,
    OptimizationSuggester,
    ExperienceStore
)


def demo_basic_usage():
    """演示基本使用"""
    print("\n" + "=" * 60)
    print("演示 1: 基本使用流程")
    print("=" * 60)

    coordinator = ReflectionLearningCoordinator(storage_dir="./demo_reflection")

    # 1. 开始记录
    print("\n[1] 开始记录执行...")
    record_id = coordinator.start("DemoWorkflow", "演示任务")
    print(f"    记录 ID: {record_id}")

    # 2. 模拟执行步骤
    print("\n[2] 模拟执行步骤...")
    for i in range(1, 4):
        coordinator.record_step_start(f"step_{i}", i, f"Agent_{i}")
        time.sleep(0.1)  # 模拟执行时间
        coordinator.record_step_end(
            step_index=i,
            agent_name=f"Agent_{i}",
            result=f"步骤{i}完成",
            success=True,
            iterations=1,
            tool_calls=2,
            input_text=f"输入{i}"
        )
        print(f"    步骤{i}执行完成")

    # 3. 结束记录
    print("\n[3] 结束记录...")
    coordinator.finish(success=True, final_output="演示输出")

    # 4. 获取统计
    print("\n[4] 性能统计:")
    stats = coordinator.get_performance_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # 5. 获取建议
    print("\n[5] 优化建议:")
    suggestions = coordinator.get_optimization_suggestions()
    if suggestions:
        for s in suggestions[:3]:  # 显示前 3 个
            print(f"    [{s.priority}] {s.title} - 预期提升{s.expected_improvement}%")
    else:
        print("    暂无建议 (演示执行太简单)")


def demo_bottleneck_analysis():
    """演示瓶颈分析"""
    print("\n" + "=" * 60)
    print("演示 2: 瓶颈分析")
    print("=" * 60)

    now = time.time()

    # 创建一个包含多种瓶颈的执行记录
    record = ExecutionRecord(
        record_id="demo_bottleneck_001",
        workflow_name="ComplexWorkflow",
        task_description="复杂任务处理",
        task_hash="abc123",
        start_time=now,
        end_time=now + 200,
        total_duration=200,
        steps=[
            # 慢步骤 (50 秒)
            StepMetrics(
                step_name="slow_analysis",
                step_index=1,
                agent_name="Developer",
                instance_id=None,
                start_time=now,
                end_time=now + 50,
                duration=50,
                input_length=1000,
                output_length=5000,
                iterations=5,
                tool_calls=10,
                success=True
            ),
            # 正常步骤
            StepMetrics(
                step_name="normal_step",
                step_index=2,
                agent_name="Reviewer",
                instance_id=None,
                start_time=now + 50,
                end_time=now + 60,
                duration=10,
                input_length=5000,
                output_length=2000,
                iterations=1,
                tool_calls=2,
                success=True
            ),
            # 另一个慢步骤 (40 秒)
            StepMetrics(
                step_name="slow_generation",
                step_index=3,
                agent_name="Generator",
                instance_id=None,
                start_time=now + 60,
                end_time=now + 100,
                duration=40,
                input_length=2000,
                output_length=8000,
                iterations=3,
                tool_calls=8,
                success=True
            ),
            # 冗余步骤 (与步骤 2 相似)
            StepMetrics(
                step_name="redundant_check",
                step_index=4,
                agent_name="Reviewer",
                instance_id=None,
                start_time=now + 100,
                end_time=now + 110,
                duration=10,
                input_length=5000,
                output_length=2000,
                iterations=1,
                tool_calls=2,
                success=True
            ),
            # 更多步骤形成长链路
            StepMetrics("step5", 5, "Agent5", None, now+110, now+130, 20, 100, 200, 1, 2, True),
            StepMetrics("step6", 6, "Agent6", None, now+130, now+150, 20, 100, 200, 1, 2, True),
            StepMetrics("step7", 7, "Agent7", None, now+150, now+170, 20, 100, 200, 1, 2, True),
        ],
        success=True,
        parallel_steps=0,
        sequential_steps=7,
        retry_count=4,
        total_token_usage=50000
    )

    # 分析
    analyzer = PerformanceAnalyzer()
    bottlenecks, stats = analyzer.analyze(record)

    print(f"\n执行记录：{record.record_id}")
    print(f"总耗时：{stats['total_duration']}秒")
    print(f"步骤数：{stats['total_steps']}")
    print(f"平均步骤耗时：{stats['avg_step_duration']:.1f}秒")
    print(f"重试次数：{stats['total_retries']}")

    print(f"\n识别到 {len(bottlenecks)} 个瓶颈:")
    for b in bottlenecks:
        print(f"\n  [{b.severity.upper()}] {b.type.value}")
        print(f"  描述：{b.description}")
        print(f"  影响：{b.impact_percentage}% ({b.impact_seconds:.1f}秒)")

    # 生成建议
    suggester = OptimizationSuggester()
    suggestions = suggester.generate_suggestions(bottlenecks, record)

    print(f"\n生成 {len(suggestions)} 个优化建议:")
    for s in suggestions:
        print(f"\n  [优先级{s.priority}] {s.title}")
        print(f"  类型：{s.type.value}")
        print(f"  预期提升：{s.expected_improvement}%")
        print(f"  实施方法：{s.implementation}")
        print(f"  置信度：{s.confidence}")


def demo_experience_learning():
    """演示经验学习"""
    print("\n" + "=" * 60)
    print("演示 3: 经验学习与复用")
    print("=" * 60)

    store = ExperienceStore(storage_file="./demo_experiences.json")

    # 存储历史经验
    print("\n[1] 存储历史经验...")
    exp1_id = store.store_experience(
        task_pattern="代码审查",
        original_workflow="sequential_v1",
        optimized_workflow="parallel_v2",
        original_duration=120,
        optimized_duration=60,
        optimizations_applied=["parallelize", "skip_redundant"]
    )
    print(f"    经验 1 ID: {exp1_id}")

    exp2_id = store.store_experience(
        task_pattern="文档生成",
        original_workflow="basic_v1",
        optimized_workflow="template_v2",
        original_duration=90,
        optimized_duration=45,
        optimizations_applied=["use_template", "merge_steps"]
    )
    print(f"    经验 2 ID: {exp2_id}")

    # 查找相似经验
    print("\n[2] 查找相似经验...")
    similar = store.find_similar_experiences("审查新的代码模块")
    print(f"    找到 {len(similar)} 条相似经验:")
    for exp in similar:
        print(f"    - 任务模式：{exp.task_pattern}")
        print(f"      优化方案：{exp.optimizations_applied}")
        print(f"      提升：{(1-exp.optimized_duration/exp.original_duration)*100:.0f}%")
        print(f"      成功率：{exp.success_count/max(1,exp.total_count)*100:.0f}%")

    # 获取统计
    print("\n[3] 经验库统计:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"    {key}: {value}")


def demo_optimization_types():
    """演示优化类型"""
    print("\n" + "=" * 60)
    print("演示 4: 优化类型详解")
    print("=" * 60)

    from core.reflection_learning import Bottleneck, BottleneckType

    suggester = OptimizationSuggester()

    # 模拟各种瓶颈
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.SLOW_STEP,
            step_indices=[1],
            severity="high",
            description="步骤 1 执行过慢 (50 秒)",
            impact_seconds=30,
            impact_percentage=25
        ),
        Bottleneck(
            type=BottleneckType.LONG_CHAIN,
            step_indices=[1, 2, 3, 4, 5, 6],
            severity="medium",
            description="串行链路过长 (6 步)",
            impact_seconds=40,
            impact_percentage=33
        ),
        Bottleneck(
            type=BottleneckType.WAIT_TIME,
            step_indices=[2, 3],
            severity="high",
            description="步骤 2 和 3 可并行执行",
            impact_seconds=20,
            impact_percentage=17
        ),
        Bottleneck(
            type=BottleneckType.REDUNDANT_STEP,
            step_indices=[4],
            severity="low",
            description="步骤 4 与步骤 2 输出相似",
            impact_seconds=10,
            impact_percentage=8
        ),
    ]

    suggestions = suggester.generate_suggestions(bottlenecks, None)

    print("\n优化建议汇总:")
    print("-" * 60)
    for i, s in enumerate(suggestions, 1):
        print(f"\n{i}. {s.title}")
        print(f"   类型：{s.type.value}")
        print(f"   优先级：{s.priority}/5")
        print(f"   预期提升：{s.expected_improvement}%")
        print(f"   置信度：{s.confidence*100:.0f}%")
        print(f"   实施：{s.implementation}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("       反思学习系统演示")
    print("=" * 60)

    try:
        demo_basic_usage()
        demo_bottleneck_analysis()
        demo_experience_learning()
        demo_optimization_types()

        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        print("\n清理临时文件...")
        import shutil
        for f in ["./demo_reflection", "./demo_experiences.json"]:
            if os.path.exists(f):
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
        print("已清理")

    except Exception as e:
        print(f"\n演示出错：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
