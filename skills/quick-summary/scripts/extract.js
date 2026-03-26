#!/usr/bin/env node

/**
 * Quick Summary - 文本摘要提取脚本
 * 年年的学习练习 - OpenClaw 技能开发
 */

const fs = require('fs');

// 从命令行参数获取文本
const text = process.argv[2] || '';

if (!text) {
  console.log(JSON.stringify({
    error: '请提供需要摘要的文本',
    usage: 'node extract.js "<text>"'
  }));
  process.exit(1);
}

// 简单的摘要提取逻辑
function extractSummary(text) {
  // 按句子分割
  const sentences = text
    .split(/[。！？.!?]+/)
    .map(s => s.trim())
    .filter(s => s.length > 10);

  // 选择前5个句子作为要点
  const keyPoints = sentences.slice(0, 5);

  // 统计信息
  const charCount = text.length;
  const wordCount = text.replace(/\s+/g, '').length;
  const readingTime = Math.ceil(wordCount / 500); // 假设每分钟500字

  return {
    summary: keyPoints,
    stats: {
      originalChars: charCount,
      summaryChars: keyPoints.join('').length,
      compressionRatio: ((1 - keyPoints.join('').length / charCount) * 100).toFixed(1) + '%',
      readingTimeMinutes: readingTime
    }
  };
}

// 执行摘要
const result = extractSummary(text);
console.log(JSON.stringify(result, null, 2));
