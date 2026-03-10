# 工具使用确认机制 (Tool Confirmation Policy)

## 设计理念

**核心原则**：按人的思路执行，该确认的就确认。

> **AI 是助手，不是自动执行器。**
>
> 涉及副作用、危险操作、数据修改的命令，必须让人确认。

---

## 命令分类

### 1. 安全命令（可直接执行）

AI 可以自动执行，无需确认：

| 类别 | 命令示例 |
|------|----------|
| 查看信息 | `ls`, `cat`, `pwd`, `date`, `whoami` |
| 搜索查找 | `grep`, `find`, `locate`, `which` |
| 进程查看 | `ps`, `top`, `htop`, `free`, `df` |
| Git 只读 | `git status`, `git log`, `git diff`, `git branch` |
| 包管理查看 | `pip list`, `npm list` |
| 版本检查 | `python --version`, `node --version` |

**特点**：只读、无副作用、可重复执行

---

### 2. 需要确认的命令（必须用户确认）

AI 应该返回错误，等待用户确认后才能执行：

| 类别 | 命令示例 | 确认提示 |
|------|----------|----------|
| 删除文件 | `rm -rf`, `rmdir`, `del` | "将删除以下文件：xxx，确认？" |
| 终止进程 | `kill`, `pkill`, `killall` | "将终止进程 xxx，确认？" |
| 磁盘操作 | `format`, `fdisk`, `parted` | "将格式化磁盘，数据将丢失，确认？" |
| 系统重启 | `shutdown`, `reboot` | "将重启系统，确认？" |
| 防火墙 | `iptables`, `ufw` | "将修改防火墙规则，确认？" |
| 远程脚本 | `curl xxx \| sh` | "将执行远程脚本，来源：xxx，确认？" |
| 权限修改 | `chmod 777`, `chown` | "将修改文件权限为 xxx，确认？" |

**AI 行为**：
1. 检测到危险模式
2. 返回错误：`"等待确认：命令包含危险操作 'rm -rf'，需要用户确认"`
3. 等待用户确认
4. 用户确认后，设置 `confirmed_by_user=true` 重新调用

---

### 3. 绝对禁止的命令

AI 不应该执行，直接拒绝：

```
rm -rf /
rm -rf /*
mkfs
dd if=/dev/zero
:(){ :|:& };:  (fork bomb)
chmod -R 777 /
> /dev/sda
mv /* /dev/null
```

---

## 使用示例

### 示例 1：安全命令（直接执行）

```python
# AI 自动执行
agent.run("ls -la")      # ✓ 直接执行
agent.run("git status")  # ✓ 直接执行
agent.run("cat file.txt") # ✓ 直接执行
```

### 示例 2：危险命令（需要确认）

```python
# AI 尝试执行
result = agent.run("rm -rf build/")

# 返回：等待确认：命令包含危险操作 'rm -rf'，需要用户确认

# --- 此时 AI 应该向用户展示确认请求 ---
# AI: "我准备执行以下命令：rm -rf build/"
# AI: "这将删除 build/ 目录及其所有内容，确认继续？"
# 用户："确认"

# AI 重新调用，设置 confirmed_by_user=true
result = agent.run("rm -rf build/", confirmed_by_user=True)
# ✓ 执行成功
```

### 示例 3：安装依赖（需要确认）

```python
# AI 尝试执行
result = agent.run("pip install -r requirements.txt")

# 返回：等待确认：命令将安装多个包，可能影响环境，确认？

# --- AI 应该向用户展示 ---
# AI: "我准备执行：pip install -r requirements.txt"
# AI: "这将安装以下包：xxx, yyy, zzz，确认？"
# 用户："确认"

# AI 重新调用
result = agent.run("pip install -r requirements.txt", confirmed_by_user=True)
```

---

## CLI 交互示例

在实际 CLI 中，确认流程应该这样：

```
用户：帮我清理一下 build 目录

AI: 我准备执行以下命令来清理 build 目录：

     rm -rf build/

     这将删除 build/ 目录及其所有内容。
     确认继续？[y/N]

用户：y

AI: [执行] rm -rf build/
    [输出] 命令执行成功

    build 目录已清理完成。
```

---

## Agent 提示词建议

在 Agent 配置中，应该明确说明确认策略：

```yaml
name: 开发工程师
tools:
  - BashTool
  - ReadFileTool
  - WriteFileTool

system_prompt: |
  ...
  ## 工具使用原则

  1. **安全命令**（ls, cat, git status 等）可以直接执行
  2. **危险命令**（rm, kill, pip install 等）必须先向用户展示并获取确认
  3. **绝对禁止**的命令不要尝试执行

  确认流程:
  1. 向用户展示要执行的命令
  2. 说明命令的作用和可能的影响
  3. 等待用户明确确认（y/yes）
  4. 确认后设置 confirmed_by_user=true 执行
```

---

## 实现细节

### BashTool 参数

```python
{
    "command": "rm -rf build/",
    "confirmed_by_user": False  # 默认 false，需要确认
}
```

### 返回值

**需要确认时**：
```json
{
    "success": false,
    "error": "等待确认：命令包含危险操作 'rm -rf'，需要用户确认"
}
```

**确认后执行成功**：
```json
{
    "success": true,
    "output": "[输出]\n命令执行成功"
}
```

---

## 为什么这样设计？

### 问题：AI 自动执行的危险

1. **误删除**：AI 可能错误理解用户意图，删除错误文件
2. **环境破坏**：AI 可能安装不兼容的包，破坏环境
3. **数据丢失**：AI 可能执行不可逆的操作
4. **权限问题**：AI 可能修改关键文件权限

### 解决：让人做决定

- **人**了解哪些文件重要
- **人**知道环境的配置
- **人**承担操作的后果

所以，**人应该确认有风险的操作**。

---

## 总结

| 命令类型 | AI 行为 | 示例 |
|----------|--------|------|
| 安全只读 | 直接执行 | `ls`, `cat`, `git status` |
| 有副作用 | 等待确认 | `rm`, `pip install`, `kill` |
| 绝对禁止 | 直接拒绝 | `rm -rf /`, `mkfs` |

**设计目标**：让 AI 成为得力的助手，而不是不可控的自动执行器。
