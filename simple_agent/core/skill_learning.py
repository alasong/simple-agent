"""
技能学习系统 - 技能库管理和技能学习
"""
from typing import Optional
from dataclasses import dataclass, field
import json
import asyncio
import re


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    trigger_pattern: str
    prompt_template: str
    tools: list[str] = field(default_factory=list)
    success_rate: float = 0.5
    usage_count: int = 0
    examples: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in [
            'name', 'description', 'trigger_pattern', 'prompt_template',
            'tools', 'success_rate', 'usage_count', 'examples'
        ]}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Skill':
        return cls(**data)


class SkillLibrary:
    """技能库"""
    
    def __init__(self, storage_path: str = None):
        self.skills: dict[str, Skill] = {}
        self.storage_path = storage_path
        self._lock = asyncio.Lock()
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        """注册内置技能"""
        self.skills["代码分析"] = Skill(
            name="代码分析",
            description="分析代码结构、质量和问题",
            trigger_pattern=r"分析代码",
            prompt_template="""你是代码分析专家。请分析以下代码：

{code}

从以下角度分析：
1. 代码结构和可读性
2. 潜在问题和 bug
3. 性能和效率
4. 改进建议""",
            tools=["ReadFileTool", "WriteFileTool", "BashTool"],
            success_rate=0.8
        )
        self.skills["测试生成"] = Skill(
            name="测试生成",
            description="为代码生成单元测试",
            trigger_pattern=r"测试",
            prompt_template="""你是测试专家。请为以下代码生成单元测试：

{code}

要求：
1. 覆盖主要功能
2. 包含边界情况
3. 使用 pytest 框架""",
            tools=["ReadFileTool", "WriteFileTool"],
            success_rate=0.75
        )
        self.skills["文档编写"] = Skill(
            name="文档编写",
            description="编写技术文档和注释",
            trigger_pattern=r"文档",
            prompt_template="""你是技术文档专家。请为以下内容编写文档：

{content}

要求：
1. 清晰的概述
2. 详细的使用说明
3. 示例代码""",
            tools=["ReadFileTool", "WriteFileTool"],
            success_rate=0.85
        )
    
    async def learn_from_success(self, trajectory: list, agent) -> Optional[Skill]:
        """从成功经验中学习新技能"""
        prompt = f"""分析以下成功的执行轨迹：

{self._format_trajectory(trajectory)}

请提取一个可复用的技能：
1. 这个技能叫什么名字？
2. 什么情况下应该使用这个技能？（触发条件）
3. 执行步骤是什么？（提示模板）
4. 需要哪些工具？

返回 JSON 格式，符合 Skill 数据结构。"""
        response = await agent.llm.chat([{"role": "user", "content": prompt}])
        skill_data = agent._parse_json(response.content)
        skill = Skill.from_dict(skill_data)
        
        async with self._lock:
            self.skills[skill.name] = skill
            await self._persist_skill(skill)
        return skill
    
    def select_skill(self, context: str) -> Optional[Skill]:
        """根据上下文选择最合适的技能"""
        candidates = []
        for skill in self.skills.values():
            if re.search(skill.trigger_pattern, context, re.IGNORECASE):
                score = skill.success_rate * (1 + skill.usage_count * 0.01)
                candidates.append((skill, score))
        
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        return None
    
    async def improve_skill(self, skill_name: str, feedback: float):
        """根据反馈改进技能"""
        if skill_name not in self.skills:
            return
        
        skill = self.skills[skill_name]
        skill.usage_count += 1
        alpha = 0.1
        skill.success_rate = (1 - alpha) * skill.success_rate + alpha * feedback
        await self._persist_skill(skill)
    
    async def _persist_skill(self, skill: Skill):
        """持久化技能"""
        if not self.storage_path:
            return
        async with self._lock:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                data = {name: s.to_dict() for name, s in self.skills.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def load_skills(self):
        """加载技能"""
        if not self.storage_path:
            return
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, skill_data in data.items():
                    self.skills[name] = Skill.from_dict(skill_data)
        except FileNotFoundError:
            pass
    
    def _format_trajectory(self, trajectory: list) -> str:
        """格式化执行轨迹"""
        return "\n".join(f"步骤 {i+1}: {a} -> {r[:100]}..." for i, (_, a, r) in enumerate(trajectory))
