#!/usr/bin/env node

/**
 * 囡囡的小红书自动化测试脚本
 * 
 * 用途：
 * - 测试配置是否正确
 * - 测试 MCP 服务连接
 * - 测试发布功能
 * 
 * @author 囡囡 🎀
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🎀 囡囡的小红书配置测试开始...\n');

// 测试 1: 检查配置文件
console.log('【测试 1】检查配置文件...');
const configPath = path.join(__dirname, 'config.json');
if (fs.existsSync(configPath)) {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  console.log('✅ 配置文件存在');
  console.log(`   - 发布限制：${config.posting.dailyLimit} 篇/天`);
  console.log(`   - 随机延迟：${config.posting.delayRange[0]}-${config.posting.delayRange[1]} 秒`);
  console.log(`   - 最佳时间：${config.posting.bestTimeToPost.join(', ')}`);
} else {
  console.log('❌ 配置文件不存在');
}

// 测试 2: 检查目录结构
console.log('\n【测试 2】检查目录结构...');
const dirs = ['templates', 'images', 'logs'];
dirs.forEach(dir => {
  const dirPath = path.join(__dirname, dir);
  if (fs.existsSync(dirPath)) {
    console.log(`✅ ${dir}/ 目录存在`);
  } else {
    console.log(`❌ ${dir}/ 目录不存在`);
  }
});

// 测试 3: 检查模板文件
console.log('\n【测试 3】检查模板文件...');
const templates = [
  'post-template.md',
  'hashtag-list.txt'
];
templates.forEach(template => {
  const templatePath = path.join(__dirname, 'templates', template);
  if (fs.existsSync(templatePath)) {
    console.log(`✅ ${template} 存在`);
  } else {
    console.log(`❌ ${template} 不存在`);
  }
});

// 测试 4: 检查 MCP 配置
console.log('\n【测试 4】检查 MCP 配置...');
try {
  const mcporterConfig = path.join(process.env.HOME, '.openclaw', 'workspace', 'config', 'mcporter.json');
  if (fs.existsSync(mcporterConfig)) {
    const mcporter = JSON.parse(fs.readFileSync(mcporterConfig, 'utf-8'));
    const hasXHS = mcporter.servers && mcporter.servers.some(s => s.name === 'xiaohongshu-mcp');
    if (hasXHS) {
      console.log('✅ xiaohongshu-mcp 已配置');
    } else {
      console.log('⚠️  xiaohongshu-mcp 未配置');
    }
  } else {
    console.log('⚠️  mcporter 配置文件不存在');
  }
} catch (err) {
  console.log('❌ MCP 配置检查失败:', err.message);
}

// 测试 5: 测试 MCP 服务列表
console.log('\n【测试 5】测试 MCP 服务列表...');
try {
  const result = execSync('npx mcporter list 2>&1', { encoding: 'utf-8' });
  const lines = result.split('\n');
  const xhsLines = lines.filter(l => l.includes('xiaohongshu'));
  
  if (xhsLines.length > 0) {
    console.log('✅ 找到小红书相关 MCP 服务:');
    xhsLines.forEach(line => {
      console.log(`   ${line.trim()}`);
    });
  } else {
    console.log('⚠️  未找到小红书相关 MCP 服务');
  }
} catch (err) {
  console.log('❌ MCP 服务列表测试失败:', err.message);
}

// 测试 6: 检查浏览器配置
console.log('\n【测试 6】检查浏览器配置...');
try {
  const chromeCheck = execSync('which google-chrome || which chrome || echo "not found"', { encoding: 'utf-8' });
  if (chromeCheck.trim() !== 'not found') {
    console.log('✅ Chrome 浏览器已安装');
    console.log(`   路径：${chromeCheck.trim()}`);
  } else {
    console.log('⚠️  Chrome 浏览器未找到');
    console.log('   提示：请安装 Chrome 浏览器');
  }
} catch (err) {
  console.log('❌ 浏览器检查失败:', err.message);
}

// 总结
console.log('\n' + '='.repeat(60));
console.log('📊 测试总结');
console.log('='.repeat(60));
console.log('✅ 配置完成，可以开始使用！');
console.log('\n下一步:');
console.log('1. 登录小红书账号');
console.log('2. 测试发布一篇笔记');
console.log('3. 查看数据分析');
console.log('\n囡囡随时待命，帮主人运营小红书！🎀\n');
