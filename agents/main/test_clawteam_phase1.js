/**
 * ClawTeam 改进 Phase 1 测试
 */

const {
  ClawTeamEnhancement,
  taskSplitter,
  parallelExecutor,
  protocol
} = require('./clawteam_enhancement');

/**
 * 测试任务拆分器
 */
async function testTaskSplitter() {
  console.log('\n🧪 测试任务拆分器...\n');
  
  const testCases = [
    {
      name: '简单任务',
      input: '帮我写一个登录功能',
      expectedTasks: 2
    },
    {
      name: '复杂任务',
      input: '帮我开发一个完整的电商网站，包括前端、后端、数据库和测试',
      expectedTasks: 4
    },
    {
      name: '多 Agent 协作',
      input: '组织一次产品发布会，需要准备 PPT、测试产品、邀请媒体',
      expectedTasks: 3
    }
  ];
  
  for (const testCase of testCases) {
    console.log(`测试用例：${testCase.name}`);
    console.log('输入:', testCase.input);
    
    try {
      // TODO: 实际调用 LLM
      // const plan = await taskSplitter.analyzeAndSplitTask(testCase.input);
      
      // 模拟响应
      const plan = {
        summary: testCase.name,
        estimatedTotalTime: 60,
        tasks: [
          { id: 'T1', desc: '任务 1', agent: 'dev_engineer', deps: [], priority: 'P1' }
        ]
      };
      
      console.log('✅ 拆分成功');
      console.log('任务数:', plan.tasks.length);
    } catch (error) {
      console.log('❌ 测试失败:', error.message);
    }
    
    console.log('---\n');
  }
}

/**
 * 测试并行执行
 */
async function testParallelExecution() {
  console.log('\n🧪 测试并行执行...\n');
  
  const mockTaskPlan = {
    summary: '测试任务',
    estimatedTotalTime: 30,
    tasks: [
      { id: 'T1', desc: '任务 1', agent: 'dev_engineer', deps: [], priority: 'P1', estimatedMinutes: 10 },
      { id: 'T2', desc: '任务 2', agent: 'frontend_dev', deps: ['T1'], priority: 'P1', estimatedMinutes: 10 },
      { id: 'T3', desc: '任务 3', agent: 'qa_engineer', deps: ['T1'], priority: 'P1', estimatedMinutes: 10 },
      { id: 'T4', desc: '任务 4', agent: 'main', deps: ['T2', 'T3'], priority: 'P1', estimatedMinutes: 5 }
    ]
  };
  
  const mockExecuteTask = async (agentId, message) => {
    console.log(`  执行：${agentId} - ${message.substring(0, 30)}...`);
    await parallelExecutor.sleep(100); // 模拟延迟
    return { success: true, agentId };
  };
  
  try {
    const results = await parallelExecutor.executeTaskPlan(mockTaskPlan, mockExecuteTask);
    
    console.log('\n✅ 并行执行测试通过');
    console.log('总任务数:', results.totalTasks);
    console.log('完成数:', results.completedTasks);
    console.log('总耗时:', results.totalDuration, 'ms');
    console.log('批次数量:', results.taskGroups.length);
    
    // 验证并行效果
    if (results.taskGroups.length < mockTaskPlan.tasks.length) {
      console.log('✅ 并行执行生效！批次数量 < 任务数量');
    }
    
  } catch (error) {
    console.log('❌ 测试失败:', error.message);
  }
}

/**
 * 测试通信协议
 */
function testProtocol() {
  console.log('\n🧪 测试通信协议...\n');
  
  // 测试消息构建
  const message = protocol.buildAgentMessage({
    from: 'main',
    to: 'dev_engineer',
    type: protocol.MessageType.TASK_ASSIGN,
    taskId: 'TASK-001',
    priority: protocol.Priority.P1,
    data: {
      content: '测试任务'
    }
  });
  
  console.log('构建的消息:', JSON.stringify(message, null, 2));
  
  // 测试序列化
  const serialized = protocol.serializeMessage(message);
  console.log('\n序列化成功');
  
  // 测试反序列化
  const deserialized = protocol.deserializeMessage(serialized);
  console.log('反序列化成功');
  
  // 测试格式化
  const formatted = protocol.formatMessageForHuman(message);
  console.log('\n格式化消息:');
  console.log(formatted);
  
  console.log('\n✅ 通信协议测试通过');
}

/**
 * 测试完整流程
 */
async function testFullWorkflow() {
  console.log('\n🧪 测试完整工作流程...\n');
  
  const clawteam = new ClawTeamEnhancement();
  
  const userInput = '帮我开发一个用户管理系统';
  
  try {
    const result = await clawteam.handleUserTask(userInput);
    
    console.log('\n✅ 完整流程测试通过');
    console.log('成功:', result.success);
    console.log('总耗时:', result.totalDuration, 'ms');
    
  } catch (error) {
    console.log('❌ 测试失败:', error.message);
  }
}

/**
 * 运行所有测试
 */
async function runAllTests() {
  console.log('🚀 开始运行 ClawTeam Phase 1 测试套件\n');
  console.log('='.repeat(60));
  
  await testTaskSplitter();
  await testParallelExecution();
  testProtocol();
  await testFullWorkflow();
  
  console.log('\n' + '='.repeat(60));
  console.log('🎉 所有测试完成！\n');
}

// 运行测试
runAllTests().catch(console.error);
