"""
沙箱管理器测试

测试沙箱目录结构、文件操作、清理等功能
"""

import os
import json
import tempfile
import shutil
import time
import pytest
from datetime import datetime

# 沙箱测试
class TestSandbox:
    """沙箱基础功能测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="sandbox_test_")
        from simple_agent.core.sandbox import SandboxManager, Sandbox
        self.sandbox_manager = SandboxManager(self.test_dir)

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sandbox_create(self):
        """测试沙箱创建"""
        sandbox = self.sandbox_manager.create_sandbox("test_001")

        assert sandbox.task_id == "test_001"
        assert sandbox.root.exists()
        assert sandbox.input_dir.exists()
        assert sandbox.output_dir.exists()
        assert sandbox.temp_dir.exists()
        assert sandbox.cache_dir.exists()
        assert sandbox.logs_dir.exists()
        assert sandbox.sandbox_dir.exists()

    def test_sandbox_set_input(self):
        """测试设置输入文件"""
        sandbox = self.sandbox_manager.create_sandbox("test_002")
        sandbox.set_input("Hello, World!", "input.txt")

        input_file = sandbox.input_dir / "input.txt"
        assert input_file.exists()
        assert input_file.read_text() == "Hello, World!"
        assert "input/input.txt" in sandbox.manifest.input_files

    def test_sandbox_save_output(self):
        """测试保存输出文件"""
        sandbox = self.sandbox_manager.create_sandbox("test_003")

        # 保存最终输出
        sandbox.save_output("Final content", "output.txt", is_final=True)

        output_file = sandbox.output_dir / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Final content"
        assert "output/output.txt" in sandbox.manifest.output_files

        # 保存临时文件
        sandbox.save_output("Temp content", "temp.txt", is_final=False)

        temp_file = sandbox.temp_dir / "temp.txt"
        assert temp_file.exists()
        assert temp_file.read_text() == "Temp content"
        assert "process/temp/temp.txt" in sandbox.manifest.process_files

    def test_sandbox_save_tool_call(self):
        """测试记录工具调用"""
        from simple_agent.core.sandbox import ToolCallRecord

        sandbox = self.sandbox_manager.create_sandbox("test_004")
        record = ToolCallRecord(
            tool="BashTool",
            command="ls -la",
            duration_ms=100,
            success=True,
            output_preview="total 10"
        )
        sandbox.save_tool_call(record)

        assert len(sandbox.manifest.tool_calls) == 1
        assert sandbox.manifest.tool_calls[0].tool == "BashTool"

    def test_sandbox_save_logs(self):
        """测试保存日志"""
        sandbox = self.sandbox_manager.create_sandbox("test_005")
        sandbox.save_logs("Execution log", "execution.log")

        log_file = sandbox.logs_dir / "execution.log"
        assert log_file.exists()
        assert log_file.read_text() == "Execution log"

    def test_sandbox_list_files(self):
        """测试列出文件"""
        sandbox = self.sandbox_manager.create_sandbox("test_006")

        # 创建一些文件
        sandbox.set_input("input", "input.txt")
        sandbox.save_output("output", "output.txt", is_final=True)
        sandbox.save_output("temp", "temp.txt", is_final=False)

        files = sandbox.list_files()

        assert "input/input.txt" in files["input"]
        assert "output/output.txt" in files["output"]
        assert "process/temp/temp.txt" in files["temp"]

    def test_sandbox_get_file(self):
        """测试获取文件"""
        sandbox = self.sandbox_manager.create_sandbox("test_007")

        # 在不同目录创建文件
        sandbox.set_input("input content", "input.txt")
        sandbox.save_output("output content", "output.txt", is_final=True)
        sandbox.save_output("temp content", "temp.txt", is_final=False)

        # 按优先级搜索
        assert sandbox.get_file("input.txt") == "input content"
        assert sandbox.get_file("output.txt") == "output content"
        assert sandbox.get_file("temp.txt") == "temp content"
        assert sandbox.get_file("nonexistent.txt") is None

    def test_sandbox_cleanup_temp(self):
        """测试清理临时文件"""
        sandbox = self.sandbox_manager.create_sandbox("test_008")

        # 创建临时文件
        (sandbox.temp_dir / "temp1.txt").write_text("temp1")
        (sandbox.temp_dir / "temp2.txt").write_text("temp2")

        assert (sandbox.temp_dir / "temp1.txt").exists()

        # 清理
        sandbox.cleanup_temp()

        assert not (sandbox.temp_dir / "temp1.txt").exists()
        assert not (sandbox.temp_dir / "temp2.txt").exists()
        assert sandbox.temp_dir.exists()  # 目录应该还在

    def test_sandbox_cleanup_cache(self):
        """测试清理缓存"""
        sandbox = self.sandbox_manager.create_sandbox("test_009")

        # 创建缓存文件
        (sandbox.cache_dir / "cache1.cache").write_text("cache1")

        assert (sandbox.cache_dir / "cache1.cache").exists()

        # 清理
        sandbox.cleanup_cache()

        assert not (sandbox.cache_dir / "cache1.cache").exists()
        assert sandbox.cache_dir.exists()

    def test_sandbox_cleanup_all(self):
        """测试清理所有（除了 output 和 sandbox）"""
        sandbox = self.sandbox_manager.create_sandbox("test_010")

        # 创建各种文件
        (sandbox.temp_dir / "temp.txt").write_text("temp")
        (sandbox.cache_dir / "cache.cache").write_text("cache")
        (sandbox.logs_dir / "log.log").write_text("log")

        # 创建 output 和 sandbox 文件（应该保留）
        sandbox.save_output("output", "output.txt", is_final=True)
        (sandbox.sandbox_dir / "config.json").write_text('{}')

        # 清理
        sandbox.cleanup_all()

        # temp, cache, logs 应该被清理
        assert not (sandbox.temp_dir / "temp.txt").exists()
        assert not (sandbox.cache_dir / "cache.cache").exists()
        assert not (sandbox.logs_dir / "log.log").exists()

        # output 和 sandbox 应该保留
        assert (sandbox.output_dir / "output.txt").exists()
        assert (sandbox.sandbox_dir / "config.json").exists()

    def test_manifest_save_and_load(self):
        """测试清单保存和加载"""
        from simple_agent.core.sandbox import Manifest

        sandbox = self.sandbox_manager.create_sandbox("test_011")

        # 设置清单数据
        sandbox.manifest.user_input = "Test task"
        sandbox.manifest.status = "success"
        sandbox.manifest.created_at = datetime.now().isoformat()
        sandbox.manifest.started_at = datetime.now().isoformat()
        sandbox.manifest.completed_at = datetime.now().isoformat()
        sandbox.manifest.input_files.append("input/input.txt")
        sandbox.manifest.output_files.append("output/output.txt")

        # 保存清单
        manifest_path = sandbox.root / "manifest.json"
        sandbox.manifest.save(str(manifest_path))

        assert manifest_path.exists()

        # 加载并验证
        with open(manifest_path) as f:
            data = json.load(f)

        assert data["task_id"] == "test_011"
        assert data["user_input"] == "Test task"
        assert data["status"] == "success"


class TestSandboxManager:
    """沙箱管理器测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="sandbox_manager_test_")
        from simple_agent.core.sandbox import SandboxManager
        self.sandbox_manager = SandboxManager(self.test_dir)

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_and_get_sandbox(self):
        """测试创建和获取沙箱"""
        sandbox = self.sandbox_manager.create_sandbox("task_001")
        retrieved = self.sandbox_manager.get_sandbox("task_001")

        assert sandbox is retrieved
        assert retrieved.task_id == "task_001"

    def test_get_nonexistent_sandbox(self):
        """测试获取不存在的沙箱"""
        result = self.sandbox_manager.get_sandbox("nonexistent")
        assert result is None

    def test_cleanup_sandbox(self):
        """测试清理沙箱"""
        sandbox = self.sandbox_manager.create_sandbox("task_002")

        # 创建一些文件
        (sandbox.output_dir / "output.txt").write_text("output")
        (sandbox.temp_dir / "temp.txt").write_text("temp")

        # 清理（不删除 output）
        self.sandbox_manager.cleanup_sandbox("task_002", clear_output=False)

        # output 应该还在
        assert (sandbox.output_dir / "output.txt").exists()
        # temp 应该被清理
        assert not (sandbox.temp_dir / "temp.txt").exists()

    def test_cleanup_sandbox_with_output(self):
        """测试清理沙箱（包括 output）"""
        sandbox = self.sandbox_manager.create_sandbox("task_003")

        # 创建一些文件
        (sandbox.output_dir / "output.txt").write_text("output")

        # 完全删除沙箱
        self.sandbox_manager.cleanup_sandbox("task_003", clear_output=True)

        # 沙箱目录应该不存在
        assert not sandbox.root.exists()

    def test_list_sandboxes(self):
        """测试列出沙箱"""
        self.sandbox_manager.create_sandbox("task_004")
        self.sandbox_manager.create_sandbox("task_005")

        sandboxes = self.sandbox_manager.list_sandboxes()

        assert len(sandboxes) >= 2
        task_ids = [s["task_id"] for s in sandboxes]
        assert "task_004" in task_ids
        assert "task_005" in task_ids


class TestSandboxPathParsing:
    """沙箱路径解析测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="sandbox_path_test_")
        from simple_agent.core.sandbox import SandboxManager
        self.sandbox_manager = SandboxManager(self.test_dir)
        self.sandbox = self.sandbox_manager.create_sandbox("path_test")

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_output_prefix(self):
        """测试 output:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("output:/file.txt", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.output_dir
        assert rel_path == "file.txt"

    def test_sandbox_prefix(self):
        """测试 sandbox:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("sandbox:/config.json", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.sandbox_dir
        assert rel_path == "config.json"

    def test_temp_prefix(self):
        """测试 temp:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("temp:/cache.dat", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.temp_dir
        assert rel_path == "cache.dat"

    def test_cache_prefix(self):
        """测试 cache:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("cache:/data.cache", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.cache_dir
        assert rel_path == "data.cache"

    def test_logs_prefix(self):
        """测试 logs:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("logs:/exec.log", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.logs_dir
        assert rel_path == "exec.log"

    def test_input_prefix(self):
        """测试 input:/ 前缀"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("input:/data.txt", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.input_dir
        assert rel_path == "data.txt"

    def test_no_prefix_uses_output(self):
        """测试无前缀默认使用 output"""
        from simple_agent.core.sandbox import parse_sandbox_path

        target_dir, rel_path, error = parse_sandbox_path("default.txt", self.sandbox)

        assert error is None
        assert target_dir == self.sandbox.output_dir
        assert rel_path == "default.txt"

    def test_path_traversal_blocked(self):
        """测试路径遍历攻击阻止"""
        from simple_agent.core.sandbox import parse_sandbox_path

        # 尝试路径遍历
        target_dir, rel_path, error = parse_sandbox_path("output:/../../etc/passwd", self.sandbox)

        assert error is not None
        assert "路径遍历" in error
        assert target_dir is None
        assert rel_path is None


class TestFileToolSandbox:
    """文件工具沙箱支持测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="file_tool_test_")
        from simple_agent.core.sandbox import SandboxManager
        self.sandbox_manager = SandboxManager(self.test_dir)
        self.sandbox = self.sandbox_manager.create_sandbox("file_tool_test")

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_file_tool_with_sandbox_paths(self):
        """测试文件工具使用沙箱路径"""
        from simple_agent.tools.file import set_sandbox_dir, set_output_dir, WriteFileTool, SAFE_WORKSPACE
        from simple_agent.core.tool import ToolResult

        # 临时修改 SAFE_WORKSPACE 以允许测试
        original_workspace = WriteFileTool.__module__.split('.')[0]  # 获取模块名
        import simple_agent.tools.file as file_module
        original_safe = file_module.SAFE_WORKSPACE
        file_module.SAFE_WORKSPACE = str(self.sandbox.root)

        try:
            # 设置沙箱目录
            set_sandbox_dir(str(self.sandbox.root))
            set_output_dir(str(self.sandbox.output_dir))

            tool = WriteFileTool()

            # 使用 output:/ 前缀
            result = tool.execute("output:/output1.txt", "content1")
            assert result.success, f"Expected success, got: {result.error}"
            assert (self.sandbox.output_dir / "output1.txt").exists()

            # 使用 sandbox:/ 前缀
            result = tool.execute("sandbox:/config.json", '{"key": "value"}')
            assert result.success, f"Expected success, got: {result.error}"
            assert (self.sandbox.sandbox_dir / "config.json").exists()

            # 使用 temp:/ 前缀
            result = tool.execute("temp:/temp.dat", "temp data")
            assert result.success, f"Expected success, got: {result.error}"
            assert (self.sandbox.temp_dir / "temp.dat").exists()
        finally:
            file_module.SAFE_WORKSPACE = original_safe

    def test_file_tool_path_traversal_blocked(self):
        """测试文件工具路径遍历阻止"""
        from simple_agent.tools.file import set_sandbox_dir, WriteFileTool

        set_sandbox_dir(str(self.sandbox.root))

        tool = WriteFileTool()

        # 尝试路径遍历
        result = tool.execute("output:/../../etc/passwd", "malicious")
        assert not result.success
        assert "路径遍历" in result.error


class TestBashToolSandbox:
    """Bash 工具沙箱支持测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="bash_tool_test_")
        from simple_agent.core.sandbox import SandboxManager
        self.sandbox_manager = SandboxManager(self.test_dir)
        self.sandbox = self.sandbox_manager.create_sandbox("bash_tool_test")

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_bash_tool_uses_sandbox_dir(self):
        """测试 Bash 工具使用沙箱目录"""
        from simple_agent.tools.bash_tool import _execution_context

        # 设置沙箱目录
        _execution_context.sandbox_dir = str(self.sandbox.root)
        _execution_context.output_dir = str(self.sandbox.output_dir)

        from simple_agent.tools.bash_tool import BashTool
        tool = BashTool()

        # 在沙箱目录中执行命令
        result = tool.execute("pwd")
        assert result.success
        assert str(self.sandbox.root) in result.output

    def test_bash_tool_cwd_override(self):
        """测试 Bash 工具 cwd 覆盖"""
        from simple_agent.tools.bash_tool import _execution_context

        # 设置沙箱目录
        _execution_context.sandbox_dir = str(self.sandbox.root)

        from simple_agent.tools.bash_tool import BashTool
        tool = BashTool()

        # 使用自定义工作目录
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute("pwd", cwd=tmpdir)
            assert result.success
            assert tmpdir in result.output


class TestToolCallRecording:
    """工具调用记录测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.test_dir = tempfile.mkdtemp(prefix="tool_call_test_")
        from simple_agent.core.sandbox import SandboxManager
        self.sandbox_manager = SandboxManager(self.test_dir)
        self.sandbox = self.sandbox_manager.create_sandbox("tool_call_test")

    def teardown_method(self):
        """每个测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tool_call_record(self):
        """测试工具调用记录"""
        from simple_agent.core.sandbox import ToolCallRecord, Manifest

        record = ToolCallRecord(
            tool="BashTool",
            command="echo hello",
            duration_ms=100,
            success=True,
            output_preview="hello"
        )

        assert record.tool == "BashTool"
        assert record.command == "echo hello"
        assert record.duration_ms == 100
        assert record.success is True
        assert record.output_preview == "hello"

    def test_manifest_to_dict(self):
        """测试清单字典转换"""
        from simple_agent.core.sandbox import Manifest

        manifest = Manifest(
            task_id="test",
            user_input="test",
            created_at="2024-01-01T00:00:00",
            status="success"
        )

        data = manifest.to_dict()
        assert data["task_id"] == "test"
        assert data["status"] == "success"
        assert isinstance(data["input_files"], list)
        assert isinstance(data["output_files"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
