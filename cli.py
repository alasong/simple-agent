#!/usr/bin/env python3
"""
统一 CLI 入口 - CLI Agent

使用:
    python cli.py                    # 进入交互模式
    python cli.py "帮我写个函数"      # 单次任务（智能模式）
    python cli.py -t "任务"          # 指定任务

特性:
    - 自然语言理解，自动选择合适的 agent
    - 支持多步骤 workflow
    - 支持并行任务（多副本）
    - 输出目录隔离
    - 支持手动创建和管理 Agent
    - 富文本输出展示
"""

import sys
import argparse
import os
import re
import json

import tools  # noqa: F401
from cli_agent import CLIAgent
from core import (
    create_agent, update_prompt, get_agent, list_agents,
    Agent, Workflow, generate_workflow,
    EnhancedMemory, Experience,
    TreeOfThought, ReflectionLoop,
    SkillLibrary
)

# Debug tracking imports
try:
    from core import enable_debug, disable_debug, get_debug_summary, print_debug_summary, tracker
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False

# 富文本输出支持
try:
    from core.rich_output import get_rich_output, RichOutput
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 全局 CLI Agent 实例
cli_agent = None

# 当前手动管理的 Agent（单 Agent 模式）
current_agent = None

# 增强型 Agent（阶段 1 功能）
enhanced_agent = None
skill_library = None

# 默认保存目录（从统一配置加载）
from core.config_loader import get_config
_config = get_config()

# 转换为绝对路径，确保目录正确
AGENTS_DIR = os.path.abspath(_config.get('directories.agents', './agents'))
WORKFLOWS_DIR = os.path.abspath(_config.get('directories.workflows', './workflows'))
# 所有输出都保存到 output/ 目录，不污染根目录
OUTPUT_DIR = os.path.abspath(_config.get('directories.cli_output', './output/cli'))
OUTPUT_ROOT = os.path.abspath(_config.get('directories.output_root', './output'))

# 测试脚本防护：检测是否在测试环境中运行
def is_test_environment():
    """检测是否在测试环境中运行"""
    import sys
    # 检查是否在 pytest 或 unittest 中运行
    if any(mod.startswith('pytest') or mod.startswith('unittest') for mod in sys.modules):
        return True
    # 检查命令行参数
    if any('test' in arg.lower() for arg in sys.argv):
        return True
    # 检查环境变量
    if os.environ.get('TESTING') or os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    return False

# 如果在测试环境中，使用临时目录
if is_test_environment():
    import tempfile
    _temp_dir = tempfile.mkdtemp(prefix='cli_test_')
    AGENTS_DIR = os.path.join(_temp_dir, 'agents')
    WORKFLOWS_DIR = os.path.join(_temp_dir, 'workflows')
    OUTPUT_DIR = os.path.join(_temp_dir, 'output', 'cli')
    OUTPUT_ROOT = os.path.join(_temp_dir, 'output')
    # 创建临时目录
    os.makedirs(AGENTS_DIR, exist_ok=True)
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)


def setup_readline():
    """设置自动补全"""
    commands = [
        "/new ", "/update ", "/switch ", "/list", "/info", 
        "/clear", "/save", "/load ", "/workflow ", "/debug",
        "/isolate", "/help", "/exit",
        "/enhanced ", "/memory", "/skills", "/reasoning ",
        "/review ", "/debug summary", "/debug stats"
    ]
    
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
            # 补全已保存的 Agent 文件
            if os.path.exists(AGENTS_DIR):
                for f in os.listdir(AGENTS_DIR):
                    if f.endswith('.json') and f.startswith(partial):
                        options.append(prefix + f)
            # 补全 builtin agents
            try:
                from builtin_agents import list_available_agents
                for agent_type in list_available_agents():
                    if agent_type.startswith(partial):
                        options.append(prefix + agent_type)
            except ImportError:
                pass
        
        # 补全 workflow 文件
        if text.startswith("/workflow "):
            prefix = text.split()[0] + " "
            partial = text[len(prefix):]
            if os.path.exists(WORKFLOWS_DIR):
                for f in os.listdir(WORKFLOWS_DIR):
                    if f.endswith('.json') and f.startswith(partial):
                        options.append(prefix + f)
        
        # 补全 enhanced 策略
        if text.startswith("/enhanced "):
            prefix = "/enhanced "
            partial = text[len(prefix):]
            strategies = ["direct", "plan_reflect", "tree_of_thought"]
            for strategy in strategies:
                if strategy.startswith(partial):
                    options.append(prefix + strategy)
        
        # 补全 reasoning 模式
        if text.startswith("/reasoning "):
            prefix = "/reasoning "
            partial = text[len(prefix):]
            modes = ["tot", "tree_of_thought", "reflection", "reflection_loop"]
            for mode in modes:
                if mode.startswith(partial):
                    options.append(prefix + mode)
        
        # 补全 review 文件
        if text.startswith("/review "):
            prefix = "/review "
            partial = text[len(prefix):]
            # 补全 Python 文件
            try:
                from glob import glob
                py_files = glob("**/*.py", recursive=True)
                for py_file in py_files:
                    if py_file.startswith(partial) and not any(ex in py_file for ex in ['.venv', 'venv', '__pycache__']):
                        options.append(prefix + py_file)
            except:
                pass
        
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


def show_help():
    """显示帮助信息"""
    print("""
===== 会话管理 =====
/sessions          列出所有会话
/session <名称>     切换会话
/session new <名称> 创建新会话
/session del <名称> 删除会话
/clear             清空当前会话记忆

===== 智能模式 =====
/help              显示帮助
/exit              退出
/debug [on|off]    切换调试模式（默认已开启）
/debug summary     显示调试摘要（Agent/Workflow 执行统计）
/debug stats       显示详细统计信息
/isolate [on|off]  切换隔离模式（默认开启）

===== 后台任务管理 =====
/bg <任务>       后台执行任务，立即返回（不阻塞）
/tasks           列出所有后台任务及状态
/result <task_id> 查看任务结果（阻塞直到完成）
/cancel <task_id> 取消任务
/task_stats      查看任务统计信息

===== 单 Agent 模式 =====
/new <描述>     创建新 Agent
/update <描述>  更新当前 Agent 提示词
/switch <名称>  切换到已创建的 Agent
/list           列出所有 Agent
/info           显示当前 Agent 详情
/save           保存当前 Agent 到 ./agents/
/load <名称>    加载 Agent（支持 builtin agents）
/workflow <文件> 加载并运行工作流

===== 阶段 1 增强功能 =====
/enhanced [策略] 使用增强型 Agent 执行任务
                 策略：direct, plan_reflect, tree_of_thought
/memory         查看记忆状态（工作/短期/长期记忆）
/memory clear   清空记忆
/skills         查看技能库和技能统计
/reasoning [模式] 手动选择推理模式
                 模式：tot (思维树), reflection (反思循环)

===== 代码审查工具 =====
/review <文件>   使用 Agent 深度审查代码
/review --all    审查所有 Python 文件

===== 说明 =====
- 会话：自动保存对话历史到 ~/.simple-agent/sessions/
- 每次执行任务后自动保存
- 切换会话可恢复历史对话
- 使用 /session 切换不同任务的上下文
- 增强型 Agent 支持自动策略选择和记忆管理
- 代码审查工具使用 EnhancedAgent 的代码分析技能
- 后台任务支持并发执行（默认最多 3 个任务同时运行）
""")


def list_all_agents():
    """列出所有可用的 agents"""
    # 已创建的 agents
    agents = list_agents()
    if agents:
        print("\n===== 已创建的 Agent =====")
        for name, a in agents.items():
            print(f"  - {name} v{a.version}")
    else:
        print("\n暂无已创建的 Agent")
    
    # 已保存的 Agent 文件
    if os.path.exists(AGENTS_DIR):
        files = [f for f in os.listdir(AGENTS_DIR) if f.endswith('.json')]
        if files:
            print(f"\n===== 已保存的 Agent ({len(files)} 个) =====")
            for f in files:
                print(f"  - {f}")
    
    # Builtin agents
    try:
        from builtin_agents import list_available_agents, get_agent_info
        builtin = list_available_agents()
        if builtin:
            print(f"\n===== Builtin Agents ({len(builtin)} 个) =====")
            for agent_type in builtin:
                info = get_agent_info(agent_type)
                print(f"  - {agent_type}: {info['name']} (v{info['version']})")
    except ImportError:
        pass


def show_agent_info(agent):
    """显示 agent 详情"""
    if not agent:
        print("暂无 Agent")
        return
    
    print(f"\n{'='*60}")
    print(f"名称：{agent.name}")
    print(f"版本：{agent.version}")
    print(f"描述：{agent.description}")
    print(f"创建时间：{agent.created_at}")
    if hasattr(agent, 'instance_id') and agent.instance_id:
        print(f"实例 ID: {agent.instance_id}")
    
    print(f"\n--- LLM ---")
    print(f"  模型：{agent.llm.model}")
    print(f"  Base URL: {agent.llm.base_url or '默认'}")
    
    print(f"\n--- 提示词 ---")
    print(agent.system_prompt or "无")
    
    tools_list = agent.tool_registry.get_all_tools()
    print(f"\n--- 工具 ({len(tools_list)} 个) ---")
    for t in tools_list:
        params = list(t.parameters.get("properties", {}).keys())
        print(f"  {t.name}: {t.description}")
        if params:
            print(f"    参数：{params}")
    
    messages = agent.memory.get_messages()
    print(f"\n--- 上下文 ({len(messages)} 条消息) ---")
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"  [{i}] {role}: {content}")
    print(f"{'='*60}")


def load_agent(name):
    """加载 agent（从文件或 builtin）"""
    global current_agent
    
    # 尝试加载已保存的 Agent
    if os.path.exists(name):
        path = name
    else:
        path = os.path.join(AGENTS_DIR, f"{name}.json")
    
    if not os.path.exists(path):
        path = os.path.join(AGENTS_DIR, name)
    
    if os.path.exists(path):
        current_agent = Agent.load(path)
        print(f"\n已加载：{current_agent}")
        return True
    
    # 尝试加载 builtin agent
    try:
        from builtin_agents import get_agent
        current_agent = get_agent(name)
        print(f"\n已加载 Builtin Agent: {current_agent}")
        return True
    except (ImportError, ValueError):
        print(f"\n未找到：{name}")
        print("提示：使用 /list 查看可用的 agents")
        return False


def save_agent(agent):
    """保存 agent 到文件"""
    if not agent:
        print("暂无 Agent")
        return
    
    os.makedirs(AGENTS_DIR, exist_ok=True)
    filename = f"{agent.name}.json"
    path = os.path.join(AGENTS_DIR, filename)
    agent.save(path)
    print(f"\n已保存：{path}")


def run_workflow(workflow_path, user_input):
    """加载并运行 workflow"""
    if not os.path.exists(workflow_path):
        print(f"工作流文件不存在：{workflow_path}")
        return
    
    workflow = Workflow.load(workflow_path)
    print(f"\n已加载工作流：{workflow.name}")
    print(f"描述：{workflow.description}")
    print(f"步骤数：{len(workflow.steps)}")
    
    # 运行工作流
    result = workflow.run(user_input, verbose=True)
    print(f"\n结果：{result.get('_last_output', '完成')}")


def init_enhanced_agent():
    """初始化增强型 Agent"""
    global enhanced_agent, skill_library
    from core.agent_enhanced import EnhancedAgent
    from core.llm import OpenAILLM
    
    llm = OpenAILLM()
    memory = EnhancedMemory()
    skill_library = SkillLibrary()
    
    enhanced_agent = EnhancedAgent(llm=llm, memory=memory, skill_library=skill_library)
    
    print(f"\n[阶段 1] 增强型 Agent 已初始化")
    print(f"  - EnhancedMemory: 已启用")
    print(f"  - SkillLibrary: {len(skill_library.skills)} 个技能")
    print(f"  - 推理模式：TreeOfThought, ReflectionLoop")


def interactive_mode():
    """交互模式"""
    global cli_agent, current_agent
    
    setup_readline()
    
    # 初始化 CLI Agent（从配置加载）
    cli_agent = CLIAgent()
    
    # 加载默认会话到 CLI Agent
    from core.session import load_session
    load_session("default", cli_agent.agent)
    
    # 初始化增强型 Agent（阶段 1）
    init_enhanced_agent()
    
    # 默认启用 debug 模式
    from core import enable_debug
    enable_debug(verbose=True)
    
    print()
    print(f"{'='*60}")
    print("CLI Agent - 智能任务助手")
    print(f"{'='*60}")
    print("\n命令：/help | /exit | /list | /load | /workflow ...")
    print("(Tab 补全已启用)")
    print("\n模式说明:")
    print("  - 直接输入任务：自动分析意图，选择合适的 agent")
    print("  - /load developer: 切换到单 Agent 模式")
    print("  - /workflow xxx.json: 运行工作流")
    print("\n默认设置:")
    print("  - 隔离模式：✓ 已开启 (每个 agent 输出到独立子目录)")
    print("  - 调试模式：✓ 已开启 (显示详细执行过程)")
    print("  - 使用 /debug off 可关闭调试模式")
    
    # 状态
    debug_mode = True  # 默认开启 debug 模式
    isolate_mode = True  # 默认开启隔离模式
    
    while True:
        # 显示当前状态
        if current_agent:
            prompt = f"\n[{current_agent.name}] 你："
        else:
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
            show_help()
        
        elif user_input == "/list":
            list_all_agents()
        
        elif user_input == "/clear":
            if current_agent:
                current_agent.memory.clear()
                print(f"{current_agent.name} 记忆已清空")
            elif cli_agent:
                cli_agent.clear_memory()
                print("CLI Agent 记忆已清空")
            else:
                print("暂无 Agent")
        
        elif user_input == "/sessions":
            from core.session import list_sessions, get_session_info
            sessions = list_sessions()
            if not sessions:
                print("暂无保存的会话")
            else:
                print(f"\n{'='*60}")
                print(f"会话列表 ({len(sessions)} 个):")
                for s in sessions:
                    info = get_session_info(s)
                    if info:
                        agent_name = info.get('agent_name', 'Unknown')
                        msg_count = info.get('message_count', 0)
                        updated = info.get('updated_at', '')
                        print(f"  - {s} (Agent: {agent_name}, 消息：{msg_count}, 更新：{updated})")
                    else:
                        print(f"  - {s}")
                print(f"{'='*60}")
        
        elif user_input.startswith("/session"):
            from core.session import switch_session, get_current_session, get_session_manager
            
            parts = user_input.split()
            agent = current_agent or (cli_agent.agent if cli_agent else None)
            
            if len(parts) == 1:
                # 只显示当前会话
                current = get_current_session()
                print(f"当前会话：{current or 'default'}")
            elif len(parts) == 2:
                # /session <name> - 切换会话
                if not agent:
                    print("暂无 Agent")
                elif switch_session(parts[1], agent):
                    print(f"已切换到会话：{parts[1]}")
                else:
                    print(f"切换会话失败：{parts[1]}")
            elif parts[1] == "new" and len(parts) >= 3:
                # /session new <name> - 创建新会话
                if not agent:
                    print("暂无 Agent")
                elif switch_session(parts[2], agent):
                    print(f"已创建并切换到新会话：{parts[2]}")
                else:
                    print(f"创建会话失败：{parts[2]}")
            elif parts[1] == "del" and len(parts) >= 3:
                # /session del <name> - 删除会话
                manager = get_session_manager()
                if manager.delete(parts[2]):
                    print(f"已删除会话：{parts[2]}")
                else:
                    print(f"会话不存在：{parts[2]}")
            else:
                print("用法：")
                print("  /session              显示当前会话")
                print("  /session <名称>        切换会话")
                print("  /session new <名称>    创建新会话")
                print("  /session del <名称>    删除会话")
        
        elif user_input == "/info":
            if current_agent:
                show_agent_info(current_agent)
            elif cli_agent:
                show_agent_info(cli_agent.agent)
            else:
                print("暂无 Agent")
        
        elif user_input.startswith("/load "):
            name = user_input[6:].strip()
            if not name:
                print("用法：/load <名称或文件名>")
                continue
            load_agent(name)
        
        elif user_input.startswith("/switch "):
            name = user_input[8:].strip()
            agent = get_agent(name)
            if agent:
                current_agent = agent
                print(f"\n已切换：{current_agent}")
            else:
                print(f"\n未找到：{name}")
        
        elif user_input.startswith("/new "):
            desc = user_input[5:].strip()
            if not desc:
                print("用法：/new <描述>")
                continue
            current_agent = create_agent(desc)
            print(f"\n已创建：{current_agent}")
        
        elif user_input.startswith("/update "):
            if not current_agent:
                print("请先加载或创建 Agent")
                continue
            desc = user_input[8:].strip()
            current_agent = update_prompt(current_agent, desc)
            print(f"\n已更新：{current_agent}")
        
        elif user_input == "/save":
            if current_agent:
                save_agent(current_agent)
            else:
                print("暂无 Agent")
        
        elif user_input.startswith("/workflow"):
            # 处理 /workflow <文件> [任务描述]
            if len(user_input) == len("/workflow"):
                # 只输入了 /workflow，没有参数
                print("用法：/workflow <工作流文件> [任务描述]")
                print("示例：")
                print("  /workflow code_review.json")
                print("  /workflow code_review.json 审查这个文件的代码")
                continue
            
            # 解析参数：/workflow <文件> [任务]
            parts = user_input[len("/workflow"):].strip().split(None, 1)
            workflow_path = parts[0]
            task = parts[1] if len(parts) > 1 else None
            
            if not task:
                # 没有提供任务，让用户输入
                task = input("请输入任务描述：").strip()
            
            run_workflow(workflow_path, task)
        
        elif user_input.startswith("/debug"):
            parts = user_input.split()
            
            # 处理子命令
            if len(parts) >= 2:
                subcommand = parts[1].lower()
                
                if subcommand == "summary":
                    # 显示调试摘要
                    if not DEBUG_AVAILABLE:
                        print("[错误] 调试模块不可用")
                    else:
                        print(f"\n{'='*60}")
                        print(f"调试执行摘要")
                        print(f"{'='*60}")
                        print_debug_summary()
                
                elif subcommand == "stats":
                    # 显示详细统计
                    if not DEBUG_AVAILABLE:
                        print("[错误] 调试模块不可用")
                    else:
                        print(f"\n{'='*60}")
                        print(f"详细统计信息")
                        print(f"{'='*60}")
                        
                        # Agent 统计
                        agent_stats = tracker.get_agent_stats()
                        if agent_stats and agent_stats.get('count', 0) > 0:
                            print(f"\n📊 Agent 执行统计:")
                            print(f"  总执行次数：{agent_stats.get('count', 0)}")
                            print(f"  成功：{agent_stats.get('successful', 0)}")
                            print(f"  失败：{agent_stats.get('failed', 0)}")
                            if agent_stats.get('count', 0) > 0:
                                print(f"  成功率：{agent_stats.get('success_rate', 0):.1%}")
                                print(f"  平均耗时：{agent_stats.get('avg_duration', 0):.3f}秒")
                            
                            # 按 Agent 分类统计
                            if 'by_agent' in agent_stats and agent_stats['by_agent']:
                                print(f"\n  按 Agent 分类:")
                                for agent_name, stats in agent_stats['by_agent'].items():
                                    print(f"    - {agent_name}:")
                                    print(f"        执行：{stats.get('count', 0)} 次")
                                    print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
                                    print(f"        工具调用：{stats.get('total_tool_calls', 0)} 次")
                        else:
                            print("\n暂无 Agent 执行记录")
                        
                        # Workflow 统计
                        workflow_stats = tracker.get_workflow_stats()
                        if workflow_stats and workflow_stats.get('count', 0) > 0:
                            print(f"\n📊 Workflow 执行统计:")
                            print(f"  总执行次数：{workflow_stats.get('count', 0)}")
                            print(f"  成功：{workflow_stats.get('successful', 0)}")
                            print(f"  失败：{workflow_stats.get('failed', 0)}")
                            if workflow_stats.get('count', 0) > 0:
                                print(f"  成功率：{workflow_stats.get('success_rate', 0):.1%}")
                                print(f"  平均耗时：{workflow_stats.get('avg_duration', 0):.3f}秒")
                                print(f"  总步骤数：{workflow_stats.get('total_steps', 0)}")
                                print(f"  步骤成功率：{workflow_stats.get('step_success_rate', 0):.1%}")
                            
                            # 按 Workflow 分类统计
                            if 'by_workflow' in workflow_stats and workflow_stats['by_workflow']:
                                print(f"\n  按 Workflow 分类:")
                                for workflow_name, stats in workflow_stats['by_workflow'].items():
                                    print(f"    - {workflow_name}:")
                                    print(f"        执行：{stats.get('count', 0)} 次")
                                    print(f"        平均步骤：{stats.get('avg_steps', 0):.1f}")
                                    print(f"        平均耗时：{stats.get('avg_duration', 0):.3f}秒")
                        else:
                            print("\n暂无 Workflow 执行记录")
                        
                        print(f"\n{'='*60}")
                
                elif subcommand in ["on", "off", "true", "1", "false", "0"]:
                    # 传统用法：/debug on|off
                    debug_mode = subcommand in ["on", "true", "1"]
                    print(f"调试模式：{'已开启' if debug_mode else '已关闭'}")
                    if debug_mode:
                        print(f"输出目录：{OUTPUT_DIR}")
                        if DEBUG_AVAILABLE:
                            enable_debug(verbose=True)
                            print(f"调试跟踪器：已启用")
                    else:
                        if DEBUG_AVAILABLE:
                            disable_debug()
                            print(f"调试跟踪器：已禁用")
                
                else:
                    # 切换模式
                    debug_mode = not debug_mode
                    print(f"调试模式：{'已开启' if debug_mode else '已关闭'}")
                    if debug_mode:
                        print(f"输出目录：{OUTPUT_DIR}")
                        if DEBUG_AVAILABLE:
                            enable_debug(verbose=True)
                            print(f"调试跟踪器：已启用 (verbose=True)")
                    else:
                        if DEBUG_AVAILABLE:
                            disable_debug()
                            print(f"调试跟踪器：已禁用")
            else:
                # 只输入 /debug，切换模式
                debug_mode = not debug_mode
                print(f"调试模式：{'已开启' if debug_mode else '已关闭'}")
                if debug_mode:
                    print(f"输出目录：{OUTPUT_DIR}")
                    if DEBUG_AVAILABLE:
                        enable_debug(verbose=True)
                        print(f"调试跟踪器：已启用 (verbose=True)")
                else:
                    if DEBUG_AVAILABLE:
                        disable_debug()
                        print(f"调试跟踪器：已禁用")
        
        elif user_input.startswith("/isolate"):
            parts = user_input.split()
            if len(parts) > 1:
                isolate_mode = parts[1].lower() in ["on", "true", "1"]
            else:
                isolate_mode = not isolate_mode
            print(f"隔离模式：{'已开启' if isolate_mode else '已关闭'}")
        
        elif user_input.startswith("/enhanced"):
            # 使用增强型 Agent 执行任务
            task = user_input[len("/enhanced"):].strip()
            if not task:
                print("用法：/enhanced [策略] <任务描述>")
                print("策略：direct (直接), plan_reflect (规划反思), tree_of_thought (思维树)")
                print("示例：")
                print("  /enhanced 分析这段代码")
                print("  /enhanced tree_of_thought 设计一个系统架构")
                continue
            
            # 检查是否指定了策略
            strategies = ["direct", "plan_reflect", "tree_of_thought"]
            parts = task.split(None, 1)
            if parts[0] in strategies:
                enhanced_agent.strategy = parts[0]
                task = parts[1] if len(parts) > 1 else task
                print(f"\n[增强型 Agent] 使用策略：{enhanced_agent.strategy}")
            
            print(f"\n[增强型 Agent] 执行任务：{task}")
            import asyncio
            result = asyncio.run(enhanced_agent.run(task, verbose=True))
            print(f"\n结果：{result}")
        
        elif user_input == "/memory":
            # 查看记忆状态
            if enhanced_agent:
                mem = enhanced_agent.memory_enhanced
                print(f"\n{'='*60}")
                print(f"记忆状态")
                print(f"{'='*60}")
                print(f"工作记忆：{len(mem.working_memory)} 条")
                print(f"短期记忆：{len(mem.short_term)} 条")
                print(f"经验记录：{len(mem.experiences)} 条")
                print(f"反思总结：{len(mem.reflections)} 条")
                
                if mem.short_term:
                    print(f"\n最近 3 条短期记忆：")
                    for i, exp in enumerate(list(mem.short_term)[-3:], 1):
                        success_str = "✓" if exp.success else "✗"
                        print(f"  {i}. [{success_str}] {exp.content[:50]}...")
                
                if mem.reflections:
                    print(f"\n最新反思：")
                    print(mem.reflections[-1][:200] + "...")
                
                print(f"{'='*60}")
            else:
                print("请先使用 /enhanced 初始化增强型 Agent")
        
        elif user_input == "/memory clear":
            # 清空记忆
            if enhanced_agent:
                enhanced_agent.memory_enhanced.working_memory.clear()
                enhanced_agent.memory_enhanced.short_term.clear()
                enhanced_agent.memory_enhanced.experiences.clear()
                enhanced_agent.memory_enhanced.reflections.clear()
                print("记忆已清空")
            else:
                print("请先使用 /enhanced 初始化增强型 Agent")
        
        elif user_input == "/skills":
            # 查看技能库
            if skill_library:
                print(f"\n{'='*60}")
                print(f"技能库 ({len(skill_library.skills)} 个技能)")
                print(f"{'='*60}")
                for name, skill in skill_library.skills.items():
                    print(f"\n{name}")
                    print(f"  描述：{skill.description}")
                    print(f"  触发：{skill.trigger_pattern}")
                    print(f"  成功率：{skill.success_rate:.1%}")
                    print(f"  使用次数：{skill.usage_count}")
                    print(f"  工具：{', '.join(skill.tools)}")
                print(f"{'='*60}")
            else:
                print("请先使用 /enhanced 初始化增强型 Agent")
        
        elif user_input.startswith("/reasoning"):
            # 手动选择推理模式
            mode = user_input[len("/reasoning"):].strip().lower()
            if not mode:
                print("用法：/reasoning <模式>")
                print("模式：tot (思维树), reflection (反思循环)")
                continue
            
            if mode in ["tot", "tree_of_thought"]:
                print("\n[推理模式] 使用思维树推理 (Tree of Thought)")
                if enhanced_agent:
                    enhanced_agent.strategy = "tree_of_thought"
                print("已设置策略为 tree_of_thought")
            elif mode in ["reflection", "reflection_loop"]:
                print("\n[推理模式] 使用反思循环 (Reflection Loop)")
                if enhanced_agent:
                    # 创建反思循环实例
                    reflection = ReflectionLoop(enhanced_agent)
                    enhanced_agent._reflection_loop = reflection
                    print("已创建 ReflectionLoop 实例，可通过 /enhanced 使用")
            else:
                print(f"未知模式：{mode}")
                print("可用模式：tot, tree_of_thought, reflection, reflection_loop")
        
        elif user_input.startswith("/review"):
            # 使用 Agent 审查代码
            file_path = user_input[len("/review"):].strip()
            if not file_path:
                print("用法：/review <文件路径>")
                print("示例：")
                print("  /review core/agent.py")
                print("  /review --all  (审查所有 Python 文件)")
                continue
            
            if file_path == "--all":
                # 审查所有 Python 文件
                from glob import glob
                py_files = glob("**/*.py", recursive=True)
                py_files = [f for f in py_files if not any(ex in f for ex in ['.venv', 'venv', '__pycache__', '.git'])]
                
                if not py_files:
                    print("❌ 没有找到 Python 文件")
                else:
                    print(f"\n📋 找到 {len(py_files)} 个 Python 文件")
                    print(f"将使用 EnhancedAgent 逐个审查...")
                    
                    for i, f in enumerate(py_files[:5], 1):  # 限制为前 5 个
                        print(f"\n[{i}/{len(py_files)}] 审查：{f}")
                        import asyncio
                        result = asyncio.run(enhanced_agent.run(f"审查这个 Python 文件的代码质量和安全性：{f}", verbose=True))
                        print(result[:500] + "..." if len(result) > 500 else result)
                    
                    if len(py_files) > 5:
                        print(f"\n... 还有 {len(py_files) - 5} 个文件未显示")
            else:
                # 审查单个文件
                if not os.path.exists(file_path):
                    print(f"❌ 文件不存在：{file_path}")
                else:
                    print(f"\n🤖 使用 EnhancedAgent 审查：{file_path}")
                    import asyncio
                    result = asyncio.run(enhanced_agent.run(f"审查这个 Python 文件的代码质量和安全性：{file_path}", verbose=True))
                    print(f"\n审查结果:\n{result}")
        
        # ========== 后台任务管理命令 ==========
        
        elif user_input.startswith("/bg "):
            # 后台执行任务
            task = user_input[4:].strip()
            if not task:
                print("用法：/bg <任务描述>")
                print("示例：/bg 分析这个项目")
                continue
            
            # 确定输出目录 - 只传递基础目录，让_save_output 创建具体任务子目录
            output_dir = None
            if debug_mode:
                output_dir = OUTPUT_DIR
            
            try:
                import asyncio
                
                # 异步提交任务
                async def submit_bg_task():
                    # 确保任务队列已启动
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
                        # 在已有循环中（如 Jupyter）
                        handle = asyncio.run_coroutine_threadsafe(
                            submit_bg_task(),
                            loop
                        ).result()
                    else:
                        handle = loop.run_until_complete(submit_bg_task())
                except RuntimeError:
                    # 没有循环，创建新的
                    handle = asyncio.run(submit_bg_task())
                
                # 显示任务信息
                if RICH_AVAILABLE:
                    from core.rich_output import print_success, print_info
                    print_success(f"✓ 任务已提交到后台执行：{handle.id}")
                    print_info(f"使用 /tasks 查看状态，/result {handle.id} 查看结果")
                else:
                    print(f"\n✓ 任务已提交到后台执行：{handle.id}")
                    print(f"  使用 /tasks 查看状态，/result {handle.id} 查看结果")
            
            except Exception as e:
                if RICH_AVAILABLE:
                    from core.rich_output import print_error
                    print_error(f"提交失败：{e}")
                else:
                    print(f"\n[错误] 提交失败：{e}")
                import traceback
                traceback.print_exc()
        
        elif user_input == "/tasks":
            # 列出所有后台任务
            try:
                import asyncio
                
                async def list_bg_tasks():
                    # 确保队列已启动
                    await cli_agent.task_queue.start()
                    tasks = await cli_agent.task_queue.list_tasks()
                    return tasks
                
                try:
                    # Python 3.12+ 使用 asyncio.new_event_loop()
                    try:
                        loop = asyncio.get_running_loop()
                        # 在已有运行循环中
                        tasks = asyncio.run_coroutine_threadsafe(list_bg_tasks(), loop).result()
                    except RuntimeError:
                        # 没有运行中的循环
                        tasks = asyncio.run(list_bg_tasks())
                except Exception as e:
                    # 降级处理
                    tasks = asyncio.run(list_bg_tasks())
                
                if not tasks:
                    print("暂无后台任务")
                else:
                    print(f"\n{'='*60}")
                    print(f"后台任务列表 ({len(tasks)} 个)")
                    print(f"{'='*60}")
                    
                    if RICH_AVAILABLE:
                        # 使用富文本表格
                        from core.rich_output import TaskDisplayData
                        from core.task_handle import TaskStatusEnum
                        
                        task_data = []
                        for t in tasks[:10]:  # 限制显示 10 个
                            status_icon = {
                                TaskStatusEnum.PENDING: "⏳",
                                TaskStatusEnum.RUNNING: "🔄",
                                TaskStatusEnum.COMPLETED: "✅",
                                TaskStatusEnum.FAILED: "❌",
                                TaskStatusEnum.CANCELLED: "⚠️"
                            }.get(t.status, "?")
                            
                            task_data.append(TaskDisplayData(
                                id=t.id,
                                description=t.input[:50],
                                status=status_icon,
                                result=t.progress or "",
                                duration=t.get_elapsed_time() if hasattr(t, 'get_elapsed_time') else 0
                            ))
                        
                        from core.rich_output import get_rich_output
                        get_rich_output().show_task_table(task_data, "任务状态")
                    else:
                        # 普通文本显示
                        for t in tasks[:10]:
                            elapsed = t.get_elapsed_time() if hasattr(t, 'get_elapsed_time') else 0
                            print(f"  [{t.status.value:10}] {t.id:30} | {t.input[:40]} | {elapsed:.1f}s")
                        
                        if len(tasks) > 10:
                            print(f"\n... 还有 {len(tasks) - 10} 个任务未显示")
                    
                    print(f"{'='*60}")
                
                # 显示统计
                stats = cli_agent.task_queue.get_stats()
                print(f"\n统计：总计{stats['total']} | 等待{stats['pending']} | 运行{stats['running']} | " +
                      f"完成{stats['completed']} | 失败{stats['failed']} | 取消{stats['cancelled']}")
            
            except Exception as e:
                if RICH_AVAILABLE:
                    from core.rich_output import print_error
                    print_error(f"获取任务列表失败：{e}")
                else:
                    print(f"\n[错误] 获取任务列表失败：{e}")
                import traceback
                traceback.print_exc()
        
        elif user_input.startswith("/result "):
            # 查看任务结果
            task_id = user_input[8:].strip()
            if not task_id:
                print("用法：/result <task_id>")
                print("示例：/result task_1234567890_1234")
                continue
            
            try:
                import asyncio
                
                async def get_result():
                    await cli_agent.task_queue.start()
                    return await cli_agent.task_queue.get_result(task_id, timeout=60)
                
                print(f"\n等待任务 {task_id} 完成...（最多 60 秒）")
                
                try:
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(get_result()) if not loop.is_running() else \
                             asyncio.run_coroutine_threadsafe(get_result(), loop).result()
                    
                    if RICH_AVAILABLE:
                        from core.rich_output import print_success, print_header
                        print_header("任务结果", task_id)
                        print_success(str(result)[:1000])
                    else:
                        print(f"\n结果：{result}")
                
                except asyncio.TimeoutError:
                    if RICH_AVAILABLE:
                        from core.rich_output import print_warning
                        print_warning("任务超时，任务可能仍在执行中")
                    else:
                        print("\n[警告] 任务超时，任务可能仍在执行中")
                except Exception as e:
                    if RICH_AVAILABLE:
                        from core.rich_output import print_error
                        print_error(f"任务失败：{e}")
                    else:
                        print(f"\n[错误] 任务失败：{e}")
            
            except Exception as e:
                if RICH_AVAILABLE:
                    from core.rich_output import print_error
                    print_error(f"获取结果失败：{e}")
                else:
                    print(f"\n[错误] 获取结果失败：{e}")
                import traceback
                traceback.print_exc()
        
        elif user_input.startswith("/cancel "):
            # 取消任务
            task_id = user_input[8:].strip()
            if not task_id:
                print("用法：/cancel <task_id>")
                continue
            
            try:
                import asyncio
                
                async def cancel_task():
                    await cli_agent.task_queue.start()
                    return await cli_agent.task_queue.cancel(task_id)
                
                try:
                    loop = asyncio.get_event_loop()
                    success = loop.run_until_complete(cancel_task()) if not loop.is_running() else \
                              asyncio.run_coroutine_threadsafe(cancel_task(), loop).result()
                
                    if RICH_AVAILABLE:
                        from core.rich_output import print_success, print_error
                        if success:
                            print_success(f"✓ 已取消任务：{task_id}")
                        else:
                            print_error(f"✗ 取消失败：任务不存在或已完成")
                    else:
                        if success:
                            print(f"\n✓ 已取消任务：{task_id}")
                        else:
                            print(f"\n✗ 取消失败：任务不存在或已完成")
                
                except Exception as e:
                    if RICH_AVAILABLE:
                        from core.rich_output import print_error
                        print_error(f"取消失败：{e}")
                    else:
                        print(f"\n[错误] 取消失败：{e}")
            
            except Exception as e:
                if RICH_AVAILABLE:
                    from core.rich_output import print_error
                    print_error(f"取消失败：{e}")
                else:
                    print(f"\n[错误] 取消失败：{e}")
                import traceback
                traceback.print_exc()
        
        elif user_input == "/task_stats":
            # 查看任务统计
            stats = cli_agent.task_queue.get_stats()
            
            if RICH_AVAILABLE:
                from core.rich_output import print_header, print_info
                print_header("任务队列统计", f"最大并发：{stats['max_concurrent']}")
                
                print_info(f"""
总任务数：{stats['total']}
  - 等待中：{stats['pending']}
  - 运行中：{stats['running']}
  - 已完成：{stats['completed']}
  - 已失败：{stats['failed']}
  - 已取消：{stats['cancelled']}

队列大小：{stats['queue_size']}
最大并发：{stats['max_concurrent']}
""")
            else:
                print(f"\n{'='*60}")
                print(f"任务队列统计")
                print(f"{'='*60}")
                print(f"总任务数：{stats['total']}")
                print(f"  等待中：{stats['pending']}")
                print(f"  运行中：{stats['running']}")
                print(f"  已完成：{stats['completed']}")
                print(f"  已失败：{stats['failed']}")
                print(f"  已取消：{stats['cancelled']}")
                print(f"\n队列大小：{stats['queue_size']}")
                print(f"最大并发：{stats['max_concurrent']}")
                print(f"{'='*60}")
        
        else:
            # 执行任务
            if current_agent:
                # 单 Agent 模式
                print()
                result = current_agent.run(user_input, verbose=True)
                print(f"\n{current_agent.name}: {result}")
            else:
                # 智能模式：使用 CLI Agent
                if not cli_agent:
                    cli_agent = CLIAgent()
                
                # 确定输出目录 - 只传递基础目录，让_save_output 创建具体任务子目录
                output_dir = None
                if debug_mode:
                    output_dir = OUTPUT_DIR
                
                try:
                    result_tuple = cli_agent.execute(
                        user_input,
                        verbose=True,
                        output_dir=output_dir,
                        isolate_by_instance=isolate_mode
                    )
                    
                    # 解包结果和保存路径
                    if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                        result, saved_path = result_tuple
                    else:
                        result = result_tuple
                        saved_path = None
                    
                    # 使用富文本展示结果
                    if RICH_AVAILABLE:
                        from core.rich_output import print_header, print_info
                        print_header("任务执行结果", user_input[:60])
                        if hasattr(result, 'tasks_completed'):
                            # Swarm 结果
                            get_rich_output().show_swarm_result(result, user_input)
                        else:
                            # 普通结果
                            print_info(f"结果：{str(result)[:500]}")
                    else:
                        print(f"\n{'='*60}")
                        print(f"结果：{result}")
                        print(f"{'='*60}")
                    
                    # 显示保存路径
                    if saved_path:
                        if RICH_AVAILABLE:
                            print_info(f"输出已保存到：{saved_path}")
                        else:
                            print(f"\n[Debug] 输出已保存到：{saved_path}")
                    
                    # 保存会话
                    from core.session import save_session
                    save_session("default", cli_agent.agent)
                
                except Exception as e:
                    if RICH_AVAILABLE:
                        from core.rich_output import print_error
                        print_error(f"{e}")
                    else:
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
    
    # 创建 CLI Agent（从配置加载）
    cli = CLIAgent()
    
    # 同步到全局变量（供交互模式使用）
    global cli_agent
    cli_agent = cli
    
    # 默认启用 debug 模式
    from core import enable_debug
    enable_debug(verbose=True)
    
    # 确定输出目录
    output_dir = None
    if args.debug or args.output:
        output_dir = args.output or OUTPUT_DIR
    
    if args.input or args.task:
        # 单次任务模式（智能模式）
        task = args.task or args.input
        
        # 使用富文本展示任务开始
        if RICH_AVAILABLE:
            from core.rich_output import print_header, print_info
            print_header("CLI Agent 执行任务", task[:60])
            print_info(f"调试模式：已启用 (默认)")
            if output_dir:
                print_info(f"输出目录：{output_dir}")
                if args.isolate:
                    print_info(f"隔离模式：已开启")
        else:
            print(f"[CLI Agent] 执行任务：{task}")
            print(f"[CLI Agent] 调试模式：已启用 (默认)")
            if output_dir:
                print(f"[CLI Agent] 输出目录：{output_dir}")
                if args.isolate:
                    print(f"[CLI Agent] 隔离模式：已开启")
        
        try:
            result_tuple = cli.execute(
                task,
                verbose=args.verbose,
                output_dir=output_dir,
                isolate_by_instance=args.isolate
            )
            
            # 解包结果和保存路径
            if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                result, saved_path = result_tuple
            else:
                result = result_tuple
                saved_path = None
            
            # 使用富文本展示结果
            if RICH_AVAILABLE:
                if hasattr(result, 'tasks_completed'):
                    # Swarm 结果
                    get_rich_output().show_swarm_result(result, task)
                else:
                    # 普通结果
                    print_info(f"结果：{str(result)[:500]}")
            else:
                print(f"\n{'='*60}")
                print(f"结果：{result}")
                print(f"{'='*60}")
            
            # 显示保存路径
            if saved_path:
                if RICH_AVAILABLE:
                    print_info(f"输出已保存到：{saved_path}")
                else:
                    print(f"\n[Debug] 输出已保存到：{saved_path}")
        
        except Exception as e:
            if RICH_AVAILABLE:
                from core.rich_output import print_error
                print_error(f"{e}")
            else:
                print(f"\n[错误] {e}")
            import traceback
            traceback.print_exc()
        
        return
    
    # 交互模式
    interactive_mode()


if __name__ == "__main__":
    main()
