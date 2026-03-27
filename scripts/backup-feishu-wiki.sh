#!/bin/bash
# 飞书知识库自动备份脚本
# 用法: ./backup-feishu-wiki.sh
# 功能: 遍历所有知识库空间 → 导出文档为 Markdown → Git 提交

set -e

BACKUP_DIR="/Users/narain/.openclaw/workspace/feishu-wiki-backup"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "${BACKUP_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "=== 飞书知识库备份开始 ==="

# 检查 OpenClaw 是否可用
if ! command -v openclaw &> /dev/null; then
    log "❌ openclaw 命令不可用"
    exit 1
fi

# 备份完成后 Git 提交
git_commit() {
    cd "${BACKUP_DIR}"
    if git rev-parse --git-dir > /dev/null 2>&1; then
        git add -A
        if git diff --cached --quiet; then
            log "📝 无变更，跳过 Git 提交"
        else
            git commit -m "📚 飞书知识库备份 ${TIMESTAMP}" --quiet
            log "✅ Git 提交完成"
        fi
    else
        cd "${BACKUP_DIR}"
        git init --quiet
        git add -A
        git commit -m "📚 初始化飞书知识库备份" --quiet
        log "✅ Git 仓库初始化完成"
    fi
}

log "备份目录: ${BACKUP_DIR}"
log "提示: 此脚本需通过 OpenClaw 心跳触发（使用 feishu 工具递归遍历）"
log "=== 备份脚本就绪 ==="

# Git 提交（如果有变更）
git_commit
