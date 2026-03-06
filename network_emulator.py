import asyncio
import socket
import time
from typing import Optional
from contextlib import asynccontextmanager
import subprocess
import threading
import random


class NetworkEmulator:
    """
    网络异常模拟器，用于模拟各种网络问题
    """
    
    def __init__(self):
        self._proxy_process = None
        self._dns_server_process = None
        self._active_toxics = []
        
    async def simulate_timeout(self, timeout_duration: float):
        """
        模拟连接超时
        
        Args:
            timeout_duration: 超时持续时间（秒）
        """
        print(f"Simulating connection timeout for {timeout_duration} seconds")
        # 模拟网络延迟超过正常超时阈值
        await asyncio.sleep(timeout_duration)
        
    async def simulate_dns_failure(self, domain: str):
        """
        模拟DNS解析失败
        
        Args:
            domain: 要模拟失败的域名
        """
        print(f"Simulating DNS failure for domain: {domain}")
        # 这里可以集成真实的DNS模拟服务器
        # 当前为模拟实现
        raise socket.gaierror(f"Could not resolve domain: {domain}")
        
    async def simulate_packet_loss(self, loss_rate: float):
        """
        模拟网络丢包
        
        Args:
            loss_rate: 丢包率 (0.0 - 1.0)
        """
        if not 0.0 <= loss_rate <= 1.0:
            raise ValueError("Loss rate must be between 0.0 and 1.0")
        
        print(f"Simulating packet loss at rate: {loss_rate * 100}%")
        # 模拟丢包逻辑
        # 在实际实现中，这里会使用toxiproxy或netem等工具
        return loss_rate
    
    async def simulate_bandwidth_limit(self, bandwidth_kbps: int):
        """
        模拟带宽限制
        
        Args:
            bandwidth_kbps: 带宽限制 (kbps)
        """
        print(f"Simulating bandwidth limit: {bandwidth_kbps} kbps")
        # 模拟带宽限制逻辑
        # 在实际实现中，这里会使用流量控制工具
        return bandwidth_kbps
        
    async def simulate_high_latency(self, latency_ms: int):
        """
        模拟高延迟
        
        Args:
            latency_ms: 延迟时间（毫秒）
        """
        print(f"Simulating high latency: {latency_ms} ms")
        await asyncio.sleep(latency_ms / 1000.0)  # 转换为秒
        
    async def simulate_connection_reset(self):
        """
        模拟连接重置
        """
        print("Simulating connection reset")
        # 在实际实现中，这里会中断TCP连接
        raise ConnectionResetError("Connection was reset by peer")
        
    async def simulate_port_unreachable(self):
        """
        模拟端口不可达
        """
        print("Simulating port unreachable")
        # 在实际实现中，这里会模拟ICMP端口不可达
        raise ConnectionRefusedError("Port is unreachable")


class ToxiproxyEmulator:
    """
    基于Toxiproxy的网络异常模拟器
    """
    
    def __init__(self, proxy_host="localhost", proxy_port=8474):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxies = {}
        
    async def create_proxy(self, name: str, upstream: str):
        """
        创建代理
        
        Args:
            name: 代理名称
            upstream: 上游服务地址
        """
        # 模拟创建Toxiproxy代理
        print(f"Creating proxy '{name}' pointing to '{upstream}'")
        self.proxies[name] = {
            'name': name,
            'upstream': upstream,
            'enabled': True,
            'toxics': []
        }
        return self.proxies[name]
        
    async def add_timeout_toxic(self, proxy_name: str, timeout_ms: int):
        """
        添加超时毒性
        
        Args:
            proxy_name: 代理名称
            timeout_ms: 超时时间（毫秒）
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        toxic = {
            'type': 'timeout',
            'attributes': {'timeout': timeout_ms}
        }
        self.proxies[proxy_name]['toxics'].append(toxic)
        print(f"Added timeout toxic to proxy '{proxy_name}': {timeout_ms}ms")
        
    async def add_latency_toxic(self, proxy_name: str, latency_ms: int, jitter_ms: int = 0):
        """
        添加延迟毒性
        
        Args:
            proxy_name: 代理名称
            latency_ms: 延迟时间（毫秒）
            jitter_ms: 延迟抖动（毫秒）
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        toxic = {
            'type': 'latency',
            'attributes': {'latency': latency_ms, 'jitter': jitter_ms}
        }
        self.proxies[proxy_name]['toxics'].append(toxic)
        print(f"Added latency toxic to proxy '{proxy_name}': {latency_ms}±{jitter_ms}ms")
        
    async def add_bandwidth_toxic(self, proxy_name: str, rate_kbps: int):
        """
        添加带宽限制毒性
        
        Args:
            proxy_name: 代理名称
            rate_kbps: 带宽速率（kbps）
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        toxic = {
            'type': 'bandwidth',
            'attributes': {'rate': rate_kbps}
        }
        self.proxies[proxy_name]['toxics'].append(toxic)
        print(f"Added bandwidth toxic to proxy '{proxy_name}': {rate_kbps}kbps")
        
    async def add_slicer_toxic(self, proxy_name: str, average_size: int, size_variation: int):
        """
        添加切片毒性（模拟MTU问题）
        
        Args:
            proxy_name: 代理名称
            average_size: 平均分片大小
            size_variation: 分片大小变化
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        toxic = {
            'type': 'slicer',
            'attributes': {
                'average_size': average_size,
                'size_variation': size_variation
            }
        }
        self.proxies[proxy_name]['toxics'].append(toxic)
        print(f"Added slicer toxic to proxy '{proxy_name}': avg={average_size}, var={size_variation}")
        
    async def remove_all_toxics(self, proxy_name: str):
        """
        移除代理上的所有毒性
        
        Args:
            proxy_name: 代理名称
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        self.proxies[proxy_name]['toxics'] = []
        print(f"Removed all toxics from proxy '{proxy_name}'")
        
    async def enable_proxy(self, proxy_name: str):
        """
        启用代理
        
        Args:
            proxy_name: 代理名称
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        self.proxies[proxy_name]['enabled'] = True
        print(f"Enabled proxy '{proxy_name}'")
        
    async def disable_proxy(self, proxy_name: str):
        """
        禁用代理
        
        Args:
            proxy_name: 代理名称
        """
        if proxy_name not in self.proxies:
            raise ValueError(f"Proxy '{proxy_name}' does not exist")
            
        self.proxies[proxy_name]['enabled'] = False
        print(f"Disabled proxy '{proxy_name}'")


class AdvancedNetworkEmulator(NetworkEmulator):
    """
    高级网络异常模拟器，结合多种模拟技术
    """
    
    def __init__(self):
        super().__init__()
        self.toxiproxy = ToxiproxyEmulator()
        
    @asynccontextmanager
    async def network_scenario(self, scenario_name: str, upstream: str):
        """
        网络场景上下文管理器
        
        Args:
            scenario_name: 场景名称
            upstream: 上游服务地址
        """
        proxy_name = f"test_{scenario_name}_{int(time.time())}"
        
        # 创建代理
        proxy = await self.toxiproxy.create_proxy(proxy_name, upstream)
        
        try:
            yield self.toxiproxy
        finally:
            # 清理资源
            await self.toxiproxy.remove_all_toxics(proxy_name)
            print(f"Cleaned up proxy '{proxy_name}'")


# 示例使用
async def main():
    emulator = AdvancedNetworkEmulator()
    
    # 测试超时场景
    async with emulator.network_scenario("timeout_test", "http://example.com:80") as proxy:
        await proxy.add_timeout_toxic(proxy.proxies[list(proxy.proxies.keys())[0]]['name'], 1000)
        print("Timeout scenario configured")
        
    # 测试延迟场景
    async with emulator.network_scenario("latency_test", "http://example.com:80") as proxy:
        await proxy.add_latency_toxic(
            proxy.proxies[list(proxy.proxies.keys())[0]]['name'], 
            500, 100
        )
        print("High latency scenario configured")

if __name__ == "__main__":
    asyncio.run(main())