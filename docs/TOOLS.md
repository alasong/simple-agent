# 工具支持指南 (Tools Guide)

## 设计理念

**核心原则**：
1. **最小化工具集** - 只做 bash 做不到的事
2. **环境优先** - 优先使用系统已有命令
3. **不破坏用户习惯** - 用户用什么工具就用什么
4. **该确认的就确认** - 危险操作必须让用户确认

> **AI 是助手，不是自动执行器。**

---

## 工具列表

### 核心工具（80% 场景）

| 工具 | 功能 | 典型用途 |
|------|------|----------|
| `BashTool` | 执行 Shell 命令 | **环境安装、文件操作、运行程序** |
| `ReadFileTool` | 读取文件 | 读取配置、代码、文档 |
| `WriteFileTool` | 写入文件 | 创建/修改文件 |

### 辅助工具（按需使用）

| 工具 | 功能 |
|------|------|
| `WebSearchTool` | 网络搜索 |
| `HttpTool` | HTTP 请求 |

### Agent 协作工具

| 工具 | 功能 |
|------|------|
| `InvokeAgentTool` | 调用其他 Agent |
| `CreateWorkflowTool` | 创建工作流 |
| `ListAgentsTool` | 列出可用 Agent |

### 补充工具（LLM 驱动）

| 工具 | 功能 |
|------|------|
| `SupplementTool` | 对已有结果补充说明 |
| `ExplainReasonTool` | 解释原因 |

---

## 场景化使用指南

### 1. 环境安装

**使用 BashTool** - 调用系统的包管理器：

```bash
# Python 环境
pip install -r requirements.txt
poetry install
conda env create

# Node.js 环境
npm install
yarn install

# 系统级安装 (需要权限时用户自行处理)
apt install python3-pip
brew install node
```

**Agent 提示词示例**：
```yaml
tools:
  - BashTool
  - ReadFileTool
```

### 2. 文件处理

**使用 BashTool + 系统工具** - 尊重用户习惯：

```bash
# 用户习惯用 vim → Agent 用 cat/less 读取
# 用户习惯用 VSCode → Agent 用 WriteFileTool 写入

# 常见文件操作
cat file.txt           # 读取
cp src dest            # 复制
mv old new             # 移动
find . -name "*.py"    # 查找
grep "pattern" file    # 搜索
```

### 3. 邮件处理

**不要内置邮件工具** - 使用用户已有的方式：

```bash
# 方案 1: 命令行邮件 (mutt/mailx)
echo "正文" | mail -s "主题" user@example.com

# 方案 2: 脚本调用
python send_email.py  # 用户自己的脚本

# 方案 3: API 调用 (curl)
curl -X POST https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer $API_KEY" \
  -d @email.json
```

**原因**：
- 用户可能用 Outlook、Thunderbird、Gmail 网页版
- 内置工具会破坏用户已有的工作流
- 通过 BashTool 可以调用用户配置好的任何方式

### 4. 文档处理

**使用 BashTool + 系统工具**：

```bash
# Markdown 转换
pandoc README.md -o README.pdf

# 文档搜索
grep -r "TODO" docs/

# 批量处理
for f in *.md; do echo "处理 $f"; done
```

### 5. 数据处理

**使用 BashTool + 用户环境**：

```bash
# JSON 处理 (jq)
cat data.json | jq '.users[] | select(.age > 25)'

# CSV 处理 (Python)
python -c "import pandas as pd; print(pd.read_csv('data.csv').describe())"

# SQL 查询
sqlite3 database.db "SELECT * FROM users"
```

---

## 与 OpenHands/OpenDevin 对比

| 功能 | Simple Agent | OpenHands |
|------|-------------|-----------|
| Shell 命令 | ✓ BashTool | ✓ |
| 文件编辑 | ✓ Read/WriteFileTool | ✓ |
| 浏览器 | ✗ (通过 bash 调用) | ✓ 内置 |
| 邮件 | ✗ (通过 bash 调用) | ✗ |
| 多 Agent | ✓ | ✗ |

**差异说明**：
- OpenHands 内置浏览器是因为需要**可视化**操作
- 我们选择通过 bash 调用 `playwright-cli` 或 `curl`
- 这样不强制安装庞大依赖，用户按需选择

---

## 最佳实践

### 1. 优先使用 BashTool

```python
# ❌ 不好的做法：自己实现
class DirectoryTool(BaseTool):  # 重复造轮子
    def execute(self, path):
        return os.listdir(path)

# ✓ 好的做法：使用系统命令
agent.run("ls -la /path/to/dir")  # 通过 BashTool
```

### 2. 利用系统工具链

```python
# ❌ 自己实现复杂逻辑
def process_json(content):
    # 100 行解析代码...

# ✓ 使用 jq
agent.run(f"echo '{content}' | jq '.field'")
```

### 3. 尊重用户环境

```python
# ❌ 强制使用内置工具
send_email_builtin(to="user@company.com", ...)  # 用户可能不用

# ✓ 使用用户的方式
agent.run("send_mail.py --to user@company.com")  # 用户的脚本
```

---

## 何时需要新工具？

**判断标准**：

1. **bash 做不到** → 需要新工具
   - 例如：Agent 间调用（InvokeAgentTool）
   - 例如：LLM 驱动的操作（WebSearchTool）

2. **bash 能做到** → 用 BashTool
   - 例如：发邮件 → `mail` 命令或 API
   - 例如：浏览器 → `curl` 或 `playwright-cli`
   - 例如：数据库 → `sqlite3` 或 `psql` 命令

3. **用户习惯固定** → 不内置
   - 例如：邮件客户端
   - 例如：编辑器
   - 例如：IDE

---

## 扩展示例

如果真的需要新工具（bash 做不到时）：

```python
from core.tool import BaseTool, ToolResult

class CustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "custom_tool"

    @property
    def description(self) -> str:
        return "描述这个 bash 做不到的事情"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "arg": {"type": "string", "description": "参数说明"}
            },
            "required": ["arg"]
        }

    def execute(self, arg: str, **kwargs) -> ToolResult:
        # 实现 bash 做不到的功能
        return ToolResult(success=True, output="结果")

# 注册
from core.resource import repo
repo.register_tool(CustomTool, tags=["custom"])
```

---

## 总结

**Simple Agent 的工具哲学**：

> **工具不是功能列表，而是对用户的尊重。**

- 给用户的选择权，而不是我们的预设
- 利用环境的力量，而不是重复造轮子
- 保持最小依赖，让用户决定安装什么

**80% 的场景**：`BashTool` + `ReadFileTool` + `WriteFileTool`

**20% 的场景**：`WebSearchTool` + `HttpTool` + 特定需求
