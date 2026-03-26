#!/usr/bin/env node

/**
 * 测试群聊处理器
 */

const { groupChatHandler } = require('./group_chat_handler');

console.log('🧪 测试群聊处理器\n');
console.log('='.repeat(60));

// 测试 1：私聊消息
console.log('\n📌 测试 1: 私聊消息');
console.log('-'.repeat(60));
const directMessageEvent = {
    chat: { chat_type: 'direct' },
    sender: { open_id: 'ou_a0406c4f0dd910da73bb748272663b95' },
    message: { text: '你好囡囡' }
};

groupChatHandler.handleMessage(directMessageEvent).then(result => {
    console.log('私聊处理结果:', JSON.stringify({
        success: result.success,
        groupChat: result.groupChat,
        promptLength: result.prompt?.length
    }, null, 2));
    
    // 测试 2：群聊消息（未@）
    console.log('\n📌 测试 2: 群聊消息（未@）');
    console.log('-'.repeat(60));
    const groupMessageEvent1 = {
        chat: { 
            chat_type: 'group',
            chat_id: 'gc_test_group_001'
        },
        sender: { open_id: 'ou_a0406c4f0dd910da73bb748272663b95' },
        message: { 
            text: '今天天气不错',
            mentions: []
        }
    };
    
    groupChatHandler.handleMessage(groupMessageEvent1).then(result => {
        console.log('群聊消息（未@）结果:', JSON.stringify({
            success: result.success,
            ignored: result.ignored,
            reason: result.reason
        }, null, 2));
        
        // 测试 3：群聊消息（已@）
        console.log('\n📌 测试 3: 群聊消息（已@）');
        console.log('-'.repeat(60));
        const groupMessageEvent2 = {
            chat: { 
                chat_type: 'group',
                chat_id: 'gc_test_group_001'
            },
            sender: { open_id: 'ou_a0406c4f0dd910da73bb748272663b95' },
            message: { 
                text: '@囡囡 今天天气不错',
                mentions: [{
                    id: { open_id: 'ou_bot_id' }
                }]
            }
        };
        
        groupChatHandler.handleMessage(groupMessageEvent2).then(result => {
            console.log('群聊消息（已@）结果:', JSON.stringify({
                success: result.success,
                groupChat: result.groupChat,
                groupId: result.groupId,
                promptLength: result.prompt?.length
            }, null, 2));
            
            // 测试 4：授权群聊
            console.log('\n📌 测试 4: 授权群聊');
            console.log('-'.repeat(60));
            const authResult = groupChatHandler.authorizeGroup(
                'gc_test_group_002',
                'ou_a0406c4f0dd910da73bb748272663b95'
            );
            console.log('授权结果:', JSON.stringify(authResult, null, 2));
            
            // 测试 5：查看授权的群聊
            console.log('\n📌 测试 5: 查看授权的群聊');
            console.log('-'.repeat(60));
            const groups = groupChatHandler.getAuthorizedGroups();
            console.log('授权的群聊:', JSON.stringify(groups, null, 2));
            
            // 测试 6：禁用群聊
            console.log('\n📌 测试 6: 禁用群聊');
            console.log('-'.repeat(60));
            const disableResult = groupChatHandler.disableGroup(
                'gc_test_group_002',
                'ou_a0406c4f0dd910da73bb748272663b95'
            );
            console.log('禁用结果:', JSON.stringify(disableResult, null, 2));
            
            console.log('\n' + '='.repeat(60));
            console.log('🎉 所有测试完成！\n');
        });
    });
});
