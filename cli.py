#!/usr/bin/env python3
"""
统一 CLI 入口 - CLI Agent

使用:
    python cli.py                    # 进入交互模式
    python cli.py "帮我写个函数"      # 单次任务
    python cli.py -t "任务"          # 指定任务

特性:
    - 自然语言理解
    - 自动选择合适的 agent
    - 支持多步骤 workflow
    - 支持并行任务（多副本）
    - 输出目录隔离
"""

import sys
import argparse
import os
import re

import tools  # noqa: F401
from cli_agent import CLIAgent

# 全局 CLI Agent 实例
cli_agent = None

# 默认保存目录
WORKFLOWS_DIR = "./workflows"
OUTPUT_DIR = "./cli_output"


def setup_readline():
    """设置自动补全"""
    commands = ["/help", "/exit", "/clear", "/debug", "/isolate"]
    
    def completer(text, state):
        options = [c for c in commands if c.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    try:
        import gnureadline as readline
    except ImportError:
        import readline
    
    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind("tab: complete")


def interactive_mode():
    """交互模式"""
    global cli_agent
    cli_agent = CLIAgent()
    
    setup_readline()
    
    print()
    print(f"{'='*60}")
    print("CLI Agent - 智能任务助手")
    print(f"{'='*60}")
    print("\n命令：/help | /exit | /clear | /debug [on|off] | /isolate [on|off]")
    print("(Tab 补全已启用)")
    print("\n提示：")
    print("  - 直接输入任务描述，如'帮我写一个快速排序函数'")
    print("  - 多项目任务，如'审查 A、B、C 三个项目的代码'")
    print("  - 多步骤任务，如'先设计架构，再编码，最后测试'")
    
    # 状态
    debug_mode = False  # 是否保存输出到文件
    isolate_mode = False  # 是否隔离输出目录
    
    while True:
        prompt = f"\n[CLI Agent] 你："
        try:
            user_input = input(prompt).strip()
            user_input = user_input.encode('utf-8', errors='ignore').decode('utf-8')
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        
        if not user_input:
            continue
        
        # 命令处理
        if user_input == "/exit":
            print("再见!")
            break
        
        elif user_input == "/help":
            print("""
/help           显示帮助
/exit           退出
/clear          清空 CLI Agent 记忆
/debug [on|off] 切换调试模式（保存输出到文件）
/isolate [on|off] 切换隔离模式（每个 agent 副本独立输出目录）

示例任务:
  - "帮我写一个 Python 快速排序函数"
  - "审查这个文件的代码质量：/path/to/code.py"
  - "帮我开发一个功能，先设计，再编码，最后测试"
  - "审查 A、B、C 三个项目的代码"
""")
        
        elif user_input == "/clear":
            if cli_agent:
                cli_agent.agent.memory.clear()
                print("CLI Agent 记忆已清空")
            else:
                print("暂无 Agent")
        
        elif user_input.startswith("/debug"):
            parts = user_input.split()
            if len(parts) > 1:
                debug_mode = parts[1].lower() in ["on", "true", "1"]
            else:
                debug_mode = not debug_mode
            print(f"调试模式：{'已开启' if debug_mode else '已关闭'}")
            if debug_mode:
                print(f"输出目录：{OUTPUT_DIR}")
        
        elif user_input.startswith("/isolate"):
            parts = user_input.split()
            if len(parts) > 1:
                isolate_mode = parts[1].lower() in ["on", "true", "1"]
            else:
                isolate_mode = not isolate_mode
            print(f"隔离模式：{'已开启' if isolate_mode else '已关闭'}")
            if isolate_mode:
                print("每个 agent 副本将有独立的输出子目录")
        
        else:
            # 执行任务
            if not cli_agent:
                cli_agent = CLIAgent()
            
            # 确定输出目录
            output_dir = None
            if debug_mode:
                # 生成输出目录名
                task_prefix = user_input[:20].replace('/', '_').replace('\\', '_')
                output_dir = f"{OUTPUT_DIR}/{task_prefix}"
            
            try:
                result = cli_agent.execute(
                    user_input,
                    verbose=True,
                    output_dir=output_dir,
                    isolate_by_instance=isolate_mode
                )
                
                print(f"\n{'='*60}")
                print(f"结果：{result}")
                print(f"{'='*60}")
                
                if output_dir:
                    print(f"\n[Debug] 输出已保存到：{output_dir}")
                    if isolate_mode:
                        print(f"[Debug] 已按实例 ID 隔离到子目录")
                
            except Exception as e:
                print(f"\n[错误] {e}")
                import traceback
                traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="CLI Agent - 智能任务助手")
    
    parser.add_argument("input", nargs="?", help="任务描述")
    parser.add_argument("-t", "--task", help="单次任务")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="详细输出")
    parser.add_argument("--debug", action="store_true", help="调试模式：保存输出到文件")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--isolate", action="store_true", help="按实例 ID 隔离输出目录")
    
    args = parser.parse_args()
    
    # 创建 CLI Agent
    cli = CLIAgent()
    
    # 确定输出目录
    output_dir = None
    if args.debug or args.output:
        output_dir = args.output or OUTPUT_DIR
    
    if args.input or args.task:
        # 单次任务模式
        task = args.task or args.input
        
        print(f"[CLI Agent] 执行任务：{task}")
        if output_dir:
            print(f"[CLI Agent] 输出目录：{output_dir}")
            if args.isolate:
                print(f"[CLI Agent] 隔离模式：已开启")
        
        try:
            result = cli.execute(
                task,
                verbose=args.verbose,
                output_dir=output_dir,
                isolate_by_instance=args.isolate
            )
            
            print(f"\n{'='*60}")
            print(f"结果：{result}")
            print(f"{'='*60}")
            
            if output_dir:
                print(f"\n[Debug] 输出已保存到：{output_dir}")
                if args.isolate:
                    print(f"[Debug] 已按实例 ID 隔离到子目录")
                    
        except Exception as e:
            print(f"\n[错误] {e}")
            import traceback
            traceback.print_exc()
        
        # 单次任务不进入交互模式
        return
    
    # 交互模式
    interactive_mode()


if __name__ == "__main__":
    main()
