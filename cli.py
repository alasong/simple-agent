#!/usr/bin/env python3
"""CLI 入口 - 简单包装"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_agent.cli import main

if __name__ == "__main__":
    main()
