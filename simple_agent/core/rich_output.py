"""
富文本输出模块 (Rich Output Module)

提供美观的命令行输出，支持：
- 彩色文本
- 表格展示
- 面板显示
- 进度条
- 任务状态可视化

使用示例:
    from simple_agent.core.rich_output import RichOutput
    
    rich = RichOutput()
    rich.show_swarm_result(result)
    rich.show_task_table(tasks)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys

try:
    from rich.console import Console
    from rich.table import Table, Column
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class TaskDisplayData:
    """任务展示数据"""
    id: str
    description: str
    status: str  # pending, running, completed, failed
    agent: str = ""
    result: str = ""
    error: str = ""
    duration: float = 0.0


class RichOutput:
    """富文本输出管理器"""
    
    def __init__(self, use_color: bool = True):
        """
        初始化富文本输出
        
        Args:
            use_color: 是否使用颜色（终端不支持时自动禁用）
        """
        if RICH_AVAILABLE and use_color:
            self.console = Console(force_terminal=True)
        else:
            self.console = None
    
    def print(self, text: str, style: str = ""):
        """打印文本"""
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)
    
    def print_header(self, title: str, subtitle: str = ""):
        """打印标题"""
        if self.console:
            panel = Panel(
                f"[bold white]{title}[/bold white]\n{subtitle}" if subtitle else f"[bold white]{title}[/bold white]",
                box=box.ROUNDED,
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"\n{'='*60}")
            print(title)
            if subtitle:
                print(subtitle)
            print(f"{'='*60}\n")
    
    def print_success(self, message: str):
        """打印成功消息"""
        if self.console:
            self.console.print(f"✓ {message}", style="green")
        else:
            print(f"✓ {message}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        if self.console:
            self.console.print(f"✗ {message}", style="red")
        else:
            print(f"✗ {message}")
    
    def print_warning(self, message: str):
        """打印警告消息"""
        if self.console:
            self.console.print(f"⚠ {message}", style="yellow")
        else:
            print(f"⚠ {message}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        if self.console:
            self.console.print(f"ℹ {message}", style="cyan")
        else:
            print(f"ℹ {message}")
    
    def show_swarm_result(self, result: Any, original_task: str = ""):
        """
        展示 Swarm 执行结果
        
        Args:
            result: SwarmResult 对象
            original_task: 原始任务描述
        """
        if not hasattr(result, 'tasks_completed'):
            self.print(str(result))
            return
        
        # 1. 标题面板
        task_preview = (original_task or "Swarm 任务")[:80]
        if len(original_task or "") > 80:
            task_preview += "..."
        
        if self.console:
            self.console.print(Panel(
                f"[bold blue]Swarm 执行结果[/bold blue]\n\n"
                f"[cyan]{task_preview}[/cyan]",
                box=box.ROUNDED,
                border_style="blue",
                padding=(1, 2)
            ))
        else:
            print(f"\n{'='*60}")
            print(f"Swarm 执行结果")
            print(f"{task_preview}")
            print(f"{'='*60}\n")
        
        # 2. 统计表格
        tasks_completed = getattr(result, 'tasks_completed', 0)
        tasks_failed = getattr(result, 'tasks_failed', 0)
        execution_time = getattr(result, 'execution_time', 0.0)
        total_iterations = getattr(result, 'total_iterations', 0)
        
        if self.console:
            table = Table(
                title="任务统计",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            table.add_column("指标", style="cyan", justify="left")
            table.add_column("数值", style="green", justify="right")
            
            table.add_row("总任务数", str(tasks_completed + tasks_failed))
            table.add_row("✅ 完成", str(tasks_completed))
            table.add_row("❌ 失败", str(tasks_failed))
            table.add_row("迭代次数", str(total_iterations))
            table.add_row("耗时", f"{execution_time:.2f}秒")
            
            self.console.print(table)
        else:
            print("任务统计:")
            print(f"  总任务数：{tasks_completed + tasks_failed}")
            print(f"  ✅ 完成：{tasks_completed}")
            print(f"  ❌ 失败：{tasks_failed}")
            print(f"  迭代次数：{total_iterations}")
            print(f"  耗时：{execution_time:.2f}秒")
        
        # 3. 成功率
        total = tasks_completed + tasks_failed
        if total > 0:
            success_rate = (tasks_completed / total) * 100
            if self.console:
                if success_rate >= 80:
                    style = "green"
                elif success_rate >= 50:
                    style = "yellow"
                else:
                    style = "red"
                self.console.print(f"\n[bold {style}]成功率：{success_rate:.1f}%[/bold {style}]")
            else:
                print(f"\n成功率：{success_rate:.1f}%")
        
        # 4. Agent 负载统计
        if hasattr(result, 'agent_stats') and result.agent_stats:
            stats = result.agent_stats
            if self.console:
                self.console.print(f"\n[bold]Agent 负载统计:[/bold]")
                if 'load_distribution' in stats:
                    for agent_id, load in stats['load_distribution'].items():
                        self.console.print(f"  {agent_id}: {load} 个任务")
            else:
                print("\nAgent 负载统计:")
                if 'load_distribution' in stats:
                    for agent_id, load in stats['load_distribution'].items():
                        print(f"  {agent_id}: {load} 个任务")
    
    def show_task_table(self, tasks: List[TaskDisplayData], title: str = "任务列表"):
        """
        展示任务表格
        
        Args:
            tasks: 任务数据列表
            title: 表格标题
        """
        if self.console:
            table = Table(
                title=title,
                box=box.ROUNDED,
                show_header=True,
                header_style="bold blue"
            )
            table.add_column("ID", style="cyan", width=6)
            table.add_column("描述", style="white", max_width=40)
            table.add_column("状态", style="magenta", width=10)
            table.add_column("Agent", style="green", width=15)
            table.add_column("结果", style="yellow", max_width=50)
            
            for task in tasks:
                # 状态图标
                status_icons = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }
                status_icon = status_icons.get(task.status, "❓")
                status_style = {
                    "pending": "gray",
                    "running": "blue",
                    "completed": "green",
                    "failed": "red"
                }.get(task.status, "white")
                
                result_preview = ""
                if task.status == "completed" and task.result:
                    result_preview = task.result[:50] + "..." if len(task.result) > 50 else task.result
                elif task.status == "failed" and task.error:
                    result_preview = task.error[:50] + "..." if len(task.error) > 50 else task.error
                
                table.add_row(
                    task.id,
                    task.description[:40],
                    f"[{status_style}]{status_icon}[/]",
                    task.agent[:15] if task.agent else "-",
                    result_preview if result_preview else "-"
                )
            
            self.console.print(table)
        else:
            print(f"\n{title}:")
            print("-" * 80)
            for task in tasks:
                status = task.status.upper()
                print(f"  [{task.id}] {task.description[:40]} - {status}")
                if task.result:
                    print(f"      结果：{task.result[:50]}")
    
    def show_concurrent_tasks(self, tasks: List[TaskDisplayData]):
        """展示并发执行的任务"""
        self.print_header("并发执行任务")
        
        if self.console:
            for i, task in enumerate(tasks, 1):
                self.console.print(
                    f"[cyan]{i}.[/cyan] "
                    f"[bold white]{task.description}[/bold white] "
                    f"[gray](Agent: {task.agent or '待分配'})[/gray]"
                )
        else:
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task.description} (Agent: {task.agent or '待分配'})")
    
    def create_progress(self, description: str = "执行中..."):
        """创建进度条"""
        if self.console and RICH_AVAILABLE:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )
            return progress, progress.add_task(description, total=100)
        return None, None
    
    def show_code(self, code: str, language: str = "python"):
        """展示代码"""
        if self.console and RICH_AVAILABLE:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            print(f"```{language}\n{code}\n```")
    
    def show_markdown(self, markdown: str):
        """展示 Markdown 内容"""
        if self.console and RICH_AVAILABLE:
            md = Markdown(markdown)
            self.console.print(md)
        else:
            print(markdown)
    
    def create_layout(self):
        """创建布局"""
        if self.console and RICH_AVAILABLE:
            layout = Layout()
            layout.split(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            return layout
        return None
    
    def clear(self):
        """清空屏幕"""
        if self.console:
            self.console.clear()
        else:
            print("\n" * 50)


# 全局实例
_global_rich_output: Optional[RichOutput] = None


def get_rich_output(use_color: bool = True) -> RichOutput:
    """获取全局 RichOutput 实例"""
    global _global_rich_output
    if _global_rich_output is None:
        _global_rich_output = RichOutput(use_color=use_color)
    return _global_rich_output


# 便捷函数
def print_header(title: str, subtitle: str = ""):
    """打印标题"""
    get_rich_output().print_header(title, subtitle)


def print_success(message: str):
    """打印成功消息"""
    get_rich_output().print_success(message)


def print_error(message: str):
    """打印错误消息"""
    get_rich_output().print_error(message)


def print_warning(message: str):
    """打印警告消息"""
    get_rich_output().print_warning(message)


def print_info(message: str):
    """打印信息消息"""
    get_rich_output().print_info(message)


def show_swarm_result(result: Any, original_task: str = ""):
    """展示 Swarm 结果"""
    get_rich_output().show_swarm_result(result, original_task)


def show_task_table(tasks: List[TaskDisplayData], title: str = "任务列表"):
    """展示任务表格"""
    get_rich_output().show_task_table(tasks, title)


def show_concurrent_tasks(tasks: List[TaskDisplayData]):
    """展示并发任务"""
    get_rich_output().show_concurrent_tasks(tasks)
