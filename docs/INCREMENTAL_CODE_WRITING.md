# 软件开发任务的逐步写入机制

## 当前实现分析

### 问题：是一次性写入还是逐步写入？

**答案：是逐步写入的**，但具体取决于任务复杂度和 Agent 的执行方式。

---

## 当前写入机制详解

### 1. 单次 Agent 执行（简单任务）

**场景**: 单个文件创建

```python
agent = Agent(
    llm=llm,
    tools=[WriteFileTool()],
    name="Developer"
)

result = agent.run("创建一个 calculator.py 文件")
```

**执行流程**（逐步）:

```
迭代 1:
  → LLM 思考：需要创建文件
  → 调用 WriteFileTool(file_path="calculator.py", content="...")
  → 写入文件 ✅
  → 添加到记忆：成功写入文件
  
迭代 2:
  → LLM 看到写入成功
  → 返回结果："已成功创建文件"
  → 任务完成
```

**结论**: 每个文件**逐步写入**，一次一个

---

### 2. Swarm 执行（复杂任务）

**场景**: 多文件项目开发

```python
orchestrator = SwarmOrchestrator(agents=[架构师，开发者，测试员])
result = await orchestrator.solve("开发用户管理系统")
```

**Swarm 的逐步写入流程**:

```
Step 1: 任务分解
  → 分解为 4 个子任务:
    Task 1: 创建 models/user.py (架构师)
    Task 2: 创建 services/user_service.py (开发者)
    Task 3: 创建 api/user_api.py (开发者)
    Task 4: 创建 tests/test_user.py (测试员)

Step 2: 并行/串行执行（取决于依赖）
  
  迭代 1:
    → Task 1 (架构师) 准备就绪
    → 架构师调用 WriteFileTool 写入 models/user.py ✅
    → 任务 1 完成
  
  迭代 2:
    → Task 2 (开发者) 等待 Task 1 完成
    → Task 1 已完成，Task 2 准备就绪
    → 开发者读取 models/user.py (ReadFileTool)
    → 开发者调用 WriteFileTool 写入 services/user_service.py ✅
    → 任务 2 完成
  
  迭代 3:
    → Task 3 (开发者) 等待 Task 2 完成
    → Task 3 准备就绪
    → 开发者调用 WriteFileTool 写入 api/user_api.py ✅
    → 任务 3 完成
  
  迭代 4:
    → Task 4 (测试员) 等待 Task 2,3 完成
    → Task 4 准备就绪
    → 测试员调用 WriteFileTool 写入 tests/test_user.py ✅
    → 任务 4 完成

所有任务完成！✅
```

**结论**: Swarm 是**真正的逐步写入**：
- ✅ 按依赖顺序写入
- ✅ 每个文件独立写入
- ✅ 后续文件可以参考已写入的文件

---

## 代码实现细节

### Agent 层面的逐步写入

**core/agent.py:317-392**

```python
def run(self, user_input: str, verbose: bool = True) -> str:
    iteration = 0
    while iteration < self.max_iterations:
        iteration += 1
        
        # 1. 调用 LLM
        response = self.llm.chat(messages, tools=...)
        
        # 2. 检查工具调用
        tool_calls = response["tool_calls"]
        
        # 3. 没有工具调用则返回
        if not tool_calls:
            return content
        
        # 4. 执行工具（包括 WriteFileTool）
        for tool_call in tool_calls:
            result = self._execute_tool(tool_call)
            
            # 5. 添加工具结果到记忆
            self.memory.add_tool_result(...)
            
            # ← 这里完成了一次写入
            # 下一次迭代会基于这次的结果继续
        
    return "达到最大迭代次数"
```

**关键点**:
- ✅ 每次迭代只执行 LLM 返回的工具调用
- ✅ 工具执行完后添加到记忆
- ✅ 下一次迭代基于更新后的记忆
- ✅ 因此是**逐步写入**，不是一次性

---

### Swarm 层面的逐步写入

**swarm/orchestrator.py:148-210**

```python
async def _execute_loop(self, original_task: str) -> SwarmResult:
    while self._iteration < self.max_iterations:
        self._iteration += 1
        
        # 1. 获取就绪任务（依赖已满足）
        ready_tasks = self.task_graph.get_ready_tasks()
        
        if not ready_tasks:
            break  # 没有任务，退出
        
        # 2. 并行执行就绪任务
        for task in ready_tasks:
            agent = await self.scheduler.assign_task(task)
            if agent:
                result = await self._execute_task(task, agent)
                
                # 3. 任务完成后更新状态
                if result:
                    task.mark_completed(result)
                    # ← 这个任务写入完成
                    
        # 4. 下一轮迭代检查新的就绪任务
        # （依赖于刚才完成的任务）
```

**关键点**:
- ✅ 任务有依赖关系（DAG）
- ✅ 只有依赖满足的任务才会执行
- ✅ 每个任务独立写入文件
- ✅ 后续任务可以读取已写入的文件
- ✅ 因此是**真正的逐步写入**

---

## 实际案例分析

### 案例 1：单个 Agent 创建多个文件

```python
agent = Agent(
    llm=llm,
    tools=[WriteFileTool(), ReadFileTool()],
    name="Developer",
    max_iterations=20  # 允许最多 20 次迭代
)

result = agent.run("""
创建一个完整的 Python 项目，包括：
1. main.py - 主程序入口
2. utils.py - 工具函数
3. config.py - 配置文件
""")
```

**实际执行（逐步写入）**:

```
迭代 1:
  → LLM: "我先创建 main.py"
  → WriteFileTool("main.py", "print('Hello')")
  → ✅ 写入成功

迭代 2:
  → LLM 看到 main.py 已创建
  → "接下来创建 utils.py"
  → WriteFileTool("utils.py", "def help(): ...")
  → ✅ 写入成功

迭代 3:
  → LLM 看到 main.py, utils.py 已创建
  → "最后创建 config.py"
  → WriteFileTool("config.py", "DEBUG=True")
  → ✅ 写入成功

迭代 4:
  → LLM 看到所有文件已创建
  → "项目创建完成"
  → 返回结果
```

**文件写入顺序**:
```
main.py   → 迭代 1 写入
utils.py  → 迭代 2 写入
config.py → 迭代 3 写入
```

---

### 案例 2：Swarm 多 Agent 协作

```python
orchestrator = SwarmOrchestrator(
    agents=[
        Agent(name="架构师", system_prompt="设计系统架构"),
        Agent(name="开发者", system_prompt="编写代码"),
        Agent(name="测试员", system_prompt="编写测试"),
    ],
    llm=llm
)

result = await orchestrator.solve("开发待办事项系统")
```

**实际执行（并行 + 串行）**:

```
迭代 1:
  → Task 1 (架构师): 设计数据模型
    → WriteFileTool("models/todo.py") ✅
  
迭代 2:
  → Task 2 (开发者): 实现服务层
    → ReadFileTool("models/todo.py")  ← 读取刚写的文件
    → WriteFileTool("services/todo_service.py") ✅

迭代 3:
  → Task 3 (开发者): 实现 API
    → ReadFileTool("services/todo_service.py")  ← 读取刚写的文件
    → WriteFileTool("api/todo_api.py") ✅

迭代 4:
  → Task 4 (测试员): 编写测试
    → ReadFileTool 读取所有文件
    → WriteFileTool("tests/test_todo.py") ✅
```

**写入时间线**:
```
t1: models/todo.py         (架构师)
t2: services/todo_service.py (开发者，参考了 models/)
t3: api/todo_api.py        (开发者，参考了 services/)
t4: tests/test_todo.py     (测试员，参考了所有文件)
```

---

## 为什么是逐步写入？

### 1. Agent 执行机制决定

```python
# Agent 的 while 循环
while iteration < max_iterations:
    # 每次迭代：
    # 1. 调用 LLM
    # 2. 执行工具（包括 WriteFileTool）
    # 3. 更新记忆
    # 4. 下一次迭代基于新的记忆
```

**结论**: 每次迭代只能执行 LLM 当前返回的工具调用，因此必然是逐步的。

---

### 2. 依赖关系决定

```python
# Task 定义
Task(
    id="2",
    description="实现服务层",
    dependencies=["1"]  # ← 依赖 Task 1
)

# TaskGraph 保证顺序
ready_tasks = graph.get_ready_tasks()
# 只有 Task 1 完成后，Task 2 才会出现在 ready_tasks 中
```

**结论**: 有依赖的任务必须串行执行，因此是逐步的。

---

### 3. 黑板模式支持

```python
# Blackboard 共享上下文
class Blackboard:
    def write(self, key, value, agent_id):
        # Task 1 写入黑板
        blackboard.write("model_code", model_code, "架构师")
    
    def get_context(self, task):
        # Task 2 从黑板读取
        context = blackboard.get_context(task2)
        # → 读取到 model_code
```

**结论**: 后续任务可以读取前面任务的结果，支持逐步构建。

---

## 当前实现的限制

### 限制 1：单次迭代的工具调用数量

```python
# 当前实现：一次迭代可以调用多个工具
for tool_call in tool_calls:  # ← 可能有多个
    result = self._execute_tool(tool_call)
```

**问题**: 如果 LLM 一次返回多个 WriteFileTool 调用，会**并行写入**多个文件。

**示例**:
```python
# LLM 可能一次返回多个工具调用
tool_calls = [
    {"name": "write_file", "arguments": {"file_path": "a.py", ...}},
    {"name": "write_file", "arguments": {"file_path": "b.py", ...}},
    {"name": "write_file", "arguments": {"file_path": "c.py", ...}},
]

# 当前实现会依次执行（实际是串行，但在同一迭代中）
```

**影响**: 
- ✅ 对于独立文件没问题
- ⚠️ 对于有依赖的文件，可能导致后写入的文件无法参考先写入的

---

### 限制 2：Agent 间的协调

**问题**: 如果没有使用 Swarm，单个 Agent 创建多个相关文件时，可能无法正确处理依赖。

**示例**:
```python
# 单个 Agent 可能同时创建两个互相依赖的文件
agent.run("创建 user.py 和 order.py，order.py 依赖 user.py")

# 可能的问题:
# 迭代 1: 同时写入 user.py 和 order.py
# → order.py 可能使用了尚未定义的 user.py 中的类
```

**解决方案**: 使用 Swarm + 任务依赖

```python
tasks = [
    Task(id="1", description="创建 user.py"),
    Task(id="2", description="创建 order.py", dependencies=["1"]),
]
# 这样保证顺序执行
```

---

## 如何确保正确的逐步写入？

### 最佳实践 1：使用 Swarm 和任务依赖

```python
from swarm import SwarmOrchestrator
from swarm.scheduler import Task

orchestrator = SwarmOrchestrator(agents=[...])

# 明确定义依赖
tasks = [
    Task(id="1", description="创建基础模型 (models/user.py)"),
    Task(id="2", description="创建服务层 (services/user_service.py)", 
         dependencies=["1"]),
    Task(id="3", description="创建 API(api/user_api.py)", 
         dependencies=["2"]),
]

# 构建任务图
orchestrator._build_task_graph(tasks)

# 执行（会自动按依赖顺序逐步写入）
result = await orchestrator._execute_loop("开发用户系统")
```

---

### 最佳实践 2：合理设置 max_iterations

```python
# 太小可能导致文件写不完
agent = Agent(
    max_iterations=3  # 可能只够写 1-2 个文件
)

# 推荐
agent = Agent(
    max_iterations=20  # 足够写多个文件
)
```

---

### 最佳实践 3：使用 Pair Programming 模式

```python
from swarm.collaboration_patterns import PairProgramming

pp = PairProgramming(
    driver=driver_agent,    # 编写代码
    navigator=navigator_agent  # 审查代码
)

# 多轮迭代
result = await pp.execute("开发一个功能")

# 流程:
# Round 1: Driver 写初版 → Navigator 审查
# Round 2: Driver 修改 → Navigator 再审
# Round 3: 通过，写入文件
```

---

## 总结

### ✅ 当前是逐步写入吗？

**是的**，通过以下机制保证：

| 层面 | 机制 | 效果 |
|------|------|------|
| **Agent** | while 循环 + 工具执行 | 每次迭代写入一个/多个文件 |
| **Swarm** | 任务依赖图 (DAG) | 按依赖顺序逐步写入 |
| **Blackboard** | 共享上下文 | 后续任务可参考已写入的文件 |

---

### 📊 写入时间线对比

**单次 Agent（简单任务）**:
```
迭代 1 → 写入 file1.py
迭代 2 → 写入 file2.py
迭代 3 → 写入 file3.py
```

**Swarm（复杂任务）**:
```
迭代 1 → Task 1 (架构师) → 写入 models/user.py
迭代 2 → Task 2 (开发者) → 写入 services/user_service.py (参考 models/)
迭代 3 → Task 3 (开发者) → 写入 api/user_api.py (参考 services/)
迭代 4 → Task 4 (测试员) → 写入 tests/test_user.py (参考所有)
```

---

### 🎯 推荐做法

1. **简单任务**（单个文件）：使用单个 Agent
   ```python
   agent.run("创建 calculator.py")
   ```

2. **复杂任务**（多个文件）：使用 Swarm + 任务依赖
   ```python
   tasks = [
       Task("设计模型", id="1"),
       Task("实现服务", id="2", dependencies=["1"]),
       Task("创建 API", id="3", dependencies=["2"]),
   ]
   ```

3. **高质量代码**：使用 Pair Programming
   ```python
   pp = PairProgramming(driver, navigator)
   await pp.execute("开发功能")
   ```

---

### 📖 相关文档

- [Agent 代码开发流程](./AGENT_CODE_DEVELOPMENT.md)
- [Swarm 使用指南](./SWARM_USAGE.md)
- [如何在 CLI 中使用 Swarm](./HOW_TO_USE_SWARM_IN_CLI.md)
