"""
增强的记忆系统 - 支持工作记忆、短期记忆和长期记忆
"""
from typing import Optional, Any
from dataclasses import dataclass, field
from collections import deque
import asyncio
import time


@dataclass
class Experience:
    """经验记录"""
    content: str
    context: str
    result: str
    success: bool
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)


class EnhancedMemory:
    """增强的记忆系统"""
    
    def __init__(self, vector_store=None, max_short_term=50):
        self.working_memory = []  # 当前上下文窗口
        self.short_term = deque(maxlen=max_short_term)  # 短期记忆
        self.long_term = vector_store  # 长期记忆 (向量数据库)
        self.experiences = []  # 经验记录
        self.reflections = []  # 反思总结
        self._lock = asyncio.Lock()
    
    def add_to_working(self, content: str):
        """添加到工作记忆"""
        self.working_memory.append({
            "content": content,
            "timestamp": time.time()
        })
        if len(self.working_memory) > 20:
            self.working_memory.pop(0)
    
    def add_to_short_term(self, experience: Experience):
        """添加到短期记忆"""
        self.short_term.append(experience)
        self.experiences.append(experience)
    
    async def store_to_long_term(self, experience: Experience):
        """存储经验到长期记忆"""
        if self.long_term is None:
            return
        embedding = await self._generate_embedding(experience.content)
        self.long_term.add(
            vector=embedding,
            metadata={
                "content": experience.content,
                "context": experience.context,
                "result": experience.result,
                "success": experience.success,
                "tags": experience.tags
            }
        )
    
    async def retrieve_relevant(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关记忆"""
        if self.long_term is None:
            return []
        query_embedding = await self._generate_embedding(query)
        results = self.long_term.search(query_embedding, top_k)
        return [
            {
                "content": r.metadata["content"],
                "result": r.metadata["result"],
                "success": r.metadata["success"],
                "similarity": r.similarity
            }
            for r in results
        ]
    
    async def _generate_embedding(self, text: str) -> list[float]:
        """生成文本的嵌入向量"""
        from simple_agent.core.llm import get_llm
        llm = get_llm()
        response = await llm.embed(text)
        return response.embedding
    
    def reflect(self) -> str:
        """生成反思总结"""
        if len(self.experiences) < 5:
            return "经验不足，无法生成反思"
        
        successes = [e for e in self.experiences if e.success]
        failures = [e for e in self.experiences if not e.success]
        
        insights = []
        if successes:
            insights.append("成功经验：")
            insights.append(f"  - 共 {len(successes)} 次成功任务")
            common_tags = self._extract_common_tags(successes)
            if common_tags:
                insights.append(f"  - 擅长领域：{', '.join(common_tags)}")
        
        if failures:
            insights.append("改进建议：")
            insights.append(f"  - 共 {len(failures)} 次失败任务")
            failure_reasons = self._analyze_failures(failures)
            insights.extend(failure_reasons)
        
        return "\n".join(insights)
    
    def _extract_common_tags(self, experiences: list[Experience]) -> list[str]:
        """提取共同标签"""
        from collections import Counter
        all_tags = []
        for e in experiences:
            all_tags.extend(e.tags)
        counter = Counter(all_tags)
        return [tag for tag, count in counter.most_common(5) if count >= 2]
    
    def _analyze_failures(self, failures: list[Experience]) -> list[str]:
        """分析失败原因"""
        reasons = []
        for f in failures[:3]:
            reasons.append(f"  - {f.result[:100]}...")
        return reasons
    
    def get_context_for_task(self, task: str) -> str:
        """为任务准备上下文"""
        context_parts = []
        if self.working_memory:
            recent = self.working_memory[-3:]
            context_parts.append("当前上下文：")
            context_parts.extend(f"  - {m['content']}" for m in recent)
        return "\n".join(context_parts)
