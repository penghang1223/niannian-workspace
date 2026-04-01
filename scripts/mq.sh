#!/bin/bash
# ============================================================
# Agent 消息队列工具 - 简化的消息发送/接收脚本
# 用于 Agent 间通过文件系统通信
# ============================================================

set -e

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
INBOX="$WORKSPACE/inbox"
OUTBOX="$WORKSPACE/outbox"
TASKS="$WORKSPACE/tasks"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "用法: mq.sh <command> [options]"
    echo ""
    echo "命令:"
    echo "  send <to> <type> <summary>     发送消息到inbox"
    echo "  list [status]                  列出消息 (pending/done/all)"
    echo "  read <task_id>                 读取消息详情"
    echo "  process <task_id>              标记消息为处理中"
    echo "  done <task_id> [summary]       标记消息为已完成"
    echo "  claim <agent_id>               Agent领取outbox中的任务"
    echo "  status <task_id>               查看任务状态"
    echo "  cleanup [days]                 清理旧消息（默认30天）"
    echo ""
    echo "示例:"
    echo "  mq.sh send main task_completed '登录API已完成'"
    echo "  mq.sh list pending"
    echo "  mq.sh done task-20260401-001 '已确认并归档'"
}

# 生成任务ID
gen_task_id() {
    local date=$(date +%Y%m%d)
    local counter=1
    while [ -f "$INBOX/pending/task-${date}-${counter}.json" ] || \
          [ -f "$INBOX/processing/task-${date}-${counter}.json" ] || \
          [ -f "$INBOX/done/task-${date}-${counter}.json" ]; do
        counter=$((counter + 1))
    done
    echo "task-${date}-${counter}"
}

# 发送消息
cmd_send() {
    local to="${1:?需要指定目标 (to)}"
    local type="${2:?需要指定类型 (type)}"
    local summary="${3:?需要指定摘要}"
    local task_id=$(gen_task_id)
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S+08:00")
    local from="${AGENT_ID:-unknown}"

    local msg_file="$INBOX/pending/${task_id}.json"
    python3 -c "
import json, sys
msg = {
    'id': '${task_id}',
    'from': '${from}',
    'to': '${to}',
    'type': '${type}',
    'timestamp': '${timestamp}',
    'status': 'pending',
    'result': {
        'summary': sys.argv[1],
        'files': [],
        'test_status': 'unknown'
    }
}
with open('${msg_file}', 'w') as f:
    json.dump(msg, f, indent=2, ensure_ascii=False)
" "$summary"
    echo -e "${GREEN}✅ 消息已发送: ${task_id}${NC}"
    echo "   文件: ${msg_file}"
}

# 列出消息
cmd_list() {
    local status="${1:-all}"
    local count=0

    echo -e "${BLUE}📬 消息列表 (${status})${NC}"
    echo "─────────────────────────────────────"

    if [ "$status" = "all" ] || [ "$status" = "pending" ]; then
        shopt -s nullglob
        for f in "$INBOX/pending/"*.json; do
            [ -f "$f" ] || continue
            local id=$(python3 -c "import json; print(json.load(open('$f'))['id'])" 2>/dev/null || basename "$f" .json)
            local from=$(python3 -c "import json; print(json.load(open('$f'))['from'])" 2>/dev/null || echo "?")
            local summary=$(python3 -c "import json; print(json.load(open('$f'))['result']['summary'])" 2>/dev/null || echo "?")
            echo -e "  ${YELLOW}[pending]${NC} ${id} (${from}) - ${summary}"
            count=$((count + 1))
        done
        shopt -u nullglob
    fi

    if [ "$status" = "all" ] || [ "$status" = "processing" ]; then
        shopt -s nullglob
        for f in "$INBOX/processing/"*.json; do
            [ -f "$f" ] || continue
            local id=$(python3 -c "import json; print(json.load(open('$f'))['id'])" 2>/dev/null || basename "$f" .json)
            local from=$(python3 -c "import json; print(json.load(open('$f'))['from'])" 2>/dev/null || echo "?")
            local summary=$(python3 -c "import json; print(json.load(open('$f'))['result']['summary'])" 2>/dev/null || echo "?")
            echo -e "  ${BLUE}[processing]${NC} ${id} (${from}) - ${summary}"
            count=$((count + 1))
        done
        shopt -u nullglob
    fi

    if [ "$status" = "all" ] || [ "$status" = "done" ]; then
        shopt -s nullglob
        for f in "$INBOX/done/"*.json; do
            [ -f "$f" ] || continue
            local id=$(python3 -c "import json; print(json.load(open('$f'))['id'])" 2>/dev/null || basename "$f" .json)
            local from=$(python3 -c "import json; print(json.load(open('$f'))['from'])" 2>/dev/null || echo "?")
            local summary=$(python3 -c "import json; print(json.load(open('$f'))['result']['summary'])" 2>/dev/null || echo "?")
            echo -e "  ${GREEN}[done]${NC} ${id} (${from}) - ${summary}"
            count=$((count + 1))
        done
        shopt -u nullglob
    fi

    echo "─────────────────────────────────────"
    echo "共 ${count} 条消息"
}

# 读取消息
cmd_read() {
    local task_id="${1:?需要指定task_id}"
    local found=false

    for dir in pending processing done; do
        local file="$INBOX/$dir/${task_id}.json"
        if [ -f "$file" ]; then
            echo -e "${BLUE}📄 消息详情 (${dir})${NC}"
            cat "$file" | python3 -m json.tool
            found=true
            break
        fi
    done

    if [ "$found" = false ]; then
        echo -e "${RED}❌ 未找到消息: ${task_id}${NC}"
        return 1
    fi
}

# 标记为处理中
cmd_process() {
    local task_id="${1:?需要指定task_id}"
    local src="$INBOX/pending/${task_id}.json"
    local dst="$INBOX/processing/${task_id}.json"

    if [ -f "$src" ]; then
        mv "$src" "$dst"
        echo -e "${YELLOW}⏳ 消息标记为处理中: ${task_id}${NC}"
    else
        echo -e "${RED}❌ 消息不在pending状态: ${task_id}${NC}"
        return 1
    fi
}

# 标记为已完成
cmd_done() {
    local task_id="${1:?需要指定task_id}"
    local summary="${2:-已处理}"

    for dir in pending processing; do
        local src="$INBOX/$dir/${task_id}.json"
        local dst="$INBOX/done/${task_id}.json"
        if [ -f "$src" ]; then
            # 更新状态
            python3 -c "
import json
with open('$src') as f:
    data = json.load(f)
data['status'] = 'completed'
data['result']['summary'] = '$summary'
with open('$dst', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
" 2>/dev/null
            rm "$src"
            echo -e "${GREEN}✅ 消息标记为已完成: ${task_id}${NC}"
            return 0
        fi
    done

    echo -e "${RED}❌ 未找到消息: ${task_id}${NC}"
    return 1
}

# Agent领取任务
cmd_claim() {
    local agent_id="${1:?需要指定agent_id}"
    local claimed=0

    shopt -s nullglob
    for f in "$OUTBOX/pending/"*.json; do
        [ -f "$f" ] || continue
        local target=$(python3 -c "import json; print(json.load(open('$f')).get('to', ''))" 2>/dev/null || echo "")
        if [ "$target" = "$agent_id" ] || [ "$target" = "all" ]; then
            local task_id=$(basename "$f" .json)
            mv "$f" "$OUTBOX/done/${task_id}.json"
            echo -e "${GREEN}📥 已领取任务: ${task_id}${NC}"
            cat "$OUTBOX/done/${task_id}.json" | python3 -m json.tool
            claimed=$((claimed + 1))
        fi
    done
    shopt -u nullglob

    if [ $claimed -eq 0 ]; then
        echo "📭 没有待领取的任务"
    fi
}

# 查看任务状态
cmd_status() {
    local task_id="${1:?需要指定task_id}"

    # 检查 tasks 目录
    if [ -f "$TASKS/${task_id}.json" ]; then
        cat "$TASKS/${task_id}.json" | python3 -m json.tool
        return 0
    fi

    # 检查 inbox
    for dir in pending processing done; do
        if [ -f "$INBOX/$dir/${task_id}.json" ]; then
            echo "状态: $dir"
            cat "$INBOX/$dir/${task_id}.json" | python3 -m json.tool
            return 0
        fi
    done

    echo -e "${RED}❌ 未找到任务: ${task_id}${NC}"
    return 1
}

# 清理旧消息
cmd_cleanup() {
    local days="${1:-30}"
    local count=0

    echo "🧹 清理 ${days} 天前的已完成消息..."

    find "$INBOX/done" -name "*.json" -mtime +"$days" -type f | while read f; do
        local archive_dir="$WORKSPACE/archive/$(date -r "$f" +%Y-%m)"
        mkdir -p "$archive_dir"
        mv "$f" "$archive_dir/"
        count=$((count + 1))
    done

    find "$OUTBOX/done" -name "*.json" -mtime +"$days" -type f | while read f; do
        local archive_dir="$WORKSPACE/archive/$(date -r "$f" +%Y-%m)"
        mkdir -p "$archive_dir"
        mv "$f" "$archive_dir/"
        count=$((count + 1))
    done

    echo "✅ 清理完成，归档了 ${count} 条消息"
}

# 主入口
case "${1:-help}" in
    send)     shift; cmd_send "$@" ;;
    list)     shift; cmd_list "$@" ;;
    read)     shift; cmd_read "$@" ;;
    process)  shift; cmd_process "$@" ;;
    done)     shift; cmd_done "$@" ;;
    claim)    shift; cmd_claim "$@" ;;
    status)   shift; cmd_status "$@" ;;
    cleanup)  shift; cmd_cleanup "$@" ;;
    help|*)   usage ;;
esac
