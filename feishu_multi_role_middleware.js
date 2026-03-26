/**
 * OpenClaw 多角色系统 - 飞书插件扩展
 * 
 * 功能：
 * 1. 在飞书消息处理前注入用户上下文
 * 2. 群聊机器人调度（superMan 群专用）
 * 集成方式：作为 OpenClaw 的中间件使用
 */

const path = require('path');

// 引入多角色集成模块
const { integration } = require('./openclaw_multi_role');

// 引入群聊机器人调度器
const FeishuGroupBotScheduler = require('./feishu_group_bot_scheduler');

class FeishuMultiRoleMiddleware {
    constructor() {
        this.enabled = true;
        this.debugMode = false;
        this.scheduler = new FeishuGroupBotScheduler();
        console.log('[FeishuMultiRole] 中间件初始化完成');
        console.log('[FeishuMultiRole] 群聊机器人调度器已加载');
    }
    
    /**
     * 启用中间件
     */
    enable() {
        this.enabled = true;
        console.log('[FeishuMultiRole] 中间件已启用');
    }
    
    /**
     * 禁用中间件
     */
    disable() {
        this.enabled = false;
        console.log('[FeishuMultiRole] 中间件已禁用');
    }
    
    /**
     * 启用调试模式
     */
    enableDebug() {
        this.debugMode = true;
        integration.enableDebug();
    }
    
    /**
     * 禁用调试模式
     */
    disableDebug() {
        this.debugMode = false;
        integration.disableDebug();
    }
    
    /**
     * 处理飞书消息（在发送给 LLM 之前）
     * 
     * @param {object} event - 飞书消息事件
     * @param {string} event.sender.open_id - 发送者 ID
     * @param {string} event.message.text - 消息文本
     * @param {string} event.chat.chat_id - 群聊 ID（如果是群聊）
     * @returns {Promise<object>} 处理结果
     */
    async handleMessage(event) {
        if (!this.enabled) {
            return { success: false, skipped: true, reason: '中间件已禁用' };
        }
        
        try {
            const userId = event.sender?.open_id || event.sender?.user_id;
            const message = event.message?.text || event.message?.content?.text || '';
            const chatId = event.chat?.chat_id || event.message?.chat_id || null;
            const isGroupChat = chatId && chatId.startsWith('oc_');
            
            if (!userId) {
                console.warn('[FeishuMultiRole] 无法获取用户 ID');
                return { success: false, error: '无法获取用户 ID' };
            }
            
            if (this.debugMode) {
                console.log(`[FeishuMultiRole] 处理消息 - 用户：${userId}, 群聊：${isGroupChat}, 消息：${message.substring(0, 50)}`);
            }
            
            // 🎯 群聊消息处理：检查是否是机器人调度指令
            if (isGroupChat && chatId === 'oc_4d0e8f8d370221837d57f0f1cb7578c3') {
                const scheduleResult = await this.scheduler.handleGroupMessage(userId, message, chatId);
                
                if (scheduleResult.success) {
                    // 调度成功，记录子代理以便后续汇报
                    if (scheduleResult.subagentKey) {
                        this.pendingSubagents = this.pendingSubagents || {};
                        this.pendingSubagents[scheduleResult.subagentKey] = {
                            command: scheduleResult.command,
                            groupId: chatId,
                            createdAt: Date.now()
                        };
                        console.log(`[FeishuMultiRole] 子代理已创建，等待完成汇报：${scheduleResult.subagentKey}`);
                    }
                    // 返回拦截标志，不再继续处理
                    return { 
                        success: true, 
                        intercepted: true, 
                        reason: '群聊机器人调度',
                        subagentKey: scheduleResult.subagentKey
                    };
                }
            }
            
            // 普通消息处理：调用多角色集成
            const result = await integration.handleMessage(userId, message);
            
            if (!result.success) {
                console.error(`[FeishuMultiRole] 处理失败：${result.error}`);
                return { success: false, error: result.error };
            }
            
            if (this.debugMode) {
                console.log(`[FeishuMultiRole] 处理成功 - Prompt 长度：${result.prompt?.length}`);
            }
            
            return result;
            
        } catch (error) {
            console.error(`[FeishuMultiRole] 异常：${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 保存对话到记忆
     * 
     * @param {string} userId 
     * @param {string} message 
     * @param {string} response 
     */
    saveToMemory(userId, message, response) {
        if (!this.enabled) return;
        integration.saveToMemory(userId, message, response);
    }
    
    /**
     * 获取系统状态
     */
    getStatus() {
        return integration.getStatus();
    }
    
    /**
     * 子代理完成后的汇报处理
     * @param {string} subagentKey - 子代理会话 key
     * @param {object} result - 子代理执行结果
     */
    async onSubagentComplete(subagentKey, result) {
        if (!this.pendingSubagents || !this.pendingSubagents[subagentKey]) {
            return; // 不是群聊调度的子代理
        }
        
        const task = this.pendingSubagents[subagentKey];
        const targetGroupId = task.groupId || task.currentChatId;
        
        console.log(`[FeishuMultiRole] 子代理完成汇报：${subagentKey}`);
        console.log(`[FeishuMultiRole] 汇报到群聊：${targetGroupId}`);
        
        if (!targetGroupId) {
            console.error('[FeishuMultiRole] 错误：未找到目标群聊 ID');
            return;
        }
        
        try {
            // 在正确的群里汇报结果
            await this.scheduler.reportCompletion(targetGroupId, task.command, result);
            
            // 清理记录
            delete this.pendingSubagents[subagentKey];
            
        } catch (error) {
            console.error(`[FeishuMultiRole] 汇报失败：${error.message}`);
        }
    }
}

// 导出单例
const middleware = new FeishuMultiRoleMiddleware();

module.exports = {
    FeishuMultiRoleMiddleware,
    middleware,
    
    // 快捷方法
    handleMessage: (event) => middleware.handleMessage(event),
    saveToMemory: (userId, message, response) => middleware.saveToMemory(userId, message, response),
    enable: () => middleware.enable(),
    disable: () => middleware.disable(),
    enableDebug: () => middleware.enableDebug(),
    disableDebug: () => middleware.disableDebug(),
    getStatus: () => middleware.getStatus(),
    onSubagentComplete: (subagentKey, result) => middleware.onSubagentComplete(subagentKey, result)
};
