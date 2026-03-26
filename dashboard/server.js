/**
 * 多角色 AI 助理管理系统 - Dashboard 后端
 * 
 * 功能：
 * - 查看内测用户列表
 * - 批准配对请求
 * - 查看用户配置
 * - 发送邀请消息
 * - 监控系统状态
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3456;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 引入多角色系统
const { integration } = require('../openclaw_multi_role');

// API: 获取系统状态
app.get('/api/status', (req, res) => {
    try {
        const status = integration.getStatus();
        res.json({
            success: true,
            data: status
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取内测用户列表
app.get('/api/beta-users', (req, res) => {
    try {
        const users = integration.getBetaUsers();
        const allUsers = integration.engine.getAllUsers();
        
        const userList = users.map(userId => ({
            userId,
            config: allUsers[userId] || null,
            isActivated: !!allUsers[userId]
        }));
        
        res.json({
            success: true,
            data: userList
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 添加内测用户
app.post('/api/beta-users', (req, res) => {
    try {
        const { userId } = req.body;
        
        if (!userId) {
            return res.status(400).json({
                success: false,
                error: '缺少用户 ID'
            });
        }
        
        const result = integration.addBetaUser(userId);
        
        res.json({
            success: result.success,
            data: result,
            message: result.success ? '添加成功' : result.error || result.message
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取配对请求列表
app.get('/api/pairing-requests', (req, res) => {
    try {
        const pairingPath = path.join(process.env.HOME, '.openclaw', 'credentials', 'feishu-pairing.json');
        
        if (!fs.existsSync(pairingPath)) {
            return res.json({
                success: true,
                data: []
            });
        }
        
        const pairingData = JSON.parse(fs.readFileSync(pairingPath, 'utf8'));
        res.json({
            success: true,
            data: pairingData.requests || []
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 批准配对
app.post('/api/pairing/approve', (req, res) => {
    try {
        const { userId, code } = req.body;
        
        if (!userId || !code) {
            return res.status(400).json({
                success: false,
                error: '缺少参数'
            });
        }
        
        const pairingPath = path.join(process.env.HOME, '.openclaw', 'credentials', 'feishu-pairing.json');
        
        if (!fs.existsSync(pairingPath)) {
            return res.status(404).json({
                success: false,
                error: '配对文件不存在'
            });
        }
        
        const pairingData = JSON.parse(fs.readFileSync(pairingPath, 'utf8'));
        const request = pairingData.requests.find(r => r.code === code && r.id === userId);
        
        if (!request) {
            return res.status(404).json({
                success: false,
                error: '未找到配对请求'
            });
        }
        
        request.approvedAt = new Date().toISOString();
        request.status = 'approved';
        
        fs.writeFileSync(pairingPath, JSON.stringify(pairingData, null, 2));
        
        res.json({
            success: true,
            message: '配对已批准'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取用户配置
app.get('/api/users/:userId/config', (req, res) => {
    try {
        const { userId } = req.params;
        const config = integration.getUserConfig(userId);
        
        if (!config) {
            return res.json({
                success: true,
                data: null,
                message: '用户配置不存在'
            });
        }
        
        res.json({
            success: true,
            data: config
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 更新用户配置
app.put('/api/users/:userId/config', (req, res) => {
    try {
        const { userId } = req.params;
        const updates = req.body;
        
        const result = integration.updateUserConfig(userId, updates);
        
        res.json({
            success: result.success,
            data: result,
            message: result.success ? '配置已更新' : result.error
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 发送内测邀请
app.post('/api/invite', (req, res) => {
    try {
        const { userId } = req.body;
        
        if (!userId) {
            return res.status(400).json({
                success: false,
                error: '缺少用户 ID'
            });
        }
        
        // 先添加到白名单
        const addResult = integration.addBetaUser(userId);
        
        if (!addResult.success) {
            return res.json({
                success: false,
                error: addResult.error || addResult.message
            });
        }
        
        res.json({
            success: true,
            message: '邀请已发送',
            data: addResult
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取记忆文件列表
app.get('/api/memories', (req, res) => {
    try {
        const memoryDir = path.join(process.env.HOME, '.openclaw', 'workspace', 'memory');
        
        if (!fs.existsSync(memoryDir)) {
            return res.json({
                success: true,
                data: []
            });
        }
        
        const files = fs.readdirSync(memoryDir)
            .filter(f => f.startsWith('memory_ou_') && f.endsWith('.md'))
            .map(f => ({
                filename: f,
                userId: f.replace('memory_', '').replace('.md', ''),
                size: fs.statSync(path.join(memoryDir, f)).size
            }));
        
        res.json({
            success: true,
            data: files
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 启动服务器
app.listen(PORT, () => {
    console.log('🎭 多角色 AI 助理 Dashboard');
    console.log('='.repeat(50));
    console.log(`服务器运行在：http://localhost:${PORT}`);
    console.log('');
    console.log('API 端点:');
    console.log(`  GET  /api/status           - 系统状态`);
    console.log(`  GET  /api/beta-users       - 内测用户列表`);
    console.log(`  POST /api/beta-users       - 添加内测用户`);
    console.log(`  GET  /api/pairing-requests - 配对请求列表`);
    console.log(`  POST /api/pairing/approve  - 批准配对`);
    console.log(`  GET  /api/users/:id/config - 用户配置`);
    console.log(`  PUT  /api/users/:id/config - 更新配置`);
    console.log(`  POST /api/invite           - 发送邀请`);
    console.log(`  GET  /api/memories         - 记忆文件列表`);
    console.log('='.repeat(50));
});
