#!/bin/bash
#
# 安装 myknowledge 为 macOS launchd 服务
#
# 使用方式:
#   ./scripts/install_service.sh
#
# 安装后:
#   启动:  launchctl load ~/Library/LaunchAgents/dev.jwfing.myknowledge.*.plist
#   停止:  launchctl unload ~/Library/LaunchAgents/dev.jwfing.myknowledge.*.plist
#   日志:  tail -f ~/Library/Logs/myknowledge/*.log
#   状态:  launchctl list | grep myknowledge
#

set -e

# ── 定位项目路径 ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$(which python3)"

PLIST_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs/myknowledge"
ENV_FILE="$PROJECT_DIR/.env"

echo "=== myknowledge Service Installer ==="
echo ""
echo "Project:  $PROJECT_DIR"
echo "Python:   $PYTHON_BIN"
echo ""

# ── 前置检查 ──
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Run 'cp .env.example .env' and fill in your config first."
    exit 1
fi

# 确保目录存在
mkdir -p "$PLIST_DIR" "$LOG_DIR"

# ── 从 .env 读取端口（用于展示） ──
API_PORT=$(grep -E '^API_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "6789")
MCP_PORT=$(grep -E '^MCP_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "6788")
API_PORT="${API_PORT:-6789}"
MCP_PORT="${MCP_PORT:-6788}"

# ── 生成 API Server plist ──
API_PLIST="$PLIST_DIR/dev.jwfing.myknowledge.api.plist"
cat > "$API_PLIST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.jwfing.myknowledge.api</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>-m</string>
        <string>myknowledge</string>
        <string>api</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_DIR/src</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>5</integer>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/api.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/api.error.log</string>
</dict>
</plist>
PLIST

echo "Created: $API_PLIST"

# ── 生成 MCP Server plist ──
MCP_PLIST="$PLIST_DIR/dev.jwfing.myknowledge.mcp.plist"
cat > "$MCP_PLIST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.jwfing.myknowledge.mcp</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>-m</string>
        <string>myknowledge</string>
        <string>mcp</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_DIR/src</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>5</integer>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/mcp.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/mcp.error.log</string>
</dict>
</plist>
PLIST

echo "Created: $MCP_PLIST"

# ── 加载服务 ──
echo ""
echo "Loading services..."

# 先卸载旧的（如果存在）
launchctl unload "$API_PLIST" 2>/dev/null || true
launchctl unload "$MCP_PLIST" 2>/dev/null || true

launchctl load "$API_PLIST"
launchctl load "$MCP_PLIST"

echo ""
echo "=== Installation complete ==="
echo ""
echo "Services:"
echo "  API Server  → http://localhost:$API_PORT  (dev.jwfing.myknowledge.api)"
echo "  MCP Server  → http://localhost:$MCP_PORT  (dev.jwfing.myknowledge.mcp)"
echo ""
echo "Commands:"
echo "  状态    launchctl list | grep myknowledge"
echo "  停止    launchctl unload ~/Library/LaunchAgents/dev.jwfing.myknowledge.api.plist"
echo "          launchctl unload ~/Library/LaunchAgents/dev.jwfing.myknowledge.mcp.plist"
echo "  重启    launchctl kickstart -k gui/\$(id -u)/dev.jwfing.myknowledge.api"
echo "          launchctl kickstart -k gui/\$(id -u)/dev.jwfing.myknowledge.mcp"
echo "  日志    tail -f ~/Library/Logs/myknowledge/api.log"
echo "          tail -f ~/Library/Logs/myknowledge/mcp.log"
echo "  卸载    ./scripts/uninstall_service.sh"
