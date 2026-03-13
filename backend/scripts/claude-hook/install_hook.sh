#!/bin/bash
#
# Install rememberit Claude Code hook
#
# Usage:
#   ./scripts/install_hook.sh
#
# What it does:
#   1. Writes the Stop hook config into ~/.claude/settings.json
#   2. Sets execute permission on claude_hook.py
#
# Environment variables (optional):
#   REMEMBERIT_API_URL  — API address, default http://localhost:6789
#   REMEMBERIT_PROJECT  — Default project name (auto-detected from git if not set)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/claude_hook.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "=== rememberit Hook Installer ==="
echo ""

# Ensure hook script is executable
chmod +x "$HOOK_SCRIPT"

# Ensure ~/.claude directory exists
mkdir -p "$HOME/.claude"

# Read or create settings.json
if [ -f "$SETTINGS_FILE" ]; then
    EXISTING=$(cat "$SETTINGS_FILE")
else
    EXISTING="{}"
fi

# Check if already installed
if echo "$EXISTING" | grep -q "claude_hook.py"; then
    echo "Hook already installed in $SETTINGS_FILE"
    echo "To reinstall, remove the existing hook config first."
    exit 0
fi

# Build hook command
HOOK_CMD="python3 $HOOK_SCRIPT"

# Update claude_hook_config.json with the actual path
CONFIG_JSON="$SCRIPT_DIR/claude_hook_config.json"
python3 -c "
import json
config = {
    'hooks': {
        'Stop': [{
            'matcher': '',
            'hooks': [{
                'type': 'command',
                'command': '$HOOK_CMD',
                'async': True
            }]
        }]
    }
}
with open('$CONFIG_JSON', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
print(f'Config updated: $CONFIG_JSON')
"

# Merge config into settings.json using Python (avoids jq dependency)
python3 -c "
import json, sys

settings_file = '$SETTINGS_FILE'
hook_cmd = '$HOOK_CMD'

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# Ensure hooks structure exists
if 'hooks' not in settings:
    settings['hooks'] = {}

# Add Stop hook
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
echo "  export REMEMBERIT_API_URL=http://localhost:6789"
echo "  export REMEMBERIT_PROJECT=your-project-name"
echo ""
echo "To verify, run: claude /hooks"
echo "You should see the Stop hook listed under [User]."