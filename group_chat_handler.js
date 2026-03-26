/**
 * 群聊消息处理器
 * 
 * 功能：
 * 1. 识别群聊/私聊
 * 2. 处理@消息
 * 3. 群聊记忆管理
 * 4. 群聊权限验证
 * 5. 调用限制（群聊更严格）
 */

const MultiRoleEngine = require('./multi_role_engine');
const { permissionManager } = require('./permission_manager');
const { rateLimitManager } = require('./rate_limit_manager');
const { privacyFilter } = require('./privacy_filter');

class GroupChatHandler {
    constructor() {
        this.engine = new MultiRoleEngine();
        this.groupConfigs = new Map();
        this.debugMode = false;
        
        console.log('[GroupChat] 群聊处理器初始化完成');
    }
    
    /**
     * 处理飞书消息（统一入口）
     * 
     * @param {object} event - 飞书消息事件
     * @returns {Promise<object>} 处理结果
     */
    async handleMessage(event) {
        try {
            const chatType = event.chat?.chat_type || 'direct';
            const userId = event.sender?.open_id || event.sender?.user_id;
            const message = event.message?.text || '';
            
            // 群聊处理
            if (chatType === 'group') {
                return await this._handleGroupMessage(event, userId, message);
            }
            
            // 私聊处理
            return await this._handleDirectMessage(userId, message);
            
        } catch (error) {
            console.error(`[GroupChat Error] ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * 处理群聊消息（带隐私保护）
     * @private
     */
    async _handleGroupMessage(event, userId, message) {
        const groupId = event.chat.chat_id;
        const isMentioned = this._isMessageMentioned(event);
        
        if (this.debugMode) {
            console.log(`[GroupChat] 群聊消息 - 群：${groupId}, 用户：${userId}, @囡囡：${isMentioned}`);
        }
        
        // 检查是否@囡囡
        if (!isMentioned) {
            // 未被@，忽略消息（可配置）
            return {
                success: true,
                ignored: true,
                reason: '未被@，忽略消息'
            };
        }
        
        // 检查是否涉及隐私问题
        const privacyCheck = privacyFilter.shouldAnswer(message, true);
        if (!privacyCheck.allowed) {
            console.log(`[GroupChat] 隐私保护：拦截敏感问题 - ${message}`);
            return {
                success: true,
                response: privacyFilter.generateGroupResponse(message),
                privacyProtected: true,
                reason: privacyCheck.reason
            };
        }
        
        // 验证群聊权限
        const groupPermission = await this._checkGroupPermission(groupId, userId);
        if (!groupPermission.allowed) {
            return {
                success: false,
                permissionDenied: true,
                reason: groupPermission.reason
            };
        }
        
        // 检查调用限制（群聊更严格）
        let limitCheck;
        try {
            limitCheck = rateLimitManager.checkLimit(userId);
        } catch (error) {
            // 如果限制管理器未初始化，跳过检查
            limitCheck = { allowed: true };
        }
        
        if (!limitCheck || !limitCheck.allowed) {
            return {
                success: false,
                rateLimited: true,
                reason: limitCheck?.reason || '调用限制检查失败',
                message: `抱歉，您的调用次数已超过限制。请稍后再试。`
            };
        }
        
        // 初始化用户会话
        this.engine.initSession(userId);
        
        // 生成系统 Prompt（考虑群聊上下文）
        const systemPrompt = this._generateGroupChatSystemPrompt(userId, groupId);
        
        // 注入用户消息
        const injectedPrompt = this._createInjectedPrompt(systemPrompt, message, groupId);
        
        // 记录调用
        rateLimitManager.recordUsage(userId);
        
        // 保存到群聊记忆（不保存敏感信息）
        await this._saveToGroupMemory(groupId, userId, message);
        
        return {
            success: true,
            prompt: injectedPrompt,
            systemPrompt,
            groupChat: true,
            groupId,
            userId,
            needsPrivacyFilter: true
        };
    }
    
    /**
     * 处理私聊消息
     * @private
     */
    async _handleDirectMessage(userId, message) {
        if (this.debugMode) {
            console.log(`[GroupChat] 私聊消息 - 用户：${userId}`);
        }
        
        // 检查调用限制
        const limitCheck = rateLimitManager.checkLimit(userId);
        if (!limitCheck.allowed) {
            return {
                success: false,
                rateLimited: true,
                reason: limitCheck.reason
            };
        }
        
        // 初始化用户会话
        this.engine.initSession(userId);
        
        // 生成系统 Prompt
        const systemPrompt = this.engine.generateSystemPrompt();
        
        // 注入用户消息
        const injectedPrompt = this._createInjectedPrompt(systemPrompt, message);
        
        // 记录调用
        rateLimitManager.recordUsage(userId);
        
        // 保存到私聊记忆
        await this._saveToDirectMemory(userId, message);
        
        return {
            success: true,
            prompt: injectedPrompt,
            systemPrompt,
            groupChat: false,
            userId
        };
    }
    
    /**
     * 检查消息是否@囡囡
     * @private
     */
    _isMessageMentioned(event) {
        // 检查飞书@信息
        if (event.message?.mentions) {
            const botId = this._getBotOpenId();
            return event.message.mentions.some(mention => 
                mention.id.open_id === botId || mention.id.user_id === botId
            );
        }
        
        // 检查文本中是否有@机器人
        if (event.message?.text) {
            const botName = this._getBotName();
            return event.message.text.includes(`@${botName}`);
        }
        
        return false;
    }
    
    /**
     * 获取机器人 Open ID
     * @private
     */
    _getBotOpenId() {
        // 从配置或环境变量获取
        return process.env.BOT_OPEN_ID || 'ou_bot_id';
    }
    
    /**
     * 获取机器人名字
     * @private
     */
    _getBotName() {
        return process.env.BOT_NAME || '囡囡';
    }
    
    /**
     * 检查群聊权限
     * @private
     */
    async _checkGroupPermission(groupId, userId) {
        // 检查群聊是否在白名单
        const groupConfig = this.groupConfigs.get(groupId);
        
        if (!groupConfig) {
            // 新群聊，检查是否管理员邀请
            const isAdmin = permissionManager.isAdmin(userId);
            if (!isAdmin) {
                return {
                    allowed: false,
                    reason: '该群聊未授权，需要管理员邀请'
                };
            }
            
            // 管理员邀请的群聊，自动授权
            this.groupConfigs.set(groupId, {
                authorizedBy: userId,
                authorizedAt: new Date().toISOString(),
                active: true
            });
            
            return { allowed: true };
        }
        
        if (!groupConfig.active) {
            return {
                allowed: false,
                reason: '该群聊已被禁用'
            };
        }
        
        return { allowed: true };
    }
    
    /**
     * 生成群聊系统 Prompt
     * @private
     */
    _generateGroupChatSystemPrompt(userId, groupId) {
        // 基础系统 Prompt（群聊中使用通用身份）
        let systemPrompt = `【身份设定】
• 你的名字：囡囡
• 你的身份：AI 智能助理
• 你的风格：友好、专业、简洁

【群聊上下文】
• 当前场景：群聊
• 群聊 ID：${groupId}
• 发言用户：${userId}

【隐私保护原则】🔒
• 绝不透露任何用户的个人信息
• 不提及用户姓名、公司、职位
• 不暴露用户身份特征
• 不泄露私密对话内容

【群聊行为准则】
• 只回复@自己的消息
• 保持友好、专业、简洁
• 避免过度刷屏（每分钟最多 3 条）
• 尊重群聊规则和其他成员
• 涉及隐私问题时礼貌回避`;
        
        return systemPrompt;
    }
    
    /**
     * 创建注入后的 Prompt
     * @private
     */
    _createInjectedPrompt(systemPrompt, message, groupId = null) {
        const context = groupId ? `【群聊：${groupId}】` : '【私聊】';
        
        return `${systemPrompt}

━━━━━━━━━━━━━━━━━━━━
${context}
【用户消息】
${message}`;
    }
    
    /**
     * 保存到群聊记忆
     * @private
     */
    async _saveToGroupMemory(groupId, userId, message) {
        // 群聊记忆文件：memory_group_xxx.md
        const memoryPath = `memory/memory_group_${groupId}.md`;
        
        try {
            const fs = require('fs');
            const path = require('path');
            const memoryDir = path.join(__dirname, 'memory');
            
            if (!fs.existsSync(memoryDir)) {
                fs.mkdirSync(memoryDir, { recursive: true });
            }
            
            const timestamp = new Date().toISOString();
            const logEntry = `\n---\n时间：${timestamp}\n用户：${userId}\n消息：${message}\n---\n`;
            
            fs.appendFileSync(path.join(memoryDir, `memory_group_${groupId}.md`), logEntry);
        } catch (error) {
            console.error(`[GroupChat] 保存群聊记忆失败：${error.message}`);
        }
    }
    
    /**
     * 保存到私聊记忆
     * @private
     */
    async _saveToDirectMemory(userId, message) {
        // 使用引擎的记忆保存
        this.engine.saveToMemory(userId, message, '[待补充回复]');
    }
    
    /**
     * 授权群聊
     * @param {string} groupId 
     * @param {string} adminId 
     */
    authorizeGroup(groupId, adminId) {
        if (!permissionManager.isAdmin(adminId)) {
            return {
                success: false,
                error: '只有管理员可以授权群聊'
            };
        }
        
        this.groupConfigs.set(groupId, {
            authorizedBy: adminId,
            authorizedAt: new Date().toISOString(),
            active: true
        });
        
        console.log(`[GroupChat] 群聊 ${groupId} 已授权（管理员：${adminId}）`);
        
        return { success: true };
    }
    
    /**
     * 禁用群聊
     * @param {string} groupId 
     * @param {string} adminId 
     */
    disableGroup(groupId, adminId) {
        if (!permissionManager.isAdmin(adminId)) {
            return {
                success: false,
                error: '只有管理员可以禁用群聊'
            };
        }
        
        const groupConfig = this.groupConfigs.get(groupId);
        if (groupConfig) {
            groupConfig.active = false;
            console.log(`[GroupChat] 群聊 ${groupId} 已禁用`);
        }
        
        return { success: true };
    }
    
    /**
     * 获取授权的群聊列表
     * @returns {array}
     */
    getAuthorizedGroups() {
        const groups = [];
        this.groupConfigs.forEach((config, groupId) => {
            groups.push({
                groupId,
                authorizedBy: config.authorizedBy,
                authorizedAt: config.authorizedAt,
                active: config.active
            });
        });
        return groups;
    }
    
    /**
     * 启用调试模式
     */
    enableDebug() {
        this.debugMode = true;
        console.log('[GroupChat] 调试模式已启用');
    }
    
    /**
     * 禁用调试模式
     */
    disableDebug() {
        this.debugMode = false;
        console.log('[GroupChat] 调试模式已禁用');
    }
}

// 导出单例
const groupChatHandler = new GroupChatHandler();

module.exports = {
    GroupChatHandler,
    groupChatHandler
};
