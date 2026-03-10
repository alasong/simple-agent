# 硬编码代码修复总结

## 修复日期
2026-03-10

## 修复概述

本次修复将代码中的硬编码关键词、模式、提示词全部改为配置驱动，提高了系统的可维护性和可扩展性。

---

## 修复的问题

### 1. CLI Agent 上下文注入关键词

**修复前** (`cli_agent.py:100-113`):
```python
time_keywords = ["今天", "日期", "时间", "星期", "放假", "开学", "暑假", "寒假", "安排"]
location_keywords = ["天气", "位置", "地点", "哪里", "在哪", "北京", "上海", "广州"]
```

**修复后**:
```python
# 使用配置类
time_keywords = ContextInjectorConfig.get_time_keywords()
location_keywords = ContextInjectorConfig.get_location_keywords()
```

**配置文件**: `configs/cli_keywords.yaml`

---

### 2. CLI Agent 任务复杂度判断模式

**修复前** (`cli_agent.py:244-259`):
```python
simple_patterns = [
    "你好", "您好", "hello", "hi",
    "谢谢", "感谢", "bye", "再见",
    "你是谁", "你能做什么", "介绍下",
]
complex_patterns = [
    "工作流", "CI/CD", "部署流程", "测试流程",
]
```

**修复后**:
```python
# 使用配置类
simple_patterns = TaskComplexityConfig.get_simple_patterns()
complex_patterns = TaskComplexityConfig.get_complex_patterns()
```

**配置文件**: `configs/cli_keywords.yaml` (task_complexity 部分)

---

### 3. CLI Agent LLM 复杂度判断提示词

**修复前** (`cli_agent.py:284-294`):
```python
prompt = f"""你是一个任务复杂度分类器。请判断以下用户输入是否需要多步规划和复杂推理：

用户输入：{user_input}

判断标准：
- 简单任务：单一问题、概念解释、代码片段、翻译、计算、**信息查询**（如天气、新闻、时间、政策、安排等）
- 复杂任务：需要多步骤、多工具协作、系统设计、流程规划、分析研究、项目执行

注意：用户查询类问题（如"xxx 安排"、"xxx 时间"、"xxx 政策"）通常是简单信息查询，不是复杂任务。

请只回答一个词：simple 或 complex"""
```

**修复后**:
```python
# 从配置加载提示词模板
prompt_template = TaskComplexityConfig.get_complexity_judge_prompt()
prompt = prompt_template.format(user_input=user_input)
```

**配置文件**: `configs/cli_keywords.yaml` (llm_prompts 部分)

---

### 4. Workflow Generator 提示词

**修复前** (`core/workflow_generator.py:46-67`):
```python
prompt = f"""分析以下任务描述，生成一个多步骤工作流。

任务描述：{description}

请输出 JSON 格式的工作流定义：
{{
    "name": "工作流名称",
    ...
}}
"""
```

**修复后**:
```python
# 从配置加载提示词模板
prompt_template = WorkflowGeneratorConfig.get_workflow_generation_prompt()
prompt = prompt_template.format(description=description)
```

**配置文件**: `configs/workflow_generator.yaml`

---

### 5. EnhancedAgent 复杂度判断关键词

**修复前** (`core/agent_enhanced.py:92-93`):
```python
keywords = ["设计", "架构", "系统", "复杂", "多个", "完整", "从 0"]
score = sum(0.15 for kw in keywords if kw in task)
```

**修复后**:
```python
# 从配置加载关键词
keywords = CommonKeywordsConfig.get_complexity_keywords()
```

**配置文件**: `configs/common_keywords.yaml`

---

### 6. DynamicScheduler 技能关键词

**修复前** (`core/dynamic_scheduler.py:239-247`):
```python
skill_keywords = {
    'coding': ['code', 'develop', 'program', 'write', 'implement'],
    'testing': ['test', 'qa', 'verify', 'validate'],
    'reviewing': ['review', 'audit', 'check', 'inspect'],
    ...
}
```

**修复后**:
```python
# 从配置加载技能关键词映射
skill_keywords = CommonKeywordsConfig.get_skill_keywords()
```

**配置文件**: `configs/common_keywords.yaml`

---

### 7. CollaborationPatterns 审查通过关键词

**修复前** (`swarm/collaboration_patterns.py:139` 和 `485`):
```python
approval_keywords = ["lgtm", "通过", "approved", "looks good"]
```

**修复后**:
```python
# 从配置加载关键词
approval_keywords = CommonKeywordsConfig.get_approval_keywords()
```

**配置文件**: `configs/common_keywords.yaml`

---

## 新增文件

### 配置类

| 文件 | 用途 |
|------|------|
| `configs/common_keywords.py` | 通用关键词配置类 |
| `cli_agent.py` (增强) | 添加 `ContextInjectorConfig`, `TaskComplexityConfig` |
| `core/workflow_generator.py` (增强) | 添加 `WorkflowGeneratorConfig` |

### 配置文件

| 文件 | 用途 |
|------|------|
| `configs/cli_keywords.yaml` | CLI Agent 关键词和提示词 |
| `configs/workflow_generator.yaml` | Workflow Generator 配置 |
| `configs/common_keywords.yaml` | 通用关键词配置 |
| `docs/CODE_REVIEW_REPORT.md` | 代码审查报告 |

---

## 配置类设计模式

```python
class XxxConfig:
    """配置类 - 从 YAML 文件加载"""

    _config: Dict = None
    _loaded: bool = False
    _default_xxx = [...]  # 默认值

    @classmethod
    def _load_config(cls):
        """从 YAML 加载配置"""
        if cls._loaded:
            return
        # 加载逻辑...

    @classmethod
    def get_xxx(cls):
        """获取配置值"""
        if not cls._loaded:
            cls._load_config()
        return cls._config.get('key', cls._default_xxx)
```

**特点**:
- 懒加载，避免重复读取文件
- 提供默认值回退
- 配置加载失败时静默回退
- 支持默认值和配置值合并

---

## 测试验证

### 配置加载测试
```bash
# 所有配置类加载成功
✓ CommonKeywordsConfig
✓ PromptTemplates
✓ WorkflowGeneratorConfig
✓ ContextInjectorConfig
✓ TaskComplexityConfig
```

### 功能测试
```bash
# CLI Agent 任务判断
✓ "北京暑假安排" -> 简单任务
✓ "创建一个完整的项目开发工作流" -> 复杂任务

# 核心测试
✓ 14 个深度核心测试全部通过
✓ 3 个 CLI Tab 补全测试全部通过
```

---

## 修复效果

### 可维护性提升
- 修改关键词无需改代码
- 非技术人员可调整配置
- 配置文件集中管理

### 可扩展性提升
- 新增模式只需更新配置文件
- 支持运行时动态扩展
- 配置缺失时自动回退

### 可测试性提升
- 配置文件便于单元测试
- 可快速切换不同配置场景
- 配置验证更简单

---

## 剩余待优化项

### 中等优先级
- `core/resource.py:220-244` - 工具标签映射硬编码
- `core/tool_parser.py` - 解析规则硬编码（难以配置化）

### 低优先级（可保持现状）
- `cli_coordinator.py:128-154` - 命令分类硬编码（逻辑相关）
- `core/debug.py` - 调试跟踪逻辑
- `core/llm.py` - LLM 接口定义

---

## 使用示例

### 修改日期查询关键词

**编辑** `configs/cli_keywords.yaml`:
```yaml
date_keywords:
  - "今天"
  - "日期"
  - "几号"
  - "星期"
  - "时间"
  - "现在几点"
  - "你的新增关键词"  # 添加新关键词
```

无需修改 Python 代码。

### 修改任务复杂度判断模式

**编辑** `configs/cli_keywords.yaml`:
```yaml
task_complexity:
  simple_patterns:
    - "你好"
    - "您的新简单模式"  # 添加新简单模式

  complex_patterns:
    - "工作流"
    - "您的新复杂模式"  # 添加新复杂模式
```

无需修改 Python 代码。

### 修改 LLM 复杂度判断提示词

**编辑** `configs/cli_keywords.yaml`:
```yaml
llm_prompts:
  complexity_judge: |
    你的新提示词模板...
    {user_input}  # 保留占位符
```

无需修改 Python 代码。

---

## 结论

本次修复将 6 处主要硬编码问题改为配置驱动，新增 3 个配置文件和 4 个配置类。所有修改保持向后兼容，配置缺失时自动回退到默认值。

核心测试全部通过，系统功能正常。
