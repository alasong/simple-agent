#!/usr/bin/env python3
"""
天气查询日期准确性测试

测试目标：确保天气查询返回的日期与系统当前日期一致
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools  # noqa: F401
from cli_agent import CLIAgent


class WeatherDateTester:
    """天气查询日期准确性测试器"""
    
    def __init__(self):
        self.cli = CLIAgent()
        self.today = datetime.now()
        self.today_str = f"{self.today.year}年{self.today.month}月{self.today.day}日"
        self.weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.weekday_str = self.weekdays[self.today.weekday()]
    
    def test_date_injection(self):
        """测试 1：日期注入功能"""
        print(f"\n{'='*60}")
        print(f"测试 1：日期注入功能")
        print(f"{'='*60}")
        print(f"系统当前日期：{self.today_str} {self.weekday_str}")
        
        # 模拟内部逻辑：检查 enhanced_input 是否包含正确日期
        from cli_agent import CLIAgent
        import types
        
        # 创建一个测试实例
        test_cli = CLIAgent()
        
        # 临时保存原始方法
        original_run = test_cli.agent.run
        
        # 拦截 run 调用，检查输入
        captured_input = []
        def mock_run(input_text, **kwargs):
            captured_input.append(input_text)
            return "Mock result"
        
        test_cli.agent.run = mock_run
        
        # 执行天气查询
        try:
            test_cli._handle_simple_task("北京天气", verbose=False)
        except:
            pass  # 忽略错误，我们只关心 captured_input
        
        # 恢复原始方法
        test_cli.agent.run = original_run
        
        # 检查注入的日期
        if captured_input:
            enhanced_input = captured_input[0]
            print(f"enhanced_input: {enhanced_input[:200]}...")
            
            if self.today_str in enhanced_input:
                print(f"✓ 日期注入成功：{self.today_str}")
                return True
            else:
                print(f"❌ 日期注入失败：未找到 {self.today_str}")
                return False
        else:
            print("❌ 未捕获到输入")
            return False
    
    def test_result_date_accuracy(self):
        """测试 2：结果日期准确性"""
        print(f"\n{'='*60}")
        print(f"测试 2：结果日期准确性")
        print(f"{'='*60}")
        
        # 执行真实的天气查询
        result_tuple = self.cli.execute("北京天气", verbose=False)
        
        # 解包结果
        if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
            result, saved_path = result_tuple
        else:
            result = result_tuple
        
        result_str = str(result)
        
        # 检查日期关键词
        date_patterns = [
            self.today_str,
            f"3 月{self.today.day}日",
            f"03 月{self.today.day:02d}日",
            f"今天",
        ]
        
        found_date = False
        for pattern in date_patterns:
            if pattern in result_str:
                found_date = True
                print(f"✓ 找到日期关键词：{pattern}")
                break
        
        if not found_date:
            print(f"❌ 结果中未找到正确的日期（期望包含：{self.today_str}）")
            print(f"结果预览：{result_str[:200]}...")
            return False
        
        # 检查是否有明显的错误日期（如 3 月 12 日等）
        error_dates = [
            "3 月 8 日", "3 月 9 日", "3 月 10 日", "3 月 11 日", 
            "3 月 12 日", "3 月 13 日", "3 月 14 日"
        ]
        
        # 排除正确的日期
        correct_date = f"3 月{self.today.day}日"
        error_dates = [d for d in error_dates if d != correct_date]
        
        for error_date in error_dates:
            if error_date in result_str:
                print(f"⚠️  警告：结果中包含可能的错误日期：{error_date}")
                # 不直接判失败，因为可能是未来预报
        
        print(f"✓ 日期准确性检查通过")
        return True
    
    def test_result_contains_temperature(self):
        """测试 3：结果包含温度信息"""
        print(f"\n{'='*60}")
        print(f"测试 3：结果包含温度信息")
        print(f"{'='*60}")
        
        result_tuple = self.cli.execute("北京天气", verbose=False)
        
        if isinstance(result_tuple, tuple):
            result = result_tuple[0]
        else:
            result = result_tuple
        
        result_str = str(result)
        
        # 检查温度关键词
        temp_patterns = ["温度", "气温", "℃", "°C", "最高气温", "最低气温"]
        
        found_temp = False
        for pattern in temp_patterns:
            if pattern in result_str:
                found_temp = True
                print(f"✓ 找到温度关键词：{pattern}")
                break
        
        if not found_temp:
            print(f"❌ 结果中未找到温度信息")
            print(f"结果预览：{result_str[:200]}...")
            return False
        
        print(f"✓ 温度信息检查通过")
        return True
    
    def test_output_file_saved(self):
        """测试 4：输出文件正确保存"""
        print(f"\n{'='*60}")
        print(f"测试 4：输出文件保存")
        print(f"{'='*60}")
        
        result_tuple = self.cli.execute(
            "北京天气", 
            verbose=False,
            output_dir="./output/test_weather",
            isolate_by_instance=False
        )
        
        if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
            result, saved_path = result_tuple
        else:
            result = result_tuple
            saved_path = None
        
        if saved_path and os.path.exists(saved_path):
            print(f"✓ 输出文件已保存：{saved_path}")
            
            # 检查文件内容
            import glob
            files = glob.glob(os.path.join(saved_path, "*.txt"))
            if files:
                print(f"✓ 找到 {len(files)} 个结果文件")
                
                # 检查第一个文件
                with open(files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 验证文件包含必要信息
                if "# 任务输入" in content and "# 执行时间" in content and "# 执行结果" in content:
                    print(f"✓ 文件格式正确")
                    return True
                else:
                    print(f"❌ 文件格式不正确")
                    return False
            else:
                print(f"❌ 未找到结果文件")
                return False
        else:
            print(f"❌ 输出文件未保存或路径不存在")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("天气查询日期准确性测试套件")
        print("="*60)
        
        tests = [
            ("日期注入功能", self.test_date_injection),
            ("结果日期准确性", self.test_result_date_accuracy),
            ("结果包含温度", self.test_result_contains_temperature),
            ("输出文件保存", self.test_output_file_saved),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                passed = test_func()
                results.append((name, passed))
            except Exception as e:
                print(f"\n❌ {name} 测试异常：{e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        # 汇总结果
        print(f"\n{'='*60}")
        print("测试结果汇总")
        print(f"{'='*60}")
        
        passed_count = sum(1 for _, p in results if p)
        total_count = len(results)
        
        for name, passed in results:
            status = "✓ 通过" if passed else "❌ 失败"
            print(f"  {name}: {status}")
        
        print(f"\n总计：{passed_count}/{total_count} 测试通过")
        
        if passed_count == total_count:
            print("\n✓ 所有测试通过！")
            return True
        else:
            print(f"\n⚠️  有 {total_count - passed_count} 个测试失败")
            return False


if __name__ == "__main__":
    tester = WeatherDateTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
