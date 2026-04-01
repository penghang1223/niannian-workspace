/**
 * Git Worktree 管理器 - Node.js 版本
 * ClawTeam 改进 Phase 2
 * 
 * 功能：为每个 Agent/任务创建独立 Git 工作区
 * 提供 JavaScript API 供 Agent 调用
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:45
 * @security 2026-03-31 天工：exec→execFile 消除命令注入（OWASP A05）
 */

const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');

// 配置
const WORKSPACE_ROOT = '/Users/narain/.openclaw/workspace';
const WORKTREES_DIR = path.join(WORKSPACE_ROOT, '.worktrees');
const AGENTS_DIR = path.join(WORKSPACE_ROOT, 'agents');
const LOG_FILE = path.join(WORKSPACE_ROOT, 'logs', 'git-worktree.log');
const WORKTREES_RECORD = path.join(WORKTREES_DIR, 'worktrees.jsonl');

/**
 * 安全执行命令
 * Why: execFile 不经过 shell，参数作为数组传递，消除命令注入。
 * @param {string} file - 可执行文件
 * @param {string[]} args - 参数数组
 * @param {string} cwd - 工作目录
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
 * 校验 agentId / taskId（只允许安全字符）
 */
function validateId(id, name) {
  if (typeof id !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(id)) {
    throw new Error(`非法 ${name}: "${id}"。只允许字母、数字、下划线和连字符。`);
  }
  return id;
}

/**
 * 校验分支名
 */
function validateBranchName(name) {
  if (typeof name !== 'string' || !/^[a-zA-Z0-9_\-./]+$/.test(name)) {
    throw new Error(`非法分支名: "${name}"`);
  }
  return name;
}

/**
 * 校验天数参数
 */
function validateDays(days) {
  const num = Number(days);
  if (!Number.isInteger(num) || num < 1 || num > 365) {
    throw new Error(`days 必须是 1-365 的整数，收到: "${days}"`);
  }
  return num;
}

/**
 * Git Worktree 管理器类
 */
class GitWorktreeManager {
  constructor() {
    this.workspaceRoot = WORKSPACE_ROOT;
    this.worktreesDir = WORKTREES_DIR;
    this.logFile = LOG_FILE;
    this.recordFile = WORKTREES_RECORD;
    
    this.ensureDirectories();
  }
  
  ensureDirectories() {
    if (!fs.existsSync(this.worktreesDir)) {
      fs.mkdirSync(this.worktreesDir, { recursive: true });
    }
    const logDir = path.dirname(this.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }
  
  log(level, message) {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] [${level}] ${message}\n`;
    fs.appendFileSync(this.logFile, logLine);
    console.log(logLine.trim());
  }
  
  /**
   * 安全执行 git 命令
   * @param {string[]} args - git 参数数组，如 ['worktree', 'add', '-b', branch, path]
   */
  async execGit(args) {
    try {
      const result = await safeExec('git', args, this.workspaceRoot);
      this.log('INFO', `git ${args[0]} 成功`);
      return result;
    } catch (error) {
      this.log('ERROR', `git ${args[0]} 失败: ${error.message}`);
      throw error;
    }
  }
  
  async isInGitRepo() {
    try {
      await this.execGit(['rev-parse', '--git-dir']);
      return true;
    } catch {
      return false;
    }
  }
  
  async createWorktree(agentId, taskId) {
    const safeAgent = validateId(agentId, 'agentId');
    const safeTask = validateId(taskId, 'taskId');
    
    this.log('INFO', `为 Agent '${safeAgent}' 任务 '${safeTask}' 创建 worktree...`);
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const branchName = `${safeAgent}-${safeTask}-${timestamp}`;
    const worktreePath = path.join(this.worktreesDir, safeAgent, safeTask);
    
    if (fs.existsSync(worktreePath)) {
      this.log('WARNING', `Worktree 已存在：${worktreePath}`);
      throw new Error(`Worktree 已存在：${worktreePath}`);
    }
    
    try {
      await this.execGit(['worktree', 'add', '-b', branchName, worktreePath]);
      
      this.log('SUCCESS', 'Worktree 创建成功');
      this.log('INFO', `路径：${worktreePath}`);
      this.log('INFO', `分支：${branchName}`);
      
      const record = {
        agent: safeAgent,
        task: safeTask,
        branch: branchName,
        path: worktreePath,
        created: new Date().toISOString()
      };
      fs.appendFileSync(this.recordFile, JSON.stringify(record) + '\n');
      
      // 创建 Agent 配置文件
      const configPath = path.join(worktreePath, 'agents', safeAgent, 'workspace_config.json');
      const configDir = path.dirname(configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      fs.writeFileSync(configPath, JSON.stringify({
        agentId: safeAgent,
        taskId: safeTask,
        worktreePath,
        branch: branchName,
        createdAt: new Date().toISOString(),
        workspaceRoot: this.workspaceRoot
      }, null, 2));
      
      return {
        success: true,
        agentId: safeAgent,
        taskId: safeTask,
        branch: branchName,
        path: worktreePath
      };
      
    } catch (error) {
      this.log('ERROR', `Worktree 创建失败：${error.message}`);
      throw error;
    }
  }
  
  async removeWorktree(agentId, taskId) {
    const safeAgent = validateId(agentId, 'agentId');
    const safeTask = validateId(taskId, 'taskId');
    
    this.log('INFO', `删除 worktree: Agent=${safeAgent}, Task=${safeTask}`);
    
    const worktreePath = path.join(this.worktreesDir, safeAgent, safeTask);
    
    if (!fs.existsSync(worktreePath)) {
      this.log('WARNING', `Worktree 不存在：${worktreePath}`);
      throw new Error(`Worktree 不存在：${worktreePath}`);
    }
    
    try {
      // 获取分支名（在 worktree 目录内执行）
      const branchName = await safeExec('git', ['rev-parse', '--abbrev-ref', 'HEAD'], worktreePath);
      
      // 删除 worktree（在主仓库执行）
      await this.execGit(['worktree', 'remove', worktreePath]);
      
      // 删除分支
      await this.execGit(['branch', '-D', validateBranchName(branchName)]);
      
      this.log('SUCCESS', 'Worktree 删除成功');
      return { success: true };
      
    } catch (error) {
      this.log('ERROR', `Worktree 删除失败：${error.message}`);
      throw error;
    }
  }
  
  async listWorktrees() {
    this.log('INFO', '列出所有 worktrees...');
    
    const worktrees = [];
    
    if (fs.existsSync(this.recordFile)) {
      const lines = fs.readFileSync(this.recordFile, 'utf-8').split('\n');
      for (const line of lines) {
        if (line.trim()) {
          try {
            worktrees.push(JSON.parse(line));
          } catch {
            this.log('WARNING', `解析记录失败：${line}`);
          }
        }
      }
    }
    
    const gitList = await this.execGit(['worktree', 'list']);
    
    return { records: worktrees, gitList };
  }
  
  async cleanupOldWorktrees(days = 7) {
    const safeDays = validateDays(days);
    this.log('INFO', `清理 ${safeDays} 天前的 worktrees...`);
    
    if (!fs.existsSync(this.recordFile)) {
      this.log('INFO', '没有 worktrees 记录');
      return { cleaned: 0 };
    }
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - safeDays);
    
    const lines = fs.readFileSync(this.recordFile, 'utf-8').split('\n');
    const keptRecords = [];
    let cleaned = 0;
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      try {
        const record = JSON.parse(line);
        if (new Date(record.created).getTime() < cutoffDate.getTime()) {
          this.log('INFO', `清理：Agent=${record.agent}, Task=${record.task}`);
          try {
            await this.removeWorktree(record.agent, record.task);
            cleaned++;
          } catch (error) {
            this.log('ERROR', `清理失败：${error.message}`);
          }
        } else {
          keptRecords.push(line);
        }
      } catch {
        this.log('WARNING', `解析记录失败：${line}`);
      }
    }
    
    fs.writeFileSync(this.recordFile, keptRecords.join('\n') + '\n');
    this.log('SUCCESS', `清理完成，共清理 ${cleaned} 个 worktrees`);
    return { cleaned };
  }
  
  async createAllAgentWorktrees() {
    this.log('INFO', '为所有 Agent 创建默认 worktrees...');
    
    const agents = [
      'main', 'product_manager', 'dev_engineer',
      'qa_engineer', 'frontend_dev', 'chief_cute_officer'
    ];
    
    const results = [];
    for (const agent of agents) {
      try {
        results.push(await this.createWorktree(agent, 'default'));
      } catch (error) {
        this.log('ERROR', `Agent ${agent} 创建失败：${error.message}`);
        results.push({ agent, success: false, error: error.message });
      }
    }
    return results;
  }
  
  getAgentWorktreePath(agentId, taskId = 'default') {
    return path.join(this.worktreesDir, agentId, taskId);
  }
  
  worktreeExists(agentId, taskId) {
    return fs.existsSync(this.getAgentWorktreePath(agentId, taskId));
  }
}

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
