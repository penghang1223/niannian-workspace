/**
 * 任务自动拆分器 - ClawTeam 改进 Phase 1
 * 
 * 功能：使用 LLM 自动分析主人任务，拆分为子任务 + 依赖关系
 * 输出：JSON 格式任务计划
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:13
 */

const AVAILABLE_AGENTS = [
  { id: 'main', name: '年年', role: '团队领导/协调员' },
  { id: 'product_manager', name: '娜尔', role: '产品经理' },
  { id: 'dev_engineer', name: '开发工程师', role: '后端开发' },
  { id: 'qa_engineer', name: '本尔', role: '测试工程师' },
  { id: 'frontend_dev', name: '夕尔', role: '前端开发' },
  { id: 'chief_cute_officer', name: '岁岁', role: '首席可爱官/内容官' },
  { id: 'taiyi', name: '太一', role: '架构师' },
  { id: 'lingxi', name: '灵犀', role: '策略顾问' },
  { id: 'jinghong', name: '惊鸿', role: '文案/翰林' },
  { id: 'tiangong', name: '天工', role: '首席架构师/工部' },
  { id: 'zhiming', name: '执明', role: '协调员' },
  { id: 'yueying', name: '月影', role: '映像/分析' },
  { id: 'shichen', name: '司辰', role: '时间管理' }
];

/**
 * 分析并拆分任务
 * @param {string} userInput - 主人输入的任务描述
 * @returns {Promise<Object>} 任务计划 JSON
 */
async function analyzeAndSplitTask(userInput) {
  const prompt = `
你是一个专业的多 Agent 系统任务规划师。请将用户的任务拆分为可执行的子任务。

## 可用 Agent 列表
${AVAILABLE_AGENTS.map(a => `- ${a.id}(${a.name}): ${a.role}`).join('\n')}

## 任务拆分要求
1. 将任务拆分为独立的子任务
2. 为每个子任务分配最合适的 Agent
3. 标注任务依赖关系（哪些任务需要先完成）
4. 估算每个任务的耗时（分钟）
5. 标注优先级（P0-紧急，P1-重要，P2-一般）

## 用户任务
${userInput}

## 输出格式（严格 JSON）
{
  "summary": "任务总体描述",
  "estimatedTotalTime": 总耗时（分钟）,
  "tasks": [
    {
      "id": "T1",
      "desc": "任务描述",
      "agent": "agent_id",
      "deps": [],
      "priority": "P0",
      "estimatedMinutes": 30
    }
  ]
}

注意：
- deps 数组包含依赖的任务 ID
- 第一个任务 deps 必须为空数组
- 确保依赖关系合理（不能循环依赖）
`;

  try {
    // 调用 LLM 进行分析
    const llmResponse = await callLLM(prompt);
    const plan = JSON.parse(llmResponse);
    
    // 验证任务计划
    validateTaskPlan(plan);
    
    console.log('✅ 任务拆分完成:', plan.summary);
    console.log('📊 子任务数量:', plan.tasks.length);
    console.log('⏱️ 预计总耗时:', plan.estimatedTotalTime, '分钟');
    
    return plan;
  } catch (error) {
    console.error('❌ 任务拆分失败:', error.message);
    throw new Error(`任务拆分失败：${error.message}`);
  }
}

/**
 * 验证任务计划的有效性
 */
function validateTaskPlan(plan) {
  if (!plan.tasks || !Array.isArray(plan.tasks)) {
    throw new Error('任务计划格式错误：缺少 tasks 数组');
  }
  
  const taskIds = new Set(plan.tasks.map(t => t.id));
  
  // 检查依赖关系
  for (const task of plan.tasks) {
    if (!task.id) throw new Error('任务缺少 id');
    if (!task.desc) throw new Error(`任务 ${task.id} 缺少描述`);
    if (!task.agent) throw new Error(`任务 ${task.id} 未分配 Agent`);
    
    // 检查依赖的任务是否存在
    for (const dep of task.deps) {
      if (!taskIds.has(dep)) {
        throw new Error(`任务 ${task.id} 依赖不存在的任务：${dep}`);
      }
    }
    
    // 检查 Agent 是否存在
    const agent = AVAILABLE_AGENTS.find(a => a.id === task.agent);
    if (!agent) {
      throw new Error(`任务 ${task.id} 分配了不存在的 Agent: ${task.agent}`);
    }
  }
  
  // 检查循环依赖
  detectCircularDependency(plan.tasks);
}

/**
 * 检测循环依赖
 */
function detectCircularDependency(tasks) {
  const visited = new Set();
  const recursionStack = new Set();
  
  function hasCycle(taskId) {
    if (recursionStack.has(taskId)) return true;
    if (visited.has(taskId)) return false;
    
    visited.add(taskId);
    recursionStack.add(taskId);
    
    const task = tasks.find(t => t.id === taskId);
    if (task) {
      for (const dep of task.deps) {
        if (hasCycle(dep)) return true;
      }
    }
    
    recursionStack.delete(taskId);
    return false;
  }
  
  for (const task of tasks) {
    if (hasCycle(task.id)) {
      throw new Error('检测到循环依赖！');
    }
  }
}

/**
 * 调用 LLM（占位符，实际使用 openclaw 的 LLM 调用）
 */
async function callLLM(prompt) {
  // TODO: 集成到 openclaw 的 LLM 调用
  // 这里使用 sessions_spawn 调用子 agent 进行分析
  return new Promise((resolve, reject) => {
    // 模拟 LLM 响应（开发时测试用）
    setTimeout(() => {
      resolve(JSON.stringify({
        summary: "模拟响应",
        estimatedTotalTime: 60,
        tasks: []
      }));
    }, 100);
  });
}

/**
 * 获取可并行执行的任务组
 * @param {Array} tasks - 任务列表
 * @returns {Array<Array>} 任务组，每组可并行执行
 */
function getParallelTaskGroups(tasks) {
  const completed = new Set();
  const pending = [...tasks];
  const groups = [];
  
  while (pending.length > 0) {
    // 找出所有可执行的任务（依赖已满足）
    const ready = pending.filter(task => 
      task.deps.every(dep => completed.has(dep))
    );
    
    if (ready.length === 0) {
      throw new Error('任务依赖错误：无法找到可执行的任务');
    }
    
    groups.push(ready);
    
    // 标记为已完成
    ready.forEach(task => {
      completed.add(task.id);
      const index = pending.findIndex(t => t.id === task.id);
      pending.splice(index, 1);
    });
  }
  
  return groups;
}

module.exports = {
  analyzeAndSplitTask,
  validateTaskPlan,
  getParallelTaskGroups,
  AVAILABLE_AGENTS
};
