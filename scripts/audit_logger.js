#!/usr/bin/env node
/**
 * 审计日志 (AuditLogger) - Layer 5
 * 
 * 职责：记录所有工具调用、拒绝/允许决策、异常检测
 * 日志格式：JSONL（每行一个JSON对象）
 * 存储位置：logs/audit/YYYY-MM-DD.jsonl
 * 
 * 用法：
 *   const { AuditLogger } = require('./audit_logger');
 *   const logger = new AuditLogger();
 *   logger.log({ agent_id, tool, action, decision, ... });
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class AuditLogger {
  constructor(logDir) {
    this.logDir = logDir || path.join(__dirname, '..', 'logs', 'audit');
    this._ensureDir();
    
    // 告警状态跟踪
    this._recentDenials = new Map(); // agent_id -> [timestamps]
    this._highRiskAllowed = [];
    
    // 告警阈值
    this.ALERT_THRESHOLDS = {
      denialBurstCount: 3,       // 1分钟内被拒绝3次
      denialBurstWindowMs: 60000,
      maxRecentAlerts: 100,      // 内存中保留的最大告警数
    };
  }

  /**
   * 确保日志目录存在
   */
  _ensureDir() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  /**
   * 获取今天的日志文件路径
   */
  _getTodayLogFile() {
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
    return path.join(this.logDir, `${dateStr}.jsonl`);
  }

  /**
   * 记录一条审计日志
   * @param {object} entry
   * @param {string} entry.agent_id - Agent标识
   * @param {string} entry.tool - 工具名称
   * @param {string} [entry.action] - 操作类型
   * @param {object} [entry.params] - 工具参数（会被hash，不记录明文）
   * @param {string} entry.decision - 'allow'|'deny'|'ask'
   * @param {string} [entry.reason] - 决策原因
   * @param {string} [entry.risk_level] - 风险等级
   * @param {boolean} [entry.success] - 执行是否成功
   * @param {number} [entry.execution_time_ms] - 执行耗时
   */
  log(entry) {
    const record = {
      timestamp: new Date().toISOString(),
      id: crypto.randomUUID(),
      agent_id: entry.agent_id || 'unknown',
      tool: entry.tool || 'unknown',
      action: entry.action || '',
      params_hash: entry.params ? this._hashParams(entry.params) : null,
      decision: entry.decision || 'unknown',
      reason: entry.reason || '',
      risk_level: entry.risk_level || 'low',
      success: entry.success !== undefined ? entry.success : null,
      execution_time_ms: entry.execution_time_ms || null,
    };

    // 写入日志文件
    const logFile = this._getTodayLogFile();
    const line = JSON.stringify(record) + '\n';
    fs.appendFileSync(logFile, line, 'utf8');

    // 检查是否需要告警
    const alerts = this._checkAlerts(record);
    if (alerts.length > 0) {
      this._emitAlerts(alerts, record);
    }

    return record;
  }

  /**
   * 参数hash（不记录明文，保护隐私）
   */
  _hashParams(params) {
    const str = JSON.stringify(params);
    return 'sha256:' + crypto.createHash('sha256').update(str).digest('hex').slice(0, 16);
  }

  /**
   * 检查告警条件
   */
  _checkAlerts(record) {
    const alerts = [];
    const now = Date.now();

    // 告警1：拒绝风暴 — 同一Agent短时间内多次被拒
    if (record.decision === 'deny') {
      if (!this._recentDenials.has(record.agent_id)) {
        this._recentDenials.set(record.agent_id, []);
      }
      const denials = this._recentDenials.get(record.agent_id);
      denials.push(now);
      
      // 清理过期记录
      const cutoff = now - this.ALERT_THRESHOLDS.denialBurstWindowMs;
      const recentDenials = denials.filter(t => t > cutoff);
      this._recentDenials.set(record.agent_id, recentDenials);

      if (recentDenials.length >= this.ALERT_THRESHOLDS.denialBurstCount) {
        alerts.push({
          type: 'DENIAL_BURST',
          severity: 'warning',
          message: `Agent [${record.agent_id}] 在1分钟内被拒绝${recentDenials.length}次`,
          agent_id: record.agent_id,
        });
      }
    }

    // 告警2：高风险操作被允许
    if (record.decision === 'allow' && record.risk_level === 'high') {
      alerts.push({
        type: 'HIGH_RISK_ALLOWED',
        severity: 'critical',
        message: `高风险操作被允许: Agent [${record.agent_id}] 调用 ${record.tool}`,
        agent_id: record.agent_id,
        tool: record.tool,
      });
    }

    return alerts;
  }

  /**
   * 输出告警
   */
  _emitAlerts(alerts, record) {
    for (const alert of alerts) {
      const alertRecord = {
        ...alert,
        timestamp: new Date().toISOString(),
        related_log_id: record.id,
      };
      
      // 写入告警日志
      const alertFile = path.join(this.logDir, 'alerts.jsonl');
      fs.appendFileSync(alertFile, JSON.stringify(alertRecord) + '\n', 'utf8');
      
      // 控制台输出
      const icon = alert.severity === 'critical' ? '🚨' : '⚠️';
      console.error(`${icon} [AUDIT ALERT] ${alert.message}`);
    }
  }

  /**
   * 查询审计日志
   * @param {object} filters
   * @param {string} [filters.date] - YYYY-MM-DD
   * @param {string} [filters.agent_id]
   * @param {string} [filters.tool]
   * @param {string} [filters.decision]
   * @param {number} [filters.limit] - 最大返回条数
   * @returns {Array}
   */
  query(filters = {}) {
    const date = filters.date || new Date().toISOString().split('T')[0];
    const logFile = path.join(this.logDir, `${date}.jsonl`);
    
    if (!fs.existsSync(logFile)) {
      return [];
    }

    const lines = fs.readFileSync(logFile, 'utf8').trim().split('\n').filter(Boolean);
    let records = lines.map(line => {
      try { return JSON.parse(line); } catch { return null; }
    }).filter(Boolean);

    // 过滤
    if (filters.agent_id) {
      records = records.filter(r => r.agent_id === filters.agent_id);
    }
    if (filters.tool) {
      records = records.filter(r => r.tool === filters.tool);
    }
    if (filters.decision) {
      records = records.filter(r => r.decision === filters.decision);
    }

    // 限制数量
    if (filters.limit) {
      records = records.slice(-filters.limit);
    }

    return records;
  }

  /**
   * 生成统计摘要
   * @param {string} [date] - YYYY-MM-DD，默认今天
   */
  stats(date) {
    const records = this.query({ date, limit: 10000 });
    
    const summary = {
      date: date || new Date().toISOString().split('T')[0],
      total: records.length,
      byDecision: {},
      byTool: {},
      byAgent: {},
      byRiskLevel: {},
      denialRate: 0,
    };

    for (const r of records) {
      summary.byDecision[r.decision] = (summary.byDecision[r.decision] || 0) + 1;
      summary.byTool[r.tool] = (summary.byTool[r.tool] || 0) + 1;
      summary.byAgent[r.agent_id] = (summary.byAgent[r.agent_id] || 0) + 1;
      summary.byRiskLevel[r.risk_level] = (summary.byRiskLevel[r.risk_level] || 0) + 1;
    }

    if (summary.total > 0) {
      summary.denialRate = ((summary.byDecision.deny || 0) / summary.total * 100).toFixed(1) + '%';
    }

    return summary;
  }
}

// ═══════════════════════════════════════════════
// CLI模式
// ═══════════════════════════════════════════════

if (require.main === module) {
  const logger = new AuditLogger();
  const args = process.argv.slice(2);

  if (args[0] === '--stats') {
    console.log(JSON.stringify(logger.stats(args[1]), null, 2));
    process.exit(0);
  }

  if (args[0] === '--query') {
    const filters = args[1] ? JSON.parse(args[1]) : {};
    console.log(JSON.stringify(logger.query(filters), null, 2));
    process.exit(0);
  }

  if (args[0] === '--log') {
    const entry = JSON.parse(args[1]);
    const record = logger.log(entry);
    console.log(JSON.stringify(record, null, 2));
    process.exit(0);
  }

  console.log('用法:');
  console.log('  node audit_logger.js --log \'{"agent_id":"main","tool":"exec","decision":"allow"}\'');
  console.log('  node audit_logger.js --query \'{"agent_id":"main","limit":10}\'');
  console.log('  node audit_logger.js --stats [YYYY-MM-DD]');
  process.exit(1);
}

module.exports = { AuditLogger };
