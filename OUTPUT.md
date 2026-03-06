# 输出管理指南

任务执行结果按日期和项目分类保存在根目录的 `output/` 目录下。

## 目录结构

```
output/
└── YYYY-MM-DD/          # 日期目录
    └── project_name/    # 项目子目录（可选）
        └── filename.txt # 任务结果文件
```

### 示例结构

```
output/
├── 2026-03-06/
│   ├── stock_analysis/
│   │   ├── analysis_result.txt
│   │   └── market_report.md
│   └── code_review/
│       ├── review_summary.txt
│       └── suggestions.md
├── 2026-03-07/
│   └── unclassified/
│       └── task_143052.txt
└── 2026-03-08/
    └── research/
        └── findings.json
```

## 使用方式

### 1. 自动保存

任务完成时，CLI Agent 会自动调用 `OutputManagerTool` 保存结果：

```
用户：请帮我分析这个代码文件，保存到 output 目录
Agent: [执行分析...]
       [调用 OutputManagerTool 保存结果到 output/2026-03-06/code_review/xxx.txt]
```

### 2. 手动指定项目

```
用户：把这个报告保存到 stock_analysis 项目
Agent: [调用 OutputManagerTool]
       文件已保存至：./output/2026-03-06/stock_analysis/report.txt
```

### 3. 指定文件名

```
用户：保存结果为 my_analysis.md
Agent: [调用 OutputManagerTool]
       文件已保存至：./output/2026-03-06/my_analysis.md
```

## OutputManagerTool 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project | string | 否 | 项目名称，用于创建子目录 |
| filename | string | 否 | 文件名（不含路径） |
| content | string | 否 | 要保存的内容 |
| file_type | string | 否 | 文件类型：txt/md/json/log，默认 txt |

### 调用示例

```json
{
  "name": "OutputManagerTool",
  "arguments": {
    "project": "stock_analysis",
    "filename": "market_report",
    "content": "分析结果内容...",
    "file_type": "md"
  }
}
```

## 配置说明

在 `config/settings.yaml` 中可以配置输出目录：

```yaml
directories:
  output: "${OUTPUT_DIR:./output}"      # 输出根目录
  output_root: "${OUTPUT_ROOT:./output}" # 输出根目录（别名）
  reports: "${REPORTS_DIR:./output/reports}" # 报告目录
```

通过环境变量覆盖：

```bash
export OUTPUT_DIR=/path/to/custom/output
```

## 最佳实践

### 1. 使用项目分类

为相关任务使用相同的项目名，便于后续查找：

```
# 同一项目的所有输出
output/2026-03-06/stock_analysis/...
output/2026-03-07/stock_analysis/...
output/2026-03-08/stock_analysis/...
```

### 2. 有意义的文件名

使用描述性的文件名：

```
✓ 推荐：market_analysis_2026-03-06.md
✓ 推荐：code_review_summary.txt
✗ 避免：result.txt
✗ 避免：output1.txt
```

### 3. 合适的文件类型

根据内容选择合适的文件类型：

- `md`: 格式化文档、报告
- `txt`: 纯文本结果
- `json`: 结构化数据
- `log`: 日志文件

### 4. 定期整理

按日期自动分类便于定期整理和归档：

```bash
# 查看本月所有输出
ls output/2026-03-*/

# 查找特定项目的输出
find output/ -name "*stock_analysis*" -type d
```

## 查找输出文件

### 按日期查找

```bash
# 查看今天的输出
ls output/$(date +%Y-%m-%d)/

# 查看特定日期的输出
ls output/2026-03-06/
```

### 按项目查找

```bash
# 查找项目目录
find output/ -type d -name "stock_analysis"

# 查找项目下所有文件
find output/ -path "*/stock_analysis/*" -type f
```

### 按文件类型查找

```bash
# 查找所有 Markdown 文件
find output/ -name "*.md" -type f

# 查找所有 JSON 文件
find output/ -name "*.json" -type f
```

## 注意事项

1. **输出目录自动创建**：无需手动创建 output 目录，系统会自动创建
2. **日期基于系统时间**：使用执行任务时的系统日期
3. **项目名可选**：不提供项目名时，文件直接保存在日期目录下
4. **文件覆盖保护**：如果文件名冲突，建议修改文件名避免覆盖
