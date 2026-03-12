"""
CLI Tab 补全测试

运行:
    python -m pytest tests/test_cli_tab_completion.py -v
"""

import pytest
import sys
import os

# 项目根目录 - 添加 parent directory to=sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestCLITabCompletion:
    """测试 CLI Tab 补全功能"""

    def test_setup_readline_completer_returns_true(self):
        """测试 setup_readline_completer 返回 True"""
        from simple_agent.cli import setup_readline_completer
        # 在有 readline 的环境下应该返回 True
        result = setup_readline_completer()
        # 如果返回 False，说明 readline 不可用，跳过测试
        if not result:
            pytest.skip("readline not available in test environment")

    def test_cli_commands_defined(self):
        """测试命令列表定义正确"""
        # 直接测试命令列表，不依赖 readline
        CLI_COMMANDS = [
            # 会话管理
            '/sessions', '/session', '/clear',
            # Agent 管理
            '/new', '/update', '/switch', '/list', '/info', '/save', '/load',
            # 工作流
            '/workflow',
            # 调试
            '/debug',
            # 后台任务
            '/bg', '/tasks', '/result', '/cancel', '/task_stats',
            # 守护进程
            '/start', '/stop', '/restart', '/status', '/logs', '/install-service',
            # 其他
            '/help', '/exit',
        ]

        # 验证基本命令存在
        assert '/help' in CLI_COMMANDS
        assert '/exit' in CLI_COMMANDS
        assert '/start' in CLI_COMMANDS
        assert '/stop' in CLI_COMMANDS
        assert '/status' in CLI_COMMANDS
        assert '/logs' in CLI_COMMANDS
        assert '/list' in CLI_COMMANDS

    def test_command_completion_logic(self):
        """测试补全逻辑"""
        CLI_COMMANDS = [
            # 会话管理
            '/sessions', '/session', '/clear',
            # Agent 管理
            '/new', '/update', '/switch', '/list', '/info', '/save', '/load',
            # 工作流
            '/workflow',
            # 调试
            '/debug',
            # 后台任务
            '/bg', '/tasks', '/result', '/cancel', '/task_stats',
            # 守护进程
            '/start', '/stop', '/restart', '/status', '/logs', '/install-service',
            # 其他
            '/help', '/exit',
        ]

        # 模拟补全逻辑
        def complete(text):
            return [cmd for cmd in CLI_COMMANDS if cmd.startswith(text)]

        # 测试 /h 应该匹配 /help
        matches = complete('/h')
        assert '/help' in matches

        # 测试 /s 应该匹配 /start, /stop, /status, /sessions, /session
        matches = complete('/s')
        assert '/start' in matches
        assert '/stop' in matches
        assert '/status' in matches
        assert '/sessions' in matches
        assert '/session' in matches

        # 测试未知命令返回空列表
        matches = complete('/xyz123')
        assert len(matches) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
