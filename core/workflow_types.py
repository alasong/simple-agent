"""
Workflow 类型定义

包含:
- ResultType: 结果类型枚举
- StepType: 步骤类型枚举
- StepResult: 步骤结果数据类
"""
import json
from typing import List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ResultType(Enum):
    """结果类型"""
    TEXT = "text"       # 文本字符串
    FILE = "file"       # 文件路径
    FILES = "files"     # 多文件
    JSON = "json"       # 结构化数据
    AUTO = "auto"       # 自动检测


class StepType(Enum):
    """步骤类型"""
    SEQUENCE = "sequence"  # 顺序
    PARALLEL = "parallel"  # 并行
    CONDITION = "condition"  # 条件


@dataclass
class StepResult:
    """步骤结果"""
    type: ResultType
    content: Any
    files: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_summary(self, max_length: int = 200) -> str:
        """生成摘要"""
        if self.type == ResultType.FILE:
            return f"[文件] {self.content}"
        elif self.type == ResultType.FILES:
            return f"[{len(self.files)} 个文件] {', '.join(self.files[:3])}"
        elif self.type == ResultType.JSON:
            return f"[JSON] {json.dumps(self.content, ensure_ascii=False)[:max_length]}"
        else:
            text = str(self.content)
            return text[:max_length] + "..." if len(text) > max_length else text


@dataclass
class ParallelExecutionResult:
    """并行执行结果"""
    step_name: str
    instance_id: str
    success: bool
    result: Any = None  # StepResult
    error: str = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_name': self.step_name,
            'instance_id': self.instance_id,
            'success': self.success,
            'result': {
                'type': self.result.type.value,
                'content': self.result.content,
                'files': self.result.files,
                'metadata': self.result.metadata
            } if self.result else None,
            'error': self.error,
            'execution_time': self.execution_time
        }
