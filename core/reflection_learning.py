"""
Reflection & Learning System - 反思学习系统

支持：
1. 执行过程记录 - 详细记录 workflow+agent 执行的每个步骤
2. 性能分析 - 识别瓶颈、低效步骤、资源浪费
3. 优化建议生成 - 自动生成具体的优化方案
4. 经验积累 - 将成功的优化策略存储到经验库
5. 自动应用 - 在类似任务中自动应用已验证的优化策略

架构:
┌─────────────────────────────────────────────────────────┐
│              ExecutionRecorder                          │
│              (执行记录器)                                │
│  - 记录每个步骤的执行时间、结果、资源消耗                 │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           PerformanceAnalyzer                           │
│           (性能分析器)                                   │
│  - 识别瓶颈步骤                                          │
│  - 检测低效模式                                          │
│  - 计算优化空间                                          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│        OptimizationSuggester                            │
│        (优化建议生成器)                                  │
│  - 生成具体优化建议                                      │
│  - 优先级排序                                            │
│  - 预估收益                                              │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           ExperienceStore                               │
│           (经验存储库)                                   │
│  - 存储成功的优化策略                                    │
│  - 按任务类型索引                                        │
│  - 支持相似度匹配                                        │
└─────────────────────────────────────────────────────────┘
"""

import json
import os
import time
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

import threading


# ==================== 数据模型 ====================

class OptimizationType(Enum):
    """优化类型"""
    PARALLELIZE = "parallelize"           # 并行化
    SKIP_STEP = "skip_step"               # 跳过步骤
    MERGE_STEPS = "merge_steps"           # 合并步骤
    ADJUST_ORDER = "adjust_order"         # 调整顺序
    REDUCE_ITERATIONS = "reduce_iterations"  # 减少迭代
    INCREASE_ITERATIONS = "increase_iterations"  # 增加迭代
    CHANGE_AGENT = "change_agent"         # 更换 Agent
    ADJUST_TIMEOUT = "adjust_timeout"     # 调整超时
    CACHE_RESULT = "cache_result"         # 缓存结果
    SIMPLIFY_PROMPT = "simplify_prompt"   # 简化提示词


class BottleneckType(Enum):
    """瓶颈类型"""
    SLOW_STEP = "slow_step"              # 步骤过慢
    LONG_CHAIN = "long_chain"            # 链路过长
    REDUNDANT_STEP = "redundant_step"    # 冗余步骤
    WAIT_TIME = "wait_time"              # 等待时间过长
    RETRY_OVERHEAD = "retry_overhead"    # 重试开销
    MEMORY_OVERHEAD = "memory_overhead"  # 内存开销


@dataclass
class StepMetrics:
    """步骤执行指标"""
    step_name: str
    step_index: int
    agent_name: str
    instance_id: Optional[str]
    start_time: float
    end_time: float
    duration: float  # 秒
    input_length: int
    output_length: int
    iterations: int
    tool_calls: int
    success: bool
    error_message: Optional[str] = None
    memory_usage_mb: float = 0.0
    token_usage: int = 0


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    workflow_name: str
    task_description: str
    task_hash: str  # 任务描述的哈希，用于相似度匹配
    start_time: float
    end_time: float
    total_duration: float
    steps: List[StepMetrics]
    success: bool
    final_output: Optional[str] = None
    error_message: Optional[str] = None
    parallel_steps: int = 0
    sequential_steps: int = 0
    retry_count: int = 0
    total_token_usage: int = 0

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "workflow_name": self.workflow_name,
            "task_description": self.task_description,
            "task_hash": self.task_hash,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "steps": [asdict(s) for s in self.steps],
            "success": self.success,
            "final_output": self.final_output,
            "error_message": self.error_message,
            "parallel_steps": self.parallel_steps,
            "sequential_steps": self.sequential_steps,
            "retry_count": self.retry_count,
            "total_token_usage": self.total_token_usage
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecord":
        steps = [StepMetrics(**s) for s in data.get("steps", [])]
        return cls(
            record_id=data["record_id"],
            workflow_name=data["workflow_name"],
            task_description=data["task_description"],
            task_hash=data["task_hash"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            total_duration=data["total_duration"],
            steps=steps,
            success=data["success"],
            final_output=data.get("final_output"),
            error_message=data.get("error_message"),
            parallel_steps=data.get("parallel_steps", 0),
            sequential_steps=data.get("sequential_steps", 0),
            retry_count=data.get("retry_count", 0),
            total_token_usage=data.get("total_token_usage", 0)
        )


@dataclass
class Bottleneck:
    """瓶颈识别结果"""
    type: BottleneckType
    step_indices: List[int]
    severity: str  # "high", "medium", "low"
    description: str
    impact_seconds: float
    impact_percentage: float


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    type: OptimizationType
    priority: int  # 1-5, 5 最高
    title: str
    description: str
    expected_improvement: float  # 预期提升百分比
    implementation: str
    confidence: float  # 置信度 0-1
    related_steps: List[int]


@dataclass
class Experience:
    """经验记录"""
    experience_id: str
    task_pattern: str  # 任务模式关键词
    original_workflow: str
    optimized_workflow: str
    original_duration: float
    optimized_duration: float
    improvement_percentage: float
    optimization_applied: List[str]
    success_count: int = 1
    last_used: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Experience":
        return cls(**data)


# ==================== 执行记录器 ====================

class ExecutionRecorder:
    """
    执行记录器 - 详细记录 workflow+agent 执行过程
    """

    def __init__(self, storage_dir: str = "./execution_logs"):
        self.storage_dir = storage_dir
        self._current_record: Optional[ExecutionRecord] = None
        self._step_start_times: Dict[str, float] = {}
        self._lock = threading.Lock()

        os.makedirs(storage_dir, exist_ok=True)

    def start_recording(self, workflow_name: str, task_description: str) -> str:
        """开始记录"""
        with self._lock:
            record_id = f"{workflow_name}_{int(time.time())}_{os.getpid()}"
            task_hash = hashlib.md5(task_description.encode()).hexdigest()[:8]

            self._current_record = ExecutionRecord(
                record_id=record_id,
                workflow_name=workflow_name,
                task_description=task_description,
                task_hash=task_hash,
                start_time=time.time(),
                end_time=0,
                total_duration=0,
                steps=[],
                success=False
            )
            self._step_start_times = {}

            return record_id

    def record_step_start(self, step_name: str, step_index: int, agent_name: str, instance_id: Optional[str] = None):
        """记录步骤开始"""
        self._step_start_times[f"{step_index}"] = time.time()

    def record_step_end(
        self,
        step_index: int,
        agent_name: str,
        result: str,
        success: bool,
        iterations: int = 1,
        tool_calls: int = 0,
        input_text: str = "",
        error_message: Optional[str] = None
    ):
        """记录步骤结束"""
        if self._current_record is None:
            return

        start_time = self._step_start_times.get(f"{step_index}", time.time())
        end_time = time.time()

        step_metrics = StepMetrics(
            step_name=f"step_{step_index}",
            step_index=step_index,
            agent_name=agent_name,
            instance_id=None,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            input_length=len(input_text),
            output_length=len(result),
            iterations=iterations,
            tool_calls=tool_calls,
            success=success,
            error_message=error_message
        )

        self._current_record.steps.append(step_metrics)

    def record_parallel_execution(self, num_parallel: int):
        """记录并行执行"""
        if self._current_record:
            self._current_record.parallel_steps += num_parallel

    def record_retry(self):
        """记录重试"""
        if self._current_record:
            self._current_record.retry_count += 1

    def finish_recording(self, success: bool, final_output: str = "", error_message: Optional[str] = None):
        """结束记录"""
        if self._current_record is None:
            return

        self._current_record.end_time = time.time()
        self._current_record.total_duration = self._current_record.end_time - self._current_record.start_time
        self._current_record.success = success
        self._current_record.final_output = final_output[:1000] if final_output else ""
        self._current_record.error_message = error_message
        self._current_record.sequential_steps = len(self._current_record.steps)

        # 计算总 token 使用
        total_tokens = sum(s.token_usage for s in self._current_record.steps)
        self._current_record.total_token_usage = total_tokens

        # 保存到文件
        self._save_record(self._current_record)

        # 重置当前记录
        self._current_record = None

    def _save_record(self, record: ExecutionRecord):
        """保存记录到文件"""
        try:
            filename = f"{record.record_id}.json"
            filepath = os.path.join(self.storage_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ExecutionRecorder] 保存记录失败：{e}")

    def get_current_record(self) -> Optional[ExecutionRecord]:
        """获取当前记录"""
        return self._current_record


# ==================== 性能分析器 ====================

class PerformanceAnalyzer:
    """
    性能分析器 - 识别瓶颈和低效模式
    """

    def __init__(self):
        self._bottleneck_thresholds = {
            "slow_step_seconds": 30.0,       # 单步骤超过 30 秒认为过慢
            "long_chain_steps": 5,           # 超过 5 步认为链路过长
            "redundant_similarity": 0.8,     # 输出相似度超过 80% 认为冗余
            "wait_time_ratio": 0.3,          # 等待时间超过 30% 认为过长
            "retry_threshold": 2,            # 重试超过 2 次认为开销大
        }

    def analyze(self, record: ExecutionRecord) -> Tuple[List[Bottleneck], Dict[str, float]]:
        """
        分析执行记录，识别瓶颈

        Returns:
            (瓶颈列表，性能统计)
        """
        bottlenecks = []
        stats = self._calculate_stats(record)

        # 1. 识别慢步骤
        bottlenecks.extend(self._identify_slow_steps(record))

        # 2. 识别过长链路
        bottlenecks.extend(self._identify_long_chain(record))

        # 3. 识别冗余步骤
        bottlenecks.extend(self._identify_redundant_steps(record))

        # 4. 识别重试开销
        bottlenecks.extend(self._identify_retry_overhead(record))

        # 5. 识别并行机会
        bottlenecks.extend(self._identify_parallel_opportunities(record))

        return bottlenecks, stats

    def _calculate_stats(self, record: ExecutionRecord) -> Dict[str, float]:
        """计算性能统计"""
        if not record.steps:
            return {}

        durations = [s.duration for s in record.steps]
        total_duration = sum(durations)

        return {
            "total_duration": record.total_duration,
            "avg_step_duration": sum(durations) / len(durations),
            "max_step_duration": max(durations),
            "min_step_duration": min(durations),
            "total_steps": len(record.steps),
            "success_rate": sum(1 for s in record.steps if s.success) / len(record.steps),
            "total_retries": record.retry_count,
            "parallel_ratio": record.parallel_steps / (record.parallel_steps + record.sequential_steps) if (record.parallel_steps + record.sequential_steps) > 0 else 0,
            "total_token_usage": record.total_token_usage
        }

    def _identify_slow_steps(self, record: ExecutionRecord) -> List[Bottleneck]:
        """识别慢步骤"""
        bottlenecks = []

        for step in record.steps:
            if step.duration > self._bottleneck_thresholds["slow_step_seconds"]:
                impact = step.duration - self._bottleneck_thresholds["slow_step_seconds"]
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.SLOW_STEP,
                    step_indices=[step.step_index],
                    severity="high" if step.duration > 60 else "medium",
                    description=f"步骤 {step.step_index} ({step.agent_name}) 执行过慢：{step.duration:.1f}秒",
                    impact_seconds=impact,
                    impact_percentage=(impact / record.total_duration * 100) if record.total_duration > 0 else 0
                ))

        return bottlenecks

    def _identify_long_chain(self, record: ExecutionRecord) -> List[Bottleneck]:
        """识别过长链路"""
        bottlenecks = []

        if len(record.steps) > self._bottleneck_thresholds["long_chain_steps"]:
            avg_duration = sum(s.duration for s in record.steps) / len(record.steps)
            estimated_savings = (len(record.steps) - 3) * avg_duration * 0.3

            bottlenecks.append(Bottleneck(
                type=BottleneckType.LONG_CHAIN,
                step_indices=list(range(len(record.steps))),
                severity="medium",
                description=f"工作流链路过长：{len(record.steps)}步，建议优化为 3-5 步",
                impact_seconds=estimated_savings,
                impact_percentage=(estimated_savings / record.total_duration * 100) if record.total_duration > 0 else 0
            ))

        return bottlenecks

    def _identify_redundant_steps(self, record: ExecutionRecord) -> List[Bottleneck]:
        """识别冗余步骤（简化版：基于输出长度和时间的启发式判断）"""
        bottlenecks = []

        # 查找输出很短但耗时较长的步骤
        for step in record.steps:
            if step.duration > 10 and step.output_length < 100:
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.REDUNDANT_STEP,
                    step_indices=[step.step_index],
                    severity="low",
                    description=f"步骤 {step.step_index} 可能冗余：耗时{step.duration:.1f}秒，输出仅{step.output_length}字符",
                    impact_seconds=step.duration * 0.5,
                    impact_percentage=(step.duration * 0.5 / record.total_duration * 100) if record.total_duration > 0 else 0
                ))

        return bottlenecks

    def _identify_retry_overhead(self, record: ExecutionRecord) -> List[Bottleneck]:
        """识别重试开销"""
        bottlenecks = []

        if record.retry_count > self._bottleneck_thresholds["retry_threshold"]:
            avg_step_duration = sum(s.duration for s in record.steps) / len(record.steps) if record.steps else 0
            retry_overhead = record.retry_count * avg_step_duration

            bottlenecks.append(Bottleneck(
                type=BottleneckType.RETRY_OVERHEAD,
                step_indices=[],
                severity="high" if record.retry_count > 5 else "medium",
                description=f"重试开销过大：{record.retry_count}次重试，估计浪费{retry_overhead:.1f}秒",
                impact_seconds=retry_overhead,
                impact_percentage=(retry_overhead / record.total_duration * 100) if record.total_duration > 0 else 0
            ))

        return bottlenecks

    def _identify_parallel_opportunities(self, record: ExecutionRecord) -> List[Bottleneck]:
        """识别并行化机会"""
        bottlenecks = []

        # 如果并行比例为 0 且有多个步骤，可能存在并行机会
        if record.parallel_steps == 0 and len(record.steps) >= 3:
            # 查找独立的步骤（简化：基于步骤间的低依赖）
            sequential_duration = sum(s.duration for s in record.steps[1:])  # 假设第一步是独立的

            bottlenecks.append(Bottleneck(
                type=BottleneckType.WAIT_TIME,
                step_indices=[s.step_index for s in record.steps[1:]],
                severity="low",
                description=f"可能存在并行化机会：{len(record.steps)}个步骤顺序执行，可考虑并行化",
                impact_seconds=sequential_duration * 0.5,  # 估计可节省 50%
                impact_percentage=30  # 估计可节省 30%
            ))

        return bottlenecks


# ==================== 优化建议生成器 ====================

class OptimizationSuggester:
    """
    优化建议生成器 - 基于瓶颈生成具体优化建议
    """

    def __init__(self):
        self._optimization_templates = {
            BottleneckType.SLOW_STEP: [
                OptimizationSuggestion(
                    type=OptimizationType.ADJUST_TIMEOUT,
                    priority=4,
                    title="调整超时配置",
                    description="为慢步骤增加超时时间，避免不必要的重试",
                    expected_improvement=20.0,
                    implementation="设置该步骤的 timeout 参数为当前执行时间的 1.5 倍",
                    confidence=0.8,
                    related_steps=[]
                ),
                OptimizationSuggestion(
                    type=OptimizationType.CHANGE_AGENT,
                    priority=3,
                    title="更换更快的 Agent",
                    description="使用更轻量级的 Agent 或调整配置",
                    expected_improvement=30.0,
                    implementation="尝试使用 max_iterations 更小的配置，或切换到更专注的 Agent 类型",
                    confidence=0.6,
                    related_steps=[]
                ),
            ],
            BottleneckType.LONG_CHAIN: [
                OptimizationSuggestion(
                    type=OptimizationType.MERGE_STEPS,
                    priority=5,
                    title="合并相关步骤",
                    description="将多个相关步骤合并为一个复合步骤",
                    expected_improvement=40.0,
                    implementation="分析步骤间的依赖关系，将连续的相关步骤合并为一个多任务 Agent",
                    confidence=0.75,
                    related_steps=[]
                ),
                OptimizationSuggestion(
                    type=OptimizationType.SKIP_STEP,
                    priority=3,
                    title="移除冗余步骤",
                    description="识别并移除对最终结果贡献小的步骤",
                    expected_improvement=25.0,
                    implementation="分析每个步骤的输出对最终结果的贡献度，移除低贡献步骤",
                    confidence=0.6,
                    related_steps=[]
                ),
            ],
            BottleneckType.REDUNDANT_STEP: [
                OptimizationSuggestion(
                    type=OptimizationType.SKIP_STEP,
                    priority=4,
                    title="跳过冗余步骤",
                    description="移除产出低的步骤",
                    expected_improvement=50.0,
                    implementation="直接从工作流中移除该步骤，观察对最终结果的影响",
                    confidence=0.7,
                    related_steps=[]
                ),
            ],
            BottleneckType.WAIT_TIME: [
                OptimizationSuggestion(
                    type=OptimizationType.PARALLELIZE,
                    priority=5,
                    title="并行化执行",
                    description="将独立步骤改为并行执行",
                    expected_improvement=50.0,
                    implementation="使用 ParallelWorkflow 或设置 parallel=true，将无依赖的步骤并行化",
                    confidence=0.85,
                    related_steps=[]
                ),
            ],
            BottleneckType.RETRY_OVERHEAD: [
                OptimizationSuggestion(
                    type=OptimizationType.INCREASE_ITERATIONS,
                    priority=4,
                    title="增加迭代次数",
                    description="增加 Agent 的 max_iterations，减少因达到上限导致的重试",
                    expected_improvement=30.0,
                    implementation="将频繁重试的 Agent 的 max_iterations 增加到 15-20",
                    confidence=0.7,
                    related_steps=[]
                ),
            ],
        }

    def generate_suggestions(
        self,
        bottlenecks: List[Bottleneck],
        record: ExecutionRecord
    ) -> List[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []

        for bottleneck in bottlenecks:
            templates = self._optimization_templates.get(bottleneck.type, [])

            for template in templates:
                suggestion = OptimizationSuggestion(
                    type=template.type,
                    priority=template.priority,
                    title=template.title,
                    description=f"[{bottleneck.severity.upper()}] {template.description}\n\n问题：{bottleneck.description}",
                    expected_improvement=template.expected_improvement * (bottleneck.impact_percentage / 100 + 1),
                    implementation=template.implementation,
                    confidence=template.confidence,
                    related_steps=bottleneck.step_indices
                )
                suggestions.append(suggestion)

        # 按优先级排序
        suggestions.sort(key=lambda s: (-s.priority, -s.expected_improvement))

        return suggestions

    def generate_summary(self, record: ExecutionRecord, suggestions: List[OptimizationSuggestion]) -> str:
        """生成优化总结"""
        if not suggestions:
            return "执行效率良好，暂无优化建议"

        lines = [
            "=" * 60,
            "工作流执行优化建议",
            "=" * 60,
            f"任务：{record.task_description[:50]}...",
            f"总耗时：{record.total_duration:.1f}秒",
            f"步骤数：{len(record.steps)}",
            f"并行步骤：{record.parallel_steps}",
            f"重试次数：{record.retry_count}",
            "",
            f"找到 {len(suggestions)} 个优化建议:",
            ""
        ]

        for i, sug in enumerate(suggestions[:5], 1):  # 只显示前 5 个
            lines.extend([
                f"{i}. [{sug.type.value.upper()}] {sug.title} (优先级：{sug.priority})",
                f"   {sug.description[:100]}...",
                f"   预期提升：{sug.expected_improvement:.1f}%",
                f"   实施：{sug.implementation[:80]}...",
                ""
            ])

        if len(suggestions) > 5:
            lines.append(f"... 还有 {len(suggestions) - 5} 个建议")

        return "\n".join(lines)


# ==================== 经验存储库 ====================

class ExperienceStore:
    """
    经验存储库 - 存储和检索成功的优化经验
    """

    def __init__(self, storage_file: str = "./experience_db.json"):
        self.storage_file = storage_file
        self._experiences: Dict[str, Experience] = {}
        self._lock = threading.Lock()

        self._load_experiences()

    def _load_experiences(self):
        """加载经验"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for exp_data in data:
                        exp = Experience.from_dict(exp_data)
                        self._experiences[exp.experience_id] = exp
            except Exception as e:
                print(f"[ExperienceStore] 加载经验失败：{e}")

    def _save_experiences(self):
        """保存经验"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(e) for e in self._experiences.values()], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ExperienceStore] 保存经验失败：{e}")

    def store_experience(
        self,
        task_pattern: str,
        original_workflow: str,
        optimized_workflow: str,
        original_duration: float,
        optimized_duration: float,
        optimizations_applied: List[str]
    ) -> str:
        """存储优化经验"""
        with self._lock:
            experience_id = hashlib.md5(f"{task_pattern}_{time.time()}".encode()).hexdigest()[:12]

            improvement = ((original_duration - optimized_duration) / original_duration * 100) if original_duration > 0 else 0

            experience = Experience(
                experience_id=experience_id,
                task_pattern=task_pattern,
                original_workflow=original_workflow,
                optimized_workflow=optimized_workflow,
                original_duration=original_duration,
                optimized_duration=optimized_duration,
                improvement_percentage=improvement,
                optimization_applied=optimizations_applied,
                success_count=1,
                last_used=datetime.now().isoformat()
            )

            self._experiences[experience_id] = experience
            self._save_experiences()

            return experience_id

    def find_similar_experiences(self, task_description: str, threshold: float = 0.6) -> List[Experience]:
        """查找相似任务的经验"""
        from difflib import SequenceMatcher

        similar = []

        for exp in self._experiences.values():
            # 简单的相似度计算
            similarity = SequenceMatcher(None, task_description, exp.task_pattern).ratio()

            if similarity >= threshold:
                similar.append((similarity, exp))

        # 按相似度排序
        similar.sort(key=lambda x: -x[0])

        return [exp for _, exp in similar]

    def update_experience_success(self, experience_id: str):
        """更新经验成功次数"""
        with self._lock:
            if experience_id in self._experiences:
                self._experiences[experience_id].success_count += 1
                self._experiences[experience_id].last_used = datetime.now().isoformat()
                self._save_experiences()

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self._experiences:
            return {"total": 0}

        return {
            "total": len(self._experiences),
            "avg_improvement": sum(e.improvement_percentage for e in self._experiences.values()) / len(self._experiences),
            "total_successes": sum(e.success_count for e in self._experiences.values()),
            "top_optimizations": self._get_top_optimizations()
        }

    def _get_top_optimizations(self) -> List[Dict]:
        """获取最常见的优化"""
        opt_counts = defaultdict(int)
        for exp in self._experiences.values():
            for opt in exp.optimization_applied:
                opt_counts[opt] += 1

        sorted_opts = sorted(opt_counts.items(), key=lambda x: -x[1])[:5]
        return [{"name": name, "count": count} for name, count in sorted_opts]


# ==================== 反思学习协调器 ====================

class ReflectionLearningCoordinator:
    """
    反思学习协调器 - 统一管理反思学习流程

    使用方式:
    1. 执行前：coordinator.start(task_description)
    2. 执行中：coordinator.record_step_start/end(...)
    3. 执行后：coordinator.finish(success, output)
    4. 获取建议：coordinator.get_optimization_suggestions()
    5. 应用经验：coordinator.apply_learned_experience(task_description)
    """

    def __init__(self, storage_dir: str = "./reflection_logs"):
        self.recorder = ExecutionRecorder(storage_dir=f"{storage_dir}/records")
        self.analyzer = PerformanceAnalyzer()
        self.suggester = OptimizationSuggester()
        self.experience_store = ExperienceStore(f"{storage_dir}/experience_db.json")

        self._current_bottlenecks: List[Bottleneck] = []
        self._current_suggestions: List[OptimizationSuggestion] = []
        self._current_stats: Dict[str, float] = {}

    def start(self, workflow_name: str, task_description: str) -> str:
        """开始记录和反思"""
        # 检查是否有类似经验
        similar_experiences = self.experience_store.find_similar_experiences(task_description)

        if similar_experiences:
            print(f"\n[反思学习] 发现 {len(similar_experiences)} 条相似经验:")
            for exp in similar_experiences[:2]:
                print(f"  - 优化：{exp.optimization_applied}")
                print(f"  - 提升：{exp.improvement_percentage:.1f}%")

        # 开始记录
        record_id = self.recorder.start_recording(workflow_name, task_description)

        return record_id

    def record_step_start(self, step_name: str, step_index: int, agent_name: str, instance_id: Optional[str] = None):
        """记录步骤开始"""
        self.recorder.record_step_start(step_name, step_index, agent_name, instance_id)

    def record_step_end(
        self,
        step_index: int,
        agent_name: str,
        result: str,
        success: bool,
        iterations: int = 1,
        tool_calls: int = 0,
        input_text: str = "",
        error_message: Optional[str] = None
    ):
        """记录步骤结束"""
        self.recorder.record_step_end(
            step_index, agent_name, result, success,
            iterations, tool_calls, input_text, error_message
        )

    def finish(self, success: bool, final_output: str = "", error_message: Optional[str] = None):
        """结束记录并分析"""
        self.recorder.finish_recording(success, final_output, error_message)

        # 分析性能
        record = self.recorder.get_current_record()
        if record:
            self._current_bottlenecks, self._current_stats = self.analyzer.analyze(record)
            self._current_suggestions = self.suggester.generate_suggestions(self._current_bottlenecks, record)

            # 打印优化建议
            if self._current_suggestions:
                print("\n" + self.suggester.generate_summary(record, self._current_suggestions))

    def get_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """获取优化建议"""
        return self._current_suggestions

    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        return self._current_stats

    def apply_learned_experience(self, task_description: str) -> Optional[Dict]:
        """应用已学习的经验"""
        similar = self.experience_store.find_similar_experiences(task_description)

        if not similar:
            return None

        # 返回最相似的经验
        best_exp = similar[0]

        # 更新成功使用次数
        self.experience_store.update_experience_success(best_exp.experience_id)

        return {
            "experience_id": best_exp.experience_id,
            "optimizations": best_exp.optimization_applied,
            "expected_improvement": best_exp.improvement_percentage
        }

    def store_optimization_result(
        self,
        task_pattern: str,
        original_workflow: str,
        optimized_workflow: str,
        original_duration: float,
        optimized_duration: float,
        optimizations_applied: List[str]
    ):
        """存储优化结果到经验库"""
        self.experience_store.store_experience(
            task_pattern, original_workflow, optimized_workflow,
            original_duration, optimized_duration, optimizations_applied
        )

    def get_experience_statistics(self) -> Dict:
        """获取经验库统计"""
        return self.experience_store.get_statistics()


# ==================== 全局实例 ====================

_learning_coordinator: Optional[ReflectionLearningCoordinator] = None


def get_learning_coordinator(storage_dir: str = "./reflection_logs") -> ReflectionLearningCoordinator:
    """获取反思学习协调器（单例）"""
    global _learning_coordinator
    if _learning_coordinator is None:
        _learning_coordinator = ReflectionLearningCoordinator(storage_dir=storage_dir)
    return _learning_coordinator


def reset_learning_coordinator():
    """重置协调器（用于测试）"""
    global _learning_coordinator
    _learning_coordinator = None
