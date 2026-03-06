"""Agent - 智能体核心实现 - 简化版"""
import json, re
from datetime import datetime
from typing import Optional, Dict, Any, List
from .memory import Memory
from .tool import BaseTool, ToolResult
from .llm import LLMInterface

class AgentInfo:
    def __init__(self, name, version, description, created_at, tools):
        self.name, self.version, self.description, self.created_at, self.tools = name, version, description, created_at, tools

class ToolRegistry:
    def __init__(self): self._tools = {}
    def register(self, tool): self._tools[tool.__class__.__name__] = tool
    def get(self, name): return self._tools.get(name)
    def get_all_tools(self): return list(self._tools.values())
    def get_openai_tools(self): return [{"type":"function","function":{"name":t.name,"description":t.description,"parameters":t.parameters}} for t in self._tools.values()]

class Agent:
    def __init__(self, llm, tools=None, system_prompt=None, name="Agent", version="1.0.0", description="", max_iterations=10, created_at=None, instance_id=None):
        self.llm, self.name, self.version, self.description = llm, name, version, description
        self.max_iterations, self.created_at, self.instance_id = max_iterations, created_at or datetime.now().isoformat(), instance_id
        self.memory, self.tool_registry, self._tool_names = Memory(system_prompt), ToolRegistry(), []
        for tool in (tools or []): self.tool_registry.register(tool); self._tool_names.append(tool.__class__.__name__)
    
    @property
    def info(self): return AgentInfo(self.name, self.version, self.description, self.created_at, self._tool_names)
    @property
    def system_prompt(self):
        for msg in self.memory.get_messages():
            if msg.get("role")=="system": return msg.get("content","")
        return ""
    def __repr__(self): return f"<Agent {self.name} v{self.version}>"
    def to_dict(self): return {"name":self.name,"version":self.version,"description":self.description,"created_at":self.created_at,"system_prompt":self.system_prompt,"tools":self._tool_names,"max_iterations":self.max_iterations,"memory":{"messages":self.memory.get_messages()}}
    def save(self, path):
        import os; os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,'w',encoding='utf-8') as f: json.dump(self.to_dict(),f,ensure_ascii=False,indent=2)
    @classmethod
    def from_dict(cls, data, llm=None):
        from core.agent import Agent as AC
        a=AC(llm=llm,name=data.get("name","Agent"),version=data.get("version","1.0.0"),description=data.get("description",""),max_iterations=data.get("max_iterations",10),created_at=data.get("created_at"),system_prompt=data.get("system_prompt",""))
        if "memory" in data and "messages" in data["memory"]: a.memory.messages=data["memory"]["messages"]
        return a
    @classmethod
    def load(cls, path, llm=None):
        with open(path,'r',encoding='utf-8') as f: data=json.load(f)
        return cls.from_dict(data,llm)
    def _execute_tool(self, name, args):
        tool=self.tool_registry.get(name)
        return tool.execute(**args) if tool else ToolResult(success=False,output="",error=f"未知工具：{name}")
    def run(self, user_input, verbose=True):
        try:
            from tools.agent_tools import set_verbose; set_verbose(verbose)
        except: pass
        self.memory.add_user(user_input)
        for i in range(self.max_iterations):
            r=self.llm.chat(messages=self.memory.get_messages(),tools=self.tool_registry.get_openai_tools())
            c,tc=r["content"],r["tool_calls"]
            if not tc and c: tc=self._parse_tool_calls(c)
            if not tc: self.memory.add_assistant(c); return c
            self.memory.add_assistant(c,tool_calls=[{"id":t["id"],"type":"function","function":{"name":t["name"],"arguments":json.dumps(t["arguments"])}} for t in tc])
            for t in tc:
                res=self._execute_tool(t["name"],t["arguments"])
                self.memory.add_tool_result(tool_call_id=t["id"],name=t["name"],content=res.output if res.success else f"错误：{res.error}")
        return f"达到最大迭代次数 ({self.max_iterations})，任务可能未完成"
    def _parse_tool_calls(self, content):
        tc=[]
        # 解析 JSON 格式：{"name": "Tool", "arguments": {...}}
        for m in re.finditer(r'\{ *"name" *"([^"]+)" *"arguments" *(\{[^}]*\}) *\}',content):
            try: tc.append({"id":f"call_{len(tc)}","name":m.group(1),"arguments":json.loads(m.group(2))})
            except: pass
        # 解析 XML 格式：<invoke name="Tool"></invoke>
        if not tc:
            for n,a in re.findall(r'<invoke\s+name="([^"]+)">(.*?)</invoke>',content,re.DOTALL):
                args={}
                for pn,pv in re.findall(r'<parameter\s+name="([^"]+)">(.*?)