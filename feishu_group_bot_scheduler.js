/**
 * 飞书群聊机器人调度器
 * 
 * 功能：
 * 1. 在飞书群聊中识别主人指令
 * 2. 调用对应的机器人账号创建子代理
 * 3. 完成后在群里汇报结果
 * 
 * 使用场景：
 * 主人在 superMan 群里：@囡囡 安排产品经理写 PRD
 * → 囡囡识别指令
 * → 用 product_manager bot 创建子代理
 * → 完成后在群里回复
 */

const { sessions_spawn, message } = require('openclaw-tools');

class FeishuGroupBotScheduler {
    constructor() {
        // 机器人映射
        this.botMapping = {
            '产品经理': 'product_manager',
            '开发工程师': 'dev_engineer',
            '开发': 'dev_engineer',
            '测试工程师': 'qa_engineer',
            '测试': 'qa_engineer',
            '前端设计师': 'frontend_dev',
            '前端': 'frontend_dev',
            '囡囡': 'main'
        };
        
        // superMan 群 ID
        this.superManGroupId = 'oc_4d0e8f8d370221837d57f0f1cb7578c3';
        
        // 飞书账号配置
        this.feishuAccounts = {
            'main': { appId: 'cli_a92842babb389ccd' },
            'product_manager': { appId: 'cli_a92f041773a15cd9' },
            'dev_engineer': { appId: 'cli_a928eda8d5bbdbcc' },
            'qa_engineer': { appId: 'cli_a92efa839cf8dcbb' },
            'frontend_dev': { appId: 'cli_a92a29cc7cb8dcba' }
        };
        
        console.log('[FeishuGroupBotScheduler] 初始化完成');
    }
    
    /**
     * 处理群聊消息
     * @param {string} userId - 发送者 ID
     * @param {string} message - 消息内容
     * @param {string} groupId - 群聊 ID
     * @returns {Promise<object>} 处理结果
     */
    async handleGroupMessage(userId, message, groupId) {
        // 检查是否是 superMan 群
        if (groupId !== this.superManGroupId) {
            return { success: false, reason: '非授权群聊' };
        }
        
        // 检查是否是主人
        if (!this.isOwner(userId)) {
            return { success: false, reason: '非授权用户' };
        }
        
        // 解析指令
        const command = this.parseCommand(message);
        if (!command) {
            return { success: false, reason: '无法识别的指令' };
        }
        
        console.log(`[调度器] 识别到指令：${command.type} -> ${command.task}`);
        
        // 创建子代理
        return await this.spawnSubagent(command, groupId);
    }
    
    /**
     * 检查是否是主人
     */
    isOwner(userId) {
        // 主人的飞书 open_id
        const ownerIds = [
            'ou_2d3aeca8b8ff0aa238124692e10936d6', // 彭航
            'ou_a0406c4f0dd910da73bb748272663b95'  // 主人
        ];
        return ownerIds.includes(userId);
    }
    
    /**
     * 解析指令
     * 支持格式：
     * - "@囡囡 安排产品经理写 PRD"
     * - "@囡囡 让开发写个接口"
     * - "@囡囡 让测试写用例"
     */
    parseCommand(message) {
        // 移除@提及
        const cleanMessage = message.replace(/@囡囡/g, '').trim();
        
        // 匹配模式
        const patterns = [
            {
                regex: /安排 (\w+) (.+)/,
                type: 'arrange',
                extract: (match) => ({ bot: match[1], task: match[2] })
            },
            {
                regex: /让 (\w+) (.+)/,
                type: 'assign',
                extract: (match) => ({ bot: match[1], task: match[2] })
            },
            {
                regex: /(\w+) 机器人 (.+)/,
                type: 'direct',
                extract: (match) => ({ bot: match[1], task: match[2] })
            }
        ];
        
        for (const pattern of patterns) {
            const match = cleanMessage.match(pattern.regex);
            if (match) {
                const extracted = pattern.extract(match);
                const botKey = this.normalizeBotName(extracted.bot);
                const botAccount = this.botMapping[botKey];
                
                if (botAccount) {
                    return {
                        type: pattern.type,
                        bot: botAccount,
                        botName: botKey,
                        task: extracted.task,
                        originalMessage: cleanMessage
                    };
                }
            }
        }
        
        return null;
    }
    
    /**
     * 标准化机器人名称
     */
    normalizeBotName(name) {
        const mapping = {
            '产品': '产品经理',
            '开发': '开发工程师',
            '测试': '测试工程师',
            '囡囡': '囡囡'
        };
        return mapping[name] || name;
    }
    
    /**
     * 创建子代理
     */
    async spawnSubagent(command, groupId) {
        try {
            // 发送确认消息
            await this.sendGroupMessage(groupId, `🎯 收到！正在安排${command.botName}机器人处理...`);
            
            // 创建子代理，传递 chat_id 上下文
            const result = await sessions_spawn({
                agentId: command.bot,
                task: this.buildTaskPrompt(command, groupId),
                mode: 'run',
                runtime: 'subagent',
                timeoutSeconds: 300,
                label: `${command.botName}-${Date.now()}`
            });
            
            console.log(`[调度器] 子代理创建成功：${result.childSessionKey}`);
            
            // 等待完成并汇报（带上 groupId）
            return {
                success: true,
                subagentKey: result.childSessionKey,
                command: command,
                willReportToGroup: groupId,  // 关键：确保汇报到正确的群
                currentChatId: groupId       // 传递当前聊天 ID
            };
            
        } catch (error) {
            console.error(`[调度器] 创建子代理失败：${error.message}`);
            await this.sendGroupMessage(groupId, `❌ 安排失败：${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 构建任务 Prompt
     */
    buildTaskPrompt(command, groupId) {
        // 添加聊天上下文指令
        const contextInstruction = `

📍 **重要回复规则**：
- 你正在群聊中工作，群聊 ID：${groupId}
- 所有回复必须发送到**当前群聊**，不允许发送到其他聊天窗口
- 使用 OpenClaw message 工具发送消息时，target 参数设置为：${groupId}
- 私聊消息发送到私聊窗口，群聊消息发送到群聊窗口，不允许回复错位置！

`;
        
        const taskTemplates = {
            'product_manager': `你是一位资深产品经理，请完成以下任务：${command.task}

请用专业的方式完成，并在完成后提供清晰的总结。`,
            
            'dev_engineer': `你是一位资深开发工程师，请完成以下任务：${command.task}

请用专业的方式完成，并在完成后提供清晰的总结。`,
            
            'qa_engineer': `你是一位资深测试工程师，请完成以下任务：${command.task}

请用专业的方式完成，并在完成后提供清晰的总结。`
        };
        
        return (taskTemplates[command.bot] || `请完成以下任务：${command.task}`) + contextInstruction;
    }
    
    /**
     * 发送群消息
     */
    async sendGroupMessage(groupId, text) {
        try {
            await message.send({
                action: 'send',
                target: groupId,
                message: text
            });
            console.log(`[调度器] 群消息发送成功：${groupId}`);
            return { success: true };
        } catch (error) {
            console.error(`[调度器] 群消息发送失败：${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 子代理完成后汇报
     */
    async reportCompletion(groupId, command, result) {
        try {
            // 1. 先发送机器人汇报
            const botReport = this.formatReport(command, result);
            await this.sendGroupMessage(groupId, botReport);
            
            // 等待 2 秒再发囡囡的总结
            await this.sleep(2000);
            
            // 2. 发送囡囡的总结汇报
            const nannanSummary = this.formatNannanSummary(command, result, botReport);
            await this.sendGroupMessage(groupId, nannanSummary);
            
            console.log(`[调度器] 完成汇报已发送到群：${groupId}`);
            return { success: true };
            
        } catch (error) {
            console.error(`[调度器] 汇报发送失败：${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 休眠辅助方法
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 格式化汇报消息
     */
    formatReport(command, result) {
        // 主人的飞书 open_id，用于@提及
        const ownerOpenId = 'ou_2d3aeca8b8ff0aa238124692e10936d6';
        
        return `✅ **${command.botName}机器人**完成任务！

📋 **任务**：${command.task}

📄 **结果**：
${result.summary || '任务已完成，详情请查看文件输出。'}

📁 **输出文件**：
${result.files ? result.files.join('\n') : '无文件输出'}

---
🎀 囡囡：主人，还有其他任务要安排吗？`;
    }
    
    /**
     * 格式化囡囡的总结汇报
     */
    formatNannanSummary(command, result, botReport) {
        return `🎀 **囡囡的任务完成总结**

━━━━━━━━━━━━━━━━━━━━
✅ **执行机器人**：${command.botName}
📝 **任务内容**：${command.task}
⏱️ **完成时间**：${new Date().toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai'})}
━━━━━━━━━━━━━━━━━━━━

📊 **任务详情**：
${result.summary || '任务已顺利完成'}

📁 **产出文件**：
${result.files && result.files.length > 0 ? result.files.map(f => `• ${f}`).join('\n') : '• 无文件产出'}

💡 **囡囡的建议**：
• 如需修改或补充，随时吩咐囡囡
• 可以继续安排其他机器人干活
• 囡囡会持续跟踪任务进度

━━━━━━━━━━━━━━━━━━━━
🎀 囡囡随时待命，主人请吩咐～
`;
    }
}

module.exports = FeishuGroupBotScheduler;
