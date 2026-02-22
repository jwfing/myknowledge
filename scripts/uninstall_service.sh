#!/bin/bash
#
# 卸载 myknowledge launchd 服务
#

set -e

PLIST_DIR="$HOME/Library/LaunchAgents"
API_PLIST="$PLIST_DIR/dev.jwfing.myknowledge.api.plist"
MCP_PLIST="$PLIST_DIR/dev.jwfing.myknowledge.mcp.plist"

echo "=== Uninstalling myknowledge services ==="

# 停止并卸载
launchctl unload "$API_PLIST" 2>/dev/null && echo "Unloaded: API Server" || echo "API Server not loaded"
launchctl unload "$MCP_PLIST" 2>/dev/null && echo "Unloaded: MCP Server" || echo "MCP Server not loaded"

# 删除 plist 文件
rm -f "$API_PLIST" "$MCP_PLIST"

echo ""
echo "Services removed. Log files retained at ~/Library/Logs/myknowledge/"
echo "To also remove logs: rm -rf ~/Library/Logs/myknowledge"
