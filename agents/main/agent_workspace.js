/**
 * Agent 工作区集成 - ClawTeam 改进 Phase 2
 * 
 * 功能：每个 Agent 自动使用独立 worktree
 * 自动切换工作区、提交代码、管理分支
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:52
 */

const { worktreeManager } = require('./git_worktree_manager');
const fs = require('fs');
const path = require('path');

/**
 * Agent 工作区管理器
 */
class AgentWorkspaceManager {
  constructor(agentId) {
    this.agentId = agentId;
    this.currentTaskId = null;
    this.worktreePath = null;
    this.initialized = false;
  }
  
  /**
   * 初始化 Agent 工作区
   */
  async initialize(taskId = 'default') {
    console.log(`🔧 初始化 Agent '${this.agentId}' 工作区...`);
    
    this.currentTaskId = taskId;
    
    // 检查 worktree 是否存在
    if (!worktreeManager.worktreeExists(this.agentId, taskId)) {
      console.log(`📦 Worktree 不存在，创建中...`);
      await worktreeManager.createWorktree(this.agentId, taskId);
    }
    
    // 获取 worktree 路径
    this.worktreePath = worktreeManager.getAgentWorktreePath(this.agentId, taskId);
    
    // 加载配置
    const configPath = path.join(this.worktreePath, 'agents', this.agentId, 'workspace_config.json');
    
    if (fs.existsSync(configPath)) {
      this.config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    }
    
    this.initialized = true;
    
    console.log(`✅ Agent '${this.agentId}' 工作区初始化完成`);
    console.log(`📂 路径：${this.worktreePath}`);
    
    return {
      success: true,
      agentId: this.agentId,
      taskId,
      worktreePath: this.worktreePath
    };
  }
  
  /**
   * 在工作区执行命令
   */
  async executeInWorktree(command) {
    if (!this.initialized) {
      throw new Error('工作区未初始化，请先调用 initialize()');
    }
    
    const { exec } = require('child_process');
    
    return new Promise((resolve, reject) => {
      exec(command, { cwd: this.worktreePath }, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr || error.message));
          return;
        }
        resolve(stdout.trim());
      });
    });
  }
  
  /**
   * Git 提交
   */
  async commit(message) {
    console.log(`💾 Git 提交：${message}`);
    
    try {
      // 添加所有更改
      await this.executeInWorktree('git add -A');
      
      // 提交
      await this.executeInWorktree(`git commit -m "${message}"`);
      
      console.log(`✅ 提交成功`);
      
      return { success: true, message };
      
    } catch (error) {
      if (error.message.includes('nothing to commit')) {
        console.log(`⚠️ 没有更改需要提交`);
        return { success: false, error: 'nothing_to_commit' };
      }
      
      console.error(`❌ 提交失败：${error.message}`);
      throw error;
    }
  }
  
  /**
   * 创建分支
   */
  async createBranch(branchName) {
    console.log(`🌿 创建分支：${branchName}`);
    
    await this.executeInWorktree(`git checkout -b ${branchName}`);
    
    console.log(`✅ 分支创建成功`);
    
    return { success: true, branch: branchName };
  }
  
  /**
   * 切换分支
   */
  async checkoutBranch(branchName) {
    console.log(`🔄 切换分支：${branchName}`);
    
    await this.executeInWorktree(`git checkout ${branchName}`);
    
    console.log(`✅ 分支切换成功`);
    
    return { success: true, branch: branchName };
  }
  
  /**
   * 合并分支
   */
  async mergeBranch(branchName) {
    console.log(`🔀 合并分支：${branchName}`);
    
    await this.executeInWorktree(`git merge ${branchName}`);
    
    console.log(`✅ 分支合并成功`);
    
    return { success: true };
  }
  
  /**
   * 获取当前分支
   */
  async getCurrentBranch() {
    const branch = await this.executeInWorktree('git rev-parse --abbrev-ref HEAD');
    return branch;
  }
  
  /**
   * 获取提交历史
   */
  async getCommitHistory(limit = 10) {
    const log = await this.executeInWorktree(`git log --oneline -${limit}`);
    return log.split('\n');
  }
  
  /**
   * 获取文件差异
   */
  async getDiff(branch1, branch2) {
    const diff = await this.executeInWorktree(`git diff ${branch1}..${branch2}`);
    return diff;
  }
  
  /**
   * 清理工作区
   */
  async cleanup() {
    console.log(`🧹 清理 Agent '${this.agentId}' 工作区...`);
    
    if (this.currentTaskId) {
      await worktreeManager.removeWorktree(this.agentId, this.currentTaskId);
    }
    
    this.initialized = false;
    this.worktreePath = null;
    this.currentTaskId = null;
    
    console.log(`✅ 工作区清理完成`);
  }
}

/**
 * 创建 Agent 工作区管理器
 */
function createAgentWorkspace(agentId) {
  return new AgentWorkspaceManager(agentId);
}

/**
 * 快速在工作区执行代码
 */
async function runInWorkspace(agentId, taskId, code) {
  const workspace = createAgentWorkspace(agentId);
  
  try {
    await workspace.initialize(taskId);
    
    // 执行代码（这里可以是任何操作）
    const result = await code(workspace);
    
    // 自动提交
    await workspace.commit(`Auto-commit: ${taskId}`);
    
    return result;
    
  } finally {
    // 可选：清理或保留工作区
    // await workspace.cleanup();
  }
}

module.exports = {
  AgentWorkspaceManager,
  createAgentWorkspace,
  runInWorkspace
};
