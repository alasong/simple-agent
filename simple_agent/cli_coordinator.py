"""
CLI Coordinator - CLI 协调层

职责:
1. 命令路由和分发
2. 会话状态管理
3. Agent 生命周期管理
4. 错误处理和重试
5. 输出目录管理
6. 执行模式管理（自动/评审）

执行模式:
- auto: 完全自动模式，所有操作自动执行
- review: 用户评审模式，关键节点需要确认

架构:
┌─────────────────────────────────────┐
│   CLI Coordinator                   │
│  ┌─────────────────────────────┐    │
│  │  CommandRouter              │    │
│  │  - 命令注册                 │    │
│  │  - 命令分发                 │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │  SessionManager             │    │
│  │  - 会话切换                 │    │
│  │  - 会话状态                 │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │  OutputManager              │    │
│  │  - 输出格式化               │    │
│  │  - 结果保存                 │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

from simple_agent.cli_agent import CLIAgent
from simple_agent.cli_commands import (
    CommandHandler, CommandResult,
    get_all_commands, get_session_commands,
    get_agent_commands, get_workflow_commands,
    get_debug_commands, get_task_commands, get_daemon_commands
)

# 任务执行模式
try:
    from simple_agent.core.task_mode import ExecutionMode, set_execution_mode
    TASK_MODE_ENABLED = True
except ImportError:
    TASK_MODE_ENABLED = False

# 获取输出根目录（避免循环导入，直接使用默认值）
OUTPUT_ROOT = os.path.abspath('./output')


@dataclass
class CLIContext:
    """CLI 执行上下文"""
    current_agent: Optional[Any] = None
    cli_agent: Optional[CLIAgent] = None
    debug_mode: bool = True
    isolate_mode: bool = True
    output_dir: str = "./output/cli"
    agents_dir: str = "./agents"
    workflows_dir: str = "./workflows"
    enhanced_agent: Optional[Any] = None
    skill_library: Optional[Any] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    # 任务执行模式：'auto' 或 'review'
    execution_mode: str = "auto"

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return getattr(self, key, default)

    def set(self, key: str, value: Any):
        """设置上下文数据"""
        setattr(self, key, value)


class CommandRouter:
    """命令路由器"""
    
    def __init__(self):
        self._handlers: Dict[str, CommandHandler] = {}
        self._aliases: Dict[str, str] = {}  # 命令别名
    
    def register(self, handler: CommandHandler):
        """注册命令处理器"""
        # 处理带空格的命令名（如 "session new"）
        name = handler.name
        self._handlers[name] = handler
        
        # 注册别名（第一个单词作为快捷命令）
        if ' ' in name:
            prefix = name.split()[0]
            if prefix not in self._handlers:
                self._aliases[prefix] = name
    
    def register_all(self, handlers: List[CommandHandler]):
        """批量注册命令处理器"""
        for handler in handlers:
            self.register(handler)
    
    def get_handler(self, cmd: str) -> Optional[CommandHandler]:
        """获取命令处理器"""
        # 直接匹配
        if cmd in self._handlers:
            return self._handlers[cmd]
        
        # 别名匹配
        if cmd in self._aliases:
            full_name = self._aliases[cmd]
            return self._handlers.get(full_name)
        
        # 前缀匹配（支持部分命令名）
        for name, handler in self._handlers.items():
            if name.startswith(cmd):
                return handler
        
        return None
    
    def list_commands(self) -> List[str]:
        """获取所有注册的命令"""
        return list(self._handlers.keys())
    
    def get_help(self, cmd: Optional[str] = None) -> str:
        """获取命令帮助信息"""
        if cmd:
            handler = self.get_handler(cmd)
            if handler:
                lines = [
                    f"/{handler.name}",
                    f"  描述：{handler.description}",
                    f"  用法：{handler.usage}"
                ]
                return "\n".join(lines)
            return f"未知命令：{cmd}"
        
        # 所有命令列表
        lines = ["\n可用命令:"]
        categories = {
            'session': '会话管理',
            'agent': 'Agent 管理',
            'workflow': '工作流',
            'debug': '调试',
            'task': '任务管理',
            'bg': '后台任务',
            'tasks': '后台任务',
            'result': '后台任务',
            'cancel': '后台任务',
            'task_stats': '后台任务',
            'clear': '会话管理',
            'sessions': '会话管理',
            'list': 'Agent 管理',
            'info': 'Agent 管理',
            'new': 'Agent 管理',
            'update': 'Agent 管理',
            'switch': 'Agent 管理',
            'save': 'Agent 管理',
            'load': 'Agent 管理',
            'start': '守护进程',
            'stop': '守护进程',
            'restart': '守护进程',
            'status': '守护进程',
            'logs': '守护进程',
            'install-service': '守护进程',
        }

        for handler in self._handlers.values():
            category = categories.get(handler.name.split()[0], '其他')
            lines.append(f"  /{handler.name:20} - {handler.description}")

        return "\n".join(lines)


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self._current_session: Optional[str] = None
        self._session_history: Dict[str, Any] = {}
    
    def get_current(self) -> str:
        """获取当前会话名称"""
        return self._current_session or "default"
    
    def switch(self, session_name: str, agent: Any) -> bool:
        """切换会话"""
        try:
            from simple_agent.core.session import switch_session as core_switch
            
            if core_switch(session_name, agent):
                self._current_session = session_name
                return True
            return False
        except Exception:
            return False
    
    def create(self, session_name: str, agent: Any) -> bool:
        """创建新会话"""
        return self.switch(session_name, agent)
    
    def delete(self, session_name: str) -> bool:
        """删除会话"""
        try:
            from simple_agent.core.session import get_session_manager
            manager = get_session_manager()
            return manager.delete(session_name)
        except Exception:
            return False
    
    def list_all(self) -> List[str]:
        """列出所有会话"""
        try:
            from simple_agent.core.session import list_sessions
            return list_sessions()
        except Exception:
            return []


class OutputManager:
    """输出管理器"""
    
    def __init__(self):
        self._output_history: List[Dict[str, Any]] = []
    
    def format_result(self, result: CommandResult, use_rich: bool = False) -> str:
        """格式化命令结果"""
        if use_rich:
            # TODO: 使用 RichOutput 格式化
            pass
        
        if result.success:
            return result.message
        else:
            error_msg = f"[错误] {result.message}"
            if result.error:
                error_msg += f"\n详情：{result.error}"
            return error_msg
    
    def save_result(self, result: Any, user_input: str, output_dir: str,
                   isolate_by_instance: bool = False, instance_id: Optional[str] = None) -> Optional[str]:
        """保存输出到文件"""
        try:
            # 测试环境防护
            if self._is_test_environment():
                return None
            
            # 创建输出目录
            if isolate_by_instance and instance_id:
                output_path = os.path.join(output_dir, instance_id)
            else:
                task_prefix = user_input[:20].replace('/', '_').replace('\\', '_').replace(' ', '_')
                output_path = os.path.join(output_dir, task_prefix)
            
            os.makedirs(output_path, exist_ok=True)
            
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(output_path, f'result_{timestamp}.txt')
            
            # 保存结果
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 任务输入\n{user_input}\n\n")
                f.write(f"# 执行时间\n{datetime.now().isoformat()}\n\n")
                f.write(f"# 执行结果\n{result}\n")
            
            return output_path
        
        except Exception as e:
            print(f"\n[警告] 保存输出失败：{e}")
            return None
    
    def _is_test_environment(self) -> bool:
        """检测是否在测试环境中"""
        import sys
        if any(mod.startswith('pytest') or mod.startswith('unittest') for mod in sys.modules):
            return True
        if os.environ.get('TESTING') or os.environ.get('PYTEST_CURRENT_TEST'):
            return True
        return False


class CLICoordinator:
    """CLI 协调器"""
    
    def __init__(self):
        self.context = CLIContext()
        self.router = CommandRouter()
        self.session_manager = SessionManager()
        self.output_manager = OutputManager()

        # 初始化 CLI Agent（默认 debug_mode 为 False，由 initialize() 设置）
        self.context.cli_agent = CLIAgent(debug_mode=False)

        # 注册所有命令
        self._register_commands()
    
    def _register_commands(self):
        """注册所有命令处理器"""
        # 注册所有命令
        self.router.register_all(get_all_commands())
        
        # 添加额外命令（如 help, exit 等）
        self.router.register(HelpCommand())
        self.router.register(ExitCommand())
    
    def initialize(self):
        """初始化协调器"""
        # 加载默认会话
        try:
            from simple_agent.core.session import load_session
            load_session("default", self.context.cli_agent.agent)
        except Exception as e:
            print(f"[警告] 加载默认会话失败：{e}")
        
        # 初始化增强型 Agent（阶段 1 功能）
        try:
            from simple_agent.core.agent_enhanced import EnhancedAgent
            from simple_agent.core.llm import OpenAILLM
            from simple_agent.core import EnhancedMemory, SkillLibrary
            
            llm = OpenAILLM()
            memory = EnhancedMemory()
            skill_library = SkillLibrary()
            
            self.context.enhanced_agent = EnhancedAgent(llm=llm, memory=memory, skill_library=skill_library)
            self.context.skill_library = skill_library
            
            print(f"\n[阶段 1] 增强型 Agent 已初始化")
        except Exception as e:
            print(f"[警告] 初始化增强型 Agent 失败：{e}")

        # 默认启用 debug 模式（设置到 CLI Agent）
        self.context.cli_agent.debug_mode = True

        try:
            from simple_agent.core import enable_debug
            enable_debug(verbose=True)
        except Exception:
            pass

    def process_command(self, user_input: str) -> CommandResult:
        """处理命令
        
        Args:
            user_input: 用户输入（以/开头的命令）
        
        Returns:
            CommandResult: 执行结果
        """
        # 解析命令
        parts = user_input[1:].strip().split()  # 去掉开头的/
        if not parts:
            return CommandResult.error("无效命令")
        
        cmd = parts[0]
        args = parts[1:]
        
        # 获取命令处理器
        handler = self.router.get_handler(cmd)
        if not handler:
            return CommandResult.error(f"未知命令：{cmd}", "输入 /help 查看所有可用命令")
        
        # 执行命令
        try:
            context_dict = {
                'current_agent': self.context.current_agent,
                'cli_agent': self.context.cli_agent,
                'debug_mode': self.context.debug_mode,
                'isolate_mode': self.context.isolate_mode,
                'output_dir': self.context.output_dir,
                'agents_dir': self.context.agents_dir,
                'workflows_dir': self.context.workflows_dir,
                'enhanced_agent': self.context.enhanced_agent,
                'skill_library': self.context.skill_library,
            }
            
            result = handler.execute(args, context_dict)
            
            # 更新上下文
            if 'current_agent' in context_dict:
                self.context.current_agent = context_dict['current_agent']
            
            return result
        
        except Exception as e:
            import traceback
            return CommandResult.error(
                f"命令执行失败：{cmd}",
                f"{e}\n{traceback.format_exc()}"
            )
    
    def execute(self, user_input: str) -> Any:
        """执行任务或命令

        Args:
            user_input: 用户输入

        Returns:
            执行结果
        """
        # 判断是否为命令
        if user_input.startswith('/'):
            result = self.process_command(user_input)
            return self.output_manager.format_result(result)

        # 普通任务，委托给 CLI Agent
        try:
            # 生成任务专属输出目录: output/<task_name>+<timestamp>/
            output_dir = self._generate_task_output_dir(user_input)

            # 设置执行模式
            if TASK_MODE_ENABLED:
                mode = self.context.execution_mode
                set_execution_mode(ExecutionMode.AUTO if mode == "auto" else ExecutionMode.REVIEW)

            result_tuple = self.context.cli_agent.execute(
                user_input,
                verbose=True,
                output_dir=output_dir,
                isolate_by_instance=self.context.isolate_mode
            )

            # 保存输出
            if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                result, saved_path = result_tuple
            else:
                result = result_tuple
                saved_path = None

            # 打印 debug 摘要（如果 debug 模式启用）
            self._print_debug_summary(result)

            return result

        except Exception as e:
            import traceback
            return f"[错误] 任务执行失败：{e}\n{traceback.format_exc()}"

    def _print_debug_summary(self, result: Any):
        """打印 debug 摘要（如果 debug 模式启用）"""
        try:
            from simple_agent.core import get_debug_summary, print_debug_summary, tracker

            # 检查 debug 模式是否启用
            if not tracker or not tracker.enabled:
                return

            # 打印执行摘要
            print_debug_summary()

            # 如果有质量评估，也显示（通过环境变量或 debug_mode）
            is_debug = os.environ.get('DEBUG') == '1' or self.context.debug_mode
            if is_debug and result:
                # 质量评估已在 cli_agent._show_quality_assessment 中打印
                # 这里只打印分隔符
                print("\n" + "=" * 60)

        except Exception:
            # debug 打印失败不影响主流程
            pass

    def _generate_task_output_dir(self, user_input: str) -> str:
        """生成任务专属输出目录（优化结构）

        目录结构：
        output/
        ├── YYYYMMDD/           # 按日期分类
        │   ├── HHMMSS_task/    # 按时间+任务名
        │   │   ├── result.txt  # 主结果文件
        │   │   ├── workflow/   # Workflow 执行记录
        │   │   └── files/      # 生成的文件
        │   └── summary.json    # 今日任务摘要

        Args:
            user_input: 用户任务描述

        Returns:
            输出目录路径
        """
        import re
        import hashlib

        # 从配置获取输出根目录（默认 ./output）
        output_root = OUTPUT_ROOT

        # 生成日期目录（按天分类）
        date_dir = datetime.now().strftime('%Y%m%d')
        date_path = os.path.join(output_root, date_dir)
        os.makedirs(date_path, exist_ok=True)

        # 生成时间戳（精确到秒）
        timestamp = datetime.now().strftime('%H%M%S')

        # 从任务描述中提取简要任务名
        words = re.findall(r'[a-zA-Z0-9]+', user_input)
        if words:
            # 优先使用前几个英文单词作为任务名
            task_name = '_'.join(words[:min(3, len(words))])
        else:
            # 如果没有英文单词，使用 hash 值前缀
            hash_val = hashlib.md5(user_input.encode('utf-8')).hexdigest()[:6]
            task_name = f"task_{hash_val}"

        # 转小写
        task_name = task_name.lower()
        # 限制长度
        if len(task_name) > 20:
            task_name = task_name[:20]

        # 组合：output/YYYYMMDD/HHMMSS_taskname/
        task_dir_name = f"{timestamp}_{task_name}"
        return os.path.join(date_path, task_dir_name)
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'current_agent': self.context.current_agent.name if self.context.current_agent else None,
            'current_session': self.session_manager.get_current(),
            'debug_mode': self.context.debug_mode,
            'isolate_mode': self.context.isolate_mode,
        }


# 基础命令实现
from simple_agent.cli_commands import CommandHandler

class HelpCommand(CommandHandler):
    """帮助命令"""

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "显示帮助信息"

    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        router = context.get('router')  # 需要传入 router

        if args:
            # 显示特定命令的帮助
            cmd_name = args[0]
            handler = router.get_handler(cmd_name)
            if handler:
                help_text = f"""
/{handler.name}
  描述：{handler.description}
  用法：{handler.usage}
"""
                return CommandResult.ok(help_text)
            else:
                return CommandResult.error(f"未知命令：{cmd_name}")
        else:
            # 显示所有命令 - 按分类显示
            help_text = """
===== 会话管理 =====
/sessions          列出所有会话
/session <名称>     切换会话
/session new <名称> 创建新会话
/session del <名称> 删除会话
/session continue <task_id> <消息>  在 session 中继续交互
/session history <task_id>  查看 session 历史
/session end <task_id>  结束 session
/clear             清空当前会话记忆

===== Agent 管理 =====
/new <描述>        创建新 Agent
/update <描述>     更新当前 Agent 提示词
/switch <名称>     切换到已创建的 Agent
/list              列出所有 Agent
/info              显示当前 Agent 详情
/save              保存当前 Agent
/load <名称>       加载 Agent

===== 工作流 =====
/workflow <文件>    加载并运行工作流

===== 调试 =====
/debug [on|off]    切换调试模式
/debug summary     显示调试摘要
/debug stats       显示详细统计

===== 任务追踪 =====
/tasks status <task_id>  查看任务详细状态
/tasks running         查看正在执行的任务
/tasks list            列出所有任务（按状态分组）

===== 后台任务管理 =====
/bg <任务>         后台执行任务，立即返回
/tasks             列出所有后台任务
/result <task_id>  查看任务结果
/cancel <task_id>  取消任务
/task_stats        查看任务统计

===== 守护进程 =====
/start             启动 API 守护进程
/stop              停止 API 守护进程
/restart           重启 API 守护进程
/status            查看守护进程状态
/logs [行数]       查看日志（默认 50 行）
/install-service   生成 systemd/launchd 服务配置

===== 其他 =====
/help              显示帮助信息
/exit              退出程序
"""
            return CommandResult.ok(help_text)


class ExitCommand(CommandHandler):
    """退出命令"""
    
    @property
    def name(self) -> str:
        return "exit"
    
    @property
    def description(self) -> str:
        return "退出程序"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        return CommandResult.ok("再见!")
