# CLI Agent 重构计划

## 当前问题

### 职责过载
CLI Agent 当前承担了**太多具体执行职责**，违背了"接口人"的定位：

1. **工具使用指导**：详细说明如何使用 WebSearchTool、GetCurrentDateTool
2. **具体业务逻辑**：天气查询、新闻资讯、股价查询的执行流程
3. **错误恢复策略**：工具失败时的应对方案
4. **领域专家角色**：软件开发、数据分析、运维部署等

### 提示词过大
- **总字符数**：~5000 字符
- **工具说明**：~3000 字符（60%）
- **错误处理**：~1500 字符（30%）
- **核心职责**：~500 字符（10%）

### 执行效率低
- LLM 需要处理大量无关信息
- 容易混淆"入口判断"和"具体执行"的边界
- 维护成本高（每次修改都影响全局）

---

## 重构目标

### 核心原则
**CLI Agent 只负责三件事**：
1. **理解用户意图**（Intent Recognition）
2. **任务分类分发**（Task Routing）
3. **结果汇总返回**（Result Aggregation）

### 职责边界

| 职责 | CLI Agent | 专业 Agent |
|------|---------|----------|
| 用户交互入口 | ✅ | ❌ |
| 意图识别 | ✅ | ❌ |
| 简单问答 | ❌ **交给 Assistant Agent** | ✅ |
| 天气查询 | ❌ | ✅ **Weather Agent** |
| 新闻查询 | ❌ | ✅ **News Agent** |
| 代码开发 | ❌ | ✅ **Developer Agent** |
| 工具调用 | ❌ | ✅ **各 Agent 自己的工具** |
| 错误恢复 | ❌ | ✅ **工具自己处理** |

---

## 重构方案

### 方案 1：纯路由模式（推荐）

```python
class CLIAgent:
    """
    CLI Agent - 只负责路由
    """
    
    def execute(self, user_input: str) -> str:
        # 1. 意图识别
        intent = self._recognize_intent(user_input)
        
        # 2. 路由到对应 Agent
        if intent == "weather":
            return self._route_to("weather_agent", user_input)
        elif intent == "news":
            return self._route_to("news_agent", user_input)
        elif intent == "general_qa":
            return self._route_to("assistant_agent", user_input)
        elif intent == "complex_task":
            return self._route_to("planner_agent", user_input)
        else:
            return self._route_to("assistant_agent", user_input)
    
    def _recognize_intent(self, text: str) -> str:
        """
        极简意图识别
        - 天气关键词 → weather
        - 新闻关键词 → news
        - 复杂任务关键词 → complex_task
        - 其他 → general_qa
        """
        weather_kw = ["天气", "气温", "下雨", "刮风"]
        news_kw = ["新闻", "头条", "热搜"]
        complex_kw = ["工作流", "部署", "测试流程", "CI/CD"]
        
        if any(kw in text for kw in weather_kw):
            return "weather"
        elif any(kw in text for kw in news_kw):
            return "news"
        elif any(kw in text for kw in complex_kw):
            return "complex_task"
        else:
            return "general_qa"
```

### 对应的提示词（精简版）

```yaml
name: CLI Agent
version: 2.0.0
description: 用户交互入口，负责任务识别和分发
system_prompt: |
  你是 CLI Agent，是用户与系统的**唯一入口**。
  
  ## 核心职责
  1. **识别用户意图**：分析用户需求属于哪个领域
  2. **任务分发**：将任务委托给对应的专业 Agent
  3. **结果返回**：将专业 Agent 的结果汇总返回给用户
  
  ## 任务分类规则
  - **天气查询**（天气、气温、下雨等）→ 委托给 Weather Agent
  - **新闻资讯**（新闻、头条、热搜等）→ 委托给 News Agent
  - **复杂任务**（工作流、部署、测试等）→ 委托给 Planner Agent
  - **其他问题** → 委托给 Assistant Agent（通用问答）
  
  ## 委托方式
  直接调用对应 Agent 的 `run()` 方法，传入用户原始输入即可。
  
  ## 注意事项
  - 不要自己执行具体任务（如查询天气、搜索新闻）
  - 不要详细说明工具使用方法（由各 Agent 自己负责）
  - 不要处理工具失败恢复（由各 Agent 自己处理）
  - 保持简洁，只做"接线员"，不做"接线员 + 话务员"

tools: []  # CLI Agent 不需要任何工具
max_iterations: 1
```

**字符数**：~500 字符（减少 90%）

---

### 方案 2：路由 + 简单问答（折中）

保留 CLI Agent 回答简单问题的能力，但移除实时信息查询：

```yaml
name: CLI Agent
version: 2.0.0
description: 用户交互入口 + 简单问答

system_prompt: |
  你是 CLI Agent，是用户与系统的交互入口。
  
  ## 核心职责
  1. **简单问答**：概念解释、技术问答、代码片段等
  2. **任务分发**：将复杂/实时任务委托给专业 Agent
  
  ## 自己处理的问题
  - 概念解释（"什么是 Python？"）
  - 技术问答（"如何安装 pip？"）
  - 代码编写（"写个快速排序"）
  - 计算转换（"1+1=？"、"100 美元换算人民币"）
  
  ## 需要分发的问题
  - **天气查询** → Weather Agent
  - **新闻资讯** → News Agent
  - **股价/比分** → Data Agent
  - **复杂任务** → Planner Agent
  
  ## 判断规则
  - 包含"天气/气温/下雨" → Weather Agent
  - 包含"新闻/头条/热搜" → News Agent
  - 包含"工作流/部署/测试流程" → Planner Agent
  - 其他 → 自己回答

tools: []  # 简单问答不需要工具
max_iterations: 3
```

**字符数**：~800 字符（减少 84%）

---

## 专业 Agent 分工

### Weather Agent（新增）
```yaml
name: Weather Agent
description: 专业天气查询 Agent
system_prompt: |
  你是天气查询专家，负责：
  1. 获取当前日期（使用 GetCurrentDateTool）
  2. 搜索天气信息（使用 WebSearchTool，fetch_content=true）
  3. 整合信息并返回格式化的天气预报
  
  **重要**：必须使用工具获取实时数据，严禁编造！
  
  ## 标准流程
  1. 调用 GetCurrentDateTool 获取当前日期
  2. 调用 WebSearchTool 搜索"{城市}天气"
  3. 结合日期和搜索结果回答
  
  ## 输出格式
  - 今日天气（日期、天气状况、温度、风力）
  - 未来 7 天预报
  - 生活指数（穿衣、紫外线、洗车等）

tools:
  - GetCurrentDateTool
  - WebSearchTool
max_iterations: 5
```

### News Agent（新增）
```yaml
name: News Agent
description: 专业新闻查询 Agent
system_prompt: |
  你是新闻资讯专家，负责：
  1. 搜索最新新闻（使用 WebSearchTool）
  2. 提取关键信息
  3. 按重要性排序返回
  
tools:
  - WebSearchTool
max_iterations: 3
```

### Assistant Agent（已有）
```yaml
name: Assistant Agent
description: 通用问答助手
system_prompt: |
  你是通用助手，负责回答：
  - 概念解释
  - 技术问答
  - 代码编写
  - 计算转换
  - 建议指导
  
  基于你的训练数据回答，无需调用工具。

tools: []
max_iterations: 3
```

---

## 实施步骤

### Step 1: 创建专业 Agent
- [ ] 创建 `builtin_agents/configs/weather.yaml`
- [ ] 创建 `builtin_agents/configs/news.yaml`
- [ ] 创建 `builtin_agents/configs/assistant.yaml`

### Step 2: 重构 CLI Agent
- [ ] 精简提示词到 500 字符以内
- [ ] 移除工具调用说明
- [ ] 添加意图识别逻辑
- [ ] 添加路由逻辑

### Step 3: 更新路由逻辑
```python
def _recognize_intent(self, user_input: str) -> str:
    """意图识别"""
    if any(kw in user_input for kw in ["天气", "气温", "下雨"]):
        return "weather"
    elif any(kw in user_input for kw in ["新闻", "头条", "热搜"]):
        return "news"
    elif any(kw in user_input for kw in ["工作流", "部署", "测试"]):
        return "complex"
    else:
        return "general"

def execute(self, user_input: str) -> str:
    """执行路由"""
    intent = self._recognize_intent(user_input)
    
    if intent == "weather":
        agent = get_agent("weather")
    elif intent == "news":
        agent = get_agent("news")
    elif intent == "complex":
        agent = get_agent("planner")
    else:
        agent = get_agent("assistant")
    
    return agent.run(user_input)
```

### Step 4: 测试验证
- [ ] 测试天气查询 → Weather Agent
- [ ] 测试新闻查询 → News Agent
- [ ] 测试简单问答 → Assistant Agent
- [ ] 测试复杂任务 → Planner Agent

---

## 预期收益

| 指标 | 重构前 | 重构后 | 改善 |
|------|-------|-------|------|
| CLI 提示词字符数 | ~5000 | ~500 | **90%↓** |
| CLI Agent 职责 | 10+ | 3 | **70%↓** |
| 工具数量 | 5 | 0 | **100%↓** |
| 维护复杂度 | 高 | 低 | **显著改善** |
| 专业 Agent 职责 | 模糊 | 清晰 | **明确分工** |

---

## 推荐方案

**推荐方案 1（纯路由模式）**：
- ✅ 职责最清晰
- ✅ 维护成本最低
- ✅ 扩展性最好
- ⚠️ 需要创建多个专业 Agent

**如果时间有限，可以先实施"日期注入"修复**：
- 在当前架构下，通过代码注入准确日期
- 确保天气查询日期正确
- 作为临时方案，后续再重构
