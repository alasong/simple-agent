# 测试策略与脚本防护

## 问题背景
每个执行节点后添加测试节点会导致：
- ❌ 执行流程冗长
- ❌ 维护成本高
- ❌ 测试代码与业务代码耦合
- ❌ 难以覆盖边界情况

## 推荐方案：多层防护体系

### 第一层：输入验证（Input Validation）
```python
def validate_weather_query(user_input: str) -> dict:
    """输入验证：确保查询合法"""
    if not user_input or len(user_input.strip()) < 2:
        raise ValueError("查询不能为空")
    
    # 返回结构化的查询参数
    return {
        'query': user_input,
        'date': datetime.now().isoformat(),  # 注入准确日期
        'validated': True
    }
```

### 第二层：断言检查（Assertion Checks）
```python
def execute_weather_query(query: str) -> WeatherResult:
    """执行天气查询，包含断言检查"""
    result = web_search_tool(query)
    
    # 断言：结果必须包含日期信息
    assert result.date is not None, "天气结果必须包含日期"
    
    # 断言：日期必须与当前日期一致（允许±1 天误差）
    today = datetime.now().date()
    assert abs((result.date - today).days) <= 1, f"日期偏差过大：{result.date}"
    
    # 断言：结果必须包含温度信息
    assert result.temperature is not None, "天气结果必须包含温度"
    
    return result
```

### 第三层：结果验证器（Result Validator）
```python
class WeatherResultValidator:
    """天气结果验证器"""
    
    @staticmethod
    def validate(result: WeatherResult) -> tuple[bool, str]:
        """
        验证结果是否合法
        Returns: (是否合法，错误信息)
        """
        if not result.date:
            return False, "缺少日期信息"
        
        if not result.temperature:
            return False, "缺少温度信息"
        
        # 检查日期是否合理（不能是过去或太远未来）
        today = datetime.now().date()
        if result.date < today - timedelta(days=1):
            return False, f"日期过时：{result.date}"
        
        if result.date > today + timedelta(days=10):
            return False, f"日期超前：{result.date}"
        
        # 检查温度是否合理（北京：-30°C ~ 45°C）
        if result.temperature < -30 or result.temperature > 45:
            return False, f"温度异常：{result.temperature}"
        
        return True, ""
```

### 第四层：测试脚本（独立运行）
```python
#!/usr/bin/env python3
# tests/test_weather_query.py
"""天气查询独立测试脚本"""

def test_weather_date_accuracy():
    """测试天气查询日期准确性"""
    result = query_weather("北京天气")
    
    # 验证日期是今天
    assert result.date == datetime.now().date(), \
        f"日期不正确：期望{datetime.now().date()}, 实际{result.date}"
    
    # 验证结果包含必要信息
    assert result.temperature is not None
    assert result.conditions is not None

if __name__ == "__main__":
    test_weather_date_accuracy()
    print("✓ 天气查询日期准确性测试通过")
```

### 第五层：集成测试（CI/CD）
```yaml
# .github/workflows/test.yml
name: Weather Query Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run weather tests
        run: python tests/test_weather_query.py
```

## 实际应用示例

### 修复后的天气查询
```python
def _handle_weather_query(self, user_input: str, verbose: bool = True):
    """处理天气查询 - 包含多层防护"""
    
    # ========== 第一层：输入验证 ==========
    if not any(kw in user_input for kw in ["天气", "气温", "下雨"]):
        raise ValueError("不是天气查询")
    
    # ========== 第二层：注入准确日期 ==========
    from datetime import datetime
    now = datetime.now()
    current_date_str = f"{now.year}年{now.month}月{now.day}日，星期{['一','二','三','四','五','六','日'][now.weekday()]}"
    
    if verbose:
        print(f"[CLI Agent] 系统当前日期：{current_date_str}")
    
    # ========== 第三层：构造强化的提示词 ==========
    enhanced_input = f"{user_input}（**当前准确日期：{current_date_str}。请使用 WebSearchTool 搜索，严禁编造数据！**）"
    
    # ========== 第四层：执行查询 ==========
    result = self.agent.run(enhanced_input, verbose=verbose)
    
    # ========== 第五层：结果验证 ==========
    if self._validate_weather_result(result, current_date_str):
        return result
    else:
        # 验证失败，重试或报错
        if verbose:
            print("[警告] 天气结果验证失败，重试...")
        return self._retry_weather_query(user_input)
    
def _validate_weather_result(self, result: str, expected_date: str) -> bool:
    """验证天气结果是否包含正确日期"""
    # 检查结果中是否包含期望的日期
    if expected_date not in result and "今天" not in result:
        return False
    
    # 检查是否包含温度信息
    if "温度" not in result and "℃" not in result and "°C" not in result:
        return False
    
    return True
```

## 何时使用哪种防护？

| 场景 | 推荐防护 | 理由 |
|------|---------|------|
| **关键业务逻辑** | 全部 5 层 | 天气、支付等不能出错 |
| **用户体验相关** | 第 1-3 层 | 输入验证 + 断言 + 结果验证 |
| **内部工具** | 第 2-3 层 | 断言 + 结果验证 |
| **原型开发** | 第 2 层 | 快速迭代，只保留关键断言 |

## 脚本防护最佳实践

1. **独立性**：测试脚本可以独立运行
   ```bash
   python tests/test_weather_query.py  # 单独测试天气查询
   ```

2. **可组合性**：多个测试可以组合运行
   ```bash
   python -m pytest tests/  # 运行所有测试
   ```

3. **环境隔离**：测试不影响生产数据
   ```python
   # 使用临时目录
   temp_dir = tempfile.mkdtemp(prefix='test_')
   ```

4. **快速失败**：发现问题立即停止
   ```python
   if not validate(result):
       print("❌ 验证失败，停止测试")
       sys.exit(1)
   ```

5. **清晰报告**：输出明确的测试结果
   ```python
   print("✓ 测试通过")  # 或
   print("❌ 测试失败：日期不正确")
   ```

## 总结

**不要**在每个执行节点后添加测试节点，而是：
1. ✅ 在关键点添加**断言检查**
2. ✅ 为关键功能编写**独立测试脚本**
3. ✅ 在 CI/CD 中运行**集成测试**
4. ✅ 使用**结果验证器**确保输出质量
5. ✅ 对**输入验证**保持严格

这样既保证了质量，又不会拖慢开发效率。
