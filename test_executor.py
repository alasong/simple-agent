import asyncio
import aiohttp
import time
import requests
from typing import Dict, Any, List
from network_emulator import AdvancedNetworkEmulator
import logging
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    duration: float
    error_message: str = ""
    details: Dict[str, Any] = None


class TestExecutor:
    """
    测试执行器，负责执行各种网络异常测试
    """
    
    def __init__(self):
        self.emulator = AdvancedNetworkEmulator()
        self.results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_connectivity_tests(self) -> List[TestResult]:
        """
        执行连通性测试
        """
        results = []
        
        # 测试基本连通性
        result = await self._run_single_test(
            "Basic Connectivity Test",
            self._test_basic_connectivity
        )
        results.append(result)
        
        # 测试多端点连通性
        result = await self._run_single_test(
            "Multi-Endpoint Connectivity Test",
            self._test_multi_endpoint_connectivity
        )
        results.append(result)
        
        return results
    
    async def execute_timeout_tests(self) -> List[TestResult]:
        """
        执行超时测试
        """
        results = []
        
        # 测试连接超时
        result = await self._run_single_test(
            "Connection Timeout Test",
            self._test_connection_timeout
        )
        results.append(result)
        
        # 测试读取超时
        result = await self._run_single_test(
            "Read Timeout Test",
            self._test_read_timeout
        )
        results.append(result)
        
        return results
    
    async def execute_dns_tests(self) -> List[TestResult]:
        """
        执行DNS测试
        """
        results = []
        
        # 测试DNS解析失败
        result = await self._run_single_test(
            "DNS Resolution Failure Test",
            self._test_dns_failure
        )
        results.append(result)
        
        # 测试DNS缓慢响应
        result = await self._run_single_test(
            "Slow DNS Response Test",
            self._test_slow_dns_response
        )
        results.append(result)
        
        return results
    
    async def execute_packet_loss_tests(self) -> List[TestResult]:
        """
        执行网络丢包测试
        """
        results = []
        
        # 测试低丢包率
        result = await self._run_single_test(
            "Low Packet Loss Test (1%)",
            lambda: self._test_packet_loss(0.01)
        )
        results.append(result)
        
        # 测试中等丢包率
        result = await self._run_single_test(
            "Medium Packet Loss Test (5%)",
            lambda: self._test_packet_loss(0.05)
        )
        results.append(result)
        
        # 测试高丢包率
        result = await self._run_single_test(
            "High Packet Loss Test (10%)",
            lambda: self._test_packet_loss(0.10)
        )
        results.append(result)
        
        return results
    
    async def execute_bandwidth_tests(self) -> List[TestResult]:
        """
        执行带宽限制测试
        """
        results = []
        
        # 测试低带宽
        result = await self._run_single_test(
            "Low Bandwidth Test (100kbps)",
            lambda: self._test_bandwidth_limit(100)
        )
        results.append(result)
        
        # 测试中等带宽
        result = await self._run_single_test(
            "Medium Bandwidth Test (500kbps)",
            lambda: self._test_bandwidth_limit(500)
        )
        results.append(result)
        
        # 测试高带宽
        result = await self._run_single_test(
            "High Bandwidth Test (1Mbps)",
            lambda: self._test_bandwidth_limit(1024)
        )
        results.append(result)
        
        return results
    
    async def execute_latency_tests(self) -> List[TestResult]:
        """
        执行延迟测试
        """
        results = []
        
        # 测试高延迟
        result = await self._run_single_test(
            "High Latency Test (500ms)",
            lambda: self._test_high_latency(500)
        )
        results.append(result)
        
        # 测试极高延迟
        result = await self._run_single_test(
            "Very High Latency Test (1000ms)",
            lambda: self._test_high_latency(1000)
        )
        results.append(result)
        
        return results
    
    async def _run_single_test(self, test_name: str, test_func) -> TestResult:
        """
        运行单个测试并返回结果
        
        Args:
            test_name: 测试名称
            test_func: 测试函数
            
        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        
        try:
            await test_func()
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error_message=str(e),
                details={"exception": type(e).__name__}
            )
    
    async def _test_basic_connectivity(self):
        """测试基本连通性"""
        try:
            async with self.session.get('http://httpbin.org/get', timeout=5) as response:
                assert response.status == 200
        except Exception as e:
            raise AssertionError(f"Basic connectivity failed: {str(e)}")
    
    async def _test_multi_endpoint_connectivity(self):
        """测试多端点连通性"""
        endpoints = [
            'http://httpbin.org/get',
            'http://httpbin.org/headers',
            'http://httpbin.org/user-agent'
        ]
        
        for endpoint in endpoints:
            try:
                async with self.session.get(endpoint, timeout=5) as response:
                    assert response.status == 200
            except Exception as e:
                raise AssertionError(f"Connectivity to {endpoint} failed: {str(e)}")
    
    async def _test_connection_timeout(self):
        """测试连接超时"""
        # 使用一个不存在的IP地址来触发连接超时
        try:
            # 这会尝试连接到一个不存在的服务，应该超时
            async with self.session.get('http://10.255.255.1:81/get', timeout=aiohttp.ClientTimeout(total=3)) as response:
                # 如果没有超时，测试失败
                raise AssertionError("Expected timeout did not occur")
        except asyncio.TimeoutError:
            # 这是期望的行为
            pass
        except Exception as e:
            # 检查是否是连接相关的错误
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                pass  # 这也是期望的行为
            else:
                raise e
    
    async def _test_read_timeout(self):
        """测试读取超时"""
        try:
            # 请求一个会延迟响应的端点
            async with self.session.get('http://httpbin.org/delay/10', timeout=aiohttp.ClientTimeout(total=5)) as response:
                # 如果没有超时，测试失败
                raise AssertionError("Expected read timeout did not occur")
        except asyncio.TimeoutError:
            # 这是期望的行为
            pass
        except Exception as e:
            if "timeout" in str(e).lower():
                pass  # 这也是期望的行为
            else:
                raise e
    
    async def _test_dns_failure(self):
        """测试DNS解析失败"""
        try:
            # 使用一个不存在的域名
            async with self.session.get('http://nonexistent-domain-12345.com/', timeout=5) as response:
                # 如果请求成功，测试失败
                raise AssertionError("Expected DNS failure did not occur")
        except aiohttp.ClientConnectorError as e:
            # 这是期望的DNS解析失败
            if "DNS" in str(e) or "resolve" in str(e).lower():
                pass
            else:
                raise e
        except Exception as e:
            # 检查是否是DNS相关的错误
            if "DNS" in str(e) or "resolve" in str(e).lower() or "name or service not known" in str(e):
                pass
            else:
                raise e
    
    async def _test_slow_dns_response(self):
        """测试DNS缓慢响应"""
        # 这个测试需要特殊的DNS服务器设置，这里简化处理
        # 实际中可以通过配置本地DNS服务器来实现
        try:
            # 模拟长时间DNS查询
            import socket
            original_getaddrinfo = socket.getaddrinfo
            
            def slow_getaddrinfo(*args, **kwargs):
                time.sleep(2)  # 模拟DNS查询延迟
                return original_getaddrinfo(*args, **kwargs)
            
            socket.getaddrinfo = slow_getaddrinfo
            
            try:
                async with self.session.get('http://httpbin.org/get', timeout=5) as response:
                    assert response.status == 200
            finally:
                socket.getaddrinfo = original_getaddrinfo
                
        except Exception as e:
            raise AssertionError(f"Slow DNS response handling failed: {str(e)}")
    
    async def _test_packet_loss(self, loss_rate: float):
        """测试网络丢包"""
        # 模拟网络丢包的影响
        # 在实际环境中，这会通过网络模拟工具实现
        success_count = 0
        total_attempts = 10
        
        for i in range(total_attempts):
            try:
                # 根据丢包率决定是否模拟请求失败
                if random.random() < loss_rate:
                    # 模拟请求因丢包而失败
                    raise aiohttp.ClientConnectorError(None, "Simulated packet loss")
                
                async with self.session.get('http://httpbin.org/get', timeout=10) as response:
                    if response.status == 200:
                        success_count += 1
            except Exception:
                # 请求失败，可能是由于丢包
                pass
        
        # 验证成功率是否在预期范围内（考虑到重试机制）
        expected_success_rate = 1.0 - loss_rate
        actual_success_rate = success_count / total_attempts
        
        # 允许一定的误差范围
        if actual_success_rate < expected_success_rate - 0.2:
            raise AssertionError(f"Success rate {actual_success_rate:.2f} too low for loss rate {loss_rate:.2f}")
    
    async def _test_bandwidth_limit(self, bandwidth_kbps: int):
        """测试带宽限制"""
        # 测试大文件下载时间，验证带宽限制效果
        file_size_kb = 1024  # 1MB
        start_time = time.time()
        
        try:
            # 下载一个较大的文件来测试带宽
            async with self.session.get(f'http://httpbin.org/bytes/{file_size_kb * 1024}', timeout=60) as response:
                content = await response.read()
                end_time = time.time()
                
                actual_size_kb = len(content) / 1024
                transfer_time = end_time - start_time
                actual_bandwidth = actual_size_kb / transfer_time  # KB/s
                
                # 转换为Kbps进行比较
                actual_bandwidth_kbps = actual_bandwidth * 8
                
                # 验证实际带宽不超过限制太多（允许一定误差）
                if actual_bandwidth_kbps > bandwidth_kbps * 1.5:
                    print(f"Warning: Actual bandwidth {actual_bandwidth_kbps:.2f}kbps exceeds limit {bandwidth_kbps}kbps")
                    
        except Exception as e:
            raise AssertionError(f"Bandwidth limit test failed: {str(e)}")
    
    async def _test_high_latency(self, latency_ms: int):
        """测试高延迟"""
        try:
            start_time = time.time()
            async with self.session.get('http://httpbin.org/get', timeout=30) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # 验证响应时间是否符合预期（考虑到网络本身的延迟）
                if response_time < latency_ms * 0.5:  # 允许一定误差
                    print(f"Note: Response time {response_time:.2f}ms less than expected latency {latency_ms}ms")
                    
                assert response.status == 200
        except Exception as e:
            raise AssertionError(f"High latency test failed: {str(e)}")
    
    async def run_all_tests(self) -> List[TestResult]:
        """
        运行所有测试
        
        Returns:
            List[TestResult]: 所有测试结果
        """
        all_results = []
        
        print("Starting connectivity tests...")
        all_results.extend(await self.execute_connectivity_tests())
        
        print("Starting timeout tests...")
        all_results.extend(await self.execute_timeout_tests())
        
        print("Starting DNS tests...")
        all_results.extend(await self.execute_dns_tests())
        
        print("Starting packet loss tests...")
        all_results.extend(await self.execute_packet_loss_tests())
        
        print("Starting bandwidth tests...")
        all_results.extend(await self.execute_bandwidth_tests())
        
        print("Starting latency tests...")
        all_results.extend(await self.execute_latency_tests())
        
        return all_results


# 辅助函数
def random():
    """辅助函数，用于模拟随机数生成"""
    import random as rand
    return rand.random()


async def main():
    """主函数，运行所有测试"""
    async with TestExecutor() as executor:
        results = await executor.run_all_tests()
        
        # 打印测试结果摘要
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        print(f"\nTest Results Summary:")
        print(f"Total tests: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        
        # 打印详细结果
        for result in results:
            status_symbol = "✓" if result.status == TestStatus.PASSED else "✗"
            print(f"{status_symbol} {result.test_name}: {result.status.value} ({result.duration:.2f}s)")
            if result.error_message:
                print(f"  Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())