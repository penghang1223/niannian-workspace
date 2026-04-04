#!/bin/bash

echo "=== OpenClaw Status Line Integration ==="

# 1. Backup current config
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup

# 2. Add statusLine config
python3 << 'PYTHON'
import json

with open('/Users/narain/.openclaw/openclaw.json', 'r') as f:
    config = json.load(f)

config["statusLine"] = {
    "enabled": True,
    "command": "node /Users/narain/.openclaw/workspace/openclaw-statusline/dist/openclaw-statusline.js",
    "refreshInterval": 5,
    "widgets": ["Agent", "Model", "Tokens", "Cost", "SessionClock", "GitBranch", "Project"]
}

with open('/Users/narain/.openclaw/openclaw.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Status line configuration added")
PYTHON

echo "✅ Integration complete!"
echo "Restart OpenClaw to see the status line"
