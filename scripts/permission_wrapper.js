#!/usr/bin/env node
/**
 * 权限检查主引擎 (PermissionWrapper) - 综合5层检查
 * 
 * 职责：串联5层权限检查，提供统一入口
 * 
 * 用法：
 *   const { checkPermission } = require('./permission_wrapper');
 *   const result = checkPermission({
 *     agent_id: 'frontend_dev',
 *     tool: 'exec',
 *     command: 'git push origin main'
 *   });
 */

'use strict';

const { validateInput } = require('./input_validator');
const { RuleEngine } = require('./rule_engine');
const { AuditLogger } = require('./audit_logger');

// ═══════════════════════════════════════════════
// Agent权限配置
// ═══════════════════════════════════════════════

const fs = require('fs');
const path = require('path');

function loadAgentPermissions() {
  const configPath = path.join(__dirname, '..', 'permissions', 'agent_permissions.json');
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (err) {
    console.error(`[Permission] 加载Agent权限失败: ${err.message}`);
    return { agentProfiles: {} };
  }
}

// ═══════════════════════════════════════════════
// 核心检查函数
// ═══════════════════════════════════════════════

const ruleEngine = new RuleEngine();
const auditLogger = new AuditLogger();

/**
 * 综合权限检查
 * @param {object} request
 * @param {string} request.agent_id - Agent标识
 * @param {string} request.tool - 工具名称
 * @param {object} [request.params] - 工具参数
 * @param {string} [request.input] - 原始输入文本（用于注入检测）
 * @returns {{ allowed: boolean, decision: string, layers: object[], summary: string }}
 */
function checkPermission(request) {
  const startTime = Date.now();
  const layers = [];
  let finalDecision = 'allow';
  let finalReason = '';

  // ═══ Layer 1: 输入验证 ═══
  if (request.input) {
    const inputResult = validateInput(request.input);
    layers.push({
      layer: 1,
      name: '输入验证',
      passed: inputResult.valid,
      details: inputResult,
    });
    if (!inputResult.valid) {
      finalDecision = 'deny';
      finalReason = `输入验证失败: ${inputResult.reasons.join('; ')}`;
    }
  }

  // ═══ Layer 2: 规则匹配 ═══
  const params = request.params || {};
  const ruleResult = ruleEngine.check(request.tool, params);
  layers.push({
    layer: 2,
    name: '规则匹配',
    passed: ruleResult.action !== 'deny',
    details: ruleResult,
  });
  
  if (ruleResult.action === 'deny') {
    finalDecision = 'deny';
    finalReason = ruleResult.reason;
  } else if (ruleResult.action === 'ask' && finalDecision !== 'deny') {
    finalDecision = 'ask';
    finalReason = ruleResult.reason;
  }

  // ═══ Layer 3: Agent权限检查 ═══
  if (request.agent_id) {
    const agentResult = checkAgentPermission(request.agent_id, request.tool, params);
    layers.push({
      layer: 3,
      name: 'Agent权限',
      passed: agentResult.allowed,
      details: agentResult,
    });
    if (!agentResult.allowed) {
      finalDecision = 'deny';
      finalReason = agentResult.reason;
    }
  }

  // ═══ Layer 4: 工具特定检查 ═══
  if (['read', 'write', 'edit', 'delete'].includes(request.tool)) {
    const filePath = params.path || params.file_path || params.file || '';
    if (filePath) {
      const pathResult = ruleEngine.checkPath(filePath, request.tool === 'read' ? 'read' : 'write');
      layers.push({
        layer: 4,
        name: '路径沙箱',
        passed: pathResult.allowed,
        details: pathResult,
      });
      if (!pathResult.allowed) {
        finalDecision = 'deny';
        finalReason = pathResult.reason;
      }
    }
  }

  // ═══ Layer 5: 审计日志 ═══
  const riskLevel = layers.some(l => !l.passed) ? 'high' : 
                    finalDecision === 'ask' ? 'medium' : 'low';
  
  auditLogger.log({
    agent_id: request.agent_id || 'unknown',
    tool: request.tool,
    action: params.action || '',
    params: params,
    decision: finalDecision,
    reason: finalReason || '通过所有检查',
    risk_level: riskLevel,
    execution_time_ms: Date.now() - startTime,
  });

  return {
    allowed: finalDecision === 'allow',
    decision: finalDecision,
    reason: finalReason,
    layers,
    summary: buildSummary(finalDecision, layers),
  };
}

/**
 * Agent权限检查 - Layer 3
 */
function checkAgentPermission(agentId, tool, params) {
  const config = loadAgentPermissions();
  const profile = config.agentProfiles[agentId] || config.agentProfiles.default;
  
  if (!profile) {
    return { allowed: false, reason: `未知Agent: ${agentId}` };
  }

  // 检查拒绝列表
  for (const denied of (profile.deniedTools || [])) {
    if (denied === '*') {
      return { allowed: false, reason: `Agent [${agentId}] 被完全禁止` };
    }
    if (denied === tool || (denied.endsWith('*') && tool.startsWith(denied.slice(0, -1)))) {
      return { allowed: false, reason: `Agent [${agentId}] 不允许使用工具: ${tool}` };
    }
  }

  // 检查允许列表（*表示全部允许）
  const allowed = profile.allowedTools || [];
  if (allowed.includes('*')) {
    // 全部允许，但还要检查requireApproval
    return checkRequireApproval(profile, tool, params, agentId);
  }

  const toolAllowed = allowed.some(t => 
    t === tool || (t.endsWith('*') && tool.startsWith(t.slice(0, -1)))
  );
  
  if (!toolAllowed) {
    return { allowed: false, reason: `Agent [${agentId}] 的权限列表中不包含工具: ${tool}` };
  }

  return checkRequireApproval(profile, tool, params, agentId);
}

/**
 * 检查是否需要审批
 */
function checkRequireApproval(profile, tool, params, agentId) {
  const approvalRules = profile.requireApproval || [];
  
  for (const rule of approvalRules) {
    if (rule === '*') {
      return { allowed: false, reason: `Agent [${agentId}] 所有操作需要审批` };
    }
    
    // 规则格式: "tool:commandPattern" 或 "tool"
    const [ruleTool, rulePattern] = rule.includes(':') ? rule.split(':') : [rule, '*'];
    
    if (ruleTool === tool || (ruleTool.endsWith('*') && tool.startsWith(ruleTool.slice(0, -1)))) {
      if (rulePattern === '*') {
        return { allowed: false, reason: `Agent [${agentId}] 使用 ${tool} 需要审批` };
      }
      
      const command = params.command || params.script || '';
      if (globMatch(rulePattern, command)) {
        return { allowed: false, reason: `Agent [${agentId}] 命令 "${command}" 需要审批` };
      }
    }
  }

  return { allowed: true };
}

/**
 * 简单glob匹配
 */
function globMatch(pattern, text) {
  if (pattern === '*') return true;
  const regexStr = pattern
    .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\*\*/g, '.*')
    .replace(/\*/g, '[^/]*');
  try {
    return new RegExp(`^${regexStr}$`, 'i').test(text);
  } catch {
    return pattern === text;
  }
}

/**
 * 构建结果摘要
 */
function buildSummary(decision, layers) {
  const passed = layers.filter(l => l.passed).length;
  const total = layers.length;
  const icon = decision === 'allow' ? '✅' : decision === 'deny' ? '❌' : '❓';
  return `${icon} ${decision.toUpperCase()} (${passed}/${total}层通过)`;
}

// ═══════════════════════════════════════════════
// CLI模式
// ═══════════════════════════════════════════════

if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.log('用法:');
    console.log('  node permission_wrapper.js --check \'{"agent_id":"main","tool":"exec","params":{"command":"ls"}}\'');
    console.log('  node permission_wrapper.js --agent <agent_id> --tool <tool> [--params \'{...}\']');
    console.log('  node permission_wrapper.js --stats [date]');
    process.exit(1);
  }

  if (args[0] === '--stats') {
    console.log(JSON.stringify(auditLogger.stats(args[1]), null, 2));
    process.exit(0);
  }

  let request;
  if (args[0] === '--check') {
    request = JSON.parse(args[1]);
  } else {
    request = {};
    for (let i = 0; i < args.length; i += 2) {
      const key = args[i].replace('--', '');
      const val = args[i + 1];
      request[key] = key === 'params' ? JSON.parse(val) : val;
    }
  }

  const result = checkPermission(request);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.allowed ? 0 : 1);
}

module.exports = { checkPermission, checkAgentPermission, auditLogger };
