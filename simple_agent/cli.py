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
from simple_agent.cli_coordinator import CLICoordinator
from simple_agent.cli_agent import CLIAgent

# 注意：不再需要 import tools 副作用导入
# 常用工具（BashTool, ReadFileTool, WriteFileTool）已默认导出
# 其他工具通过 ToolRegistry 按需加载

# 富文本输出支持
try:
    from simple_agent.core.rich_output import get_rich_output, RichOutput, print_header, print_info, print_error
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 调试支持
try:
    from simple_agent.core import enable_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False

# 配置目录
from simple_agent.core.config_loader import get_config
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
        from simple_agent.services.daemon import get_daemon, generate_systemd_service, generate_launchd_plist
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


# ============================================================================
# Template 系统命令处理
# ============================================================================

def handle_list_templates():
    """处理 --list-templates 命令"""
    try:
        from simple_agent.templates import list_templates, get_template_help
        from simple_agent.core.rich_output import print_header, print_info
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

    templates = list_templates()

    if RICH_AVAILABLE:
        print_header("可用模板列表", "=" * 20)
        print_info(f"\n找到 {len(templates)} 个可用模板:\n")
        for t in templates:
            is_base = " (基础模板)" if t.get('base', True) else " (场景模板)"
            print_info(f"  {t['name']:<20} - {t['description']}{is_base}")
        print()
    else:
        print("可用模板列表:")
        for t in templates:
            print(f"  {t['name']}: {t['description']}")
        print(f"\n共 {len(templates)} 个模板")


def handle_create_agent(agent_name: str, template_name: str):
    """处理 --create-agent 命令"""
    RICH_AVAILABLE = False
    print_header = None
    print_info = None
    print_error = None
    load_template = None
    create_agent_from_template = None

    try:
        from simple_agent.templates import load_template, create_agent_from_template
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from simple_agent.core.rich_output import print_header, print_info, print_error
        RICH_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        pass

    if load_template is None:
        if RICH_AVAILABLE:
            print_error(f"错误: 无法加载模板功能")
        else:
            print(f"错误: 无法加载模板功能")
        return

    # Load template to verify it exists
    template = load_template(template_name)

    if template is None:
        if RICH_AVAILABLE:
            print_error(f"错误: 模板 '{template_name}' 不存在")
        else:
            print(f"错误: 模板 '{template_name}' 不存在")
            print("使用 --list-templates 查看可用模板")
        return

    # Create agent from template
    result = create_agent_from_template(
        template_name=template_name,
        agent_name=agent_name,
        output_dir="./agents"
    )

    if result:
        if RICH_AVAILABLE:
            print_header("Agent 创建成功", "=" * 20)
            print_info(f"  名称: {result.get('name', 'Unknown')}")
            print_info(f"  版本: {result.get('version', 'Unknown')}")
            print_info(f"  描述: {result.get('description', 'N/A')}")
            print_info(f"  保存路径: {result.get('_saved_path', 'N/A')}")
            print_info(f"  工具: {', '.join(result.get('tools', []))}")
            print()
        else:
            print(f"Agent '{agent_name}' 创建成功!")
            print(f"  模板: {template_name}")
            print(f"  保存路径: {result.get('_saved_path', './agents')}")
    else:
        if RICH_AVAILABLE:
            print_error("错误: 创建 Agent 失败")
        else:
            print("错误: 创建 Agent 失败")


# ============================================================================
# Config 验证命令处理
# ============================================================================

def handle_validate_config(config_path: str):
    """处理 --validate-config 命令"""
    try:
        from simple_agent.config_validation import get_validation_status
        from simple_agent.core.rich_output import print_header, print_info, print_error
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

    status = get_validation_status(config_path)

    if RICH_AVAILABLE:
        print_header("配置验证结果", "=" * 20)
        print_info(f"文件路径: {status.get('file_path', 'Unknown')}")
        print_info(f"配置类型: {status.get('config_type', 'Unknown')}")
        print_info(f"文件存在: {'是' if status.get('file_exists', False) else '否'}")
        print_info(f"验证状态: {'✓ 通过' if status.get('valid', False) else '✗ 失败'}")
        print_info(f"错误数量: {status.get('error_count', 0)}")
        print()

        if status.get('errors'):
            print_info("错误详情:")
            for i, error in enumerate(status['errors'], 1):
                print_error(f"  {i}. {error}")
    else:
        print(f"配置验证: {config_path}")
        print(f"状态: {'通过' if status['valid'] else '失败'}")
        if status['errors']:
            for error in status['errors']:
                print(f"  {error}")


def handle_generate_config(output_path: str, config_type: str = "agent"):
    """处理 --generate-config 命令"""
    try:
        from simple_agent.config_validation import generate_config_file
        from simple_agent.core.rich_output import print_header, print_info
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

    path = generate_config_file(config_type=config_type, output_path=output_path)

    if path:
        if RICH_AVAILABLE:
            print_header("配置文件生成成功", "=" * 20)
            print_info(f"文件路径: {path}")
            print_info(f"配置类型: {config_type}")
            print()
        else:
            print(f"配置文件已生成: {path}")
    else:
        if RICH_AVAILABLE:
            print_error("错误: 生成配置文件失败")
        else:
            print("错误: 生成配置文件失败")


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
            from simple_agent.core.session import save_session
            save_session("default", coordinator.context.cli_agent.agent)
        except Exception:
            pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CLI Agent - 智能任务助手（精简版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py                      # 进入交互模式
  python cli.py "帮我写个函数"        # 单次任务
  python cli.py --create-agent my_agent --template developer  # 创建新 Agent
  python cli.py --list-templates     # 列出所有模板

深度定制命令（交互模式）:
  /edit <描述>                       # 使用自然语言编辑 Agent
  /gen <文档> [--name 名称]          # 从文档生成 Agent
  /extend tools <工具列表>           # 扩展 Agent 工具
        """
    )

    # 守护进程命令
    daemon_group = parser.add_argument_group('守护进程命令')
    daemon_group.add_argument("--start", action="store_true", help="启动 API 守护进程")
    daemon_group.add_argument("--stop", action="store_true", help="停止 API 守护进程")
    daemon_group.add_argument("--restart", action="store_true", help="重启 API 守护进程")
    daemon_group.add_argument("--status", action="store_true", help="查看守护进程状态")
    daemon_group.add_argument("--logs", nargs="?", const=50, type=int, help="查看日志（默认 50 行）")
    daemon_group.add_argument("--install-service", action="store_true", help="生成 systemd/launchd 服务配置")

    # Template 系统命令
    template_group = parser.add_argument_group('Template 系统')
    template_group.add_argument("--create-agent", type=str, metavar="NAME",
                               help="创建新 Agent，需要配合 --template 使用")
    template_group.add_argument("--template", type=str, metavar="NAME",
                               help="使用的模板名称（配合 --create-agent）")
    template_group.add_argument("--list-templates", action="store_true",
                               help="列出所有可用模板")
    template_group.add_argument("--template-dir", action="store_true",
                               help="显示模板目录路径")

    # Config 验证命令
    config_group = parser.add_argument_group('Config 验证')
    config_group.add_argument("--validate-config", type=str, metavar="PATH",
                             help="验证配置文件")
    config_group.add_argument("--generate-config", type=str, metavar="PATH",
                             help="生成配置文件模板")
    config_group.add_argument("--config-type", choices=["agent", "extension"],
                             default="agent", help="配置类型（配合 --generate-config）")

    parser.add_argument("input", nargs="?", help="任务描述")
    parser.add_argument("-t", "--task", help="单次任务")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="详细输出")
    parser.add_argument("--debug", action="store_true", help="调试模式：保存输出到文件")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--isolate", action="store_true", help="按实例 ID 隔离输出目录")
    parser.add_argument("--mode", choices=["auto", "review"], default="auto",
                       help="执行模式：auto(自动) 或 review(用户评审)")

    args = parser.parse_args()

    # 守护进程命令处理
    if args.start or args.stop or args.restart or args.status or args.logs or args.install_service:
        handle_daemon_commands(args)
        return

    # Template 系统命令处理
    if args.list_templates:
        handle_list_templates()
        return

    if args.template_dir:
        from simple_agent.templates.loader import get_template_dir
        print(f"模板目录: {get_template_dir()}")
        return

    if args.create_agent and args.template:
        handle_create_agent(args.create_agent, args.template)
        return

    if args.create_agent and not args.template:
        print_error("错误: --create-agent 需要配合 --template 使用")
        print("示例: python cli.py --create-agent my_agent --template developer")
        return

    # Config 验证命令处理
    if args.validate_config:
        handle_validate_config(args.validate_config)
        return

    if args.generate_config:
        handle_generate_config(args.generate_config, args.config_type)
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
    # 设置执行模式
    coordinator.context.execution_mode = args.mode

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

            # 如果 debug 模式启用，打印 debug 摘要
            if args.debug or coordinator.context.debug_mode:
                try:
                    from simple_agent.core import print_debug_summary
                    print_debug_summary()
                except Exception:
                    pass  # debug 打印失败不影响主流程

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
