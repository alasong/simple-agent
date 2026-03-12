"""
Workflow 并行执行支持

包含:
- ParallelStep: 并行步骤
- ParallelWorkflow: 并行工作流执行器
- create_parallel_workflow: 便捷创建函数
"""
import asyncio
import json
import os
import shutil
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from simple_agent.core.agent import Agent
from .workflow_types import ResultType, StepResult, ParallelExecutionResult


@dataclass
class ParallelStep:
    """并行步骤"""
    name: str
    agent: Agent
    instance_id: Optional[str] = None
    input_key: Optional[str] = None
    output_key: Optional[str] = None
    timeout: Optional[float] = None  # 超时时间（秒）
    ignore_errors: bool = False  # 是否忽略错误

    async def run_async(
        self,
        context: Dict,
        shared_memory: bool = True,
        verbose: bool = True,
        output_dir: Optional[str] = None,
        step_index: int = 0
    ) -> ParallelExecutionResult:
        """
        异步执行步骤

        Args:
            context: 工作流上下文
            shared_memory: 是否共享上下文
            verbose: 是否打印详细过程
            output_dir: 输出目录
            step_index: 步骤索引

        Returns:
            ParallelExecutionResult: 执行结果
        """
        start_time = time.time()

        try:
            # 构建输入
            if self.input_key and self.input_key in context:
                user_input = str(context[self.input_key])
            else:
                user_input = str(context.get("_initial_input", ""))

            # 共享上下文
            if shared_memory:
                context_summary = self._build_context_summary(context)
                if context_summary:
                    user_input = f"{context_summary}\n\n当前任务：{user_input}"

            if verbose:
                print(f"\n[并行] 步骤：{self.name} (实例：{self.instance_id or 'default'})")

            # 执行 Agent（支持同步和异步）
            if asyncio.iscoroutinefunction(self.agent.run):
                result_text = await self.agent.run(user_input, verbose=False)
            else:
                # 同步执行放在线程池中
                loop = asyncio.get_event_loop()
                result_text = await loop.run_in_executor(
                    None,
                    lambda: self.agent.run(user_input, verbose=False)
                )

            # 解析结果
            step_result = self._parse_result(result_text)

            # 保存输出
            execution_time = time.time() - start_time

            return ParallelExecutionResult(
                step_name=self.name,
                instance_id=self.instance_id or "default",
                success=True,
                result=step_result,
                execution_time=execution_time
            )

        except asyncio.TimeoutError:
            return ParallelExecutionResult(
                step_name=self.name,
                instance_id=self.instance_id or "default",
                success=False,
                error=f"执行超时（超过 {self.timeout}秒）",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ParallelExecutionResult(
                step_name=self.name,
                instance_id=self.instance_id or "default",
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _build_context_summary(self, context: Dict) -> str:
        """构建上下文摘要"""
        parts = []

        if context.get("_initial_input"):
            parts.append(f"初始任务：{context['_initial_input']}")

        step_results = context.get("_step_results", {})
        if step_results:
            parts.append("\n之前步骤的结果:")
            for step_name, result in step_results.items():
                if isinstance(result, StepResult):
                    summary = result.to_summary()
                    parts.append(f"  [{step_name}]: {summary}")

        return "\n".join(parts) if parts else ""

    def _parse_result(self, result_text: str) -> StepResult:
        """解析结果"""
        import re
        result = StepResult(type=ResultType.TEXT, content=result_text)

        file_patterns = [
            r'(?:文件 | 保存到 | 写入 | 输出)[:：]?\s*([/\w\-\.]+\.\w+)',
            r'([/\w\-\.]+\.(?:txt|json|csv|py|md|html|xml))',
        ]

        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, result_text)
            files.extend(matches)

        if len(files) == 1:
            result.type = ResultType.FILE
            result.content = files[0]
            result.files = files
        elif len(files) > 1:
            result.type = ResultType.FILES
            result.files = files

        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result.type = ResultType.JSON
                result.content = json.loads(json_match.group(1))
        except:
            pass

        return result


class ParallelWorkflow:
    """
    并行工作流执行器

    支持:
    - 真正并行执行多个独立任务（使用 asyncio.gather）
    - 超时控制
    - 错误隔离
    - 结果聚合

    示例:
        parallel = ParallelWorkflow()

        # 添加并行任务
        parallel.add_task("审查项目 A", reviewer_agent, instance_id="project-A")
        parallel.add_task("审查项目 B", reviewer_agent, instance_id="project-B")
        parallel.add_task("审查项目 C", reviewer_agent, instance_id="project-C")

        # 执行
        results = await parallel.execute()
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        default_timeout: Optional[float] = None,
        continue_on_error: bool = True
    ):
        """
        初始化并行工作流

        Args:
            max_concurrent: 最大并发数
            default_timeout: 默认超时时间（秒）
            continue_on_error: 错误时是否继续执行其他任务
        """
        self.tasks: List[ParallelStep] = []
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.continue_on_error = continue_on_error
        self.context: Dict[str, Any] = {}
        self.shared_memory = True

    def add_task(
        self,
        name: str,
        agent: Agent,
        instance_id: Optional[str] = None,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        timeout: Optional[float] = None,
        ignore_errors: bool = False
    ) -> "ParallelWorkflow":
        """
        添加并行任务

        Returns:
            ParallelWorkflow 自身，支持链式调用
        """
        step = ParallelStep(
            name=name,
            agent=agent,
            instance_id=instance_id,
            input_key=input_key,
            output_key=output_key,
            timeout=timeout or self.default_timeout,
            ignore_errors=ignore_errors
        )
        self.tasks.append(step)
        return self

    async def execute(
        self,
        initial_input: str,
        verbose: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, ParallelExecutionResult]:
        """
        并行执行所有任务

        Returns:
            Dict[str, ParallelExecutionResult]: 任务 ID 到结果的映射
        """
        # 初始化上下文
        self.context = {
            "_initial_input": initial_input,
            "_last_output": initial_input
        }

        if verbose:
            print(f"\n{'#'*60}")
            print(f"# 并行工作流执行")
            print(f"# 任务数：{len(self.tasks)}")
            print(f"# 最大并发：{self.max_concurrent}")
            print(f"{'#'*60}")

        # 批量执行
        results = await self._execute_batch(verbose, output_dir)

        if verbose:
            success_count = sum(1 for r in results.values() if r.success)
            fail_count = len(results) - success_count
            print(f"\n[完成] 成功：{success_count}, 失败：{fail_count}")

        return results

    async def _execute_batch(
        self,
        verbose: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, ParallelExecutionResult]:
        """批量执行任务（带并发限制）"""
        results = {}

        # 将任务分成多个批次
        for i in range(0, len(self.tasks), self.max_concurrent):
            batch = self.tasks[i:i + self.max_concurrent]

            if verbose:
                print(f"\n[批次] 执行批次 {i // self.max_concurrent + 1} ({len(batch)} 个任务)")

            # 创建协程
            coroutines = []
            for task in batch:
                coro = task.run_async(
                    self.context,
                    shared_memory=self.shared_memory,
                    verbose=verbose,
                    output_dir=output_dir
                )

                # 如果有超时，包装为 asyncio.wait_for
                if task.timeout:
                    coro = asyncio.wait_for(coro, timeout=task.timeout)

                coroutines.append(coro)

            # 并行执行（使用 return_exceptions 捕获异常）
            batch_results = await asyncio.gather(*coroutines, return_exceptions=True)

            # 处理结果
            for task, result in zip(batch, batch_results):
                key = f"{task.instance_id or task.name}"

                if isinstance(result, Exception):
                    # 异常（包括 asyncio.TimeoutError）
                    exec_result = ParallelExecutionResult(
                        step_name=task.name,
                        instance_id=task.instance_id or "default",
                        success=False,
                        error=f"{type(result).__name__}: {result}"
                    )
                    results[key] = exec_result
                elif isinstance(result, ParallelExecutionResult):
                    results[key] = result

                    # 保存输出到上下文
                    if task.output_key and result.result:
                        self.context[task.output_key] = result.result

                    # 保存文件（如果有）
                    if output_dir and result.result and result.result.files:
                        self._save_files(result, output_dir, task.instance_id)

                # 错误处理
                if results[key].success == False and not task.ignore_errors:
                    if not self.continue_on_error:
                        if verbose:
                            print(f"\n[错误] 任务 {key} 失败，停止执行")
                        return results

        return results

    def _save_files(self, result: ParallelExecutionResult, output_dir: str, instance_id: Optional[str]):
        """保存结果文件"""
        if not result.result or not result.result.files:
            return

        # 创建子目录
        if instance_id:
            files_dir = os.path.join(output_dir, instance_id, "files")
        else:
            files_dir = os.path.join(output_dir, "files")
        os.makedirs(files_dir, exist_ok=True)

        # 复制文件
        for file_path in result.result.files:
            if os.path.exists(file_path):
                try:
                    dest_path = os.path.join(files_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
                except Exception as e:
                    # 文件复制失败不影响其他文件
                    pass

        # 保存 JSON 结果
        if result.result and result.result.type == ResultType.JSON:
            if instance_id:
                json_file = os.path.join(output_dir, instance_id, f"{result.step_name}_data.json")
            else:
                json_file = os.path.join(output_dir, f"{result.step_name}_data.json")
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result.result.content, f, ensure_ascii=False, indent=2)
            except Exception as e:
                # JSON 保存失败不中断执行
                pass

    async def execute_sequential(
        self,
        initial_input: str,
        verbose: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, ParallelExecutionResult]:
        """
        顺序执行所有任务

        Returns:
            Dict[str, ParallelExecutionResult]: 任务 ID 到结果的映射
        """
        self.context = {
            "_initial_input": initial_input,
            "_last_output": initial_input
        }

        results = {}

        for task in self.tasks:
            try:
                if verbose:
                    print(f"\n[执行] 任务：{task.name} (实例：{task.instance_id or 'default'})")

                coro = task.run_async(
                    self.context,
                    shared_memory=self.shared_memory,
                    verbose=verbose,
                    output_dir=output_dir
                )

                if task.timeout:
                    result = await asyncio.wait_for(coro, timeout=task.timeout)
                else:
                    result = await coro

                key = task.instance_id or task.name
                results[key] = result

                # 保存输出
                if task.output_key and result.result:
                    self.context[task.output_key] = result.result

            except asyncio.TimeoutError:
                results[task.instance_id or task.name] = ParallelExecutionResult(
                    step_name=task.name,
                    instance_id=task.instance_id or "default",
                    success=False,
                    error=f"执行超时（超过 {task.timeout}秒）"
                )
            except Exception as e:
                results[task.instance_id or task.name] = ParallelExecutionResult(
                    step_name=task.name,
                    instance_id=task.instance_id or "default",
                    success=False,
                    error=str(e)
                )

        return results

    def add_from_inputs(
        self,
        base_agent: Agent,
        inputs: Dict[str, str],
        name_prefix: str = "任务",
        output_key_prefix: Optional[str] = None
    ) -> "ParallelWorkflow":
        """
        从输入字典批量添加任务

        Args:
            base_agent: 基础 Agent
            inputs: {instance_id: input_text}
            name_prefix: 名称前缀
            output_key_prefix: 输出 key 前缀

        Returns:
            ParallelWorkflow 自身
        """
        for instance_id, input_text in inputs.items():
            self.add_task(
                name=f"{name_prefix}-{instance_id}",
                agent=base_agent,
                instance_id=instance_id,
                input_key=input_text,
                output_key=f"{output_key_prefix or 'result_'}{instance_id}"
            )
        return self


# ==================== 便捷函数 ====================

def create_parallel_workflow(
    max_concurrent: int = 5,
    default_timeout: Optional[float] = None,
    continue_on_error: bool = True
) -> ParallelWorkflow:
    """
    创建并行工作流

    Args:
        max_concurrent: 最大并发数
        default_timeout: 默认超时时间
        continue_on_error: 错误时是否继续

    Returns:
        ParallelWorkflow 实例
    """
    return ParallelWorkflow(
        max_concurrent=max_concurrent,
        default_timeout=default_timeout,
        continue_on_error=continue_on_error
    )
