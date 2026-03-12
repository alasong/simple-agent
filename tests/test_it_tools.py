"""
IT Tools Tests

Tests for IT/Software Development tool extensions.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path for module discovery
project_root = "/home/song/simple-agent"
sys.path.insert(0, project_root)

# Manually load the IT module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "it_tools",
    "/home/song/simple_agent/tools/it/__init__.py"
)
it_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(it_module)

# Import from the manually loaded module
GitWorkflow = it_module.GitWorkflow
CICDIntegration = it_module.CICDIntegration
TestingFramework = it_module.TestingFramework
CodeQualityTools = it_module.CodeQualityTools
GitStatus = it_module.GitStatus
CIResult = it_module.CIResult
from simple_agent.extensions import ExtensionConfig


class TestGitWorkflow:
    """Tests for Git workflow extension."""

    def test_workflow_creation(self):
        """Test Git workflow initialization."""
        config = ExtensionConfig(name="git_test")
        workflow = GitWorkflow(config)

        assert workflow.name == "git_workflow"
        assert workflow.repo_path == "."

    def test_workflow_creation_with_path(self):
        """Test Git workflow with custom path."""
        config = ExtensionConfig(name="git_test", config={"repo_path": "/tmp"})
        workflow = GitWorkflow(config)

        assert workflow.repo_path == "/tmp"

    def test_workflow_load_unload(self):
        """Test load and unload."""
        workflow = GitWorkflow()
        workflow.load()

        assert "loaded_at" in workflow._metadata
        assert workflow._metadata["version"] == "1.0.0"

        workflow.unload()


class TestCICDIntegration:
    """Tests for CI/CD integration extension."""

    def test_cicd_creation(self):
        """Test CI/CD integration initialization."""
        config = ExtensionConfig(name="cicd_test")
        cicd = CICDIntegration(config)

        assert cicd.name == "cicd_integration"

    def test_cicd_with_pipelines(self):
        """Test CI/CD with pipeline configuration."""
        config = ExtensionConfig(
            name="cicd_test",
            config={
                "pipelines": {
                    "build": {
                        "steps": [
                            {"name": "install", "type": "command", "command": "echo 'install'"}
                        ]
                    }
                }
            }
        )
        cicd = CICDIntegration(config)
        cicd.load()

        assert "pipelines" in cicd._metadata
        assert "build" in cicd._metadata["pipelines"]

    def test_cicd_load_unload(self):
        """Test load and unload."""
        cicd = CICDIntegration()
        cicd.load()

        assert "loaded_at" in cicd._metadata

        cicd.unload()


class TestTestingFramework:
    """Tests for testing framework extension."""

    def test_testing_creation(self):
        """Test testing framework initialization."""
        config = ExtensionConfig(name="test_test")
        testing = TestingFramework(config)

        assert testing.name == "testing_framework"

    def test_testing_load_unload(self):
        """Test load and unload."""
        testing = TestingFramework()
        testing.load()

        assert "loaded_at" in testing._metadata
        assert testing._metadata["version"] == "1.0.0"

        testing.unload()


class TestCodeQualityTools:
    """Tests for code quality tools extension."""

    def test_quality_creation(self):
        """Test code quality tools initialization."""
        config = ExtensionConfig(name="quality_test")
        quality = CodeQualityTools(config)

        assert quality.name == "code_quality_tools"

    def test_quality_load_unload(self):
        """Test load and unload."""
        quality = CodeQualityTools()
        quality.load()

        assert "loaded_at" in quality._metadata
        assert quality._metadata["version"] == "1.0.0"
        assert "pylint" in quality._metadata.get("tools", [])

        quality.unload()

    def test_code_metrics(self):
        """Test code metrics collection."""
        quality = CodeQualityTools()

        # Test with project root
        metrics = quality.get_code_metrics("/home/song/simple-agent")

        assert "total_files" in metrics
        assert "python_files" in metrics
        assert "lines_of_code" in metrics


class TestGitWorkflowIntegration:
    """Integration tests for Git workflow."""

    def test_git_status(self):
        """Test git status in a real repository."""
        workflow = GitWorkflow()
        workflow.repo_path = "/home/song/simple-agent"

        # Check if it's a git repo
        if os.path.exists("/home/song/simple-agent/.git"):
            status = workflow.get_status("/home/song/simple-agent")

            assert status.branch is not None
            assert status.branch != ""

    def test_git_commit_workflow(self, tmp_path):
        """Test git commit workflow."""
        workflow = GitWorkflow()

        # Create a temp directory with git
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        # Create and commit a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        workflow.stage_file("test.txt", str(tmp_path))
        result = workflow.commit("Initial commit", str(tmp_path))

        assert result is True
