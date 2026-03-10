#!/usr/bin/env python3
"""
统一 CLI 入口 - 精简版

使用新的 CLI Coordinator 架构，将职责委托给协调器。

使用:
    python cli.py                    # 进入交互模式
    python cli.py "帮我写个函数"      # 单次任务
    python cli.py -t "任务"          # 指定任务

架构:
┌─────────────────────────────────────┐
│   CLI Interface (cli.py)            │  ← 只负责输入输出
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   CLI Coordinator                   │  ← 协调层（已实现）
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Core Agent Layer                  │  ← 核心业务逻辑
└─────────────────────────────────────┘
"""

import sys
import argparse
import os

# 导入协调器
from cli_coordinator import CLICoordinator
from cli_agent import CLIAgent

# 注意：不再需要 import tools 副作用导入
# 常用工具（BashTool, ReadFileTool, WriteFileTool）已默认导出
# 其他工具通过 ToolRegistry 按需加载

# 富文本输出支持
try:
    from core.rich_output import get_rich_output, RichOutput, print_header, print_info, print_error
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 调试支持
try:
    from core import enable_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False

# 配置目录
from core.config_loader import get_config
_config = get_config()
OUTPUT_DIR = os.path.abspath(_config.get('directories.cli_output', './output/cli'))
OUTPUT_ROOT = os.path.abspath(_config.get('directories.output_root', './output'))


# ============================================================================
# Tab 自动补全
# ============================================================================

def setup_readline_completer():
    """设置 readline 自动补全"""
    try:
        import gnureadline as readline
    except ImportError:
        try:
            import readline
        except ImportError:
            return False

    # 命令补全列表（和 /help 显示的一致）
    CLI_COMMANDS = [
        # 会话管理
        '/sessions',
        '/session',
        '/clear',
        # Agent 管理
        '/new',
        '/update',
        '/switch',
        '/list',
        '/info',
        '/save',
        '/load',
        # 工作流
        '/workflow',
        # 调试
        '/debug',
        # 后台任务
        '/bg',
        '/tasks',
        '/result',
        '/cancel',
        '/task_stats',
        # 守护进程
        '/start',
        '/stop',
        '/restart',
        '/status',
        '/logs',
        '/install-service',
        # 其他
        '/help',
        '/exit',
    ]

    def completer(text, state):
        """补全函数"""
        try:
            # 直接补全所有匹配的命令
            options = [cmd for cmd in CLI_COMMANDS if cmd.startswith(text)]
            if state < len(options):
                return options[state]
            return None
        except Exception:
            return None

    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind("tab: complete")
    return True


def handle_daemon_commands(args):
    """处理守护进程命令"""
    try:
        from core.daemon import get_daemon, generate_systemd_service, generate_launchd_plist
    except ImportError as e:
        print(f"[错误] 无法导入守护进程模块：{e}")
        return

    daemon = get_daemon()

    if args.start:
        success, msg = daemon.start()
        symbol = "✓" if success else "✗"
        print(f"[守护进程] {msg}")
        if success and RICH_AVAILABLE:
            print_info("API 服务已在后台运行")
            print_info("访问 http://localhost:8000/docs 查看 API 文档")

    elif args.stop:
        success, msg = daemon.stop()
        symbol = "✓" if success else "✗"
        print(f"[守护进程] {msg}")

    elif args.restart:
        success, msg = daemon.restart()
        symbol = "✓" if success else "✗"
        print(f"[守护进程] {msg}")

    elif args.status:
        status = daemon.status()
        print(f"\n{'='*50}")
        print(f"守护进程：{status['name']}")
        print(f"运行状态：{'运行中' if status['running'] else '已停止'}")
        if status['pid']:
            print(f"PID: {status['pid']}")
        print(f"PID 文件：{status['pid_file']}")
        print(f"日志文件：{status['log_file']}")

        if status['running'] and 'create_time' in status:
            print(f"启动时间：{status['create_time']}")
        if status['running'] and 'cpu_percent' in status:
            print(f"CPU: {status['cpu_percent']:.1f}%")
            print(f"内存：{status['memory_percent']:.1f}%")
        print(f"{'='*50}\n")

    elif args.logs:
        lines = args.logs if args.logs else 50
        logs = daemon.logs(lines=lines)
        print(f"\n{'='*50}")
        print(f"最近 {lines} 行日志:")
        print(f"{'='*50}")
        print(logs)

    elif args.install_service:
        import platform
        system = platform.system()

        if system == "Linux":
            service_content = generate_systemd_service()
            service_file = "/etc/systemd/system/simple-agent.service"
            print(f"\n{'='*50}")
            print("systemd 服务配置:")
            print(f"{'='*50}")
            print(service_content)
            print(f"\n安装步骤:")
            print(f"1. sudo tee {service_file} << 'EOF'")
            print(service_content)
            print("EOF")
            print("2. sudo systemctl daemon-reload")
            print("3. sudo systemctl enable simple-agent")
            print("4. sudo systemctl start simple-agent")

        elif system == "Darwin":  # macOS
            plist_content = generate_launchd_plist()
            home = os.path.expanduser("~")
            plist_file = os.path.join(home, "Library", "LaunchAgents", "simple-agent.plist")
            print(f"\n{'='*50}")
            print("launchd 服务配置:")
            print(f"{'='*50}")
            print(plist_content)
            print(f"\n安装步骤:")
            print(f"1. mkdir -p ~/Library/LaunchAgents")
            print(f"2. 保存配置到：{plist_file}")
            print("3. launchctl load -w ~/Library/LaunchAgents/simple-agent.plist")


def interactive_mode(coordinator: CLICoordinator):
    """交互模式"""
    # 设置 readline 自动补全
    if setup_readline_completer():
        print("[Tab 补全] 已启用")

    print()
    print(f"{'='*60}")
    print("CLI Agent - 智能任务助手 (精简版)")
    print(f"{'='*60}")
    print(f"\n输出目录：{coordinator.context.output_dir}")
    print("命令：/help | /exit | /list | /load | /workflow ...")
    print("守护进程：/start | /stop | /restart | /logs | /install-service")
    print("(使用 Tab 可补全命令)")
    
    while True:
        # 显示当前状态
        state = coordinator.get_current_state()
        agent_name = state.get('current_agent') or 'CLI Agent'
        session_name = state.get('current_session') or 'default'
        
        prompt = f"\n[{agent_name} | {session_name}] 你："
        
        try:
            user_input = input(prompt).strip()
            user_input = user_input.encode('utf-8', errors='ignore').decode('utf-8')
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        
        if not user_input:
            continue
        
        # 退出命令
        if user_input == "/exit":
            print("再见!")
            break
        
        # 执行命令或任务
        result = coordinator.execute(user_input)
        
        # 显示结果
        if RICH_AVAILABLE:
            if hasattr(result, 'tasks_completed'):
                # Swarm 结果
                get_rich_output().show_swarm_result(result, user_input)
            else:
                print_info(str(result)[:500] if len(str(result)) > 500 else result)
        else:
            print(f"\n{'='*60}")
            print(result[:500] + "..." if len(str(result)) > 500 else result)
            print(f"{'='*60}")
        
        # 保存会话
        try:
            from core.session import save_session
            save_session("default", coordinator.context.cli_agent.agent)
        except Exception:
            pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CLI Agent - 智能任务助手（精简版）")

    # 守护进程命令
    daemon_group = parser.add_argument_group('守护进程命令')
    daemon_group.add_argument("--start", action="store_true", help="启动 API 守护进程")
    daemon_group.add_argument("--stop", action="store_true", help="停止 API 守护进程")
    daemon_group.add_argument("--restart", action="store_true", help="重启 API 守护进程")
    daemon_group.add_argument("--status", action="store_true", help="查看守护进程状态")
    daemon_group.add_argument("--logs", nargs="?", const=50, type=int, help="查看日志（默认 50 行）")
    daemon_group.add_argument("--install-service", action="store_true", help="生成 systemd/launchd 服务配置")

    parser.add_argument("input", nargs="?", help="任务描述")
    parser.add_argument("-t", "--task", help="单次任务")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="详细输出")
    parser.add_argument("--debug", action="store_true", help="调试模式：保存输出到文件")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--isolate", action="store_true", help="按实例 ID 隔离输出目录")

    args = parser.parse_args()

    # 守护进程命令处理
    if args.start or args.stop or args.restart or args.status or args.logs or args.install_service:
        handle_daemon_commands(args)
        return

    # 创建协调器
    coordinator = CLICoordinator()
    coordinator.initialize()

    # 设置配置 - 默认启用 output_dir，所有过程文件都输出到 output 目录
    coordinator.context.output_dir = args.output or OUTPUT_DIR
    if args.debug:
        coordinator.context.debug_mode = True
    if args.isolate:
        coordinator.context.isolate_mode = True
    
    # 单次任务模式
    if args.input or args.task:
        task = args.task or args.input
        
        # 使用富文本展示
        if RICH_AVAILABLE:
            print_header("CLI Agent 执行任务", task[:60])
            print_info(f"调试模式：已启用 (默认)")
            if coordinator.context.output_dir:
                print_info(f"输出目录：{coordinator.context.output_dir}")
        else:
            print(f"[CLI Agent] 执行任务：{task}")
        
        try:
            result = coordinator.execute(task)
            
            # 展示结果
            if RICH_AVAILABLE:
                if hasattr(result, 'tasks_completed'):
                    get_rich_output().show_swarm_result(result, task)
                else:
                    print_info(f"结果：{str(result)[:500]}")
            else:
                print(f"\n{'='*60}")
                print(f"结果：{result}")
                print(f"{'='*60}")
        
        except Exception as e:
            if RICH_AVAILABLE:
                print_error(f"{e}")
            else:
                print(f"\n[错误] {e}")
            import traceback
            traceback.print_exc()
        
        return
    
    # 交互模式
    interactive_mode(coordinator)


if __name__ == "__main__":
    main()
