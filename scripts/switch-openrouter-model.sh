#!/bin/bash
# OpenRouter 免费模型快速切换脚本
# 用法：./switch-openrouter-model.sh <模型名>

CONFIG_FILE="$HOME/.openclaw/openclaw.json"

# 可用模型列表
declare -A MODELS=(
  ["qwen"]="openrouter/qwen/qwen3.6-plus:free"
  ["minimax"]="openrouter/minimax/minimax-m2.5:free"
  ["glm"]="openrouter/z-ai/glm-4.5-air:free"
  ["gemma"]="openrouter/google/gemma-3-27b-it:free"
  ["llama"]="openrouter/meta-llama/llama-3.3-70b-instruct:free"
)

echo "📚 OpenRouter 免费模型切换工具"
echo "================================"
echo ""

# 显示可用模型
echo "可用模型："
echo "  1) qwen    - Qwen3.6-Plus (免费，中文网文最强)"
echo "  2) minimax - MiniMax M2.5 (免费，稳定推荐)"
echo "  3) glm     - GLM-4.5-Air (免费，逻辑强)"
echo "  4) gemma   - Gemma 3 27B (免费)"
echo "  5) llama   - Llama 3.3 70B (免费)"
echo ""

if [ -z "$1" ]; then
  echo "用法：$0 <模型名>"
  echo "示例：$0 minimax"
  exit 1
fi

MODEL_KEY="$1"
MODEL_ID="${MODELS[$MODEL_KEY]}"

if [ -z "$MODEL_ID" ]; then
  echo "❌ 未知模型：$MODEL_KEY"
  echo "可用：qwen, minimax, glm, gemma, llama"
  exit 1
fi

echo "🔄 切换到模型：$MODEL_ID"

# 备份配置文件
cp "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"

# 使用 Python 更新 JSON
python3 << EOF
import json

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

# 更新默认模型
config['agents']['defaults']['model']['primary'] = '$MODEL_ID'

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 配置已更新")
EOF

echo ""
echo "📝 当前默认模型：$MODEL_ID"
echo ""
echo "💡 提示："
echo "  - 重启 OpenClaw 生效：openclaw gateway restart"
echo "  - 或在聊天中使用命令：/model $MODEL_ID"
echo ""
echo "📊 模型状态（2026-04-06）："
echo "  ✅ MiniMax M2.5 - 稳定可用"
echo "  ✅ GLM-4.5-Air - 稳定可用"
echo "  ⚠️  Qwen3.6-Plus - 可能 Rate Limit"
