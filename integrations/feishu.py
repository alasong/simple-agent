"""
Feishu Bot Integration - 飞书机器人集成

支持:
- 群聊@机器人
- 私聊
- 命令解析（/help, /status）

用法:
    python -m integrations.feishu --app-id=xxx --app-secret=xxx
"""

import argparse
import hashlib
import hmac
import base64
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from flask import Flask, request, jsonify

# 或者使用 aiohttp 实现异步版本
# 这里使用 Flask 简化实现


app = Flask(__name__)


class FeishuBot:
    """飞书机器人"""

    def __init__(self, app_id: str, app_secret: str, port: int = 8080):
        self.app_id = app_id
        self.app_secret = app_secret
        self.port = port
        self.access_token: Optional[str] = None
        self.token_expire_at: float = 0

        # Simple Agent API 配置
        self.api_base = "http://localhost:8000/api/v1"
        self.api_key = ""

    def get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token and time.time() < self.token_expire_at:
            return self.access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if data.get("code") == 0:
            self.access_token = data["tenant_access_token"]
            self.token_expire_at = time.time() + data["expire"] - 60
            return self.access_token
        else:
            raise Exception(f"获取 token 失败：{data}")

    def send_message(self, chat_id: str, content: Dict[str, Any], msg_type: str = "text"):
        """发送消息"""
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }

        payload = {
            "receive_id": chat_id,
            "msg_type": msg_type,
            "content": json.dumps(content)
        }

        # query 参数指定消息类型
        params = {"receive_id_type": "chat_id"}

        response = requests.post(url, headers=headers, json=payload, params=params)
        return response.json()

    def send_text_message(self, chat_id: str, text: str):
        """发送文本消息"""
        return self.send_message(chat_id, {"text": text}, "text")

    def send_post_message(self, chat_id: str, content: list):
        """发送富文本消息"""
        return self.send_message(chat_id, {"post": content}, "post")

    def process_command(self, command: str, sender: str, chat_id: str) -> str:
        """处理命令"""
        cmd = command.strip().lower()

        if cmd in ["/help", "帮助"]:
            return """🤖 Simple Agent 助手

可用命令:
/help - 显示帮助
/status - 查看系统状态
/run <任务> - 运行 Agent 任务
/agents - 列出可用 Agent

示例:
/run 分析当前目录的项目结构"""

        elif cmd == "/status":
            try:
                response = requests.get(
                    f"{self.api_base}/health",
                    headers={"X-API-Key": self.api_key}
                )
                data = response.json()
                return f"""系统状态:
- 状态：{data.get('status', 'unknown')}
- 版本：{data.get('version', 'unknown')}
- 运行时长：{data.get('uptime', 0):.1f} 秒"""
            except Exception as e:
                return f"获取状态失败：{e}"

        elif cmd == "/agents":
            try:
                response = requests.get(
                    f"{self.api_base}/agent/list",
                    headers={"X-API-Key": self.api_key}
                )
                data = response.json()
                agents = data.get("agents", [])
                text = "📋 可用 Agent 列表:\n\n"
                for agent in agents[:10]:  # 最多显示 10 个
                    text += f"• {agent['name']} - {agent.get('description', '')[:50]}\n"
                return text
            except Exception as e:
                return f"获取 Agent 列表失败：{e}"

        elif cmd.startswith("/run "):
            task = command[5:].strip()
            if not task:
                return "请提供任务描述，例如：/run 分析当前目录"

            try:
                # 提交任务到 Simple Agent API
                response = requests.post(
                    f"{self.api_base}/agent/run",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "agent_name": "developer",
                        "input": task
                    }
                )
                data = response.json()
                task_id = data.get("task_id", "unknown")
                return f"✅ 任务已提交\n任务 ID: `{task_id}`\n\n使用 /status {task_id} 查看进度"
            except Exception as e:
                return f"提交任务失败：{e}"

        else:
            # 尝试作为普通任务处理
            return self.run_agent_task(command, "developer")

    def run_agent_task(self, input_text: str, agent_name: str = "developer") -> str:
        """运行 Agent 任务"""
        try:
            response = requests.post(
                f"{self.api_base}/agent/run",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "agent_name": agent_name,
                    "input": input_text
                }
            )
            data = response.json()
            task_id = data.get("task_id")

            # 轮询任务状态（同步等待结果）
            for _ in range(60):  # 最多等待 60 秒
                time.sleep(1)
                status_response = requests.get(
                    f"{self.api_base}/task/{task_id}/status",
                    headers={"X-API-Key": self.api_key}
                )
                status_data = status_response.json()

                if status_data.get("status") in ["completed", "failed"]:
                    if status_data.get("output"):
                        # 截取前 500 字符
                        output = status_data["output"][:500]
                        if len(status_data["output"]) > 500:
                            output += "..."
                        return f"✅ 任务完成\n\n{output}"
                    elif status_data.get("error"):
                        return f"❌ 任务失败\n{status_data['error']}"

            return f"⏳ 任务仍在运行中\n任务 ID: `{task_id}`"

        except Exception as e:
            return f"执行失败：{e}"


# 全局机器人实例
bot: Optional[FeishuBot] = None


@app.route("/webhook", methods=["POST"])
def webhook():
    """飞书 Webhook 入口"""
    data = request.json

    # 验证签名（可选）
    # challenge 验证
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # 解析消息
    try:
        header = data.get("header", {})
        event = data.get("event", {})

        # 消息类型
        msg_type = header.get("event_type", "")

        if msg_type == "im.message.receive_v1":
            # 收到消息
            message = event.get("message", {})
            sender = event.get("sender", {})

            chat_id = message.get("chat_id")
            content = message.get("content")
            mention_info = message.get("mentions", [])

            # 解析消息内容
            msg_content = json.loads(content) if isinstance(content, str) else content
            text = msg_content.get("text", "")

            # 检查是否@了机器人
            is_mentioned = any(
                mention.get("name") == "bot"
                for mention in mention_info
            )

            # 如果是群聊且没有@机器人，忽略
            if message.get("chat_type") == "group" and not is_mentioned:
                return jsonify({"ok": True})

            # 移除@标记
            for mention in mention_info:
                text = text.replace(mention.get("name", ""), "").strip()

            if not text:
                return jsonify({"ok": True})

            # 处理命令
            response_text = bot.process_command(text, sender, chat_id)

            # 发送回复
            bot.send_text_message(chat_id, response_text)

    except Exception as e:
        print(f"处理消息失败：{e}")

    return jsonify({"ok": True})


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Feishu Bot Integration")
    parser.add_argument("--app-id", required=True, help="飞书 App ID")
    parser.add_argument("--app-secret", required=True, help="飞书 App Secret")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    parser.add_argument("--api-key", default="", help="Simple Agent API Key")
    parser.add_argument("--api-base", default="http://localhost:8000/api/v1", help="Simple Agent API 地址")

    args = parser.parse_args()

    global bot
    bot = FeishuBot(args.app_id, args.app_secret, args.port)
    bot.api_key = args.api_key
    bot.api_base = args.api_base

    print(f"🤖 Feishu Bot 启动中...")
    print(f"监听端口：{args.port}")
    print(f"Webhook: http://localhost:{args.port}/webhook")
    print("=" * 50)

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
