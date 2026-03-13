#!/bin/bash
#
# Uninstall rememberit launchd service
#

set -e

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/dev.jwfing.rememberit.plist"

echo "=== Uninstalling rememberit service ==="

# Stop and unload (also clean up old split services if they exist)
launchctl unload "$PLIST" 2>/dev/null && echo "Unloaded: rememberit" || echo "Service not loaded"
launchctl unload "$PLIST_DIR/dev.jwfing.rememberit.api.plist" 2>/dev/null || true
launchctl unload "$PLIST_DIR/dev.jwfing.rememberit.mcp.plist" 2>/dev/null || true

# Remove plist files
rm -f "$PLIST"
rm -f "$PLIST_DIR/dev.jwfing.rememberit.api.plist"
rm -f "$PLIST_DIR/dev.jwfing.rememberit.mcp.plist"

echo ""
echo "Service removed. Log files retained at ~/Library/Logs/rememberit/"
echo "To also remove logs: rm -rf ~/Library/Logs/rememberit"