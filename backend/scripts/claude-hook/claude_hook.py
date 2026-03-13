#!/usr/bin/env python3
"""
Claude Code Hook Script — Background Path ingestion entry point

Automatically triggered at the end of each Claude Code conversation (Stop event).
Reads the full conversation transcript and sends it to the rememberit API
for knowledge extraction.

Usage:
  Configure this script as a Claude Code Stop hook.
  See claude_hook_config.json in the same directory.

Environment variables:
  REMEMBERIT_API_URL   — API address, default http://localhost:6789
  REMEMBERIT_PROJECT   — Current project name, used to associate memories with a project
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_URL = os.environ.get("REMEMBERIT_API_URL", "http://localhost:6789")
INGEST_ENDPOINT = f"{API_URL}/api/v1/ingest"

# Infer project name from environment variable or config
PROJECT_NAME = os.environ.get("REMEMBERIT_PROJECT", "")


def read_hook_input() -> dict:
    """Read JSON data passed by Claude Code via stdin."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str) -> list[dict]:
    """
    Read the Claude Code conversation transcript file (JSONL format).
    Each line is a JSON object representing a single message.
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
                # Extract conversation messages (filter out internal system events)
                msg_type = entry.get("type", "")
                if msg_type in ("human", "assistant"):
                    role = "user" if msg_type == "human" else "assistant"
                    content = entry.get("message", {}).get("content", "")
                    # content can be a string or a list of blocks
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
    Attempt to infer the project name from the working directory.
    Priority: environment variable > git remote > directory name.
    """
    if PROJECT_NAME:
        return PROJECT_NAME

    # Try to get project name from git remote
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=cwd, timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract project name from git URL: git@github.com:user/repo.git -> repo
            name = url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
    except Exception:
        pass

    # Fall back to directory name
    return Path(cwd).name


def send_to_api(session_id: str, project_name: str, messages: list[dict]) -> bool:
    """Send the conversation to the rememberit API ingest endpoint."""
    if not messages:
        return False

    payload = json.dumps({
        "session_id": session_id,
        "project_name": project_name or None,
        "messages": messages,
        "metadata": {
            "source": "claude-hook-code-hook",
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
            # Output to stderr (visible in Claude Code verbose mode)
            print(
                f"[rememberit] Conversation ingested: {result.get('conversation_id', 'unknown')}",
                file=sys.stderr,
            )
            return True
    except urllib.error.URLError as e:
        print(f"[rememberit] API unreachable: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[rememberit] Ingest failed: {e}", file=sys.stderr)
        return False


def main():
    hook_input = read_hook_input()

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())

    # Read conversation transcript
    if not transcript_path:
        print("[rememberit] No transcript_path in hook input, skipping.", file=sys.stderr)
        sys.exit(0)

    messages = read_transcript(transcript_path)
    if not messages:
        print("[rememberit] No messages found in transcript, skipping.", file=sys.stderr)
        sys.exit(0)

    # Skip short conversations (< 4 exchanges), typically not valuable
    if len(messages) < 4:
        print(f"[rememberit] Conversation too short ({len(messages)} messages), skipping.", file=sys.stderr)
        sys.exit(0)

    # Skip conversations with very little content (< 500 chars total)
    total_chars = sum(len(m.get("content", "")) for m in messages)
    if total_chars < 500:
        print(f"[rememberit] Conversation content too short ({total_chars} chars), skipping.", file=sys.stderr)
        sys.exit(0)

    # Truncate very long conversations to reduce token usage
    # Keep first 2 messages (context) + last 30 messages (most relevant work)
    MAX_MESSAGES = 32
    if len(messages) > MAX_MESSAGES:
        original_count = len(messages)
        messages = messages[:2] + messages[-(MAX_MESSAGES - 2):]
        print(f"[rememberit] Truncated {original_count} messages to {len(messages)} for cost control.", file=sys.stderr)

    # Detect project name
    project_name = detect_project_name(cwd)

    # Send to API
    send_to_api(session_id, project_name, messages)

    # Exit cleanly without blocking Claude Code
    sys.exit(0)


if __name__ == "__main__":
    main()