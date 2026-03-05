#!/usr/bin/env python3
"""
CLI 插件

一句话创建 Agent:
    python cli.py "文件管理助手"
    python cli.py "代码审查" --tags check,code
    python cli.py "高级助手" --base FileAgent
"""

import sys
import argparse
import os

# 导入工具以注册到仓库
import tools  # noqa: F401

from core import (
    repo, create_agent, update_prompt, get_agent, list_agents,
    OpenAILLM, register_llm
)

# ==================== 自动补全 ====================

COMMANDS = [
    "/new ", "/update ", "/switch ", "/list", "/info", 
    "/clear", "/save ", "/exit", "/help"
]

def get_completions(text):
    """获取补全选项"""
    options = []
    
    # 命令补全
    for cmd in COMMANDS:
        if cmd.startswith(text):
            options.append(cmd)
    
    # /switch 和 /update 补全 Agent 名称
    if text.startswith("/switch ") or text.startswith("/update "):
        prefix = text.split()[0] + " "
        partial = text[len(prefix):]
        for name in list_agents().keys():
            if name.startswith(partial):
                options.append(prefix + name)
    
    return options


def completer(text, state):
    """readline 补全函数"""
    options = get_completions(text)
    if state < len(options):
        return options[state]
    return None


def setup_readline():
    """设置 readline 补全"""
    try:
        # 优先使用 gnureadline
        try:
            import gnureadline as readline
        except ImportError:
            import readline
        
        # 设置补全函数
        readline.set_completer(completer)
        
        # 设置补全分隔符（不分割 / 符号）
        readline.set_completer_delims(' \t\n')
        
        # 启用 tab 补全
        readline.parse_and_bind("tab: complete")
        
        return True
    except ImportError:
        return False


# ==================== 交互模式 ====================

def interactive_mode(agent):
    """交互式对话模式"""
    
    # 设置自动补全
    has_readline = setup_readline()
    
    print()
    print(f"{'='*60}")
    print(f"{agent.name} v{agent.version}")
    print(f"{agent.description}")
    print(f"{'='*60}")
    print("\n命令: /new | /update | /switch | /list | /info | /clear | /save | /exit")
    if has_readline:
        print("(Tab 补全已启用)")
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            user_input = user_input.encode('utf-8', errors='ignore').decode('utf-8')
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        except:
            continue
        
        if not user_input:
            continue
        
        # 命令
        if user_input == "/exit":
            print("再见!")
            break
        
        elif user_input == "/clear":
            agent.memory.clear()
            print("记忆已清空")
            continue
        
        elif user_input == "/info":
            # 显示 Agent 全部信息
            print(f"\n{'='*50}")
            print(f"名称: {agent.name}")
            print(f"版本: {agent.version}")
            print(f"描述: {agent.description}")
            print(f"创建时间: {agent.created_at}")
            
            # LLM
            print(f"\n--- LLM ---")
            print(f"  模型: {agent.llm.model}")
            print(f"  Base URL: {agent.llm.base_url or '默认'}")
            
            # 提示词
            print(f"\n--- 提示词 ---")
            print(agent.system_prompt or "无")
            
            # 工具
            tools = agent.tool_registry.get_all_tools()
            print(f"\n--- 工具 ({len(tools)} 个) ---")
            for t in tools:
                params = list(t.parameters.get("properties", {}).keys())
                print(f"  {t.name}: {t.description}")
                if params:
                    print(f"    参数: {params}")
            
            # 上下文
            messages = agent.memory.get_messages()
            print(f"\n--- 上下文 ({len(messages)} 条消息) ---")
            for i, msg in enumerate(messages, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"  [{i}] {role}: {content}")
            
            print(f"\n{'='*50}")
            continue
        
        elif user_input.startswith("/save "):
            path = user_input[6:].strip()
            if not path:
                print("用法: /save <路径>")
            else:
                agent.save(path)
                print(f"\n已保存到: {path}")
            continue
        
        elif user_input == "/list":
            agents = list_agents()
            if agents:
                print("\n已创建的 Agent:")
                for name, a in agents.items():
                    print(f"  - {name} v{a.version}")
            else:
                print("\n暂无 Agent")
            continue
        
        elif user_input.startswith("/new "):
            desc = user_input[5:].strip()
            agent = create_agent(desc)
            print(f"\n创建: {agent}")
            continue
        
        elif user_input.startswith("/update "):
            desc = user_input[8:].strip()
            agent = update_prompt(agent, desc)
            print(f"\n更新: {agent}")
            continue
        
        elif user_input.startswith("/switch "):
            name = user_input[8:].strip()
            new_agent = get_agent(name)
            if new_agent:
                agent = new_agent
                print(f"\n切换: {agent}")
            else:
                print(f"\n未找到: {name}")
            continue
        
        elif user_input == "/help":
            print("""
/new <描述>       创建新 Agent
/update <描述>    更新提示词（生成新版本）
/switch <名称>    切换 Agent
/list             列出所有 Agent
/info             显示 Agent 全部信息（提示词、工具、上下文）
/clear            清空记忆
/save <路径>      保存 Agent 到文件
/exit             退出
""")
            continue
        
        else:
            print()
            result = agent.run(user_input)
            print(f"\n{agent.name}: {result}")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="最小 Agent 框架")
    
    # 位置参数
    parser.add_argument("description", nargs="?", help="Agent 描述")
    
    # 资源抽取
    parser.add_argument("--tools", nargs="+", help="指定工具")
    parser.add_argument("--tags", nargs="+", help="工具标签")
    parser.add_argument("--llm", default="default", help="LLM 名称")
    
    # 继承
    parser.add_argument("--base", help="继承的 Agent")
    
    # 提示词更新
    parser.add_argument("--update", metavar="NAME", help="更新指定 Agent")
    
    # 运行
    parser.add_argument("-t", "--task", help="单次任务")
    
    # 列表
    parser.add_argument("--list-tools", action="store_true", help="列出工具")
    parser.add_argument("--list-llms", action="store_true", help="列出 LLM")
    parser.add_argument("--list-agents", action="store_true", help="列出 Agent")
    
    args = parser.parse_args()
    
    # 列出资源
    if args.list_tools:
        print("工具仓库:")
        for name, entry in repo.list_tools().items():
            print(f"  - {name}: {entry.tags}")
        return
    
    if args.list_llms:
        print("LLM 仓库:")
        for name, entry in repo.list_llms().items():
            print(f"  - {name}")
        return
    
    if args.list_agents:
        agents = list_agents()
        if agents:
            print("Agent 注册表:")
            for name, a in agents.items():
                print(f"  - {name} v{a.version}: {a.description[:30]}...")
        else:
            print("暂无 Agent")
        return
    
    # 更新
    if args.update:
        existing = get_agent(args.update)
        if existing:
            if not args.description:
                print("错误: 需要新描述")
                return
            agent = update_prompt(existing, args.description)
            print(f"更新: {agent}")
            if args.task:
                result = agent.run(args.task)
                print(result)
        else:
            print(f"未找到: {args.update}")
        return
    
    # 创建 Agent
    if args.description:
        base_agent = get_agent(args.base) if args.base else None
        agent = create_agent(
            description=args.description,
            tools=args.tools,
            tags=args.tags,
            llm=args.llm,
            base=base_agent
        )
    elif args.base:
        agent = get_agent(args.base)
        if not agent:
            print(f"未找到: {args.base}")
            return
    else:
        agent = create_agent("智能助手")
    
    print(f"\n{agent}")
    
    if args.task:
        print()
        result = agent.run(args.task)
        print(result)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
