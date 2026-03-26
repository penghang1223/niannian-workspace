/**
 * 多角色 AI 助理管理系统 - Dashboard 后端 v2
 * 添加调用次数限制功能
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
const { integration } = require('../openclaw_multi_role_v2');
const { permissionManager } = require('../permission_manager');

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
        const allUsage = integration.getAllUsage();
        const allLimits = integration.getAllLimits();
        
        const userList = users.map(userId => ({
            userId,
            config: allUsers[userId] || null,
            usage: allUsage[userId] || null,
            limits: allLimits.users?.[userId] || allLimits[allUsers[userId]?.profile?.role] || allLimits.default,
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

// API: 添加内测用户（支持设置限制）
app.post('/api/beta-users', (req, res) => {
    try {
        const { userId, daily, hourly, perMinute } = req.body;
        
        if (!userId) {
            return res.status(400).json({
                success: false,
                error: '缺少用户 ID'
            });
        }
        
        // 添加用户到白名单
        const result = integration.addBetaUser(userId);
        
        if (!result.success) {
            return res.json({
                success: false,
                data: result,
                message: result.error || result.message
            });
        }
        
        // 如果有限制参数，设置调用限制
        if (daily || hourly || perMinute) {
            const limits = {};
            if (daily) limits.daily = parseInt(daily);
            if (hourly) limits.hourly = parseInt(hourly);
            if (perMinute) limits.perMinute = parseInt(perMinute);
            
            integration.setUserLimit(userId, limits);
            return res.json({
                success: true,
                data: { ...result, limits },
                message: '添加成功并设置限制'
            });
        }
        
        res.json({
            success: true,
            data: result,
            message: '添加成功'
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

// API: 设置用户调用限制（需要管理员权限）
app.post('/api/users/:userId/rate-limit', (req, res) => {
    try {
        const { userId } = req.params;
        const { daily, hourly, perMinute } = req.body;
        const operatorId = req.headers['x-operator-id']; // 从请求头获取操作者 ID
        
        // 验证权限
        if (operatorId && !permissionManager.canModifyRateLimit(operatorId, userId)) {
            return res.status(403).json({
                success: false,
                error: '权限不足：只有管理员可以修改其他用户的调用限制'
            });
        }
        
        if (!daily && !hourly && !perMinute) {
            return res.status(400).json({
                success: false,
                error: '至少需要一个限制参数'
            });
        }
        
        const limits = {};
        if (daily) limits.daily = parseInt(daily);
        if (hourly) limits.hourly = parseInt(hourly);
        if (perMinute) limits.perMinute = parseInt(perMinute);
        
        integration.setUserLimit(userId, limits);
        
        res.json({
            success: true,
            message: '限制已设置',
            data: limits
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 重置用户调用统计（需要管理员权限）
app.post('/api/users/:userId/reset-usage', (req, res) => {
    try {
        const { userId } = req.params;
        const operatorId = req.headers['x-operator-id']; // 从请求头获取操作者 ID
        
        // 验证权限
        if (operatorId && operatorId !== userId && !permissionManager.isAdmin(operatorId)) {
            return res.status(403).json({
                success: false,
                error: '权限不足：只有管理员可以重置其他用户的统计'
            });
        }
        
        integration.resetUserUsage(userId);
        
        res.json({
            success: true,
            message: '统计已重置'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 重置用户调用统计
app.post('/api/users/:userId/reset-usage', (req, res) => {
    try {
        const { userId } = req.params;
        
        integration.resetUserUsage(userId);
        
        res.json({
            success: true,
            message: '统计已重置'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取调用限制配置
app.get('/api/rate-limits', (req, res) => {
    try {
        const limits = integration.getAllLimits();
        res.json({
            success: true,
            data: limits
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API: 获取所有用户使用统计
app.get('/api/usage-stats', (req, res) => {
    try {
        const usage = integration.getAllUsage();
        res.json({
            success: true,
            data: usage
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
    console.log('🎭 多角色 AI 助理 Dashboard v2');
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
    console.log(`  POST /api/users/:id/rate-limit - 设置调用限制`);
    console.log(`  POST /api/users/:id/reset-usage - 重置统计`);
    console.log(`  GET  /api/rate-limits      - 限制配置`);
    console.log(`  GET  /api/usage-stats      - 使用统计`);
    console.log(`  POST /api/invite           - 发送邀请`);
    console.log(`  GET  /api/memories         - 记忆文件列表`);
    console.log('='.repeat(50));
});
