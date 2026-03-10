"""
Resilience Layer - 韧性层

包含:
- 自愈系统 (SelfHealing)
- 反思学习 (Reflection Learning)
"""

from simple_agent.core.resilience.self_healing import (
    SelfHealingCoordinator,
    CircuitBreaker,
    RecoveryResult,
    get_coordinator,
)

from simple_agent.core.resilience.reflection import (
    ReflectionLearningCoordinator,
    ExecutionRecord,
    PerformanceAnalyzer,
    get_learning_coordinator,
)

__all__ = [
    # Self Healing
    "SelfHealingCoordinator",
    "CircuitBreaker",
    "RecoveryResult",
    "get_coordinator",
    # Reflection Learning
    "ReflectionLearningCoordinator",
    "ExecutionRecord",
    "PerformanceAnalyzer",
    "get_learning_coordinator",
]
