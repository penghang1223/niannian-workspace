#!/usr/bin/env node
/**
 * 飞书知识库自动备份脚本
 * 通过 OpenClaw feishu 工具递归遍历所有知识库 → 导出为 Markdown → Git 提交
 * 
 * 用法：在 OpenClaw 心跳中触发，或手动执行
 */

const fs = require('fs');
const path = require('path');

const BACKUP_DIR = '/Users/narain/.openclaw/workspace/feishu-wiki-backup';
const SPACES = [
    { id: '7617488727301524409', name: '云梦泽AIGC' },
    { id: '7612140814470253789', name: 'AI学习知识库' },
    { id: '7612357583059291336', name: 'test' }
];

function safeName(name) {
    return name.replace(/[\/\\:*?"<>|]/g, '_').trim();
}

function saveDoc(spaceName, pathParts, title, markdown) {
    const dir = path.join(BACKUP_DIR, safeName(spaceName), ...pathParts.map(safeName));
    fs.mkdirSync(dir, { recursive: true });
    const filePath = path.join(dir, `${safeName(title)}.md`);
    fs.writeFileSync(filePath, markdown, 'utf8');
    return filePath;
}

function saveManifest(spaceName, nodes) {
    const manifest = {
        space: spaceName,
        backup_time: new Date().toISOString(),
        nodes: nodes.map(n => ({
            title: n.title,
            node_token: n.node_token,
            obj_token: n.obj_token,
            obj_type: n.obj_type,
            has_child: n.has_child
        }))
    };
    const filePath = path.join(BACKUP_DIR, safeName(spaceName), '_manifest.json');
    fs.writeFileSync(filePath, JSON.stringify(manifest, null, 2), 'utf8');
}

// 导出供 OpenClaw 调用的辅助函数
module.exports = { safeName, saveDoc, saveManifest, BACKUP_DIR, SPACES };
console.log('📚 飞书知识库备份模块已加载');
console.log(`   备份目录: ${BACKUP_DIR}`);
console.log(`   知识库数量: ${SPACES.length}`);
