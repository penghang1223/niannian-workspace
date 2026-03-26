/**
 * 囡囡的记忆自动提取器
 * 
 * 功能：
 * 1. 从对话中自动识别记忆项
 * 2. 重要性评分（0-1 分）
 * 3. 分类存储（HOT/WARM/COLD）
 * 4. 冲突检测与处理
 */

const fs = require('fs');
const path = require('path');

class MemoryAutoExtract {
    constructor() {
        this.workspaceRoot = path.join(__dirname, '..');
        this.memoryDir = path.join(this.workspaceRoot, 'memory');
    }
    
    /**
     * 从对话中提取记忆
     * @param {string} message - 主人的消息
     * @returns {object|null} 提取的记忆项
     */
    extract(message) {
        // 1. 检查是否是垃圾信息
        if (this.isTrash(message)) {
            return null;
        }
        
        // 2. 识别记忆类型
        const match = this.identifyType(message);
        if (!match) {
            return null;
        }
        
        // 3. 计算重要性评分
        const importance = this.calculateImportance(message, match);
        
        // 4. 低于阈值不存储
        if (importance < 0.3) {
            return null;
        }
        
        // 5. 创建记忆项
        const memory = {
            id: this.generateId(),
            type: match.type,
            category: match.category,
            text: message.trim(),
            importance,
            storage: match.storage,
            timestamp: new Date().toISOString(),
            source: 'dialogue'
        };
        
        return memory;
    }
    
    /**
     * 检查是否是垃圾信息
     * @private
     */
    isTrash(message) {
        const trimmed = message.trim();
        if (trimmed.length < 3) return true;
        if (trimmed === 'HEARTBEAT_OK') return true;
        return false;
    }
    
    /**
     * 识别记忆类型
     * @private
     */
    identifyType(message) {
        // 偏好类
        if (message.includes('喜欢') || message.includes('不喜欢') || 
            message.includes('习惯') || message.includes('偏好')) {
            return { type: 'preference', category: 'preference', storage: 'warm', baseScore: 0.8 };
        }
        
        // 事实类
        if (message.includes('我是') || message.includes('我在') || 
            message.includes('公司是') || message.includes('职位是')) {
            return { type: 'fact', category: 'fact', storage: 'warm', baseScore: 0.9 };
        }
        
        // 决定类
        if (message.includes('决定') || message.includes('选择') || 
            message.includes('采用') || message.includes('确认')) {
            return { type: 'decision', category: 'decision', storage: 'cold', baseScore: 0.85 };
        }
        
        // 待办类
        if (message.includes('需要') || message.includes('帮我') || 
            message.includes('记得') || message.includes('提醒我')) {
            return { type: 'todo', category: 'todo', storage: 'hot', baseScore: 0.7 };
        }
        
        // 想要类
        if (message.includes('我要') || message.includes('想要')) {
            return { type: 'todo', category: 'todo', storage: 'hot', baseScore: 0.75 };
        }
        
        // 项目类
        if (message.includes('项目') || message.includes('功能') || 
            message.includes('开发') || message.includes('实现')) {
            return { type: 'project', category: 'project', storage: 'warm', baseScore: 0.75 };
        }
        
        // 知识类
        if (message.includes('学会') || message.includes('学到') || 
            message.includes('发现') || message.includes('了解')) {
            return { type: 'knowledge', category: 'knowledge', storage: 'cold', baseScore: 0.7 };
        }
        
        return null;
    }
    
    /**
     * 计算重要性评分
     * @private
     */
    calculateImportance(message, match) {
        let score = match.baseScore;
        if (message.includes('我')) score += 0.1;
        if (message.includes('一定') || message.includes('必须')) score += 0.1;
        if (/\d+/.test(message)) score += 0.05;
        if (message.length > 20) score += 0.05;
        return Math.min(1.0, score);
    }
    
    /**
     * 生成记忆 ID
     * @private
     */
    generateId() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 6);
        return `MEM-${timestamp}-${random}`;
    }
    
    /**
     * 存储记忆到对应层级
     * @param {object} memory - 记忆项
     * @returns {boolean} 是否成功
     */
    store(memory) {
        try {
            const storageFile = path.join(
                this.memoryDir,
                memory.storage === 'hot' ? 'hot/HOT_MEMORY.md' :
                memory.storage === 'warm' ? 'warm/WARM_MEMORY.md' :
                'MEMORY.md'
            );
            
            const dir = path.dirname(storageFile);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            
            let content = '';
            if (fs.existsSync(storageFile)) {
                content = fs.readFileSync(storageFile, 'utf8');
            }
            
            const memoryEntry = this.formatMemoryEntry(memory);
            content += '\n\n' + memoryEntry;
            
            fs.writeFileSync(storageFile, content, 'utf8');
            return true;
        } catch (error) {
            console.error(`[MemoryExtract] 存储失败：${error.message}`);
            return false;
        }
    }
    
    /**
     * 格式化记忆条目
     * @private
     */
    formatMemoryEntry(memory) {
        const emoji = { hot: '📌', warm: '❤️', cold: '📚' };
        const typeEmoji = {
            preference: '❤️', fact: '📝', decision: '✅',
            todo: '📌', project: '🎯', knowledge: '💡'
        };
        
        return `
---
**${emoji[memory.storage]} ${typeEmoji[memory.type]} ${memory.type.toUpperCase()}**
- **ID**: ${memory.id}
- **时间**: ${new Date(memory.timestamp).toLocaleString('zh-CN')}
- **重要性**: ${memory.importance.toFixed(2)}
- **内容**: ${memory.text}
---`.trim();
    }
}

// 导出
module.exports = MemoryAutoExtract;

// 命令行测试
if (require.main === module) {
    const extractor = new MemoryAutoExtract();
    
    const testMessages = [
        '我喜欢用中文交流',
        '我在店小秘工作',
        '我决定学习 AI',
        '帮我记得明天开会',
        '我要做个爬虫项目',
        '我学会了 Docker',
        '好的',
        'HEARTBEAT_OK'
    ];
    
    console.log('=== 记忆提取测试 ===\n');
    
    for (const message of testMessages) {
        console.log(`\n输入："${message}"`);
        const memory = extractor.extract(message);
        if (memory) {
            console.log(`✅ 提取：${memory.type} (${memory.importance.toFixed(2)}) → ${memory.storage}`);
        } else {
            console.log('❌ 未提取到记忆');
        }
    }
}
