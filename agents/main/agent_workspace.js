/**
 * Agent 工作区集成 - ClawTeam 改进 Phase 2
 * 
 * 功能：每个 Agent 自动使用独立 worktree
 * 自动切换工作区、提交代码、管理分支
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:52
 * @security 2026-03-31 天工：exec→execFile 消除命令注入（OWASP A05）
 */

const { execFile } = require('child_process');
const { worktreeManager } = require('./git_worktree_manager');
const fs = require('fs');
const path = require('path');

/**
 * 安全执行命令
 * Why: execFile 不经过 shell 解释，参数作为数组传递，消除命令注入风险。
 * 对比：exec(command) 会将整个字符串传给 /bin/sh -c，攻击者可通过
 *       "git commit -m \"legit\"; rm -rf /" 注入任意命令。
 * @param {string} file - 可执行文件路径
 * @param {string[]} args - 参数数组（每个参数独立传递，不被 shell 解释）
 * @param {string} cwd - 工作目录
 * @returns {Promise<string>} stdout
 */
function safeExec(file, args, cwd) {
  return new Promise((resolve, reject) => {
    execFile(file, args, { cwd }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(stderr || error.message));
        return;
      }
      resolve(stdout.trim());
    });
  });
}

/**
 * 校验分支名（防命令注入 + 防非法 git 引用）
 * Why: 分支名可能来自外部输入，必须限制为安全字符集。
 */
function validateBranchName(name) {
  if (typeof name !== 'string' || !/^[a-zA-Z0-9_\-./]+$/.test(name)) {
    throw new Error(`非法分支名: "${name}"。只允许字母、数字、下划线、连字符、点和斜杠。`);
  }
  return name;
}

/**
 * 校验提交消息（防注入 + 防空消息）
 */
function validateCommitMessage(msg) {
  if (typeof msg !== 'string' || msg.trim().length === 0) {
    throw new Error('提交消息不能为空');
  }
  // 限制长度，防超长输入
  if (msg.length > 1000) {
    throw new Error('提交消息过长（最大 1000 字符）');
  }
  return msg.trim();
}

/**
 * 校验数字参数
 */
function validateNumber(n, name) {
  const num = Number(n);
  if (!Number.isInteger(num) || num < 1 || num > 1000) {
    throw new Error(`${name} 必须是 1-1000 的整数，收到: "${n}"`);
  }
  return num;
}

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
   * 在工作区安全执行 git 命令
   * @param {string[]} args - git 子命令和参数数组，如 ['add', '-A']
   */
  async execGit(args) {
    if (!this.initialized) {
      throw new Error('工作区未初始化，请先调用 initialize()');
    }
    return safeExec('git', args, this.worktreePath);
  }
  
  /**
   * Git 提交（安全版）
   */
  async commit(message) {
    const safeMsg = validateCommitMessage(message);
    console.log(`💾 Git 提交：${safeMsg}`);
    
    try {
      await this.execGit(['add', '-A']);
      await this.execGit(['commit', '-m', safeMsg]);
      
      console.log(`✅ 提交成功`);
      return { success: true, message: safeMsg };
      
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
   * 创建分支（安全版）
   */
  async createBranch(branchName) {
    const safeName = validateBranchName(branchName);
    console.log(`🌿 创建分支：${safeName}`);
    
    await this.execGit(['checkout', '-b', safeName]);
    
    console.log(`✅ 分支创建成功`);
    return { success: true, branch: safeName };
  }
  
  /**
   * 切换分支（安全版）
   */
  async checkoutBranch(branchName) {
    const safeName = validateBranchName(branchName);
    console.log(`🔄 切换分支：${safeName}`);
    
    await this.execGit(['checkout', safeName]);
    
    console.log(`✅ 分支切换成功`);
    return { success: true, branch: safeName };
  }
  
  /**
   * 合并分支（安全版）
   */
  async mergeBranch(branchName) {
    const safeName = validateBranchName(branchName);
    console.log(`🔀 合并分支：${safeName}`);
    
    await this.execGit(['merge', safeName]);
    
    console.log(`✅ 分支合并成功`);
    return { success: true };
  }
  
  /**
   * 获取当前分支
   */
  async getCurrentBranch() {
    return this.execGit(['rev-parse', '--abbrev-ref', 'HEAD']);
  }
  
  /**
   * 获取提交历史（安全版）
   */
  async getCommitHistory(limit = 10) {
    const safeLimit = validateNumber(limit, 'limit');
    const log = await this.execGit(['log', '--oneline', `-${safeLimit}`]);
    return log.split('\n');
  }
  
  /**
   * 获取文件差异（安全版）
   */
  async getDiff(branch1, branch2) {
    const b1 = validateBranchName(branch1);
    const b2 = validateBranchName(branch2);
    return this.execGit(['diff', `${b1}..${b2}`]);
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
    const result = await code(workspace);
    await workspace.commit(`Auto-commit: ${taskId}`);
    return result;
  } finally {
    // await workspace.cleanup();
  }
}

module.exports = {
  AgentWorkspaceManager,
  createAgentWorkspace,
  runInWorkspace
};
