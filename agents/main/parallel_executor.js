/**
 * 并行执行引擎 - ClawTeam 改进 Phase 1
 * 
 * 功能：基于 DAG 的并行执行，依赖管理，自动重试
 * 输出：任务执行结果汇总
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:20
 */

const { getParallelTaskGroups } = require('./task_splitter');

/**
 * 并行执行任务计划
 * @param {Object} taskPlan - 任务计划（来自 task_splitter）
 * @param {Function} executeTask - 执行单个任务的函数（注入 sessions_send）
 * @returns {Promise<Object>} 执行结果汇总
 */
async function executeTaskPlan(taskPlan, executeTask) {
  console.log('🚀 开始执行任务计划:', taskPlan.summary);
  console.log('📊 任务总数:', taskPlan.tasks.length);
  
  const results = {
    summary: taskPlan.summary,
    startTime: Date.now(),
    taskGroups: [],
    totalTasks: taskPlan.tasks.length,
    completedTasks: 0,
    failedTasks: 0,
    errors: []
  };
  
  // 获取可并行执行的任务组
  const taskGroups = getParallelTaskGroups(taskPlan.tasks);
  
  console.log('📦 任务分组完成，共', taskGroups.length, '个并行批次');
  
  // 逐组执行
  for (let i = 0; i < taskGroups.length; i++) {
    const group = taskGroups[i];
    console.log(`\n🔄 执行第 ${i + 1}/${taskGroups.length} 批次，任务数：${group.length}`);
    
    const groupResult = {
      batchIndex: i + 1,
      tasks: [],
      startTime: Date.now()
    };
    
    // 并行执行当前批次的所有任务
    const taskPromises = group.map(async (task) => {
      const taskResult = await executeSingleTask(task, executeTask);
      groupResult.tasks.push(taskResult);
      
      if (taskResult.success) {
        results.completedTasks++;
      } else {
        results.failedTasks++;
        results.errors.push({
          taskId: task.id,
          error: taskResult.error
        });
      }
      
      return taskResult;
    });
    
    // 等待当前批次全部完成
    await Promise.all(taskPromises);
    
    groupResult.endTime = Date.now();
    groupResult.duration = groupResult.endTime - groupResult.startTime;
    results.taskGroups.push(groupResult);
    
    console.log(`✅ 第 ${i + 1} 批次完成，耗时：${groupResult.duration}ms`);
  }
  
  results.endTime = Date.now();
  results.totalDuration = results.endTime - results.startTime;
  results.successRate = (results.completedTasks / results.totalTasks * 100).toFixed(2) + '%';
  
  console.log('\n🎉 任务计划执行完成！');
  console.log('⏱️ 总耗时:', results.totalDuration, 'ms');
  console.log('✅ 成功:', results.completedTasks, '/', results.totalTasks);
  console.log('📊 成功率:', results.successRate);
  
  return results;
}

/**
 * 执行单个任务
 */
async function executeSingleTask(task, executeTask) {
  console.log(`  📝 执行任务 ${task.id}: ${task.desc.substring(0, 50)}...`);
  
  const result = {
    taskId: task.id,
    agent: task.agent,
    desc: task.desc,
    startTime: Date.now(),
    success: false,
    error: null,
    responseData: null
  };
  
  try {
    // 构建任务消息
    const message = buildTaskMessage(task);
    
    // 执行任务（调用 sessions_send 或其他执行函数）
    const response = await executeTask(task.agent, message);
    
    result.success = true;
    result.responseData = response;
    result.endTime = Date.now();
    result.duration = result.endTime - result.startTime;
    
    console.log(`  ✅ 任务 ${task.id} 完成，耗时：${result.duration}ms`);
  } catch (error) {
    result.success = false;
    result.error = error.message;
    result.endTime = Date.now();
    result.duration = result.endTime - result.startTime;
    
    console.error(`  ❌ 任务 ${task.id} 失败:`, error.message);
  }
  
  return result;
}

/**
 * 构建任务消息
 */
function buildTaskMessage(task) {
  return `
📋 **新任务分配**

**任务 ID**: ${task.id}
**优先级**: ${task.priority || 'P1'}
**任务描述**: ${task.desc}

请开始执行，完成后回复结果。
`.trim();
}

/**
 * 重试执行（可选功能）
 */
async function executeWithRetry(task, executeTask, maxRetries = 3) {
  let lastError = null;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await executeSingleTask(task, executeTask);
      if (result.success) {
        return result;
      }
      lastError = result.error;
    } catch (error) {
      lastError = error.message;
    }
    
    console.log(`🔄 任务 ${task.id} 重试 ${i + 1}/${maxRetries}`);
    await sleep(1000 * (i + 1)); // 指数退避
  }
  
  return {
    taskId: task.id,
    success: false,
    error: `重试 ${maxRetries} 次后仍然失败：${lastError}`
  };
}

/**
 * 睡眠函数
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 生成执行报告
 */
function generateExecutionReport(results) {
  const report = {
    title: '任务执行报告',
    generatedAt: new Date().toISOString(),
    summary: results.summary,
    statistics: {
      totalTasks: results.totalTasks,
      completedTasks: results.completedTasks,
      failedTasks: results.failedTasks,
      successRate: results.successRate,
      totalDuration: results.totalDuration,
      totalDurationFormatted: formatDuration(results.totalDuration)
    },
    batchDetails: results.taskGroups.map(group => ({
      batchIndex: group.batchIndex,
      taskCount: group.tasks.length,
      duration: group.duration,
      successCount: group.tasks.filter(t => t.success).length,
      failedCount: group.tasks.filter(t => !t.success).length
    })),
    errors: results.errors.length > 0 ? results.errors : null
  };
  
  return report;
}

/**
 * 格式化持续时间
 */
function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`;
  }
  return `${seconds}秒`;
}

module.exports = {
  executeTaskPlan,
  executeSingleTask,
  executeWithRetry,
  buildTaskMessage,
  generateExecutionReport,
  sleep
};
