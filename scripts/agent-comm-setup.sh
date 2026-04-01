#!/bin/bash
# ============================================================
# Agent 通信机制 v2 - 初始化脚本
# 创建消息队列目录结构 + 配置超时参数
# ============================================================

set -e

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
echo "🔧 Agent 通信机制 v2 初始化"
echo "   工作目录: $WORKSPACE"

# 1. 创建消息队列目录结构
echo ""
echo "📁 创建消息队列目录..."
mkdir -p "$WORKSPACE/inbox/pending"
mkdir -p "$WORKSPACE/inbox/processing"
mkdir -p "$WORKSPACE/inbox/done"
mkdir -p "$WORKSPACE/outbox/pending"
mkdir -p "$WORKSPACE/outbox/done"
mkdir -p "$WORKSPACE/tasks"
mkdir -p "$WORKSPACE/archive"

# 2. 创建 .gitkeep 文件确保空目录被git跟踪
for dir in inbox/pending inbox/processing inbox/done outbox/pending outbox/done tasks archive; do
    touch "$WORKSPACE/$dir/.gitkeep"
done

# 3. 创建 README 文件说明目录用途
cat > "$WORKSPACE/inbox/README.md" << 'EOF'
# Inbox - Agent 消息接收队列

## 目录结构
- `pending/` - 待处理消息
- `processing/` - 处理中消息
- `done/` - 已完成消息

## 消息格式
每个消息是一个 JSON 文件，格式见 `AGENT_COMM_V2_DESIGN.md`

## 处理流程
1. Agent 完成任务 → 写入 `pending/{task_id}.json`
2. 年年心跳检查 → 移动到 `processing/`
3. 处理完成 → 移动到 `done/`
4. 定期清理 → 归档到 `archive/`
EOF

cat > "$WORKSPACE/outbox/README.md" << 'EOF'
# Outbox - 年年指令发送队列

## 目录结构
- `pending/` - 待分发指令
- `done/` - 已分发指令

## 指令格式
每个指令是一个 JSON 文件，格式与 inbox 类似但 from=main

## 分发流程
1. 年年写入指令 → `pending/{task_id}.json`
2. 子Agent心跳 → 检查并读取
3. 执行完成 → 移动到 `done/`
EOF

cat > "$WORKSPACE/tasks/README.md" << 'EOF'
# Tasks - 任务状态跟踪

每个任务一个 JSON 文件，包含完整的任务生命周期信息。
与 inbox/ 配合使用，提供更详细的任务状态。
EOF

# 4. 配置超时参数
echo ""
echo "⚙️  配置超时参数..."
openclaw config set agents.defaults.subagents.runTimeoutSeconds 1800 2>/dev/null && echo "   ✅ 子Agent超时: 1800s (30分钟)" || echo "   ⚠️  无法设置子Agent超时（可能需要手动配置）"
openclaw config set agents.defaults.maxConcurrent 6 2>/dev/null && echo "   ✅ 主Agent并发: 6" || echo "   ⚠️  无法设置主Agent并发"
openclaw config set agents.defaults.subagents.maxConcurrent 12 2>/dev/null && echo "   ✅ 子Agent并发: 12" || echo "   ⚠️  无法设置子Agent并发"

# 5. 创建消息处理模板
cat > "$WORKSPACE/inbox/TEMPLATE.json" << 'EOF'
{
  "id": "task-YYYYMMDD-NNN",
  "from": "agent_id",
  "to": "main",
  "type": "task_completed|task_failed|request|notification",
  "timestamp": "ISO-8601",
  "status": "completed|failed|pending",
  "task": {
    "name": "任务名称",
    "wave": 1,
    "acceptance_criteria": ["AC-1"]
  },
  "result": {
    "summary": "完成摘要",
    "files": ["相关文件路径"],
    "test_status": "all_passed|partial|failed"
  },
  "metadata": {
    "session_key": "agent:main:subagent:xxx",
    "duration_seconds": 180,
    "tokens_used": 45000
  }
}
EOF

# 6. 验证
echo ""
echo "✅ 初始化完成！"
echo ""
echo "📊 目录结构:"
find "$WORKSPACE/inbox" "$WORKSPACE/outbox" "$WORKSPACE/tasks" "$WORKSPACE/archive" -type f | head -20
echo ""
echo "📋 下一步:"
echo "   1. 更新 AGENTS.md 的分发原则"
echo "   2. 更新 HEARTBEAT.md 添加消息检查"
echo "   3. 测试 sessions_spawn 通信"
echo ""
echo "📖 详细设计: $WORKSPACE/AGENT_COMM_V2_DESIGN.md"
