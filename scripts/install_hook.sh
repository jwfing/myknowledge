#!/bin/bash
#
# 安装 myknowledge Claude Code hook
#
# 使用方式:
#   ./scripts/install_hook.sh
#
# 做了什么:
#   1. 将 Stop hook 配置写入 ~/.claude/settings.json
#   2. 设置 claude_hook.py 的执行权限
#
# 环境变量 (可选):
#   MYKNOWLEDGE_API_URL  — API 地址，默认 http://localhost:8000
#   MYKNOWLEDGE_PROJECT  — 默认项目名（不设则自动从 git 推断）
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/claude_hook.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "=== myknowledge Hook Installer ==="
echo ""

# 确保 hook 脚本可执行
chmod +x "$HOOK_SCRIPT"

# 确保 ~/.claude 目录存在
mkdir -p "$HOME/.claude"

# 读取或创建 settings.json
if [ -f "$SETTINGS_FILE" ]; then
    EXISTING=$(cat "$SETTINGS_FILE")
else
    EXISTING="{}"
fi

# 检查是否已经安装过
if echo "$EXISTING" | grep -q "claude_hook.py"; then
    echo "Hook already installed in $SETTINGS_FILE"
    echo "To reinstall, remove the existing hook config first."
    exit 0
fi

# 构建 hook 命令
HOOK_CMD="python3 $HOOK_SCRIPT"

# 用 python 合并配置（避免 jq 依赖）
python3 -c "
import json, sys

settings_file = '$SETTINGS_FILE'
hook_cmd = '$HOOK_CMD'

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# 确保 hooks 结构存在
if 'hooks' not in settings:
    settings['hooks'] = {}

# 添加 Stop hook
stop_hooks = settings['hooks'].get('Stop', [])

new_hook_entry = {
    'matcher': '',
    'hooks': [
        {
            'type': 'command',
            'command': hook_cmd,
            'async': True
        }
    ]
}
stop_hooks.append(new_hook_entry)
settings['hooks']['Stop'] = stop_hooks

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print(f'Hook config written to {settings_file}')
"

echo ""
echo "Installation complete!"
echo ""
echo "Hook script: $HOOK_SCRIPT"
echo "Config file: $SETTINGS_FILE"
echo ""
echo "Optional environment variables (add to your shell profile):"
echo "  export MYKNOWLEDGE_API_URL=http://localhost:6789"
echo "  export MYKNOWLEDGE_PROJECT=your-project-name"
echo ""
echo "To verify, run: claude /hooks"
echo "You should see the Stop hook listed under [User]."
