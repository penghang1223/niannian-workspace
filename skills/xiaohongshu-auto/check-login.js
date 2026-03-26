#!/usr/bin/env node

/**
 * 囡囡的小红书登录检查脚本
 * 
 * 用途：
 * - 检查 Chrome 是否运行
 * - 检查小红书是否登录
 * - 生成检查报告
 * 
 * @author 囡囡 🎀
 */

const fs = require('fs');
const path = require('path');

console.log('🎀 囡囡的小红书登录状态检查...\n');

// 检查 1: Chrome 是否安装
console.log('【检查 1】检查 Chrome 浏览器...');
const chromePaths = [
  '/Applications/Google Chrome.app',
  process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
  '/usr/bin/google-chrome'
];

let chromeInstalled = false;
for (const chromePath of chromePaths) {
  if (fs.existsSync(chromePath)) {
    console.log(`✅ Chrome 已安装：${chromePath}`);
    chromeInstalled = true;
    break;
  }
}

if (!chromeInstalled) {
  console.log('❌ 未找到 Chrome 浏览器');
}

// 检查 2: 检查技能配置
console.log('\n【检查 2】检查技能配置...');
const configPath = path.join(__dirname, 'config.json');
if (fs.existsSync(configPath)) {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  console.log('✅ 技能配置完成');
  console.log(`   发布限制：${config.posting.dailyLimit} 篇/天`);
  console.log(`   随机延迟：${config.posting.delayRange[0]}-${config.posting.delayRange[1]} 秒`);
} else {
  console.log('❌ 技能配置不存在');
}

// 检查 3: 检查 MCP 配置
console.log('\n【检查 3】检查 MCP 服务...');
try {
  const { execSync } = require('child_process');
  const result = execSync('npx mcporter list 2>&1', { encoding: 'utf-8' });
  const xhsLines = result.split('\n').filter(l => l.includes('xiaohongshu'));
  
  if (xhsLines.length > 0) {
    console.log('✅ 小红书 MCP 服务已配置:');
    xhsLines.forEach(line => {
      const status = line.includes('offline') ? '⚠️  离线' : '✅ 在线';
      console.log(`   ${line.trim()} - ${status}`);
    });
  } else {
    console.log('⚠️  未找到小红书 MCP 服务');
  }
} catch (err) {
  console.log('❌ MCP 服务检查失败:', err.message);
}

// 检查 4: 检查 Cookie 文件
console.log('\n【检查 4】检查登录状态...');
const cookieFile = path.join(__dirname, 'cookies.json');
const sessionFile = path.join(__dirname, 'session.json');

if (fs.existsSync(cookieFile)) {
  console.log('✅ Cookie 文件存在');
  const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf-8'));
  if (cookies.length > 0) {
    console.log(`   Cookie 数量：${cookies.length}`);
    console.log('   ✅ 可能已登录');
  } else {
    console.log('   ⚠️  Cookie 为空，需要登录');
  }
} else if (fs.existsSync(sessionFile)) {
  console.log('✅ Session 文件存在');
  console.log('   ✅ 可能已登录');
} else {
  console.log('⚠️  未找到 Cookie/Session 文件');
  console.log('   需要登录小红书账号');
}

// 检查 5: 检查目录结构
console.log('\n【检查 5】检查目录结构...');
const requiredDirs = ['templates', 'images', 'logs'];
let allDirsExist = true;

requiredDirs.forEach(dir => {
  const dirPath = path.join(__dirname, dir);
  if (fs.existsSync(dirPath)) {
    console.log(`✅ ${dir}/ 目录存在`);
  } else {
    console.log(`❌ ${dir}/ 目录不存在`);
    allDirsExist = false;
  }
});

// 检查 6: 检查模板文件
console.log('\n【检查 6】检查模板文件...');
const requiredFiles = [
  'templates/post-template.md',
  'templates/hashtag-list.txt'
];

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file} 存在`);
  } else {
    console.log(`⚠️  ${file} 不存在`);
  }
});

// 总结
console.log('\n' + '='.repeat(60));
console.log('📊 检查总结');
console.log('='.repeat(60));

const allChecks = [
  chromeInstalled,
  fs.existsSync(configPath),
  allDirsExist
];

if (allChecks.every(c => c)) {
  console.log('✅ 配置完成，可以开始使用！');
  console.log('\n下一步:');
  console.log('1. 打开 Chrome 浏览器');
  console.log('2. 访问 https://www.xiaohongshu.com');
  console.log('3. 扫码登录账号');
  console.log('4. 告诉囡囡"登录好了"');
} else {
  console.log('⚠️  部分配置未完成，请检查上述报告');
}

console.log('\n囡囡随时待命！🎀\n');
