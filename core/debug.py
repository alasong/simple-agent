"""
调试支持 - 显示 Agent 和 Workflow 使用情况
"""

import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentExecutionRecord:
    """Agent 执行记录"""
    agent_name: str
    agent_version: str
    instance_id: Optional[str]
    input: str
    output: str
    start_time: float
    end_time: float
    tool_calls: int = 0
    iterations: int = 1
    success: bool = True
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """执行时长（秒）"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "instance_id": self.instance_id,
            "input": self.input[:200] if len(self.input) > 200 else self.input,
            "output": self.output[:200] if len(self.output) > 200 else self.output,
            "duration": round(self.duration, 3),
            "tool_calls": self.tool_calls,
            "iterations": self.iterations,
            "success": self.success,
            "error": self.error,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat()
        }


@dataclass
class WorkflowStepRecord:
    """Workflow 步骤执行记录"""
    workflow_name: str
    step_name: str
    step_index: int
    agent_name: str
    instance_id: Optional[str]
    input_key: Optional[str]
    output_key: Optional[str]
    input_data: str
    output_data: str
    start_time: float
    end_time: float
    success: bool = True
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            "workflow_name": self.workflow_name,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "agent_name": self.agent_name,
            "instance_id": self.instance_id,
            "duration": round(self.duration, 3),
            "success": self.success,
            "error": self.error
        }


@dataclass
class WorkflowExecutionRecord:
    """Workflow 执行记录"""
    workflow_name: str
    description: str
    start_time: float
    end_time: float
    steps: List[WorkflowStepRecord] = field(default_factory=list)
    initial_input: str = ""
    final_output: str = ""
    success: bool = True
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def total_steps(self) -> int:
        return len(self.steps)
    
    @property
    def successful_steps(self) -> int:
        return sum(1 for s in self.steps if s.success)
    
    def to_dict(self) -> Dict:
        return {
            "workflow_name": self.workflow_name,
            "description": self.description,
            "duration": round(self.duration, 3),
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat()
        }


class DebugTracker:
    """
    调试跟踪器
    
    跟踪所有 Agent 和 Workflow 的执行情况
    """
    
    _instance: Optional['DebugTracker'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._agent_records: List[AgentExecutionRecord] = []
        self._workflow_records: List[WorkflowExecutionRecord] = []
        self._enabled = True
        self._verbose = False
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    @property
    def verbose(self) -> bool:
        return self._verbose
    
    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value
    
    # ==================== Agent 跟踪 ====================
    
    def start_agent_execution(
        self,
        agent_name: str,
        agent_version: str,
        instance_id: Optional[str],
        input_text: str
    ) -> AgentExecutionRecord:
        """开始 Agent 执行跟踪"""
        if not self._enabled:
            return None
        
        record = AgentExecutionRecord(
            agent_name=agent_name,
            agent_version=agent_version,
            instance_id=instance_id,
            input=input_text,
            output="",
            start_time=time.time(),
            end_time=time.time()
        )
        
        if self._verbose:
            print(f"\n[Debug] Agent 开始执行:")
            print(f"  名称：{agent_name}")
            if instance_id:
                print(f"  实例 ID: {instance_id}")
            print(f"  输入：{input_text[:100]}...")
        
        return record
    
    def end_agent_execution(
        self,
        record: AgentExecutionRecord,
        output: str,
        success: bool = True,
        error: Optional[str] = None,
        tool_calls: int = 0,
        iterations: int = 1
    ):
        """结束 Agent 执行跟踪"""
        if not self._enabled or record is None:
            return
        
        record.output = output
        record.end_time = time.time()
        record.success = success
        record.error = error
        record.tool_calls = tool_calls
        record.iterations = iterations
        
        self._agent_records.append(record)
        
        if self._verbose:
            print(f"\n[Debug] Agent 执行完成:")
            print(f"  状态：{'✓ 成功' if success else '✗ 失败'}")
            print(f"  时长：{record.duration:.3f}s")
            if error:
                print(f"  错误：{error}")
    
    # ==================== Workflow 跟踪 ====================
    
    def start_workflow_execution(
        self,
        workflow_name: str,
        description: str,
        initial_input: str
    ) -> WorkflowExecutionRecord:
        """开始 Workflow 执行跟踪"""
        if not self._enabled:
            return None
        
        record = WorkflowExecutionRecord(
            workflow_name=workflow_name,
            description=description,
            start_time=time.time(),
            end_time=time.time(),
            initial_input=initial_input
        )
        
        if self._verbose:
            print(f"\n{'='*60}")
            print(f"[Debug] Workflow 开始执行:")
            print(f"  名称：{workflow_name}")
            print(f"  描述：{description}")
            print(f"  输入：{initial_input[:100]}...")
            print(f"{'='*60}")
        
        return record
    
    def add_workflow_step(
        self,
        workflow_record: WorkflowExecutionRecord,
        step_name: str,
        step_index: int,
        agent_name: str,
        instance_id: Optional[str],
        input_key: Optional[str],
        output_key: Optional[str],
        input_data: str,
        output_data: str,
        start_time: float,
        end_time: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """添加 Workflow 步骤记录"""
        if not self._enabled or workflow_record is None:
            return
        
        step_record = WorkflowStepRecord(
            workflow_name=workflow_record.workflow_name,
            step_name=step_name,
            step_index=step_index,
            agent_name=agent_name,
            instance_id=instance_id,
            input_key=input_key,
            output_key=output_key,
            input_data=input_data,
            output_data=output_data,
            start_time=start_time,
            end_time=end_time,
            success=success,
            error=error
        )
        
        workflow_record.steps.append(step_record)
        
        if self._verbose:
            print(f"\n[Debug] Workflow 步骤 {step_index}:")
            print(f"  名称：{step_name}")
            print(f"  Agent: {agent_name}")
            if instance_id:
                print(f"  实例 ID: {instance_id}")
            print(f"  状态：{'✓ 成功' if success else '✗ 失败'}")
            print(f"  时长：{step_record.duration:.3f}s")
    
    def end_workflow_execution(
        self,
        record: WorkflowExecutionRecord,
        final_output: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """结束 Workflow 执行跟踪"""
        if not self._enabled or record is None:
            return
        
        record.end_time = time.time()
        record.final_output = final_output
        record.success = success
        record.error = error
        
        self._workflow_records.append(record)
        
        if self._verbose:
            print(f"\n{'='*60}")
            print(f"[Debug] Workflow 执行完成:")
            print(f"  总步骤：{record.total_steps}")
            print(f"  成功：{record.successful_steps}/{record.total_steps}")
            print(f"  总时长：{record.duration:.3f}s")
            if error:
                print(f"  错误：{error}")
            print(f"{'='*60}\n")
    
    # ==================== 统计和报告 ====================
    
    def get_agent_stats(self) -> Dict:
        """获取 Agent 统计"""
        if not self._agent_records:
            return {"count": 0}
        
        total_duration = sum(r.duration for r in self._agent_records)
        total_tool_calls = sum(r.tool_calls for r in self._agent_records)
        successful = sum(1 for r in self._agent_records if r.success)
        
        # 按 Agent 分组
        by_agent = {}
        for record in self._agent_records:
            key = record.agent_name
            if key not in by_agent:
                by_agent[key] = {"count": 0, "success": 0, "total_duration": 0}
            by_agent[key]["count"] += 1
            if record.success:
                by_agent[key]["success"] += 1
            by_agent[key]["total_duration"] += record.duration
        
        return {
            "count": len(self._agent_records),
            "successful": successful,
            "failed": len(self._agent_records) - successful,
            "total_duration": round(total_duration, 3),
            "avg_duration": round(total_duration / len(self._agent_records), 3),
            "total_tool_calls": total_tool_calls,
            "by_agent": {
                k: {
                    "count": v["count"],
                    "success_rate": round(v["success"] / v["count"] * 100, 1),
                    "avg_duration": round(v["total_duration"] / v["count"], 3)
                }
                for k, v in by_agent.items()
            }
        }
    
    def get_workflow_stats(self) -> Dict:
        """获取 Workflow 统计"""
        if not self._workflow_records:
            return {"count": 0}
        
        total_duration = sum(r.duration for r in self._workflow_records)
        total_steps = sum(r.total_steps for r in self._workflow_records)
        successful_steps = sum(r.successful_steps for r in self._workflow_records)
        successful = sum(1 for r in self._workflow_records if r.success)
        
        # 按 Workflow 分组
        by_workflow = {}
        for record in self._workflow_records:
            key = record.workflow_name
            if key not in by_workflow:
                by_workflow[key] = {"count": 0, "success": 0, "total_duration": 0, "total_steps": 0}
            by_workflow[key]["count"] += 1
            if record.success:
                by_workflow[key]["success"] += 1
            by_workflow[key]["total_duration"] += record.duration
            by_workflow[key]["total_steps"] += record.total_steps
        
        return {
            "count": len(self._workflow_records),
            "successful": successful,
            "failed": len(self._workflow_records) - successful,
            "total_duration": round(total_duration, 3),
            "avg_duration": round(total_duration / len(self._workflow_records), 3),
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "step_success_rate": round(successful_steps / total_steps * 100, 1) if total_steps > 0 else 0,
            "by_workflow": {
                k: {
                    "count": v["count"],
                    "success_rate": round(v["success"] / v["count"] * 100, 1),
                    "avg_duration": round(v["total_duration"] / v["count"], 3),
                    "avg_steps": round(v["total_steps"] / v["count"], 1)
                }
                for k, v in by_workflow.items()
            }
        }
    
    def get_summary(self) -> Dict:
        """获取执行摘要"""
        return {
            "agent": self.get_agent_stats(),
            "workflow": self.get_workflow_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    def print_summary(self):
        """打印执行摘要"""
        print("\n" + "=" * 60)
        print("[调试摘要] 执行统计")
        print("=" * 60)
        
        agent_stats = self.get_agent_stats()
        workflow_stats = self.get_workflow_stats()
        
        if agent_stats["count"] > 0:
            print(f"\n📊 Agent 执行:")
            print(f"  总次数：{agent_stats['count']}")
            print(f"  成功：{agent_stats['successful']}")
            print(f"  失败：{agent_stats['failed']}")
            print(f"  总时长：{agent_stats['total_duration']:.3f}s")
            print(f"  平均时长：{agent_stats['avg_duration']:.3f}s")
            print(f"  工具调用：{agent_stats['total_tool_calls']} 次")
            
            if agent_stats.get('by_agent'):
                print(f"\n  按 Agent 统计:")
                for name, stats in agent_stats['by_agent'].items():
                    print(f"    {name}:")
                    print(f"      执行：{stats['count']} 次")
                    print(f"      成功率：{stats['success_rate']}%")
                    print(f"      平均：{stats['avg_duration']:.3f}s")
        
        if workflow_stats["count"] > 0:
            print(f"\n📊 Workflow 执行:")
            print(f"  总次数：{workflow_stats['count']}")
            print(f"  成功：{workflow_stats['successful']}")
            print(f"  失败：{workflow_stats['failed']}")
            print(f"  总时长：{workflow_stats['total_duration']:.3f}s")
            print(f"  平均时长：{workflow_stats['avg_duration']:.3f}s")
            print(f"  总步骤：{workflow_stats['total_steps']}")
            print(f"  成功步骤：{workflow_stats['successful_steps']}")
            print(f"  步骤成功率：{workflow_stats['step_success_rate']}%")
        
        print("\n" + "=" * 60)
    
    def get_recent_agent_records(self, limit: int = 10) -> List[Dict]:
        """获取最近的 Agent 执行记录"""
        return [r.to_dict() for r in self._agent_records[-limit:]]
    
    def get_recent_workflow_records(self, limit: int = 10) -> List[Dict]:
        """获取最近的 Workflow 执行记录"""
        return [r.to_dict() for r in self._workflow_records[-limit:]]
    
    def clear(self):
        """清空所有记录"""
        self._agent_records.clear()
        self._workflow_records.clear()


# 全局跟踪器实例
tracker = DebugTracker()


def enable_debug(verbose: bool = True):
    """启用调试跟踪"""
    tracker.enabled = True
    tracker.verbose = verbose


def disable_debug():
    """禁用调试跟踪"""
    tracker.enabled = False


def get_debug_summary() -> Dict:
    """获取调试摘要"""
    return tracker.get_summary()


def print_debug_summary():
    """打印调试摘要"""
    tracker.print_summary()
