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

# 导入工具模块
import tools  # noqa: F401

# 导入协调器
from cli_coordinator import CLICoordinator
from cli_agent import CLIAgent

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


def interactive_mode(coordinator: CLICoordinator):
    """交互模式"""
    # 设置 readline 自动补全（可选）
    try:
        import readline
        # 简化版，暂时不实现复杂补全
    except ImportError:
        pass
    
    print()
    print(f"{'='*60}")
    print("CLI Agent - 智能任务助手 (精简版)")
    print(f"{'='*60}")
    print("\n命令：/help | /exit | /list | /load | /workflow ...")
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
    
    parser.add_argument("input", nargs="?", help="任务描述")
    parser.add_argument("-t", "--task", help="单次任务")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="详细输出")
    parser.add_argument("--debug", action="store_true", help="调试模式：保存输出到文件")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--isolate", action="store_true", help="按实例 ID 隔离输出目录")
    
    args = parser.parse_args()
    
    # 创建协调器
    coordinator = CLICoordinator()
    coordinator.initialize()
    
    # 设置配置
    if args.debug or args.output:
        coordinator.context.output_dir = args.output or OUTPUT_DIR
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
