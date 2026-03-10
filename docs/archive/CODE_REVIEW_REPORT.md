# 代码审查报告 - 硬编码问题修复

## 审查日期
2026-03-10

## 审查范围
- Agent 提示词配置
- 核心代码中的硬编码问题
- 关键词列表和模式匹配

---

## 一、Agent 提示词配置审查

### 审查结果：良好实践

所有内置 Agent（25 个）都使用 YAML 配置文件，位于 `builtin_agents/configs/` 目录：

| Agent | 配置文件 | 状态 |
|-------|---------|------|
| CLI Agent | `cli.yaml` | 配置化 |
| Planner | `planner.yaml` | 配置化 |
| Developer | `developer.yaml` | 配置化 |
| Tester | `tester.yaml` | 配置化 |
| ... | ... | 配置化 |

**优点**：
- 提示词与代码分离
- 支持热更新和运行时修改
- 便于非技术人员调整 Agent 行为

---

## 二、发现的硬编码问题及修复

### 问题 1: CLI Agent 中的硬编码关键词列表

**位置**: `cli_agent.py:100-113`

**原代码**:
```python
time_keywords = ["今天", "日期", "时间", "星期", "放假", "开学", "暑假", "寒假", "安排"]
location_keywords = ["天气", "位置", "地点", "哪里", "在哪", "北京", "上海", "广州"]
```

**修复方案**:
- 创建 `ContextInjectorConfig` 类
- 从 `configs/cli_keywords.yaml` 加载关键词
- 支持运行时动态扩展

**修复文件**:
- `cli_agent.py` - 添加 `ContextInjectorConfig` 类
- `configs/cli_keywords.yaml` - 扩展关键词配置

### 问题 2: CLI Agent 中的硬编码任务复杂度判断模式

**位置**: `cli_agent.py:244-259`

**原代码**:
```python
simple_patterns = [
    "你好", "您好", "hello", "hi",
    "谢谢", "感谢", "bye", "再见",
    "你是谁", "你能做什么", "介绍下",
]
```

**修复方案**:
- 创建 `TaskComplexityConfig` 类
- 从 `configs/cli_keywords.yaml` 加载 `task_complexity` 配置
- 支持 LLM 复杂度判断提示词配置化

**修复文件**:
- `cli_agent.py` - 添加 `TaskComplexityConfig` 类
- `configs/cli_keywords.yaml` - 添加 `task_complexity` 和 `llm_prompts` 配置

### 问题 3: Workflow Generator 中的硬编码提示词

**位置**: `core/workflow_generator.py:46-67`

**原代码**:
```python
prompt = f"""分析以下任务描述，生成一个多步骤工作流。
任务描述：{description}
请输出 JSON 格式的工作流定义：..."""
```

**修复方案**:
- 创建 `WorkflowGeneratorConfig` 类
- 从 `configs/workflow_generator.yaml` 加载提示词
- 默认工作流定义配置化
- 步骤命名前缀配置化

**修复文件**:
- `core/workflow_generator.py` - 添加 `WorkflowGeneratorConfig` 类
- `configs/workflow_generator.yaml` - 新建配置文件

### 问题 4: EnhancedAgent 中的硬编码复杂度关键词

**位置**: `core/agent_enhanced.py:92-93`

**原代码**:
```python
keywords = ["设计", "架构", "系统", "复杂", "多个", "完整", "从 0"]
```

**修复方案**:
- 使用 `CommonKeywordsConfig.get_complexity_keywords()`
- 从 `configs/common_keywords.yaml` 加载

**修复文件**:
- `core/agent_enhanced.py` - 修改为使用配置类

### 问题 5: DynamicScheduler 中的硬编码技能关键词

**位置**: `core/dynamic_scheduler.py:239-247`

**原代码**:
```python
skill_keywords = {
    'coding': ['code', 'develop', 'program', 'write', 'implement'],
    'testing': ['test', 'qa', 'verify', 'validate'],
    ...
}
```

**修复方案**:
- 使用 `CommonKeywordsConfig.get_skill_keywords()`
- 从 `configs/common_keywords.yaml` 加载

**修复文件**:
- `core/dynamic_scheduler.py` - 修改为使用配置类

### 问题 6: CollaborationPatterns 中的硬编码审查通过关键词

**位置**: `swarm/collaboration_patterns.py:139` 和 `485`

**原代码**:
```python
approval_keywords = ["lgtm", "通过", "approved", "looks good"]
```

**修复方案**:
- 使用 `CommonKeywordsConfig.get_approval_keywords()`
- 从 `configs/common_keywords.yaml` 加载

**修复文件**:
- `swarm/collaboration_patterns.py` - 修改为使用配置类（两处）

---

## 三、新增配置文件

### 1. `configs/cli_keywords.yaml`
CLI Agent 关键词和提示词配置：
- 日期/天气/实时信息关键词
- 任务复杂度判断模式
- LLM 复杂度判断提示词
- 日志消息模板
- 星期配置

### 2. `configs/workflow_generator.yaml`
Workflow Generator 配置：
- 工作流生成提示词模板
- 默认工作流定义
- 步骤命名规则
- 工具标签映射

### 3. `configs/common_keywords.yaml`
通用关键词配置：
- 复杂度判断关键词
- 审查通过关键词
- 技能关键词映射（7 类技能）

### 4. `configs/common_keywords.py`
通用关键词配置读取类：
- 支持 YAML 配置加载
- 提供默认值回退
- 暴露统一访问接口

---

## 四、配置模式总结

### 配置类设计模式

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
    def get_xxx(cls) -> List:
        """获取配置值"""
        if not cls._loaded:
            cls._load_config()
        return cls._config.get('key', cls._default_xxx)
```

### 配置文件命名规范

- `configs/cli_keywords.yaml` - CLI 关键词
- `configs/workflow_generator.yaml` - 工作流生成器
- `configs/common_keywords.yaml` - 通用关键词
- `builtin_agents/configs/{agent}.yaml` - Agent 提示词

---

## 五、剩余待审查项

### 中等优先级

| 文件 | 位置 | 问题 | 优先级 |
|------|------|------|--------|
| `core/resource.py` | 220-244 | 工具标签映射硬编码 | 中 |
| `core/tool_parser.py` | 全部 | 解析规则硬编码 | 低 |
| `cli_coordinator.py` | 128-154 | 命令分类硬编码 | 低 |

### 低优先级（可保持现状）

- `core/debug.py` - 调试跟踪逻辑
- `core/llm.py` - LLM 接口定义
- `core/memory.py` - 记忆管理

---

## 六、测试验证

### 配置加载测试
```bash
# 所有配置类加载成功
configs.common_keywords.CommonKeywordsConfig
configs.cli_prompts.PromptTemplates
core.workflow_generator.WorkflowGeneratorConfig
cli_agent.ContextInjectorConfig
cli_agent.TaskComplexityConfig
```

### CLI Agent 任务判断测试
- "北京暑假安排" -> 简单任务 (正确)
- "创建一个完整的项目开发工作流" -> 复杂任务 (正确)

---

## 七、建议与最佳实践

### 1. 配置优先原则
- 所有可能变化的关键词/模式/提示词都应配置化
- 默认值放在配置类中，便于回退
- YAML 文件用于用户自定义配置

### 2. 配置类设计规范
- 使用类方法而非实例方法
- 懒加载，避免重复读取文件
- 提供 `_default_xxx` 默认值
- 配置加载失败时静默回退到默认值

### 3. 配置文件组织
- 按功能模块组织配置文件
- 统一的目录结构 `configs/`
- 配置文件使用 UTF-8 编码
- 配置文件提供注释说明

### 4. 向后兼容
- 配置类始终提供默认值
- 新增配置项时保持向后兼容
- 配置文件缺失时不影响系统运行

---

## 八、修复统计

| 类别 | 数量 |
|------|------|
| 新增配置类 | 4 个 |
| 新增配置文件 | 3 个 |
| 修复硬编码问题 | 6 处 |
| 修改的源文件 | 6 个 |

---

## 九、结论

本次代码审查发现并修复了 6 处主要的硬编码问题，将关键词、模式、提示词等全部改为配置驱动。系统现在具备以下优势：

1. **可维护性**: 修改关键词无需改代码
2. **可扩展性**: 新增模式只需更新配置文件
3. **可测试性**: 配置文件便于单元测试
4. **可定制性**: 用户可根据需求调整配置

所有修复均保持向后兼容，配置缺失时自动回退到默认值，不影响系统稳定性。
