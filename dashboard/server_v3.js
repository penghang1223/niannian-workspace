/**
 * 年年团队 Dashboard - 轻量版服务器
 * 不依赖旧版 multi_role 模块，直接读取 STATE.yaml
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 5175;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 读取 STATE.yaml（简单文本解析）
function readState() {
    try {
        const content = fs.readFileSync(path.join(__dirname, '..', 'STATE.yaml'), 'utf8');
        return content;
    } catch (e) {
        return null;
    }
}

// 读取 INSTINCTS.md
function readInstincts() {
    try {
        return fs.readFileSync(path.join(__dirname, '..', 'INSTINCTS.md'), 'utf8');
    } catch (e) {
        return null;
    }
}

// API: 健康检查
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString(), version: '3.0' });
});

// API: STATE 原始数据
app.get('/api/state', (req, res) => {
    const state = readState();
    res.json({ success: !!state, data: state });
});

// API: INSTINCTS 原始数据
app.get('/api/instincts', (req, res) => {
    const instincts = readInstincts();
    res.json({ success: !!instincts, data: instincts });
});

// 所有其他路由返回 index.html
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '127.0.0.1', () => {
    console.log(`
🎀 年年团队 Dashboard v3.0
==================================================
  地址：http://localhost:${PORT}
  状态：✅ 运行中
==================================================
`);
});
