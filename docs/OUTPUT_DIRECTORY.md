# 输出目录管理

## 📁 目录结构

所有生成的文件都保存在 `output/` 目录中，不会污染根目录。

```
simple-agent/
├── output/                    # 所有输出文件的根目录
│   ├── cli/                   # CLI 任务输出
│   │   ├── task_001/          # 按任务 ID 隔离
│   │   ├── task_002/
│   │   └── ...
│   ├── swarm/                 # Swarm 任务输出
│   │   ├── swarm_001/
│   │   └── ...
│   ├── generated/             # 代码生成输出
│   │   ├── project_name/
│   │   └── ...
│   └── reports/               # 报告文件
│       ├── code_review.md
│       └── ...
├── agents/                    # Agent 配置文件
├── workflows/                 # 工作流配置
├── config/                    # 系统配置
└── ...                        # 源代码（保持干净）
```

## ⚙️ 配置说明

### 配置文件位置

`config/settings.yaml`

### 关键配置项

```yaml
directories:
  # 输出根目录
  output: "${OUTPUT_DIR:./output}"
  output_root: "${OUTPUT_ROOT:./output}"
  
  # 各类型输出
  cli_output: "${CLI_OUTPUT_DIR:./output/cli}"
  swarm_output: "${SWARM_OUTPUT_DIR:./output/swarm}"
  generated_code: "${GENERATED_CODE_DIR:./output/generated}"
  reports: "${REPORTS_DIR:./output/reports}"
  
  # Agent 和工作流（不在 output 中）
  agents: "${AGENTS_DIR:./agents}"
  workflows: "${WORKFLOWS_DIR:./workflows}"
```

### 环境变量覆盖

可以通过环境变量自定义输出目录：

```bash
# 自定义 CLI 输出目录
export CLI_OUTPUT_DIR="./my_output/cli"

# 自定义 Swarm 输出目录
export SWARM_OUTPUT_DIR="./my_output/swarm"

# 自定义代码生成目录
export GENERATED_CODE_DIR="./my_output/code"

# 运行
python cli.py "帮我写个函数"
```

## 📝 使用方式

### 1. CLI 输出隔离

CLI 任务会自动创建独立的子目录：

```bash
python cli.py "帮我写一个计算器"
# 输出保存到：output/cli/task_计算器/
```

开启调试模式时：

```bash
python cli.py --debug "帮我写一个计算器"
# 输出保存到：output/cli/task_计算器/
```

### 2. Swarm 输出

Swarm 任务会保存到 `output/swarm/`：

```python
from swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(agents=[...])
result = await orchestrator.solve("开发用户管理系统")
# 生成的文件保存到 output/swarm/ 或 output/generated/
```

### 3. 使用 OutputManagerTool

```python
from tools.output_manager import OutputManagerTool

manager = OutputManagerTool()

# 保存到项目目录
result = manager.execute(
    project="calculator",
    filename="result",
    content="计算结果：42",
    file_type="txt"
)
# 保存到：output/YYYY-MM-DD/calculator/result.txt
```

## 🔒 Git 忽略

`output/` 目录已添加到 `.gitignore`，不会被提交：

```gitignore
# 输出目录 - 所有生成的文件
output/
*.log
*.tmp
```

## 📊 清理输出

### 清理所有输出

```bash
rm -rf output/*
```

### 清理特定日期的输出

```bash
rm -rf output/2026-03-07/
```

### 清理特定项目的输出

```bash
rm -rf output/generated/calculator/
```

## 🎯 最佳实践

### 1. 项目隔离

为不同的项目使用不同的输出子目录：

```python
# 好：项目隔离
manager.execute(project="project_a", ...)
manager.execute(project="project_b", ...)

# 不好：所有文件混在一起
manager.execute(...)  # 没有指定 project
```

### 2. 有意义的文件名

```python
# 好：有意义的文件名
manager.execute(filename="user_model", ...)

# 不好：使用默认文件名
manager.execute(...)  # 生成 task_12345.txt
```

### 3. 定期清理

建议定期清理输出目录，避免占用过多空间：

```bash
# 清理 7 天前的输出
find output/ -type d -mtime +7 -exec rm -rf {} \;
```

## 📋 相关文件

- [`config/settings.yaml`](../config/settings.yaml) - 配置文件
- [`tools/output_manager.py`](../tools/output_manager.py) - 输出管理工具
- [`cli.py`](../cli.py) - CLI 入口
- [`.gitignore`](../.gitignore) - Git 忽略规则

## 🔄 迁移指南

### 从旧版本迁移

如果你之前使用根目录保存输出文件：

```bash
# 1. 备份旧文件
mkdir -p backup/old_output
mv *.py *.md backup/old_output/  # 移动生成的文件

# 2. 更新配置
# 编辑 config/settings.yaml，确保使用新的输出目录

# 3. 验证
python cli.py "测试"
# 检查 output/cli/ 是否有输出
```

### 环境变量迁移

```bash
# 旧配置（可能污染根目录）
export OUTPUT_DIR="."

# 新配置（隔离到 output/）
export OUTPUT_DIR="./output"
export CLI_OUTPUT_DIR="./output/cli"
```

## ❓ 常见问题

### Q: 如何查看当前输出目录？

```python
from core.config_loader import get_config
config = get_config()
print(config.get('directories.output'))
print(config.get('directories.cli_output'))
```

### Q: 可以临时指定输出目录吗？

```bash
# 使用命令行参数
python cli.py -o ./custom_output "任务"
```

### Q: 如何禁用自动保存？

在代码中设置 `output_dir=None`：

```python
agent.run(task, output_dir=None)
```

### Q: 输出目录占用太多空间怎么办？

使用清理脚本：

```bash
# 清理所有输出
rm -rf output/*

# 或者只保留最近 3 天的
find output/ -type d -mtime +3 -exec rm -rf {} \;
```

---

**总结**: 所有生成的文件都保存到 `output/` 目录，保持根目录干净整洁！✨
