#!/usr/bin/env node
/**
 * 输入验证器 (InputValidator) - Layer 1
 * 
 * 职责：检测prompt注入、恶意指令、敏感关键词
 * 
 * 用法：
 *   const { validateInput } = require('./input_validator');
 *   const result = validateInput(userMessage);
 *   // result: { valid, riskLevel, reasons, sanitized }
 */

'use strict';

// ═══════════════════════════════════════════════
// Prompt注入检测模式
// ═══════════════════════════════════════════════

const INJECTION_PATTERNS = [
  // 直接指令覆盖
  { pattern: /ignore\s+(all\s+)?previous\s+instructions/i, risk: 'high', desc: '尝试忽略先前指令' },
  { pattern: /ignore\s+(all\s+)?above\s+instructions/i, risk: 'high', desc: '尝试忽略上方指令' },
  { pattern: /forget\s+(all\s+)?(your|previous)\s+instructions/i, risk: 'high', desc: '尝试遗忘指令' },
  { pattern: /disregard\s+(all\s+)?(prior|previous|above)/i, risk: 'high', desc: '尝试无视先前设置' },
  
  // 角色劫持
  { pattern: /you\s+are\s+now\s+(a|an|the|my)/i, risk: 'high', desc: '尝试角色劫持' },
  { pattern: /act\s+as\s+(a|an|the|if\s+you\s+were)/i, risk: 'high', desc: '尝试伪装角色' },
  { pattern: /pretend\s+(to\s+be|you\s+are|that)/i, risk: 'medium', desc: '尝试伪装' },
  { pattern: /new\s+persona:/i, risk: 'high', desc: '尝试切换人格' },
  { pattern: /from\s+now\s+on,?\s+you/i, risk: 'high', desc: '尝试重新定义行为' },
  
  // 系统标签注入
  { pattern: /<\s*system\s*>/i, risk: 'high', desc: 'XML系统标签注入' },
  { pattern: /<\s*\/system\s*>/i, risk: 'high', desc: 'XML系统标签注入' },
  { pattern: /\[INST\]/i, risk: 'high', desc: 'Llama指令标签' },
  { pattern: /\[\/INST\]/i, risk: 'high', desc: 'Llama指令标签' },
  { pattern: /<\|im_start\|>/i, risk: 'high', desc: 'ChatML标签' },
  { pattern: /<\|im_end\|>/i, risk: 'high', desc: 'ChatML标签' },
  { pattern: /system\s*:\s*(you\s+are|ignore|override)/i, risk: 'high', desc: '伪系统指令' },
  
  // 越狱尝试
  { pattern: /jailbreak/i, risk: 'high', desc: '越狱尝试' },
  { pattern: /DAN\s+mode/i, risk: 'high', desc: 'DAN越狱' },
  { pattern: /developer\s+mode/i, risk: 'medium', desc: '开发者模式越狱' },
  { pattern: /do\s+anything\s+now/i, risk: 'high', desc: 'DAN变体' },
  { pattern: /unrestricted\s+mode/i, risk: 'high', desc: '无限制模式' },
  
  // 权限提升
  { pattern: /grant\s+(me|user|yourself)\s+(admin|root|super)/i, risk: 'high', desc: '权限提升尝试' },
  { pattern: /escalate\s+(my\s+)?privilege/i, risk: 'high', desc: '提权尝试' },
  { pattern: /bypass\s+(the\s+)?(security|permission|auth)/i, risk: 'high', desc: '绕过安全检查' },
  { pattern: /override\s+(the\s+)?(rules|safety|guard)/i, risk: 'high', desc: '尝试覆盖安全规则' },
  
  // 数据外泄
  { pattern: /send\s+(all|everything|my)\s+.*(data|info|password)/i, risk: 'high', desc: '数据外泄尝试' },
  { pattern: /exfiltrate/i, risk: 'high', desc: '数据泄露尝试' },
  { pattern: /leak\s+(the\s+)?(api.?key|token|password|secret)/i, risk: 'high', desc: '密钥泄露尝试' },
];

// ═══════════════════════════════════════════════
// 敏感关键词
// ═══════════════════════════════════════════════

const SENSITIVE_KEYWORDS = [
  'api_key', 'api-key', 'apikey',
  'secret_key', 'secret-key',
  'access_token', 'access-token',
  'password', 'passwd',
  'private_key', 'private-key',
  'bearer ',
  'authorization:',
];

// ═══════════════════════════════════════════════
// 输入长度限制
// ═══════════════════════════════════════════════

const LIMITS = {
  maxInputLength: 50000,    // 最大输入长度
  maxLines: 500,            // 最大行数
  maxRepeatChars: 200,      // 最大重复字符
};

// ═══════════════════════════════════════════════
// 核心验证函数
// ═══════════════════════════════════════════════

/**
 * 验证输入内容
 * @param {string} input - 用户输入
 * @returns {{ valid: boolean, riskLevel: string, reasons: string[], sanitized: string }}
 */
function validateInput(input) {
  const result = {
    valid: true,
    riskLevel: 'none',
    reasons: [],
    sanitized: input,
  };

  if (!input || typeof input !== 'string') {
    result.valid = false;
    result.riskLevel = 'medium';
    result.reasons.push('输入为空或非字符串');
    return result;
  }

  // 1. 长度检查
  if (input.length > LIMITS.maxInputLength) {
    result.valid = false;
    result.riskLevel = 'medium';
    result.reasons.push(`输入过长: ${input.length} > ${LIMITS.maxInputLength}`);
    return result;
  }

  const lines = input.split('\n');
  if (lines.length > LIMITS.maxLines) {
    result.valid = false;
    result.riskLevel = 'medium';
    result.reasons.push(`行数过多: ${lines.length} > ${LIMITS.maxLines}`);
    return result;
  }

  // 2. 重复字符检测（flood/DoS）
  const repeatMatch = input.match(/(.)\1{199,}/);
  if (repeatMatch) {
    result.valid = false;
    result.riskLevel = 'medium';
    result.reasons.push('检测到大量重复字符');
    return result;
  }

  // 3. Prompt注入检测
  for (const { pattern, risk, desc } of INJECTION_PATTERNS) {
    if (pattern.test(input)) {
      result.reasons.push(`[注入] ${desc}`);
      if (riskLevel_priority(risk) > level_priority(result.riskLevel)) {
        result.riskLevel = risk;
      }
      if (risk === 'high') {
        result.valid = false;
      }
    }
  }

  // 4. 敏感关键词检测（不阻断，只标记）
  const lowerInput = input.toLowerCase();
  for (const keyword of SENSITIVE_KEYWORDS) {
    if (lowerInput.includes(keyword.toLowerCase())) {
      result.reasons.push(`[敏感] 检测到可能的密钥/凭证: ${keyword}`);
      if (level_priority(result.riskLevel) < level_priority('medium')) {
        result.riskLevel = 'medium';
      }
    }
  }

  return result;
}

/**
 * 风险等级优先级
 */
function level_priority(level) {
  const priorities = { none: 0, low: 1, medium: 2, high: 3 };
  return priorities[level] || 0;
}
function riskLevel_priority(level) {
  return level_priority(level);
}

/**
 * 便捷检查：是否安全
 */
function isSafe(input) {
  return validateInput(input).valid;
}

/**
 * 快速提取被命中的模式名
 */
function getMatchedPatterns(input) {
  return INJECTION_PATTERNS
    .filter(({ pattern }) => pattern.test(input))
    .map(({ desc, risk }) => ({ desc, risk }));
}

// ═══════════════════════════════════════════════
// CLI模式
// ═══════════════════════════════════════════════

if (require.main === module) {
  const input = process.argv.slice(2).join(' ');
  if (!input) {
    console.log('用法: node input_validator.js <待检查的文本>');
    process.exit(1);
  }
  const result = validateInput(input);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}

module.exports = {
  validateInput,
  isSafe,
  getMatchedPatterns,
  INJECTION_PATTERNS,
  SENSITIVE_KEYWORDS,
};
