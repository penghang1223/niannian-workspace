/**
 * Git Worktree 管理器 - Node.js 版本
 * ClawTeam 改进 Phase 2
 * 
 * 功能：为每个 Agent/任务创建独立 Git 工作区
 * 提供 JavaScript API 供 Agent 调用
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:45
 */

const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// 配置
const WORKSPACE_ROOT = '/Users/narain/.openclaw/workspace';
const WORKTREES_DIR = path.join(WORKSPACE_ROOT, '.worktrees');
const AGENTS_DIR = path.join(WORKSPACE_ROOT, 'agents');
const LOG_FILE = path.join(WORKSPACE_ROOT, 'logs', 'git-worktree.log');
const WORKTREES_RECORD = path.join(WORKTREES_DIR, 'worktrees.jsonl');

/**
 * Git Worktree 管理器类
 */
class GitWorktreeManager {
  constructor() {
    this.workspaceRoot = WORKSPACE_ROOT;
    this.worktreesDir = WORKTREES_DIR;
    this.logFile = LOG_FILE;
    this.recordFile = WORKTREES_RECORD;
    
    // 确保目录存在
    this.ensureDirectories();
  }
  
  /**
   * 确保目录存在
   */
  ensureDirectories() {
    if (!fs.existsSync(this.worktreesDir)) {
      fs.mkdirSync(this.worktreesDir, { recursive: true });
    }
    
    const logDir = path.dirname(this.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }
  
  /**
   * 日志记录
   */
  log(level, message) {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] [${level}] ${message}\n`;
    fs.appendFileSync(this.logFile, logLine);
    console.log(logLine.trim());
  }
  
  /**
   * 执行 shell 命令
   */
  execCommand(command, options = {}) {
    return new Promise((resolve, reject) => {
      const cwd = options.cwd || this.workspaceRoot;
      
      exec(command, { cwd }, (error, stdout, stderr) => {
        if (error) {
          this.log('ERROR', `命令执行失败：${command}`);
          this.log('ERROR', stderr);
          reject(new Error(stderr || error.message));
          return;
        }
        
        this.log('INFO', `命令执行成功：${command}`);
        resolve(stdout.trim());
      });
    });
  }
  
  /**
   * 检查是否在 Git 仓库中
   */
  async isInGitRepo() {
    try {
      await this.execCommand('git rev-parse --git-dir');
      return true;
    } catch (error) {
      return false;
    }
  }
  
  /**
   * 为 Agent 创建 worktree
   */
  async createWorktree(agentId, taskId) {
    this.log('INFO', `为 Agent '${agentId}' 任务 '${taskId}' 创建 worktree...`);
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const branchName = `${agentId}-${taskId}-${timestamp}`;
    const worktreePath = path.join(this.worktreesDir, agentId, taskId);
    
    // 检查是否已存在
    if (fs.existsSync(worktreePath)) {
      this.log('WARNING', `Worktree 已存在：${worktreePath}`);
      throw new Error(`Worktree 已存在：${worktreePath}`);
    }
    
    // 创建 branch 和 worktree
    try {
      await this.execCommand(`git worktree add -b ${branchName} ${worktreePath}`);
      
      this.log('SUCCESS', 'Worktree 创建成功');
      this.log('INFO', `路径：${worktreePath}`);
      this.log('INFO', `分支：${branchName}`);
      
      // 记录 worktree 信息
      const record = {
        agent: agentId,
        task: taskId,
        branch: branchName,
        path: worktreePath,
        created: new Date().toISOString()
      };
      
      fs.appendFileSync(this.recordFile, JSON.stringify(record) + '\n');
      
      // 创建 Agent 配置文件
      const configPath = path.join(worktreePath, 'agents', agentId, 'workspace_config.json');
      const configDir = path.dirname(configPath);
      
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      fs.writeFileSync(configPath, JSON.stringify({
        agentId,
        taskId,
        worktreePath,
        branch: branchName,
        createdAt: new Date().toISOString(),
        workspaceRoot: this.workspaceRoot
      }, null, 2));
      
      return {
        success: true,
        agentId,
        taskId,
        branch: branchName,
        path: worktreePath
      };
      
    } catch (error) {
      this.log('ERROR', `Worktree 创建失败：${error.message}`);
      throw error;
    }
  }
  
  /**
   * 删除 worktree
   */
  async removeWorktree(agentId, taskId) {
    this.log('INFO', `删除 worktree: Agent=${agentId}, Task=${taskId}`);
    
    const worktreePath = path.join(this.worktreesDir, agentId, taskId);
    
    if (!fs.existsSync(worktreePath)) {
      this.log('WARNING', `Worktree 不存在：${worktreePath}`);
      throw new Error(`Worktree 不存在：${worktreePath}`);
    }
    
    try {
      // 获取分支名
      const branchName = await this.execCommand(
        `cd ${worktreePath} && git rev-parse --abbrev-ref HEAD`
      );
      
      // 删除 worktree
      await this.execCommand(`git worktree remove ${worktreePath}`);
      
      // 删除分支
      await this.execCommand(`git branch -D ${branchName}`);
      
      this.log('SUCCESS', 'Worktree 删除成功');
      
      return { success: true };
      
    } catch (error) {
      this.log('ERROR', `Worktree 删除失败：${error.message}`);
      throw error;
    }
  }
  
  /**
   * 列出所有 worktrees
   */
  async listWorktrees() {
    this.log('INFO', '列出所有 worktrees...');
    
    const worktrees = [];
    
    if (fs.existsSync(this.recordFile)) {
      const lines = fs.readFileSync(this.recordFile, 'utf-8').split('\n');
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const record = JSON.parse(line);
            worktrees.push(record);
          } catch (error) {
            this.log('WARNING', `解析记录失败：${line}`);
          }
        }
      }
    }
    
    // 获取 git worktree 列表
    const gitList = await this.execCommand('git worktree list');
    
    return {
      records: worktrees,
      gitList
    };
  }
  
  /**
   * 清理旧的 worktrees
   */
  async cleanupOldWorktrees(days = 7) {
    this.log('INFO', `清理 ${days} 天前的 worktrees...`);
    
    if (!fs.existsSync(this.recordFile)) {
      this.log('INFO', '没有 worktrees 记录');
      return { cleaned: 0 };
    }
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    const cutoffTime = cutoffDate.getTime();
    
    const lines = fs.readFileSync(this.recordFile, 'utf-8').split('\n');
    const keptRecords = [];
    let cleaned = 0;
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      try {
        const record = JSON.parse(line);
        const createdTime = new Date(record.created).getTime();
        
        if (createdTime < cutoffTime) {
          // 清理
          this.log('INFO', `清理：Agent=${record.agent}, Task=${record.task}`);
          
          try {
            await this.removeWorktree(record.agent, record.task);
            cleaned++;
          } catch (error) {
            this.log('ERROR', `清理失败：${error.message}`);
          }
        } else {
          // 保留
          keptRecords.push(line);
        }
      } catch (error) {
        this.log('WARNING', `解析记录失败：${line}`);
      }
    }
    
    // 更新记录文件
    fs.writeFileSync(this.recordFile, keptRecords.join('\n') + '\n');
    
    this.log('SUCCESS', `清理完成，共清理 ${cleaned} 个 worktrees`);
    
    return { cleaned };
  }
  
  /**
   * 为所有 Agent 创建默认 worktrees
   */
  async createAllAgentWorktrees() {
    this.log('INFO', '为所有 Agent 创建默认 worktrees...');
    
    const agents = [
      'main',
      'product_manager',
      'dev_engineer',
      'qa_engineer',
      'frontend_dev',
      'chief_cute_officer'
    ];
    
    const results = [];
    
    for (const agent of agents) {
      try {
        const result = await this.createWorktree(agent, 'default');
        results.push(result);
      } catch (error) {
        this.log('ERROR', `Agent ${agent} 创建失败：${error.message}`);
        results.push({
          agent,
          success: false,
          error: error.message
        });
      }
    }
    
    return results;
  }
  
  /**
   * 获取 Agent 的 worktree 路径
   */
  getAgentWorktreePath(agentId, taskId = 'default') {
    return path.join(this.worktreesDir, agentId, taskId);
  }
  
  /**
   * 检查 worktree 是否存在
   */
  worktreeExists(agentId, taskId) {
    const worktreePath = this.getAgentWorktreePath(agentId, taskId);
    return fs.existsSync(worktreePath);
  }
}

// 导出单例
const worktreeManager = new GitWorktreeManager();

module.exports = {
  GitWorktreeManager,
  worktreeManager,
  createWorktree: worktreeManager.createWorktree.bind(worktreeManager),
  removeWorktree: worktreeManager.removeWorktree.bind(worktreeManager),
  listWorktrees: worktreeManager.listWorktrees.bind(worktreeManager),
  cleanupOldWorktrees: worktreeManager.cleanupOldWorktrees.bind(worktreeManager),
  createAllAgentWorktrees: worktreeManager.createAllAgentWorktrees.bind(worktreeManager)
};
