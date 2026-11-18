#!/usr/bin/env bash
# One-time setup for the /reel skill: Node packages + headless Chromium, then a check.
set -e
ENGINE="$(cd "$(dirname "$0")/../engine" && pwd)"
command -v node >/dev/null || { echo "Node.js 18+ is missing. macOS: brew install node | Windows: winget install OpenJS.NodeJS | Linux: sudo apt install nodejs npm"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing. macOS: brew install ffmpeg | Windows: winget install Gyan.FFmpeg | Linux: sudo apt install ffmpeg"; exit 1; }
PY="$(command -v python3 || command -v python)" || { echo "Python 3.9+ is missing."; exit 1; }
cd "$ENGINE"
npm install --no-fund --no-audit
npx playwright install chromium
"$PY" reel.py check
