"""
User-Document Agent Generator - Generate Agent configurations from natural language

Allows users to create custom agents by describing them in natural language.

Usage:
    from simple_agent.user_doc_agent import generate_agent_from_doc

    doc = '''You are a Python code review expert. Check code quality, security, performance.'''

    config = generate_agent_from_doc(doc)
    print(config)
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class AgentProfile:
    """Extracted agent profile from user documentation."""
    name: str = ""
    role: str = ""
    expertise: List[str] = None
    tasks: List[str] = None
    domains: List[str] = None
    tools_needed: List[str] = None
    style: str = ""
    max_iterations: int = 15
    temperature: float = 0.7


# Knowledge base: common场景 mappings
SCENE_KNOWLEDGE = {
    "code_review": {
        "role": "代码审查专家",
        "tools": ["ReadFileTool", "WriteFileTool", "BashTool"],
        "domains": ["software_development", "code_review"]
    },
    "数据分析": {
        "role": "数据分析师",
        "tools": ["ReadFileTool", "BashTool"],
        "domains": ["data_analysis", "business_intelligence"]
    },
    "写作": {
        "role": "内容作家",
        "tools": ["ReadFileTool", "WriteFileTool", "WebSearchTool"],
        "domains": ["content_writing", "technical_writing"]
    },
    "研究": {
        "role": "研究员",
        "tools": ["WebSearchTool", "ReadFileTool", "WriteFileTool"],
        "domains": ["academic_research", "literature_review"]
    },
    "Web开发": {
        "role": "Web开发专家",
        "tools": ["ReadFileTool", "WriteFileTool", "BashTool"],
        "domains": ["web_development", "frontend_development"]
    },
}


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    # Chinese stop words
    stop_words = {
        '的', '是', '在', '和', '与', '及', '或', '被', '对', '于', '有', '中', '而',
        '了', '着', '过', '很', '不', '都', '就', '也', '还', '又', '其它', '其他'
    }

    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    keywords = [w.strip() for w in words if w.strip() and len(w) >= 2 and w not in stop_words]
    return keywords[:20]


def detect_domain(keywords: List[str]) -> str:
    """Detect the domain from keywords."""
    for keyword in keywords:
        for scene, data in SCENE_KNOWLEDGE.items():
            if keyword in scene or keyword in data.get("role", ""):
                return scene
    return "general"


def extract_expertise(text: str) -> List[str]:
    """Extract expertise from text."""
    expertise_patterns = [
        r'(Python|Java|JavaScript|TypeScript|Go|Rust|C\+\+|PHP|Ruby|Swift|Kotlin)',
        r'(React|Vue|Angular|Next\.js|Nuxt\.js)',
        r'(Node\.js|Express|Koa|FastAPI|Django|Flask)',
        r'(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)',
        r'(Docker|Kubernetes|CI/CD|Git)',
        r'(数据分析|机器学习|AI|大语言模型|LLM)',
        r'(写作|文档|技术文档|内容创作)',
        r'(研究|文献|论文|学术)',
    ]

    expertise = []
    for pattern in expertise_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        expertise.extend(matches)

    # Remove duplicates
    seen = set()
    unique = []
    for item in expertise:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique[:10]


def extract_tools(text: str) -> List[str]:
    """Extract needed tools from text."""
    tool_keywords = {
        "文件": "ReadFileTool",
        "读取文件": "ReadFileTool",
        "写入文件": "WriteFileTool",
        "保存文件": "WriteFileTool",
        "终端": "BashTool",
        "命令行": "BashTool",
        "执行命令": "BashTool",
        "搜索": "WebSearchTool",
        "网页搜索": "WebSearchTool",
        "查询": "WebSearchTool",
        "数据库": "DatabaseTool",
        "图表": "ChartTool",
        "绘图": "ChartTool",
    }

    tools = []
    for keyword, tool in tool_keywords.items():
        if keyword in text:
            tools.append(tool)

    if not tools:
        tools = ["ReadFileTool", "WriteFileTool", "BashTool"]

    return tools


def extract_role(text: str) -> str:
    """Extract agent role from text."""
    role_patterns = [
        r'(专家|工程师|分析师|作家|研究员|开发者|程序员|编辑|审查员)',
    ]

    for pattern in role_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) + "专家"

    return "助手"


def generate_agent_from_doc(
    doc: str,
    default_name: str = "CustomAgent"
) -> Dict[str, Any]:
    """
    Generate agent configuration from natural language documentation.

    Args:
        doc: User's natural language description of the agent
        default_name: Default name if not found in doc

    Returns:
        Agent configuration dictionary
    """
    keywords = extract_keywords(doc)
    expertise = extract_expertise(doc)
    tools = extract_tools(doc)
    role = extract_role(doc)
    domain = detect_domain(keywords)

    system_prompt = f"""{role}

{doc}

你将使用以下工具来完成任务：
{', '.join(tools[:5])}

请遵循专业规范，确保输出质量。"""

    config = {
        "name": default_name,
        "version": "1.0.0",
        "description": role,
        "system_prompt": system_prompt,
        "tools": tools,
        "domains": [domain] + expertise[:3],
        "capabilities": expertise,
        "max_iterations": 15,
        "temperature": 0.7,
        "timeout": 300,
        "collaboration": False,
        "output_format": "text",
        "_source_doc": doc,
        "_extracted_keywords": keywords,
    }

    if domain in SCENE_KNOWLEDGE:
        scene_config = SCENE_KNOWLEDGE[domain]
        config["tools"] = scene_config["tools"]
        config["domains"] = scene_config["domains"]

    return config


def generate_agent_from_template_doc(
    template_name: str,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate agent configuration using a template with parameters.

    Args:
        template_name: Name of the template to use
        params: Dictionary of parameters to fill in template

    Returns:
        Agent configuration dictionary
    """
    templates = {
        "code_reviewer": {
            "name": params.get("name", "CodeReviewer"),
            "version": "1.0.0",
            "description": "代码审查专家",
            "system_prompt": f"""你是一个专业的代码审查专家，专注于 {params.get('language', 'Python')} 代码的质量检查。

你的审查维度：
1. 代码规范 - 遵循PEP8/ESLint等规范
2. 潜在bug - 识别可能的错误和边界情况
3. 安全性 - 检查SQL注入、XSS等安全问题
4. 性能优化 - 识别性能瓶颈
5. 可维护性 - 代码是否易于理解和修改

请以专业、建设性的方式提出审查意见。""",
            "tools": ["ReadFileTool", "WriteFileTool", "BashTool"],
            "domains": ["software_development", "code_review"],
            "capabilities": ["code_analysis", "bug_detection", "security_review"],
            "max_iterations": 10,
            "temperature": 0.5,
            "timeout": 300,
            "collaboration": False,
            "output_format": "markdown",
        },
        "data_analyst": {
            "name": params.get("name", "DataAnalyst"),
            "version": "1.0.0",
            "description": "数据分析专家",
            "system_prompt": f"""你是一个专业的数据分析专家，专注于从数据中提取洞察。

你的工作流程：
1. 数据探索 - 了解数据结构和质量
2. 数据清洗 - 处理缺失值和异常值
3. 统计分析 - 计算描述性统计和相关性
4. 可视化 - 生成图表展示结果
5. 洞察提炼 - 总结关键发现和建议

请确保分析结果准确、可视化清晰。""",
            "tools": ["ReadFileTool", "WriteFileTool", "BashTool"],
            "domains": ["data_analysis", "business_intelligence"],
            "capabilities": ["data_exploration", "statistical_analysis", "visualization"],
            "max_iterations": 20,
            "temperature": 0.5,
            "timeout": 600,
            "collaboration": False,
            "output_format": "markdown",
        },
        "content_writer": {
            "name": params.get("name", "ContentWriter"),
            "version": "1.0.0",
            "description": "内容作家",
            "system_prompt": f"""你是一个专业的{params.get('type', '技术')}内容作家，专注于{params.get('domain', '技术文档')}。

你的写作风格：
- 语言简洁明了
- 结构清晰有序
- 重点突出
- 专业准确

请根据用户需求创作高质量内容。""",
            "tools": ["ReadFileTool", "WriteFileTool", "WebSearchTool"],
            "domains": ["content_writing", "technical_writing"],
            "capabilities": ["content_generation", "editing", "research"],
            "max_iterations": 10,
            "temperature": 0.8,
            "timeout": 300,
            "collaboration": False,
            "output_format": "markdown",
        },
    }

    return templates.get(template_name, generate_agent_from_doc("自定义助手"))


if __name__ == "__main__":
    doc = """你是一个专业的Python代码审查专家。
你需要检查代码的质量、安全性、性能和最佳实践。
重点关注：代码规范、潜在bug、安全漏洞、性能优化。"""

    config = generate_agent_from_doc(doc, "PythonCodeReviewer")
    print("Generated config:")
    for k, v in config.items():
        if k not in ["_source_doc", "_extracted_keywords"]:
            print(f"  {k}: {v}")
