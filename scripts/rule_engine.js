#!/usr/bin/env node
/**
 * 规则匹配引擎 (RuleEngine) - Layer 2
 * 
 * 职责：根据配置规则决定工具调用的权限（allow/deny/ask）
 * 支持通配符匹配、glob路径模式
 * 
 * 用法：
 *   const { RuleEngine } = require('./rule_engine');
 *   const engine = new RuleEngine();
 *   const decision = engine.check('exec', { command: 'ls -la' });
 *   // decision: { action: 'allow'|'deny'|'ask', rule, reason }
 */

'use strict';

const fs = require('fs');
const path = require('path');

class RuleEngine {
  constructor(rulesPath) {
    this.rulesPath = rulesPath || path.join(__dirname, '..', 'permissions', 'rules.json');
    this.rules = null;
    this._lastLoaded = 0;
    this._loadRules();
  }

  /**
   * 加载规则（带缓存，文件变更自动重载）
   */
  _loadRules() {
    try {
      const stat = fs.statSync(this.rulesPath);
      if (stat.mtimeMs <= this._lastLoaded && this.rules) return;
      
      const raw = fs.readFileSync(this.rulesPath, 'utf8');
      this.rules = JSON.parse(raw);
      this._lastLoaded = stat.mtimeMs;
      console.log(`[RuleEngine] 规则已加载: ${this.rulesPath}`);
    } catch (err) {
      console.error(`[RuleEngine] 加载规则失败: ${err.message}`);
      this.rules = { alwaysAllowRules: [], alwaysDenyRules: [], alwaysAskRules: [] };
    }
  }

  /**
   * 检查工具调用权限
   * @param {string} tool - 工具名称
   * @param {object} params - 工具参数
   * @returns {{ action: 'allow'|'deny'|'ask', rule?: object, reason?: string }}
   */
  check(tool, params = {}) {
    this._loadRules(); // 热重载

    // 优先级：deny > ask > allow
    // 1. 检查 deny 规则
    const denyMatch = this._matchRule(this.rules.alwaysDenyRules, tool, params);
    if (denyMatch) {
      return { action: 'deny', rule: denyMatch, reason: denyMatch.name || '匹配拒绝规则' };
    }

    // 2. 检查 ask 规则
    const askMatch = this._matchRule(this.rules.alwaysAskRules, tool, params);
    if (askMatch) {
      return { action: 'ask', rule: askMatch, reason: askMatch.name || '匹配询问规则' };
    }

    // 3. 检查 allow 规则
    const allowMatch = this._matchRule(this.rules.alwaysAllowRules, tool, params);
    if (allowMatch) {
      return { action: 'allow', rule: allowMatch, reason: allowMatch.name || '匹配允许规则' };
    }

    // 4. 默认：询问
    return { action: 'ask', reason: '未匹配任何规则，默认询问' };
  }

  /**
   * 检查路径沙箱
   * @param {string} filePath - 文件路径
   * @param {string} operation - 'read'|'write'
   * @returns {{ allowed: boolean, zone: string, reason: string }}
   */
  checkPath(filePath, operation = 'read') {
    this._loadRules();

    const sandbox = this.rules.pathSandbox || {};
    const normalizedPath = path.resolve(filePath.replace(/^~/, process.env.HOME));

    // 检查禁止区域
    for (const pattern of (sandbox.forbidden || [])) {
      if (this._globMatch(pattern, normalizedPath)) {
        return { allowed: false, zone: 'forbidden', reason: `路径在禁止区域: ${pattern}` };
      }
    }

    // 写操作检查读写区域
    if (operation === 'write') {
      for (const pattern of (sandbox.readWrite || [])) {
        if (this._globMatch(pattern, normalizedPath)) {
          return { allowed: true, zone: 'readWrite', reason: '路径在读写白名单' };
        }
      }
      // 不在读写白名单则拒绝
      return { allowed: false, zone: 'unknown', reason: '写操作不在允许的路径范围内' };
    }

    // 读操作：检查读写 + 只读区域
    for (const pattern of [...(sandbox.readWrite || []), ...(sandbox.readOnly || [])]) {
      if (this._globMatch(pattern, normalizedPath)) {
        return { allowed: true, zone: 'readable', reason: '路径在可读范围' };
      }
    }

    return { allowed: false, zone: 'unknown', reason: '路径不在任何允许范围内' };
  }

  /**
   * 匹配规则列表
   */
  _matchRule(rules, tool, params) {
    for (const rule of rules) {
      if (this._ruleMatches(rule, tool, params)) {
        return rule;
      }
    }
    return null;
  }

  /**
   * 单条规则匹配
   */
  _ruleMatches(rule, tool, params) {
    // 工具匹配
    if (rule.tool) {
      const tools = Array.isArray(rule.tool) ? rule.tool : [rule.tool];
      const toolMatch = tools.some(t => 
        t === '*' || t === tool || (t.endsWith('*') && tool.startsWith(t.slice(0, -1)))
      );
      if (!toolMatch) return false;
    }

    // Action 匹配
    if (rule.action) {
      const actions = Array.isArray(rule.action) ? rule.action : [rule.action];
      const paramAction = params.action || '';
      const actionMatch = actions.some(a => 
        a === '*' || a === paramAction
      );
      if (!actionMatch) return false;
    }

    // 命令模式匹配（exec工具）
    if (rule.commandPattern && tool === 'exec') {
      const command = params.command || params.script || '';
      if (!this._globMatch(rule.commandPattern, command)) return false;
    }

    // 路径模式匹配（文件操作工具）
    if (rule.pathPattern && ['read', 'write', 'edit', 'delete'].includes(tool)) {
      const filePath = params.path || params.file_path || params.file || '';
      if (!this._globMatch(rule.pathPattern, filePath)) return false;
    }

    return true;
  }

  /**
   * 简单glob匹配（支持 ** 和 *）
   */
  _globMatch(pattern, text) {
    if (pattern === '*') return true;
    
    // 转义正则特殊字符，保留 * 和 **
    const regexStr = pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\*\*/g, '§DOUBLESTAR§')
      .replace(/\*/g, '[^/]*')
      .replace(/§DOUBLESTAR§/g, '.*');
    
    try {
      return new RegExp(`^${regexStr}$`, 'i').test(text);
    } catch {
      return pattern === text;
    }
  }

  /**
   * 获取所有规则摘要
   */
  summary() {
    this._loadRules();
    return {
      allow: (this.rules.alwaysAllowRules || []).length,
      deny: (this.rules.alwaysDenyRules || []).length,
      ask: (this.rules.alwaysAskRules || []).length,
      sandbox: {
        readWrite: (this.rules.pathSandbox?.readWrite || []).length,
        readOnly: (this.rules.pathSandbox?.readOnly || []).length,
        forbidden: (this.rules.pathSandbox?.forbidden || []).length,
      },
    };
  }
}

// ═══════════════════════════════════════════════
// CLI模式
// ═══════════════════════════════════════════════

if (require.main === module) {
  const engine = new RuleEngine();
  const args = process.argv.slice(2);

  if (args[0] === '--summary') {
    console.log(JSON.stringify(engine.summary(), null, 2));
    process.exit(0);
  }

  if (args.length < 1) {
    console.log('用法:');
    console.log('  node rule_engine.js <tool> [params_json]');
    console.log('  node rule_engine.js --summary');
    console.log('  node rule_engine.js --path <file_path> <read|write>');
    process.exit(1);
  }

  if (args[0] === '--path') {
    const result = engine.checkPath(args[1], args[2] || 'read');
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.allowed ? 0 : 1);
  }

  const tool = args[0];
  const params = args[1] ? JSON.parse(args[1]) : {};
  const result = engine.check(tool, params);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.action === 'deny' ? 1 : 0);
}

module.exports = { RuleEngine };
