"""
Daemon - 守护进程管理

支持:
- 后台运行（start/stop/status）
- PID 文件管理
- 日志轮转
- systemd/launchd 集成
"""

import os
import sys
import signal
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class DaemonManager:
    """守护进程管理器"""

    def __init__(self, name: str = "simple-agent"):
        self.name = name
        self._data_dir = self._get_data_dir()
        self._pid_file = self._get_pid_file()
        self._log_file = self._get_log_file()

    def _get_data_dir(self) -> str:
        """获取数据目录"""
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".daemon"
        )
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        return data_dir

    def _get_pid_file(self) -> str:
        """获取 PID 文件路径"""
        return os.path.join(self._data_dir, f"{self.name}.pid")

    def _get_log_file(self) -> str:
        """获取日志文件路径"""
        return os.path.join(self._data_dir, f"{self.name}.log")

    def _get_log_rotate_file(self, n: int) -> str:
        """获取轮转日志文件路径"""
        return os.path.join(self._data_dir, f"{self.name}.log.{n}")

    def is_running(self) -> bool:
        """检查进程是否在运行"""
        if not os.path.exists(self._pid_file):
            return False

        try:
            with open(self._pid_file, "r") as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            os.kill(pid, 0)
            return True

        except (ValueError, FileNotFoundError, ProcessLookupError):
            # PID 文件无效或进程不存在
            if os.path.exists(self._pid_file):
                os.remove(self._pid_file)
            return False

    def get_pid(self) -> Optional[int]:
        """获取进程 ID"""
        if not os.path.exists(self._pid_file):
            return None

        try:
            with open(self._pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None

    def _write_pid(self, pid: int):
        """写入 PID 文件"""
        with open(self._pid_file, "w") as f:
            f.write(str(pid))

    def _remove_pid(self):
        """移除 PID 文件"""
        if os.path.exists(self._pid_file):
            os.remove(self._pid_file)

    def _rotate_logs(self, max_backups: int = 5):
        """轮转日志文件"""
        if os.path.exists(self._log_file):
            # 删除最旧的日志
            oldest = self._get_log_rotate_file(max_backups)
            if os.path.exists(oldest):
                os.remove(oldest)

            # 移动现有日志
            for i in range(max_backups - 1, 0, -1):
                src = self._get_log_rotate_file(i)
                dst = self._get_log_rotate_file(i + 1)
                if os.path.exists(src):
                    shutil.move(src, dst)

            # 当前日志移动到.1
            if os.path.exists(self._log_file):
                shutil.move(self._log_file, self._get_log_rotate_file(1))

    def start(self, args: Optional[list] = None) -> Tuple[bool, str]:
        """
        启动守护进程

        Args:
            args: 传递给子进程的参数列表

        Returns:
            (成功与否，消息)
        """
        if self.is_running():
            pid = self.get_pid()
            return False, f"守护进程已在运行 (PID: {pid})"

        # 构建命令
        cmd = [
            sys.executable,
            "-m",
            "core.api_server",
            "--host", "127.0.0.1",
            "--port", "8000",
        ]

        if args:
            cmd.extend(args)

        try:
            # 启动子进程（后台运行）
            with open(self._log_file, "a") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=os.path.dirname(os.path.dirname(__file__)),
                )

            # 写入 PID
            self._write_pid(process.pid)

            # 等待一小时间，检查进程是否正常启动
            import time
            time.sleep(1)
            if process.poll() is not None:
                # 进程已退出，读取日志查看错误
                self._remove_pid()
                error_msg = "进程启动失败"
                if os.path.exists(self._log_file):
                    with open(self._log_file, "r") as f:
                        error_msg += f": {f.read()[-500:]}"
                return False, error_msg

            return True, f"守护进程已启动 (PID: {process.pid})"

        except Exception as e:
            return False, f"启动失败：{e}"

    def stop(self, timeout: int = 10) -> Tuple[bool, str]:
        """
        停止守护进程

        Args:
            timeout: 等待进程退出的超时时间（秒）

        Returns:
            (成功与否，消息)
        """
        if not self.is_running():
            self._remove_pid()
            return False, "守护进程未运行"

        pid = self.get_pid()
        if pid is None:
            return False, "无法获取 PID"

        try:
            # 发送 SIGTERM 信号
            os.kill(pid, signal.SIGTERM)

            # 等待进程退出
            import time
            start = time.time()
            while time.time() - start < timeout:
                if not self.is_running():
                    return True, "守护进程已停止"
                time.sleep(0.5)

            # 超时，发送 SIGKILL
            os.kill(pid, signal.SIGKILL)
            self._remove_pid()
            return True, "守护进程已强制停止"

        except ProcessLookupError:
            self._remove_pid()
            return False, "进程不存在"

        except PermissionError:
            return False, "无权限停止进程"

        except Exception as e:
            return False, f"停止失败：{e}"

    def status(self) -> dict:
        """
        获取守护进程状态

        Returns:
            状态字典
        """
        running = self.is_running()
        pid = self.get_pid()

        status = {
            "name": self.name,
            "running": running,
            "pid": pid,
            "pid_file": self._pid_file,
            "log_file": self._log_file,
        }

        if running:
            # 获取进程信息
            try:
                import psutil
                process = psutil.Process(pid)
                status["cpu_percent"] = process.cpu_percent()
                status["memory_percent"] = process.memory_percent()
                status["create_time"] = datetime.fromtimestamp(
                    process.create_time()
                ).isoformat()
                status["status"] = process.status()
            except ImportError:
                # psutil 未安装
                status["note"] = "安装 psutil 获取详细信息"
            except Exception:
                pass

        return status

    def restart(self, args: Optional[list] = None) -> Tuple[bool, str]:
        """重启守护进程"""
        self.stop()
        import time
        time.sleep(1)
        return self.start(args)

    def logs(self, lines: int = 50, follow: bool = False) -> str:
        """
        获取日志内容

        Args:
            lines: 返回行数
            follow: 是否持续跟踪（用于 tail -f 模式）

        Returns:
            日志内容
        """
        if not os.path.exists(self._log_file):
            return "日志文件不存在"

        try:
            with open(self._log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"读取日志失败：{e}"

    def clean(self) -> Tuple[bool, str]:
        """清理守护进程文件"""
        try:
            files_cleaned = []

            # PID 文件
            if os.path.exists(self._pid_file):
                os.remove(self._pid_file)
                files_cleaned.append(self._pid_file)

            # 日志文件
            for i in range(6):
                log_file = self._get_log_rotate_file(i) if i > 0 else self._log_file
                if os.path.exists(log_file):
                    os.remove(log_file)
                    files_cleaned.append(log_file)

            return True, f"已清理 {len(files_cleaned)} 个文件"
        except Exception as e:
            return False, f"清理失败：{e}"


# systemd 服务配置文件
SYSTEMD_SERVICE = """
[Unit]
Description=Simple Agent API Server
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
Environment="PATH={path}"
ExecStart={exec_start}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""".strip()

# launchd plist 配置 (macOS)
LAUNCHD_PLIST = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>simple-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>core.api_server</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_file}</string>
    <key>StandardErrorPath</key>
    <string>{log_file}</string>
</dict>
</plist>
""".strip()


def generate_systemd_service(working_dir: Optional[str] = None) -> str:
    """生成 systemd 服务配置"""
    if working_dir is None:
        working_dir = os.path.dirname(os.path.dirname(__file__))

    return SYSTEMD_SERVICE.format(
        user=os.environ.get("USER", "user"),
        working_dir=working_dir,
        path=os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        exec_start=f"{sys.executable} -m core.api_server --port 8000",
    )


def generate_launchd_plist(working_dir: Optional[str] = None) -> str:
    """生成 launchd 配置 (macOS)"""
    if working_dir is None:
        working_dir = os.path.dirname(os.path.dirname(__file__))

    log_file = os.path.join(working_dir, ".daemon", "simple-agent.log")

    return LAUNCHD_PLIST.format(
        python=sys.executable,
        working_dir=working_dir,
        log_file=log_file,
    )


# 全局管理器
_daemon_instance: Optional[DaemonManager] = None


def get_daemon() -> DaemonManager:
    """获取全局守护进程管理器"""
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = DaemonManager()
    return _daemon_instance
