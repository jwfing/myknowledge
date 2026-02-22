#!/usr/bin/env python3
"""
Claude Code Hook Script — Background Path 采集入口

在每次 Claude Code 对话结束（Stop event）时自动触发，
读取完整对话记录，发送到 myknowledge API 进行知识提炼。

使用方式：
  将此脚本配置到 Claude Code 的 Stop hook 中，
  详见同目录下的 claude_hook_config.json。

环境变量：
  MYKNOWLEDGE_API_URL   — API 地址，默认 http://localhost:8000
  MYKNOWLEDGE_PROJECT   — 当前项目名称，用于关联记忆到项目
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_URL = os.environ.get("MYKNOWLEDGE_API_URL", "http://localhost:6789")
INGEST_ENDPOINT = f"{API_URL}/api/v1/ingest"

# 从环境变量或 .claude 配置推断项目名
PROJECT_NAME = os.environ.get("MYKNOWLEDGE_PROJECT", "")


def read_hook_input() -> dict:
    """从 stdin 读取 Claude Code 传入的 JSON 数据。"""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str) -> list[dict]:
    """
    读取 Claude Code 的对话记录文件（JSONL 格式）。
    每行是一个 JSON 对象，代表一条消息。
    """
    messages = []
    path = Path(transcript_path)
    if not path.exists():
        return messages

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # 提取对话消息（过滤掉系统内部事件）
                msg_type = entry.get("type", "")
                if msg_type in ("human", "assistant"):
                    role = "user" if msg_type == "human" else "assistant"
                    content = entry.get("message", {}).get("content", "")
                    # content 可能是 string 或 list of blocks
                    if isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, str):
                                text_parts.append(block)
                            elif isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        content = "\n".join(text_parts)
                    if content:
                        messages.append({"role": role, "content": content})
            except json.JSONDecodeError:
                continue

    return messages


def detect_project_name(cwd: str) -> str:
    """
    尝试从工作目录推断项目名称。
    优先使用环境变量，其次用 git remote，最后用目录名。
    """
    if PROJECT_NAME:
        return PROJECT_NAME

    # 尝试从 git remote 获取项目名
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=cwd, timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # 从 git URL 提取项目名：git@github.com:user/repo.git -> repo
            name = url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
    except Exception:
        pass

    # 使用目录名作为 fallback
    return Path(cwd).name


def send_to_api(session_id: str, project_name: str, messages: list[dict]) -> bool:
    """将对话发送到 myknowledge API 的 ingest endpoint。"""
    if not messages:
        return False

    payload = json.dumps({
        "session_id": session_id,
        "project_name": project_name or None,
        "messages": messages,
        "metadata": {
            "source": "claude-code-hook",
            "hook_event": "Stop",
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        INGEST_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            # 输出到 stderr（Claude Code 在 verbose 模式下会显示）
            print(
                f"[myknowledge] Conversation ingested: {result.get('conversation_id', 'unknown')}",
                file=sys.stderr,
            )
            return True
    except urllib.error.URLError as e:
        print(f"[myknowledge] API unreachable: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[myknowledge] Ingest failed: {e}", file=sys.stderr)
        return False


def main():
    hook_input = read_hook_input()

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())

    # 读取对话记录
    if not transcript_path:
        print("[myknowledge] No transcript_path in hook input, skipping.", file=sys.stderr)
        sys.exit(0)

    messages = read_transcript(transcript_path)
    if not messages:
        print("[myknowledge] No messages found in transcript, skipping.", file=sys.stderr)
        sys.exit(0)

    # 过滤太短的对话（< 3 轮），通常没有有价值的知识
    if len(messages) < 3:
        print(f"[myknowledge] Conversation too short ({len(messages)} messages), skipping.", file=sys.stderr)
        sys.exit(0)

    # 推断项目名
    project_name = detect_project_name(cwd)

    # 发送到 API
    send_to_api(session_id, project_name, messages)

    # 正常退出，不阻断 Claude Code 流程
    sys.exit(0)


if __name__ == "__main__":
    main()
