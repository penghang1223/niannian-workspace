/**
 * ClawTeam 改进集成入口 - Phase 1
 * 
 * 整合任务拆分器、并行执行引擎、通信协议
 * 提供统一的 API 接口
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:30
 */

const taskSplitter = require('./task_splitter');
const parallelExecutor = require('./parallel_executor');
const protocol = require('./agent_protocol');

/**
 * ClawTeam 改进系统主类
 */
class ClawTeamEnhancement {
  constructor(options = {}) {
    this.options = {
      enableAutoSplit: true,
      enableParallelExec: true,
      enableStructuredComm: true,
      maxRetries: 3,
      ...options
    };
    
    this.messageLog = [];
    this.taskHistory = [];
    
    console.log('🎉 ClawTeam 增强系统已初始化！');
    console.log('📦 功能:', this.options);
  }
  
  /**
   * 处理主人任务（完整流程）
   */
  async handleUserTask(userInput) {
    console.log('\n🚀 开始处理主人任务:', userInput.substring(0, 100) + '...');
    
    const startTime = Date.now();
    
    try {
      // Step 1: 自动任务拆分
      console.log('\n📝 Step 1: 自动任务拆分...');
      const taskPlan = await taskSplitter.analyzeAndSplitTask(userInput);
      
      // Step 2: 并行执行
      console.log('\n⚡ Step 2: 并行执行任务...');
      const executionResults = await parallelExecutor.executeTaskPlan(
        taskPlan,
        this.executeTask.bind(this)
      );
      
      // Step 3: 生成报告
      console.log('\n📊 Step 3: 生成执行报告...');
      const report = parallelExecutor.generateExecutionReport(executionResults);
      
      const totalDuration = Date.now() - startTime;
      
      console.log('\n✅ 任务处理完成！');
      console.log('⏱️ 总耗时:', totalDuration, 'ms');
      
      return {
        success: true,
        taskPlan,
        executionResults,
        report,
        totalDuration
      };
      
    } catch (error) {
      console.error('❌ 任务处理失败:', error.message);
      
      return {
        success: false,
        error: error.message,
        totalDuration: Date.now() - startTime
      };
    }
  }
  
  /**
   * 执行单个任务（调用 sessions_send）
   */
  async executeTask(agentId, message) {
    console.log(`  📤 发送任务给 ${agentId}...`);
    
    // 构建结构化消息
    const agentMessage = protocol.buildAgentMessage({
      from: 'main',
      to: agentId,
      type: protocol.MessageType.TASK_ASSIGN,
      taskId: 'TASK-' + Date.now(),
      data: {
        content: message
      }
    });
    
    // 记录消息
    this.messageLog.push({
      direction: 'outbound',
      message: agentMessage,
      timestamp: Date.now()
    });
    
    // TODO: 实际调用 sessions_send
    // const response = await sessions_send({
    //   agentId,
    //   message: protocol.formatMessageForHuman(agentMessage)
    // });
    
    // 模拟响应（开发测试用）
    const response = {
      success: true,
      agentId,
      receivedAt: Date.now()
    };
    
    console.log(`  ✅ ${agentId} 已接收任务`);
    
    return response;
  }
  
  /**
   * 获取消息日志
   */
  getMessageLog() {
    return this.messageLog;
  }
  
  /**
   * 获取任务历史
   */
  getTaskHistory() {
    return this.taskHistory;
  }
  
  /**
   * 导出消息日志
   */
  exportMessageLog(filePath) {
    // TODO: 写入文件
    console.log('📥 导出消息日志到:', filePath);
    return this.messageLog;
  }
}

/**
 * 创建 ClawTeam 增强系统实例
 */
function createClawTeamEnhancement(options) {
  return new ClawTeamEnhancement(options);
}

/**
 * 快速处理任务（一行代码调用）
 */
async function quickHandleTask(userInput) {
  const clawteam = createClawTeamEnhancement();
  return await clawteam.handleUserTask(userInput);
}

// 导出
module.exports = {
  ClawTeamEnhancement,
  createClawTeamEnhancement,
  quickHandleTask,
  taskSplitter,
  parallelExecutor,
  protocol
};
