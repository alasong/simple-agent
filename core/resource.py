"""
资源仓库

统一管理:
- 工具仓库
- LLM 仓库
- Agent 注册表

Agent 创建时从仓库抽取所需资源
"""

from typing import Optional, Dict, List, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from .tool import BaseTool
from .llm import LLM, OpenAILLM, LLMInterface

# 避免循环依赖：使用 TYPE_CHECKING 进行类型注解
if TYPE_CHECKING:
    from .agent import Agent


@dataclass
class ToolEntry:
    """工具条目"""
    tool: type[BaseTool]
    tags: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class LLMEntry:
    """LLM 条目"""
    llm: LLMInterface
    name: str = "default"
    tags: List[str] = field(default_factory=list)


class ResourceRepository:
    """
    资源仓库 - 单例模式
    
    管理所有可用资源，Agent 创建时从中抽取
    """
    
    _instance: Optional['ResourceRepository'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # 工具仓库: name -> ToolEntry
        self._tools: Dict[str, ToolEntry] = {}
        
        # LLM 仓库: name -> LLMEntry
        self._llms: Dict[str, LLMEntry] = {}
        
        # 标签索引: tag -> [names]
        self._tool_tags: Dict[str, List[str]] = {}
        
        # Agent 注册表
        self._agents: Dict[str, 'Agent'] = {}
    
    # ==================== 工具管理 ====================
    
    def register_tool(
        self, 
        tool_class: type[BaseTool], 
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> type[BaseTool]:
        """注册工具"""
        name = tool_class.__name__
        self._tools[name] = ToolEntry(
            tool=tool_class,
            tags=tags or [],
            description=description or tool_class.__doc__ or ""
        )
        
        # 建立标签索引
        for tag in tags or []:
            if tag not in self._tool_tags:
                self._tool_tags[tag] = []
            if name not in self._tool_tags[tag]:
                self._tool_tags[tag].append(name)
        
        return tool_class
    
    def get_tool(self, name: str) -> Optional[type[BaseTool]]:
        """获取工具类"""
        entry = self._tools.get(name)
        return entry.tool if entry else None
    
    def get_tools_by_tags(self, tags: List[str]) -> List[type[BaseTool]]:
        """按标签获取工具"""
        tool_names = set()
        for tag in tags:
            tool_names.update(self._tool_tags.get(tag, []))
        return [self._tools[n].tool for n in tool_names if n in self._tools]
    
    def list_tools(self) -> Dict[str, ToolEntry]:
        """列出所有工具"""
        return self._tools.copy()
    
    # ==================== LLM 管理 ====================
    
    def register_llm(
        self, 
        llm: LLMInterface, 
        name: str = "default",
        tags: Optional[List[str]] = None
    ):
        """注册 LLM"""
        self._llms[name] = LLMEntry(
            llm=llm,
            name=name,
            tags=tags or []
        )
    
    def get_llm(self, name: str = "default") -> Optional[LLMInterface]:
        """获取 LLM"""
        entry = self._llms.get(name)
        return entry.llm if entry else None
    
    def list_llms(self) -> Dict[str, LLMEntry]:
        """列出所有 LLM"""
        return self._llms.copy()
    
    # ==================== Agent 注册表 ====================
    
    def register_agent(self, agent: 'Agent'):
        """注册已创建的 Agent"""
        self._agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional['Agent']:
        """获取已创建的 Agent"""
        return self._agents.get(name)
    
    def list_agents(self) -> Dict[str, 'Agent']:
        """列出所有 Agent"""
        return self._agents.copy()
    
    # ==================== 资源抽取 ====================
    
    def extract_tools(self, requirements: Dict[str, Any]) -> List[BaseTool]:
        """
        根据需求抽取工具
        
        Args:
            requirements: {
                "tools": ["ToolName"],      # 明确指定工具
                "tags": ["file", "check"],  # 按标签选择
                "keywords": ["文件", "检查"] # 从描述关键词推断
            }
        """
        tool_classes = set()
        
        # 1. 明确指定的工具
        for name in requirements.get("tools", []):
            tc = self.get_tool(name)
            if tc:
                tool_classes.add(tc)
        
        # 2. 按标签选择
        for tag in requirements.get("tags", []):
            for tc in self.get_tools_by_tags([tag]):
                tool_classes.add(tc)
        
        # 3. 关键词推断（智能匹配）
        keywords = requirements.get("keywords", [])
        keyword_text = " ".join(keywords).lower()
        
        # 关键词到标签的映射
        keyword_tag_map = {
            "文件": "file",
            "file": "file",
            "读写": "file",
            "写入": "file",
            "读取": "file",
            "io": "io",
            "检查": "check",
            "check": "check",
            "验证": "check",
            "审查": "review",
            "review": "review",
            "代码": "code",
            "code": "code",
            "python": "code",
        }
        
        # 从关键词推断标签
        inferred_tags = set()
        for kw, tag in keyword_tag_map.items():
            if kw in keyword_text:
                inferred_tags.add(tag)
        
        # 添加推断标签对应的工具
        for tag in inferred_tags:
            for tc in self.get_tools_by_tags([tag]):
                tool_classes.add(tc)
        
        return [tc() for tc in tool_classes]
    
    def extract_llm(self, name: str = "default") -> LLMInterface:
        """抽取 LLM"""
        llm = self.get_llm(name)
        if not llm:
            # 自动创建默认 LLM
            llm = LLM()
            self.register_llm(llm, "default")
        return llm


# 全局仓库实例
repo = ResourceRepository()


# ==================== 便捷函数 ====================

def tool(tags: Optional[List[str]] = None, description: str = ""):
    """工具注册装饰器"""
    def decorator(cls: type[BaseTool]) -> type[BaseTool]:
        return repo.register_tool(cls, tags=tags, description=description)
    return decorator


def register_llm(llm: LLMInterface, name: str = "default", tags: Optional[List[str]] = None):
    """注册 LLM"""
    repo.register_llm(llm, name, tags)
