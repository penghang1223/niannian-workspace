/**
 * Git Worktree Phase 2 测试
 */

const {
  worktreeManager,
  createAllAgentWorktrees
} = require('./git_worktree_manager');

const {
  createAgentWorkspace
} = require('./agent_workspace');

/**
 * 测试 worktree 创建
 */
async function testCreateWorktree() {
  console.log('\n🧪 测试 Worktree 创建...\n');
  
  const agentId = 'dev_engineer';
  const taskId = 'TEST-' + Date.now();
  
  try {
    console.log('创建 worktree...');
    const result = await worktreeManager.createWorktree(agentId, taskId);
    
    console.log('✅ 创建成功');
    console.log('Agent:', result.agentId);
    console.log('Task:', result.taskId);
    console.log('Branch:', result.branch);
    console.log('Path:', result.path);
    
    // 验证路径存在
    const fs = require('fs');
    if (fs.existsSync(result.path)) {
      console.log('✅ 路径验证通过');
    } else {
      throw new Error('路径不存在');
    }
    
    // 清理
    console.log('\n清理 worktree...');
    await worktreeManager.removeWorktree(agentId, taskId);
    console.log('✅ 清理成功');
    
    return true;
    
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    return false;
  }
}

/**
 * 测试 Agent 工作区
 */
async function testAgentWorkspace() {
  console.log('\n🧪 测试 Agent 工作区...\n');
  
  const agentId = 'test_agent';
  const taskId = 'TEST-' + Date.now();
  
  try {
    const workspace = createAgentWorkspace(agentId);
    
    // 初始化
    console.log('初始化工作区...');
    await workspace.initialize(taskId);
    
    console.log('工作区路径:', workspace.worktreePath);
    
    // Git 操作测试
    console.log('\n测试 Git 操作...');
    
    // 获取当前分支
    const branch = await workspace.getCurrentBranch();
    console.log('当前分支:', branch);
    
    // 创建测试文件
    const fs = require('fs');
    const testFile = workspace.worktreePath + '/test_file.txt';
    fs.writeFileSync(testFile, 'Test content');
    console.log('创建测试文件:', testFile);
    
    // Git 提交
    console.log('\n测试 Git 提交...');
    const commitResult = await workspace.commit('Test commit');
    console.log('提交结果:', commitResult);
    
    // 获取提交历史
    console.log('\n获取提交历史...');
    const history = await workspace.getCommitHistory(5);
    console.log('提交历史:', history);
    
    // 清理
    console.log('\n清理工作区...');
    await workspace.cleanup();
    console.log('✅ 清理成功');
    
    return true;
    
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    console.error(error.stack);
    return false;
  }
}

/**
 * 测试批量创建
 */
async function testBulkCreate() {
  console.log('\n🧪 测试批量创建 Agent worktrees...\n');
  
  try {
    const results = await createAllAgentWorktrees();
    
    console.log('创建结果:');
    results.forEach(result => {
      if (result.success) {
        console.log(`  ✅ ${result.agentId}: ${result.path}`);
      } else {
        console.log(`  ❌ ${result.agentId}: ${result.error}`);
      }
    });
    
    // 列出所有 worktrees
    console.log('\n列出所有 worktrees...');
    const list = await worktreeManager.listWorktrees();
    console.log('记录数:', list.records.length);
    console.log('Git 列表:', list.gitList);
    
    return true;
    
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    return false;
  }
}

/**
 * 测试清理功能
 */
async function testCleanup() {
  console.log('\n🧪 测试清理功能...\n');
  
  try {
    const result = await worktreeManager.cleanupOldWorktrees(0);
    console.log('清理结果:', result);
    return true;
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    return false;
  }
}

/**
 * 运行所有测试
 */
async function runAllTests() {
  console.log('🚀 开始运行 Git Worktree Phase 2 测试套件\n');
  console.log('='.repeat(60));
  
  const results = {
    createWorktree: await testCreateWorktree(),
    agentWorkspace: await testAgentWorkspace(),
    bulkCreate: await testBulkCreate(),
    cleanup: await testCleanup()
  };
  
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 测试结果汇总:\n');
  
  const passed = Object.values(results).filter(r => r).length;
  const total = Object.values(results).length;
  
  console.log(`通过：${passed}/${total}`);
  
  for (const [name, result] of Object.entries(results)) {
    console.log(`  ${result ? '✅' : '❌'} ${name}`);
  }
  
  if (passed === total) {
    console.log('\n🎉 所有测试通过！\n');
  } else {
    console.log('\n⚠️ 部分测试失败\n');
  }
}

// 运行测试
runAllTests().catch(console.error);
