"""
Agent 管理命令

命令列表:
- /new <描述> - 创建新 Agent
- /update <描述> - 更新当前 Agent 提示词
- /switch <名称> - 切换到已创建的 Agent
- /list - 列出所有 Agent
- /info - 显示当前 Agent 详情
- /save - 保存当前 Agent
- /load <名称> - 加载 Agent
"""

import os
from typing import List, Dict, Any
from simple_agent.cli_commands import CommandHandler, CommandResult


class AgentNewCommand(CommandHandler):
    """创建新 Agent"""
    
    @property
    def name(self) -> str:
        return "new"
    
    @property
    def description(self) -> str:
        return "创建新 Agent"
    
    @property
    def usage(self) -> str:
        return "/new <描述>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供 Agent 描述", "用法：/new <描述>")
        
        try:
            from simple_agent.core import create_agent
            
            desc = " ".join(args)
            agent = create_agent(desc)
            context['current_agent'] = agent
            
            return CommandResult.ok(f"已创建 Agent:\n{agent}")
        
        except Exception as e:
            return CommandResult.error("创建 Agent 失败", str(e))


class AgentUpdateCommand(CommandHandler):
    """更新当前 Agent 提示词"""
    
    @property
    def name(self) -> str:
        return "update"
    
    @property
    def description(self) -> str:
        return "更新当前 Agent 的提示词"
    
    @property
    def usage(self) -> str:
        return "/update <描述>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供新的描述", "用法：/update <描述>")
        
        agent = context.get('current_agent')
        if not agent:
            return CommandResult.error("请先加载或创建 Agent")
        
        try:
            from simple_agent.core import update_prompt
            
            desc = " ".join(args)
            agent = update_prompt(agent, desc)
            context['current_agent'] = agent
            
            return CommandResult.ok(f"已更新 Agent:\n{agent}")
        
        except Exception as e:
            return CommandResult.error("更新 Agent 失败", str(e))


class AgentSwitchCommand(CommandHandler):
    """切换到已创建的 Agent"""
    
    @property
    def name(self) -> str:
        return "switch"
    
    @property
    def description(self) -> str:
        return "切换到已创建的 Agent"
    
    @property
    def usage(self) -> str:
        return "/switch <名称>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供 Agent 名称", "用法：/switch <名称>")
        
        try:
            from simple_agent.core import get_agent
            
            name = " ".join(args)
            agent = get_agent(name)
            
            if agent:
                context['current_agent'] = agent
                return CommandResult.ok(f"已切换：{agent}")
            else:
                return CommandResult.error(f"未找到 Agent: {name}")
        
        except Exception as e:
            return CommandResult.error("切换 Agent 失败", str(e))


class AgentListCommand(CommandHandler):
    """列出所有可用的 Agent"""
    
    @property
    def name(self) -> str:
        return "list"
    
    @property
    def description(self) -> str:
        return "列出所有可用的 Agent"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        try:
            from simple_agent.core import list_agents
            
            lines = []
            
            # 已创建的 agents
            agents = list_agents()
            if agents:
                lines.append(f"\n{'='*60}")
                lines.append("已创建的 Agent")
                lines.append(f"{'='*60}")
                for name, a in agents.items():
                    lines.append(f"  - {name} v{a.version}")
            else:
                lines.append("\n暂无已创建的 Agent")
            
            # 已保存的 Agent 文件
            agents_dir = context.get('agents_dir', './agents')
            if os.path.exists(agents_dir):
                files = [f for f in os.listdir(agents_dir) if f.endswith('.json')]
                if files:
                    lines.append(f"\n{'='*60}")
                    lines.append(f"已保存的 Agent ({len(files)} 个)")
                    lines.append(f"{'='*60}")
                    for f in files:
                        lines.append(f"  - {f}")
            
            # Builtin agents
            try:
                from builtin_agents import list_available_agents, get_agent_info
                builtin = list_available_agents()
                if builtin:
                    lines.append(f"\n{'='*60}")
                    lines.append(f"Builtin Agents ({len(builtin)} 个)")
                    lines.append(f"{'='*60}")
                    for agent_type in builtin:
                        info = get_agent_info(agent_type)
                        lines.append(f"  - {agent_type}: {info['name']} (v{info['version']})")
            except ImportError:
                pass
            
            return CommandResult.ok("\n".join(lines))
        
        except Exception as e:
            return CommandResult.error("列出 Agent 失败", str(e))


class AgentInfoCommand(CommandHandler):
    """显示当前 Agent 详情"""
    
    @property
    def name(self) -> str:
        return "info"
    
    @property
    def description(self) -> str:
        return "显示当前 Agent 的详细信息"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        agent = context.get('current_agent')
        cli_agent = context.get('cli_agent')
        
        if not agent and not cli_agent:
            return CommandResult.error("暂无 Agent")
        
        target_agent = agent or (cli_agent.agent if cli_agent else None)
        
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"名称：{target_agent.name}")
        lines.append(f"版本：{target_agent.version}")
        lines.append(f"描述：{target_agent.description}")
        lines.append(f"创建时间：{target_agent.created_at}")
        
        if hasattr(target_agent, 'instance_id') and target_agent.instance_id:
            lines.append(f"实例 ID: {target_agent.instance_id}")
        
        lines.append(f"\n--- LLM ---")
        lines.append(f"  模型：{target_agent.llm.model}")
        lines.append(f"  Base URL: {target_agent.llm.base_url or '默认'}")
        
        lines.append(f"\n--- 提示词 ---")
        lines.append(target_agent.system_prompt or "无")
        
        tools_list = target_agent.tool_registry.get_all_tools()
        lines.append(f"\n--- 工具 ({len(tools_list)} 个) ---")
        for t in tools_list:
            params = list(t.parameters.get("properties", {}).keys())
            lines.append(f"  {t.name}: {t.description}")
            if params:
                lines.append(f"    参数：{params}")
        
        messages = target_agent.memory.get_messages()
        lines.append(f"\n--- 上下文 ({len(messages)} 条消息) ---")
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 100:
                content = content[:100] + "..."
            lines.append(f"  [{i}] {role}: {content}")
        
        lines.append(f"{'='*60}")
        
        return CommandResult.ok("\n".join(lines))


class AgentSaveCommand(CommandHandler):
    """保存当前 Agent 到文件"""
    
    @property
    def name(self) -> str:
        return "save"
    
    @property
    def description(self) -> str:
        return "保存当前 Agent 到文件"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        agent = context.get('current_agent')
        
        if not agent:
            return CommandResult.error("暂无 Agent")
        
        try:
            agents_dir = context.get('agents_dir', './agents')
            os.makedirs(agents_dir, exist_ok=True)
            
            filename = f"{agent.name}.json"
            path = os.path.join(agents_dir, filename)
            agent.save(path)
            
            return CommandResult.ok(f"已保存：{path}")
        
        except Exception as e:
            return CommandResult.error("保存 Agent 失败", str(e))


class AgentLoadCommand(CommandHandler):
    """加载 Agent（从文件或 builtin）"""
    
    @property
    def name(self) -> str:
        return "load"
    
    @property
    def description(self) -> str:
        return "加载 Agent（支持 builtin agents）"
    
    @property
    def usage(self) -> str:
        return "/load <名称或文件名>"
    
    def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult.error("请提供 Agent 名称", "用法：/load <名称或文件名>")
        
        try:
            name = " ".join(args)
            agents_dir = context.get('agents_dir', './agents')
            
            # 尝试加载已保存的 Agent
            path_candidates = [
                name,
                os.path.join(agents_dir, f"{name}.json"),
                os.path.join(agents_dir, name)
            ]
            
            for path in path_candidates:
                if os.path.exists(path):
                    from simple_agent.core import Agent
                    agent = Agent.load(path)
                    context['current_agent'] = agent
                    return CommandResult.ok(f"已加载：{agent}")
            
            # 尝试加载 builtin agent
            try:
                from builtin_agents import get_agent
                agent = get_agent(name)
                context['current_agent'] = agent
                return CommandResult.ok(f"已加载 Builtin Agent: {agent}")
            except (ImportError, ValueError):
                pass
            
            return CommandResult.error(
                f"未找到 Agent: {name}",
                "提示：使用 /list 查看可用的 agents"
            )

        except Exception as e:
            return CommandResult.error("加载 Agent 失败", str(e))


__all__ = [
    'AgentNewCommand',
    'AgentUpdateCommand',
    'AgentSwitchCommand',
    'AgentListCommand',
    'AgentInfoCommand',
    'AgentSaveCommand',
    'AgentLoadCommand',
]
