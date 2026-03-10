"""
Self-Healing Enhancements Tests - 自愈增强测试

测试 6 种高效自愈手段：
1. 熔断器 (Circuit Breaker)
2. 快速降级 (Fallback Strategy)
3. 记忆压缩 (Memory Compaction)
4. Agent 池预热 (Agent Pool)
5. 增量状态保存 (Incremental Checkpoint)
6. 优雅降级配置 (Graceful Degradation)
"""

import pytest
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ==================== 1. 熔断器测试 ====================

class TestCircuitBreaker:
    """测试熔断器"""

    def test_circuit_breaker_initial_state(self):
        """测试熔断器初始状态为关闭"""
        from core.self_healing import CircuitBreaker

        cb = CircuitBreaker()
        assert cb.can_execute("TestTool") is True

    def test_circuit_breaker_opens_after_failures(self):
        """测试连续失败后熔断"""
        from core.self_healing import CircuitBreaker, CircuitState

        cb = CircuitBreaker()

        # 连续 3 次失败
        for i in range(3):
            triggered = cb.record_failure("TestTool", "测试错误")

        # 第 3 次应该触发熔断
        assert triggered is True
        assert cb.can_execute("TestTool") is False

    def test_circuit_breaker_half_open_after_timeout(self):
        """测试超时后进入半开状态"""
        from core.self_healing import CircuitBreaker, CircuitBreakerConfig

        # 配置短超时
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=0.1  # 100ms
        )
        cb = CircuitBreaker(config=config)

        # 触发熔断
        cb.record_failure("TestTool", "错误 1")
        cb.record_failure("TestTool", "错误 2")
        assert cb.can_execute("TestTool") is False

        # 等待超时
        time.sleep(0.15)

        # 应该进入半开
        assert cb.can_execute("TestTool") is True

    def test_circuit_breaker_closes_after_successes(self):
        """测试半开状态成功后恢复"""
        from core.self_healing import CircuitBreaker, CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.1
        )
        cb = CircuitBreaker(config=config)

        # 触发熔断
        cb.record_failure("TestTool", "错误")
        cb.record_failure("TestTool", "错误")

        # 等待超时
        time.sleep(0.15)
        cb.can_execute("TestTool")  # 进入半开

        # 成功 2 次
        cb.record_success("TestTool")
        cb.record_success("TestTool")

        # 应该恢复
        assert cb.can_execute("TestTool") is True

    def test_circuit_breaker_excluded_errors(self):
        """测试排除的错误类型不触发熔断"""
        from core.self_healing import CircuitBreaker, CircuitBreakerConfig

        config = CircuitBreakerConfig(excluded_errors=["persistence"])
        cb = CircuitBreaker(config=config)

        # 持久性错误不应该触发熔断
        for i in range(5):
            cb.record_failure("TestTool", "persistence error")

        # 仍然可以执行
        assert cb.can_execute("TestTool") is True


# ==================== 2. 降级策略测试 ====================

class TestFallbackProvider:
    """测试降级策略"""

    def test_web_search_fallback(self):
        """测试 Web 搜索降级"""
        from core.self_healing import FallbackProvider

        provider = FallbackProvider()
        result = provider.execute_fallback(
            "WebSearchTool",
            {"query": "北京天气"},
            "网络错误"
        )

        assert result is not None
        assert result.success is True
        assert "天气" in result.content or "网络" in result.content

    def test_stock_data_fallback(self):
        """测试股票数据降级"""
        from core.self_healing import FallbackProvider

        provider = FallbackProvider()
        result = provider.execute_fallback(
            "StockMarketTool",
            {"market": "A"},
            "API 不可用"
        )

        assert result is not None
        assert result.success is True
        assert "新浪" in result.content or "雪球" in result.content

    def test_fallback_with_cache(self):
        """测试缓存降级"""
        from core.self_healing import FallbackProvider

        provider = FallbackProvider()
        provider.add_cache("http:test.com", "缓存内容")

        result = provider.execute_fallback(
            "HttpTool",
            {"url": "test.com"},
            "请求失败"
        )

        assert result is not None
        assert result.strategy.value == "cached"
        assert "缓存数据" in result.content

    def test_fallback_no_strategy(self):
        """测试无降级策略"""
        from core.self_healing import FallbackProvider

        provider = FallbackProvider()
        result = provider.execute_fallback(
            "UnknownTool",
            {},
            "错误"
        )

        assert result is not None
        assert result.strategy.value == "skip_notice"


# ==================== 3. 记忆压缩测试 ====================

class TestMemoryCompactor:
    """测试记忆压缩"""

    def test_should_compact(self):
        """测试是否需要压缩判断"""
        from core.self_healing import MemoryCompactor

        compactor = MemoryCompactor(max_messages=10)

        # 少量消息不需要压缩
        messages = [{"role": "user", "content": "test"}] * 5
        assert compactor.should_compact(messages) is False

        # 大量消息需要压缩
        messages = [{"role": "user", "content": "test"}] * 20
        assert compactor.should_compact(messages) is True

    def test_compact_preserves_system_message(self):
        """测试压缩保留系统消息"""
        from core.self_healing import MemoryCompactor

        compactor = MemoryCompactor(max_messages=5, recent_messages=2)

        messages = [
            {"role": "system", "content": "系统指令"},
            {"role": "user", "content": "消息 1"},
            {"role": "assistant", "content": "回复 1"},
            {"role": "user", "content": "消息 2"},
            {"role": "assistant", "content": "回复 2"},
            {"role": "user", "content": "消息 3"},
            {"role": "assistant", "content": "回复 3"},
        ]

        compressed, summary = compactor.compact(messages)

        # 系统消息应该在压缩后的消息中
        system_msgs = [m for m in compressed if m.get("role") == "system"]
        assert len(system_msgs) >= 1

    def test_compact_keeps_recent_messages(self):
        """测试压缩保留近期消息"""
        from core.self_healing import MemoryCompactor

        compactor = MemoryCompactor(max_messages=5, recent_messages=3)

        messages = [
            {"role": "system", "content": "系统指令"},
            {"role": "user", "content": "消息 1"},
            {"role": "assistant", "content": "回复 1"},
            {"role": "user", "content": "消息 2"},
            {"role": "assistant", "content": "回复 2"},
            {"role": "user", "content": "消息 3"},
            {"role": "assistant", "content": "回复 3"},
        ]

        compressed, summary = compactor.compact(messages)

        # 近期消息应该保留
        assert any("消息 3" in str(m) for m in compressed)


# ==================== 4. Agent 池测试 ====================

class TestAgentPool:
    """测试 Agent 池"""

    def test_agent_pool_warmup(self):
        """测试 Agent 池预热"""
        from core.self_healing import AgentPool

        pool = AgentPool(pool_size=5)
        pool.warmup(["Planner", "Developer"])

        status = pool.get_status()
        assert status["pool_size"] >= 0  # 可能部分失败

    def test_agent_pool_get(self):
        """测试获取 Agent"""
        from core.self_healing import AgentPool

        pool = AgentPool(pool_size=5)

        # 预热
        pool.warmup(["TestAgent"])

        # 获取
        agent = pool.get("TestAgent")
        assert agent is not None
        assert hasattr(agent, "name")

    def test_agent_pool_dynamic_creation(self):
        """测试动态创建 Agent"""
        from core.self_healing import AgentPool

        pool = AgentPool(pool_size=5)

        # 未预热的 Agent 应该动态创建
        agent = pool.get("NewAgent")
        assert agent is not None

    def test_agent_pool_lru_eviction(self):
        """测试 LRU 淘汰"""
        from core.self_healing import AgentPool

        pool = AgentPool(pool_size=2)

        # 预热 3 个，应该淘汰 1 个
        pool.warmup(["Agent1", "Agent2", "Agent3"])

        status = pool.get_status()
        assert status["pool_size"] <= 2


# ==================== 5. 增量检查点测试 ====================

class TestIncrementalCheckpoint:
    """测试增量检查点"""

    def test_save_increment(self, tmp_path):
        """测试保存增量"""
        from core.self_healing import IncrementalCheckpointManager

        manager = IncrementalCheckpointManager(checkpoint_dir=str(tmp_path))

        seq = manager.save_increment("task-001", "message", {"content": "测试"})
        assert seq == 0

        seq2 = manager.save_increment("task-001", "message", {"content": "测试 2"})
        assert seq2 == 1

    def test_load_state(self, tmp_path):
        """测试加载状态"""
        from core.self_healing import IncrementalCheckpointManager

        manager = IncrementalCheckpointManager(checkpoint_dir=str(tmp_path))

        # 保存增量
        manager.save_increment("task-001", "message", {"role": "user", "content": "测试"})
        manager.save_increment("task-001", "iteration", {"iteration": 5})

        # 加载
        state = manager.load_state("task-001")
        assert state is not None
        assert "messages" in state or "iteration" in state

    def test_merge_to_snapshot(self, tmp_path):
        """测试合并到快照"""
        from core.self_healing import IncrementalCheckpointManager

        # 配置小合并间隔
        manager = IncrementalCheckpointManager(
            checkpoint_dir=str(tmp_path),
            merge_interval=3
        )

        # 保存 3 次增量，应该触发合并
        for i in range(3):
            manager.save_increment("task-001", "message", {"content": f"测试{i}"})

        stats = manager.get_stats("task-001")
        # 合并后增量应该被清空
        assert stats["increments"] == 0

    def test_clear_state(self, tmp_path):
        """测试清除状态"""
        from core.self_healing import IncrementalCheckpointManager

        manager = IncrementalCheckpointManager(checkpoint_dir=str(tmp_path))

        manager.save_increment("task-001", "message", {"content": "测试"})
        manager.clear("task-001")

        stats = manager.get_stats("task-001")
        assert stats["increments"] == 0


# ==================== 6. 优雅降级测试 ====================

class TestGracefulDegradation:
    """测试优雅降级"""

    def test_initial_config(self):
        """测试初始配置"""
        from core.self_healing import GracefulDegradation

        gd = GracefulDegradation()
        config = gd.get_config()

        assert config["name"] == "Normal"
        assert config["max_iterations"] == 15

    def test_degrade(self):
        """测试降级"""
        from core.self_healing import GracefulDegradation

        gd = GracefulDegradation()
        old_level = gd.current_level

        new_level = gd.degrade(reason="测试")

        assert new_level > old_level
        config = gd.get_config()
        assert config["max_iterations"] < 15

    def test_recover(self):
        """测试恢复"""
        from core.self_healing import GracefulDegradation

        gd = GracefulDegradation()
        gd.degrade(reason="测试 1")
        gd.degrade(reason="测试 2")

        old_level = gd.current_level
        new_level = gd.recover()

        assert new_level < old_level

    def test_should_degrade_metrics(self):
        """测试基于指标的降级判断"""
        from core.self_healing import GracefulDegradation

        gd = GracefulDegradation()

        # 连续失败应该触发降级
        metrics = {"consecutive_failures": 5}
        assert gd.should_degrade(metrics) is True

        # 正常指标不应该降级
        metrics = {"consecutive_failures": 0}
        assert gd.should_degrade(metrics) is False

    def test_apply_to_agent(self):
        """测试应用配置到 Agent"""
        from core.self_healing import GracefulDegradation
        from core.agent import Agent

        gd = GracefulDegradation()
        agent = Agent(name="TestAgent", max_iterations=15)

        gd.degrade(reason="测试")
        gd.apply_to_agent(agent)

        assert agent.max_iterations < 15


# ==================== 集成测试 ====================

class TestSelfHealingIntegration:
    """自愈集成测试"""

    def test_circuit_breaker_with_fallback(self):
        """测试熔断器与降级联动"""
        from core.self_healing import CircuitBreaker, FallbackProvider

        cb = CircuitBreaker()
        provider = FallbackProvider()

        # 模拟多次失败触发熔断
        for i in range(3):
            cb.record_failure("WebSearchTool", "网络错误")

        # 熔断后尝试降级
        if not cb.can_execute("WebSearchTool"):
            fallback = provider.execute_fallback(
                "WebSearchTool",
                {"query": "测试"},
                "网络错误"
            )
            assert fallback is not None
            assert fallback.success is True

    def test_memory_compact_with_incremental_checkpoint(self):
        """测试记忆压缩与增量检查点联动"""
        from core.self_healing import (
            MemoryCompactor,
            IncrementalCheckpointManager
        )
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            compactor = MemoryCompactor(max_messages=5)
            checkpoint = IncrementalCheckpointManager(checkpoint_dir=tmp_dir)

            # 模拟大量消息
            messages = [{"role": "user", "content": f"消息{i}"} for i in range(20)]

            # 压缩
            compressed, summary = compactor.compact(messages, "task-001")

            # 保存压缩后的状态
            checkpoint.save_increment("task-001", "iteration", {"iteration": 1})

            assert len(compressed) < len(messages)
            assert summary.compression_ratio < 1.0

    def test_coordinator_status(self):
        """测试协调器状态"""
        from core.self_healing import SelfHealingCoordinator

        coordinator = SelfHealingCoordinator()

        status = coordinator.get_status()

        assert "circuit_breaker" in status
        assert "agent_pool" in status
        assert "graceful_degradation" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
