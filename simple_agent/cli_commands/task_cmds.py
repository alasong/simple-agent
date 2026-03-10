"""
任务管理命令

命令列表:
- /bg <任务> - 后台执行任务
- /tasks - 列出所有后台任务
- /result <task_id> - 查看任务结果
- /cancel <task_id> - 取消任务
- /task_stats - 查看任务统计
"""

from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class BgCommand(CommandHandler):
    """后台执行任务"""
    
    @property
    def name(self) -> str:
        return "bg"
    
    @property
    def description(self) -> str:
        return "后台执行任务，立即返回（不阻塞）"
    
    @property
    def usage(self) -> str:
        return "/bg <任务描述>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供任务描述",
                "用法：/bg <任务描述>\n示例：/bg 分析这个项目"
            )
        
        try:
            import asyncio
            cli_agent = context.get('cli_agent')
            
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")
            
            task = " ".join(args)
            output_dir = context.get('output_dir') if context.get('debug_mode') else None
            isolate_mode = context.get('isolate_mode', True)
            
            # 异步提交任务
            async def submit_bg_task():
                await cli_agent.task_queue.start()
                handle = await cli_agent.execute_async(
                    task,
                    verbose=True,
                    output_dir=output_dir,
                    isolate_by_instance=isolate_mode
                )
                return handle
            
            # 运行异步代码
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    handle = asyncio.run_coroutine_threadsafe(submit_bg_task(), loop).result()
                else:
                    handle = loop.run_until_complete(submit_bg_task())
            except RuntimeError:
                handle = asyncio.run(submit_bg_task())
            
            return CommandResult.ok(
                f"✓ 任务已提交到后台执行：{handle.id}\n"
                f"使用 /tasks 查看状态，/result {handle.id} 查看结果",
                data={"handle": handle}
            )
        
        except Exception as e:
            import traceback
            return CommandResult.error("提交任务失败", f"{e}\n{traceback.format_exc()}")


class TasksCommand(CommandHandler):
    """列出所有后台任务"""
    
    @property
    def name(self) -> str:
        return "tasks"
    
    @property
    def description(self) -> str:
        return "列出所有后台任务及状态"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            import asyncio
            from simple_agent.core.task_handle import TaskStatusEnum
            
            cli_agent = context.get('cli_agent')
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")
            
            async def list_bg_tasks():
                await cli_agent.task_queue.start()
                tasks = await cli_agent.task_queue.list_tasks()
                return tasks
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    tasks = asyncio.run_coroutine_threadsafe(list_bg_tasks(), loop).result()
                else:
                    tasks = loop.run_until_complete(list_bg_tasks())
            except RuntimeError:
                tasks = asyncio.run(list_bg_tasks())
            
            if not tasks:
                return CommandResult.ok("暂无后台任务")
            
            lines = [f"\n{'='*60}"]
            lines.append(f"后台任务列表 ({len(tasks)} 个)")
            lines.append(f"{'='*60}")
            
            # 限制显示前 10 个
            for t in tasks[:10]:
                status_icon = {
                    TaskStatusEnum.PENDING: "⏳",
                    TaskStatusEnum.RUNNING: "🔄",
                    TaskStatusEnum.COMPLETED: "✅",
                    TaskStatusEnum.FAILED: "❌",
                    TaskStatusEnum.CANCELLED: "⚠️"
                }.get(t.status, "?")
                
                elapsed = t.get_elapsed_time() if hasattr(t, 'get_elapsed_time') else 0
                lines.append(f"  [{status_icon} {t.status.value:10}] {t.id:30}")
                lines.append(f"    任务：{t.input[:60]}")
                if t.progress:
                    lines.append(f"    进度：{t.progress}")
                lines.append(f"    耗时：{elapsed:.1f}s")
            
            if len(tasks) > 10:
                lines.append(f"\n... 还有 {len(tasks) - 10} 个任务未显示")
            
            lines.append(f"{'='*60}")
            
            # 显示统计
            stats = cli_agent.task_queue.get_stats()
            lines.append(f"\n统计：总计{stats['total']} | 等待{stats['pending']} | 运行{stats['running']} | " +
                        f"完成{stats['completed']} | 失败{stats['failed']} | 取消{stats['cancelled']}")
            
            return CommandResult.ok("\n".join(lines))
        
        except Exception as e:
            import traceback
            return CommandResult.error("获取任务列表失败", f"{e}\n{traceback.format_exc()}")


class ResultCommand(CommandHandler):
    """查看任务结果"""
    
    @property
    def name(self) -> str:
        return "result"
    
    @property
    def description(self) -> str:
        return "查看任务结果（阻塞直到完成）"
    
    @property
    def usage(self) -> str:
        return "/result <task_id>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供任务 ID",
                "用法：/result <task_id>\n示例：/result task_1234567890_1234"
            )
        
        try:
            import asyncio
            cli_agent = context.get('cli_agent')
            
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")
            
            task_id = args[0]
            
            async def get_result():
                await cli_agent.task_queue.start()
                return await cli_agent.task_queue.get_result(task_id, timeout=60)
            
            result_lines = [f"\n等待任务 {task_id} 完成...（最多 60 秒）"]
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    result = asyncio.run_coroutine_threadsafe(get_result(), loop).result()
                else:
                    result = loop.run_until_complete(get_result())
                
                result_lines.append(f"\n{'='*60}")
                result_lines.append(f"任务结果：{task_id}")
                result_lines.append(f"{'='*60}")
                result_lines.append(str(result)[:1000])
                
                return CommandResult.ok("\n".join(result_lines))
            
            except asyncio.TimeoutError:
                return CommandResult.error("任务超时", "任务可能仍在执行中，请使用 /tasks 查看状态")
            except Exception as e:
                return CommandResult.error("任务失败", str(e))
        
        except Exception as e:
            return CommandResult.error("获取结果失败", str(e))


class CancelCommand(CommandHandler):
    """取消任务"""
    
    @property
    def name(self) -> str:
        return "cancel"
    
    @property
    def description(self) -> str:
        return "取消后台任务"
    
    @property
    def usage(self) -> str:
        return "/cancel <task_id>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error(
                "请提供任务 ID",
                "用法：/cancel <task_id>"
            )
        
        try:
            import asyncio
            cli_agent = context.get('cli_agent')
            
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")
            
            task_id = args[0]
            
            async def cancel_task():
                await cli_agent.task_queue.start()
                return await cli_agent.task_queue.cancel(task_id)
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    success = asyncio.run_coroutine_threadsafe(cancel_task(), loop).result()
                else:
                    success = loop.run_until_complete(cancel_task())
                
                if success:
                    return CommandResult.ok(f"✓ 已取消任务：{task_id}")
                else:
                    return CommandResult.error("取消失败", "任务不存在或已完成")
            
            except Exception as e:
                return CommandResult.error("取消失败", str(e))
        
        except Exception as e:
            return CommandResult.error("取消失败", str(e))


class TaskStatsCommand(CommandHandler):
    """查看任务统计"""
    
    @property
    def name(self) -> str:
        return "task_stats"
    
    @property
    def description(self) -> str:
        return "查看任务队列统计信息"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            cli_agent = context.get('cli_agent')
            
            if not cli_agent:
                return CommandResult.error("CLI Agent 未初始化")
            
            stats = cli_agent.task_queue.get_stats()
            
            lines = [f"\n{'='*60}"]
            lines.append("任务队列统计")
            lines.append(f"{'='*60}")
            lines.append(f"总任务数：{stats['total']}")
            lines.append(f"  等待中：{stats['pending']}")
            lines.append(f"  运行中：{stats['running']}")
            lines.append(f"  已完成：{stats['completed']}")
            lines.append(f"  已失败：{stats['failed']}")
            lines.append(f"  已取消：{stats['cancelled']}")
            lines.append(f"\n队列大小：{stats['queue_size']}")
            lines.append(f"最大并发：{stats['max_concurrent']}")
            lines.append(f"{'='*60}")
            
            return CommandResult.ok("\n".join(lines))
        
        except Exception as e:
            return CommandResult.error("获取统计失败", str(e))
