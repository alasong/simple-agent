#!/usr/bin/env python3
"""
Workflow CLI - 独立的工作流入口

使用:
    python workflow_cli.py                    # 进入交互模式
    python workflow_cli.py "代码审查流程"      # 生成并运行
    python workflow_cli.py -t "任务" "流程"    # 指定任务
"""

import sys
import argparse
import os
import json

import tools  # noqa: F401
from core import generate_workflow, Workflow, create_agent, list_agents, get_agent

# 全局 workflow 注册表
workflows = {}

# 默认保存目录
WORKFLOWS_DIR = "./workflows"


def setup_readline():
    """设置自动补全"""
    commands = ["/new ", "/list", "/info", "/agents", "/save", "/load ", "/help", "/exit"]
    
    def completer(text, state):
        options = [c for c in commands if c.startswith(text)]
        
        # 补全文件
        if text.startswith("/load "):
            prefix = text.split()[0] + " "
            partial = text[len(prefix):]
            if os.path.exists(WORKFLOWS_DIR):
                for f in os.listdir(WORKFLOWS_DIR):
                    if f.endswith('.json') and f.startswith(partial):
                        options.append(prefix + f)
        
        if state < len(options):
            return options[state]
        return None
    
    try:
        import gnureadline as readline_mod
    except ImportError:
        import readline as readline_mod
    
    readline_mod.set_completer(completer)
    readline_mod.set_completer_delims(' \t\n')
    readline_mod.parse_and_bind("tab: complete")


def interactive_mode(workflow=None):
    """交互模式"""
    setup_readline()
    
    print()
    print(f"{'='*60}")
    print("Workflow CLI - 多 Agent 协作")
    print(f"{'='*60}")
    print("\n命令：/new | /list | /info | /agents | /save | /load | /help | /exit")
    print("(Tab 补全已启用)")
    
    while True:
        # 显示当前 Workflow 状态
        prompt = f"\n[{workflow.name if workflow else '无 Workflow'}] 你："
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
/new <描述>       创建新 Workflow
/list             列出所有 Workflow
/info             显示当前 Workflow 信息
/agents           列出所有 Agent
/save             保存 Workflow (默认保存到 ./workflows/)
/load <名称>      加载 Workflow
/exit             退出

调试功能:
  在任务后添加 --debug 可将各步骤结果保存到文件
  例：检查 /tmp/code.py --debug
  添加 --isolate 按实例 ID 隔离输出目录
  例：审查项目 A,B,C --debug --isolate
""")
        
        elif user_input == "/list":
            if workflows:
                print("\n已创建的 Workflow:")
                for name, wf in workflows.items():
                    print(f"  - {name}: {len(wf.steps)} 步骤")
            else:
                print("\n暂无 Workflow")
            
            # 列出已保存的
            if os.path.exists(WORKFLOWS_DIR):
                files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith('.json')]
                if files:
                    print(f"\n已保存的 Workflow ({len(files)} 个):")
                    for f in files:
                        print(f"  - {f}")
        
        elif user_input == "/agents":
            agents = list_agents()
            if agents:
                print("\n已创建的 Agent:")
                for name, a in agents.items():
                    print(f"  - {name} v{a.version}")
            else:
                print("\n暂无 Agent")
        
        elif user_input.startswith("/new "):
            desc = user_input[5:].strip()
            if not desc:
                print("用法：/new <工作流描述>")
                continue
            
            print(f"\n生成 Workflow: {desc}")
            workflow = generate_workflow(desc)
            workflows[workflow.name] = workflow
            print(f"\n已创建：{workflow.name} ({len(workflow.steps)} 步骤)")
            print("\n输入任务运行")
        
        elif user_input == "/info":
            if not workflow:
                print("暂无 Workflow")
                continue
            
            print(f"\n{'='*50}")
            print(f"名称：{workflow.name}")
            print(f"描述：{workflow.description}")
            print(f"步骤数：{len(workflow.steps)}")
            print(f"\n步骤:")
            for i, step in enumerate(workflow.steps, 1):
                print(f"  {i}. {step.name} -> {step.agent.name}")
            print(f"{'='*50}")
        
        elif user_input == "/save":
            if not workflow:
                print("暂无 Workflow")
                continue
            
            # 默认保存
            os.makedirs(WORKFLOWS_DIR, exist_ok=True)
            filename = f"{workflow.name}.json"
            path = os.path.join(WORKFLOWS_DIR, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(workflow.to_json())
            print(f"\n已保存：{path}")
        
        elif user_input.startswith("/load "):
            name = user_input[6:].strip()
            if not name:
                print("用法：/load <名称或文件名>")
                continue
            
            # 尝试加载
            if os.path.exists(name):
                path = name
            elif os.path.exists(name + ".json"):
                path = name + ".json"
            else:
                path = os.path.join(WORKFLOWS_DIR, f"{name}.json")
            
            if not os.path.exists(path):
                path = os.path.join(WORKFLOWS_DIR, name)
            
            if os.path.exists(path):
                try:
                    # 使用新的 load 方法完整加载（包含 Agent 实例）
                    workflow = Workflow.load(path)
                    workflows[workflow.name] = workflow
                    
                    print(f"\n已加载：{workflow.name}")
                    print(f"步骤数：{len(workflow.steps)}")
                    for i, step in enumerate(workflow.steps, 1):
                        print(f"  {i}. {step.name} -> {step.agent.name} (v{step.agent.version})")
                except Exception as e:
                    print(f"\n加载失败：{e}")
            else:
                print(f"\n未找到：{name}")
        
        else:
            # 默认：创建并运行 或 运行任务
            if workflow:
                print()
                # 检查是否有调试输出参数
                import re
                match = re.match(r'(.+?)\s+--debug(?:\s+(--isolate))?', user_input)
                if match:
                    # 使用 debug 模式，输出到文件
                    task = match.group(1).strip()
                    isolate = match.group(2) == '--isolate'
                    output_dir = f"./workflow_debug/{workflow.name}_{task[:20].replace('/', '_')}"
                    result = workflow.run(task, output_dir=output_dir, isolate_by_instance=isolate)
                    print(f"\n结果：{result.get('_last_output', '完成')[:300]}")
                    print(f"\n[Debug] 各步骤结果已保存到：{output_dir}")
                    if isolate:
                        print(f"[Debug] 已按实例 ID 隔离到子目录")
                else:
                    result = workflow.run(user_input)
                    print(f"\n结果：{result.get('_last_output', '完成')[:300]}")
            else:
                # 创建新 Workflow
                print(f"\n生成 Workflow: {user_input}")
                workflow = generate_workflow(user_input)
                workflows[workflow.name] = workflow
                print(f"\n已创建：{workflow.name} ({len(workflow.steps)} 步骤)")
                print("\n输入任务运行")


def main():
    parser = argparse.ArgumentParser(description="Workflow CLI - 多 Agent 协作")
    
    parser.add_argument("description", nargs="?", help="工作流描述")
    parser.add_argument("-t", "--task", help="初始任务")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="详细输出")
    parser.add_argument("--debug", action="store_true", help="调试模式：将各步骤结果保存到文件")
    parser.add_argument("-o", "--output", help="输出目录（调试模式）")
    parser.add_argument("--isolate", action="store_true", help="按实例 ID 隔离输出目录（每个 agent 副本独立子目录）")
    
    args = parser.parse_args()
    
    if args.description:
        # 生成 Workflow
        print(f"生成 Workflow: {args.description}\n")
        workflow = generate_workflow(args.description, verbose=args.verbose)
        workflows[workflow.name] = workflow
        
        # 运行
        if args.task:
            print(f"\n运行任务：{args.task}")
            
            # 确定输出目录
            output_dir = None
            if args.debug or args.output:
                output_dir = args.output or f"./workflow_debug/{workflow.name}_{args.task[:20].replace('/', '_')}"
            
            result = workflow.run(
                args.task, 
                verbose=args.verbose, 
                output_dir=output_dir,
                isolate_by_instance=args.isolate
            )
            print(f"\n结果：{result.get('_last_output', '完成')[:300]}")
            if output_dir:
                print(f"\n[Debug] 各步骤结果已保存到：{output_dir}")
                if args.isolate:
                    print(f"[Debug] 已按实例 ID 隔离到子目录")
        
        # 进入交互模式
        interactive_mode(workflow)
    else:
        # 纯交互模式
        interactive_mode()


if __name__ == "__main__":
    main()
