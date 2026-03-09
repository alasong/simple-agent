# 工具系统重构实施总结

**实施日期**: 2026-03-09
**状态**: ✅ 已完成

---

## 实施概述

将 simple-agent 工具系统从**启动时全量加载**重构为**插件型按需加载**架构，同时保留常用工具的默认导入，实现零配置、零感知升级。

---

## 用户选择：方案 A+

### 设计方案

- **常用工具**（默认导入）：
  - `BashTool` - 执行 shell 命令
  - `ReadFileTool` - 读取文件
  - `WriteFileTool` - 写入文件

- **其他工具**（按需加载）：
  - Agent 工具：`InvokeAgentTool`, `CreateWorkflowTool`, `ListAgentsTool`
  - 网络工具：`WebSearchTool`, `HttpTool`
  - 补充工具：`SupplementTool`, `ExplainReasonTool`

### 设计理念

```
┌─────────────────────────────────────────────────────────┐
│                    用户/Agent 请求                        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              ResourceRepository.extract_tools_v2()      │
│                   智能匹配工具需求                        │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│   常用工具（已加载）    │       │   ToolRegistry        │
│   BashTool            │       │   自动发现 tools/      │
│   ReadFileTool        │       │   懒加载实例化         │
│   WriteFileTool       │       │                       │
└───────────────────────┘       └───────────────────────┘
```

---

## 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `core/tool_registry.py` | 650+ | 工具注册表核心模块 |
| `docs/TOOL_REGISTRY.md` | - | 工具注册表使用文档（本文档） |

---

## 修改文件

| 文件 | 修改内容 |
|------|----------|
| `tools/__init__.py` | 只保留 BashTool, ReadFileTool, WriteFileTool 默认导入 |
| `core/resource.py` | 集成 ToolRegistry，新增 `get_tool_instance()` 和 `extract_tools_v2()` 方法 |
| `cli_agent.py` | 移除 `import tools` 副作用导入 |
| `cli.py` | 移除 `import tools` 副作用导入 |
| `builtin_agents/__init__.py` | 移除 `import tools`，改用 `get_tool_instance()` |

---

## 核心功能

### 1. 工具注册表 (ToolRegistry)

```python
from core.tool_registry import get_registry, get_tool

# 获取全局注册表
registry = get_registry()

# 自动发现 tools/ 目录中的所有工具
count = registry.discover_tools()
print(f"发现 {count} 个工具")

# 按需加载单个工具（懒加载）
tool = registry.get_tool("BashTool")
result = tool.execute("ls -la")

# 批量获取工具
tools = registry.get_tools(["ReadFileTool", "WriteFileTool"])

# 按标签筛选工具（未来扩展）
tools = registry.get_tools_by_tags(["file", "io"])
```

### 2. ResourceRepository 集成

```python
from core.resource import repo

# 获取工具实例（优先从 ToolRegistry 按需加载）
tool = repo.get_tool_instance("BashTool")

# 根据需求抽取工具（v2 版本支持 ToolRegistry）
tools = repo.extract_tools_v2({
    "tools": ["BashTool", "ReadFileTool"],
    "tags": ["file"],
    "keywords": ["文件", "读写"]
})
```

### 3. Builtin Agent 自动集成

```python
from builtin_agents import create_builtin_agent

# 创建 developer agent
# 自动从配置文件加载所需工具
agent = create_builtin_agent("developer")

# developer.yaml 配置：
# tools:
#   - ReadFileTool
#   - WriteFileTool
#   - BashTool
```

---

## 使用指南

### 场景 1: 在 Agent 配置中使用工具

```yaml
# builtin_agents/configs/custom_agent.yaml
name: 数据分析师
version: 1.0.0
description: 专注数据分析和可视化
tools:
  - BashTool        # 按需加载
  - ReadFileTool    # 按需加载
  - WriteFileTool   # 按需加载
```

### 场景 2: 在代码中按需使用工具

```python
from core.tool_registry import get_tool

# 只在需要时加载工具
def analyze_data(file_path):
    # 加载读取工具
    read_tool = get_tool("ReadFileTool")
    content = read_tool.execute(file_path)

    # 加载 BashTool 执行分析
    bash_tool = get_tool("BashTool")
    result = bash_tool.execute(f"python analyze.py {file_path}")

    return result
```

### 场景 3: 自定义工具（第三方插件）

```python
# my_tools/git_tools.py
from core.tool import BaseTool
from core.tool_registry import register_tool

@register_tool(tags=["git", "version_control"])
class GitCommitTool(BaseTool):
    """Git 提交工具"""

    def execute(self, message: str, **kwargs):
        import subprocess
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True)
        return result.stdout.decode()

# 使用
from core.tool_registry import get_tool
git_tool = get_tool("GitCommitTool")
git_tool.execute("feat: add new feature")
```

---

## 架构优势

### 1. 零配置

新增工具无需修改任何文件，只需将 Python 文件放入 `tools/` 目录：

```
tools/
├── my_new_tool.py  # 自动被发现
└── bash_tool.py    # 已有工具
```

### 2. 按需加载

只加载实际使用的工具，减少启动开销和内存占用：

```python
# 只使用 BashTool 时，只有 BashTool 被实例化
from core.tool_registry import get_tool
tool = get_tool("BashTool")  # 懒加载
```

### 3. 延迟实例化

工具类在首次使用时才实例化：

```
启动时：只扫描工具类（不实例化）
      ↓
使用时：才创建工具实例
```

### 4. 热插拔

支持运行时动态注册工具：

```python
from core.tool_registry import get_registry

registry = get_registry()

# 动态注册自定义工具
registry.register_tool(MyCustomTool, tags=["custom"])

# 动态清除缓存
registry.clear_cache()
```

---

## 性能提升

### 理论优势

| 指标 | 重构前 | 重构后 | 提升 |
|------|--------|--------|------|
| 启动工具加载 | 全部 10 个 | 常用 3 个 | -70% |
| 内存占用 | 全部实例 | 按需实例 | 取决于使用 |
| 新增工具成本 | 修改 `__init__.py` | 零配置 | 100% |

### 实际测试

```bash
# 工具发现测试
python -c "from core.tool_registry import get_registry; registry = get_registry(); registry.discover_tools()"
# 发现 10 个工具，耗时 < 100ms

# 按需加载测试
python -c "from core.tool_registry import get_tool; tool = get_tool('BashTool')"
# 只加载 BashTool，耗时 < 50ms
```

---

## 测试结果

### 1. 工具发现测试 ✅

```bash
python -c "from core.tool_registry import get_registry; registry = get_registry(); registry.discover_tools(); print('已发现工具:', registry.list_tools())"
# 已发现工具：['SupplementTool', 'ExplainReasonTool', 'BashTool', 'InvokeAgentTool', 'CreateWorkflowTool', 'ListAgentsTool', 'HttpTool', 'ReadFileTool', 'WriteFileTool', 'WebSearchTool']
```

### 2. 按需加载测试 ✅

```bash
python -c "from core.tool_registry import get_registry; registry = get_registry(); tool = registry.get_tool('BashTool'); print('已加载:', list(registry._tool_instances.keys()))"
# 已加载：['BashTool']
```

### 3. Resource 集成测试 ✅

```bash
python -c "from core.resource import repo; tool = repo.get_tool_instance('BashTool'); print('获取工具实例:', tool)"
# 获取工具实例：<tools.bash_tool.BashTool object at 0x...>
```

### 4. Builtin Agent 创建测试 ✅

```bash
python -c "from builtin_agents import create_builtin_agent; agent = create_builtin_agent('developer'); print('Agent 名称:', agent.name)"
# Agent 名称：开发工程师
```

### 5. 现有测试 ✅

```bash
./tests/run_daily_tests.sh
# 14 个核心深度测试全部通过
# 24 个安全测试全部通过
# 15 个任务调度器测试全部通过
```

---

## 兼容性

### 向后兼容

- ✅ `tools/__init__.py` 仍然导出常用工具
- ✅ 旧的 `import tools` 代码仍然有效
- ✅ 现有 Agent 配置无需修改

### 迁移路径

```
阶段 1 (已完成): 新增 ToolRegistry，保留常用工具默认导入
阶段 2 (进行中): Agent 配置改为按需声明工具
阶段 3 (未来): 完全移除 `import tools` 副作用导入
阶段 4 (未来): 废弃 `tools/__init__.py` 的显式导出
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 循环依赖 | 工具模块导入失败 | 使用延迟导入，避免模块级 import |
| 工具扫描失败 | 部分工具不可用 | 捕获异常，记录日志，继续扫描其他工具 |
| 性能下降 | glob 扫描耗时 | 缓存扫描结果，仅在首次调用时扫描 |
| 破坏现有功能 | Agent 无法获取工具 | 保留 `tools/__init__.py` 作为后备 |

---

## 后续扩展

### 1. 第三方工具插件

```bash
# 未来支持
pip install simple-agent-git-tools

# 自动发现并使用
agent = Agent(tools=["GitCommitTool", "GitPushTool"])
```

### 2. 工具分组

```python
# 按场景加载工具组
tools = registry.get_tools_by_group("file_ops")  # 文件操作相关
tools = registry.get_tools_by_group("network")   # 网络相关
```

### 3. 工具标签系统

```python
# 按标签筛选工具
tools = registry.get_tools_by_tags(["file", "io"])
```

---

## API 参考

### ToolRegistry 核心方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `discover_tools(package="tools")` | 自动发现工具 | 工具数量 |
| `get_tool(name)` | 获取工具实例（懒加载） | BaseTool |
| `get_tools(names)` | 批量获取工具 | List[BaseTool] |
| `get_tools_by_tags(tags)` | 按标签获取工具 | List[BaseTool] |
| `register_tool(tool_class, tags)` | 注册工具 | Type[BaseTool] |
| `list_tools()` | 列出所有工具名称 | List[str] |
| `clear_cache()` | 清除工具实例缓存 | None |

### ResourceRepository 新增方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_tool_instance(name)` | 获取工具实例（支持按需加载） | BaseTool |
| `extract_tools_v2(requirements)` | v2 版本抽取工具（支持 ToolRegistry） | List[BaseTool] |

---

## 最佳实践

### ✅ 推荐做法

1. **新增工具**：直接将 Python 文件放入 `tools/` 目录
2. **使用工具**：通过 `get_tool()` 按需加载
3. **自定义工具**：继承 `BaseTool` 并使用 `@register_tool` 装饰器

### ❌ 不推荐做法

1. 修改 `tools/__init__.py` 添加显式导出
2. 在模块顶层直接实例化工具
3. 硬编码工具路径

---

## 总结

**重构成功完成** ✅

- ✅ 零配置：新增工具无需修改任何文件
- ✅ 按需加载：减少启动开销和内存占用
- ✅ 向后兼容：保留现有导入方式
- ✅ 易于扩展：支持第三方插件
- ✅ 测试通过：53 个测试全部通过

---

**实施完成**: 2026-03-09
**测试通过**: 53/53 (100%)
**文档完成**: 是
