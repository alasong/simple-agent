#!/usr/bin/env python3
"""
Agent CLI - 单智能体交互

使用:
    python agent_cli.py                    # 进入交互模式
    python agent_cli.py "文件管理助手"      # 创建并交互
    python agent_cli.py -t "任务" "助手"    # 单次任务
"""

import sys
import argparse
import os

import tools  # noqa: F401
from core import repo, create_agent, update_prompt, get_agent, list_agents, Agent

# 当前 Agent
current_agent = None

# 默认保存目录
AGENTS_DIR = "./agents"


def setup_readline():
    """设置自动补全"""
    commands = ["/new ", "/update ", "/switch ", "/list", "/info", "/clear", "/save", "/load ", "/help", "/exit"]
    
    def completer(text, state):
        options = [c for c in commands if c.startswith(text)]
        
        # 补全 Agent 名称
        if text.startswith("/switch ") or text.startswith("/load "):
            prefix = text.split()[0] + " "
            partial = text[len(prefix):]
            # 补全已创建的 Agent
            for name in list_agents().keys():
                if name.startswith(partial):
                    options.append(prefix + name)
            # 补全文件
            if os.path.exists(AGENTS_DIR):
                for f in os.listdir(AGENTS_DIR):
                    if f.endswith('.json') and f.startswith(partial):
                        options.append(prefix + f)
        
        if state < len(options):
            return options[state]
        return None
    
    try:
        import gnureadline as readline
    except ImportError:
        import readline as readline
    
    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind("tab: complete")


def interactive_mode(agent=None):
    """交互模式"""
    global current_agent
    current_agent = agent
    
    setup_readline()
    
    print()
    print(f"{'='*60}")
    print("Agent CLI - 单智能体交互")
    print(f"{'='*60}")
    print("\n命令: /new | /update | /switch | /list | /info | /clear | /save | /load | /exit")
    print("(Tab 补全已启用)")
    
    while True:
        # 显示当前 Agent 状态
        prompt = f"\n[{current_agent.name if current_agent else '无Agent'}] 你: "
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
/new <描述>       创建新 Agent
/update <描述>    更新提示词
/switch <名称>    切换 Agent
/list             列出所有 Agent (包括 builtin agents)
/info             显示 Agent 信息
/clear            清空记忆
/save             保存 Agent (默认保存到 ./agents/)
/load <名称>      加载 Agent (支持 builtin agents)
/exit             退出

提示：/list 命令会显示已创建的 Agent、已保存的 Agent 和 Builtin Agents
""")
        
        elif user_input == "/list":
            agents = list_agents()
            if agents:
                print("\n已创建的 Agent:")
                for name, a in agents.items():
                    print(f"  - {name} v{a.version}")
            else:
                print("\n暂无 Agent")
            
            # 列出已保存的
            if os.path.exists(AGENTS_DIR):
                files = [f for f in os.listdir(AGENTS_DIR) if f.endswith('.json')]
                if files:
                    print(f"\n已保存的 Agent ({len(files)} 个):")
                    for f in files:
                        print(f"  - {f}")
            
            # 列出 builtin agents
            try:
                from builtin_agents import list_available_agents, get_agent_info
                builtin = list_available_agents()
                if builtin:
                    print(f"\nBuiltin Agents ({len(builtin)} 个):")
                    for agent_type in builtin:
                        info = get_agent_info(agent_type)
                        print(f"  - {agent_type}: {info['name']} (v{info['version']})")
            except ImportError:
                pass
        
        elif user_input.startswith("/new "):
            desc = user_input[5:].strip()
            if not desc:
                print("用法: /new <描述>")
                continue
            current_agent = create_agent(desc)
            print(f"\n已创建: {current_agent}")
        
        elif user_input.startswith("/update "):
            if not current_agent:
                print("请先创建 Agent: /new <描述>")
                continue
            desc = user_input[8:].strip()
            current_agent = update_prompt(current_agent, desc)
            print(f"\n已更新: {current_agent}")
        
        elif user_input.startswith("/switch "):
            name = user_input[8:].strip()
            agent = get_agent(name)
            if agent:
                current_agent = agent
                print(f"\n已切换: {current_agent}")
            else:
                print(f"\n未找到: {name}")
        
        elif user_input == "/info":
            if not current_agent:
                print("暂无 Agent")
                continue
            
            print(f"\n{'='*50}")
            print(f"名称: {current_agent.name}")
            print(f"版本: {current_agent.version}")
            print(f"描述: {current_agent.description}")
            print(f"创建时间: {current_agent.created_at}")
            
            print(f"\n--- LLM ---")
            print(f"  模型: {current_agent.llm.model}")
            print(f"  Base URL: {current_agent.llm.base_url or '默认'}")
            
            print(f"\n--- 提示词 ---")
            print(current_agent.system_prompt or "无")
            
            tools_list = current_agent.tool_registry.get_all_tools()
            print(f"\n--- 工具 ({len(tools_list)} 个) ---")
            for t in tools_list:
                params = list(t.parameters.get("properties", {}).keys())
                print(f"  {t.name}: {t.description}")
                if params:
                    print(f"    参数: {params}")
            
            messages = current_agent.memory.get_messages()
            print(f"\n--- 上下文 ({len(messages)} 条消息) ---")
            for i, msg in enumerate(messages, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"  [{i}] {role}: {content}")
            print(f"{'='*50}")
        
        elif user_input == "/clear":
            if not current_agent:
                print("暂无 Agent")
                continue
            current_agent.memory.clear()
            print("记忆已清空")
        
        elif user_input == "/save":
            if not current_agent:
                print("暂无 Agent")
                continue
            
            # 默认保存
            os.makedirs(AGENTS_DIR, exist_ok=True)
            filename = f"{current_agent.name}.json"
            path = os.path.join(AGENTS_DIR, filename)
            current_agent.save(path)
            print(f"\n已保存: {path}")
        
        elif user_input.startswith("/load "):
            name = user_input[6:].strip()
            if not name:
                print("用法: /load <名称或文件名>")
                continue
            
            # 尝试加载
            if os.path.exists(name):
                path = name
            else:
                path = os.path.join(AGENTS_DIR, f"{name}.json")
            
            if not os.path.exists(path):
                path = os.path.join(AGENTS_DIR, name)
            
            if os.path.exists(path):
                current_agent = Agent.load(path)
                print(f"已加载：{current_agent}")
            else:
                # Try to load builtin agent
                try:
                    from builtin_agents import get_agent
                    current_agent = get_agent(name)
                    print(f"已加载 Builtin Agent: {current_agent}")
                except (ImportError, ValueError):
                    print(f"未找到：{name}")
                    print("提示：可以使用 /list 查看可用的 builtin agents")
        
        else:
            # 默认：创建并运行 或 运行任务
            if current_agent:
                print()
                result = current_agent.run(user_input)
                print(f"\n{current_agent.name}: {result}")
            else:
                # 创建新 Agent
                print(f"\n创建 Agent: {user_input}")
                current_agent = create_agent(user_input)
                print(f"\n已创建: {current_agent}")
                print("\n输入任务运行，或使用命令管理")


def main():
    parser = argparse.ArgumentParser(description="Agent CLI - 单智能体交互")
    
    parser.add_argument("description", nargs="?", help="Agent 描述")
    parser.add_argument("-t", "--task", help="单次任务")
    parser.add_argument("--tags", nargs="+", help="工具标签")
    parser.add_argument("--list-tools", action="store_true", help="列出工具")
    
    args = parser.parse_args()
    
    # 列出工具
    if args.list_tools:
        print("工具仓库:")
        for name, entry in repo.list_tools().items():
            print(f"  - {name}: {entry.tags}")
        return
    
    # 创建 Agent
    agent = None
    if args.description:
        print(f"创建 Agent: {args.description}")
        agent = create_agent(args.description, tags=args.tags)
        print(f"\n{agent}")
    
    # 单次任务
    if args.task and agent:
        print()
        result = agent.run(args.task)
        print(result)
        return
    
    # 交互模式
    interactive_mode(agent)


if __name__ == "__main__":
    main()
