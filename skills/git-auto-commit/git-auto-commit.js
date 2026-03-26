#!/usr/bin/env node

/**
 * 囡囡的 Git 自动提交工具
 * 
 * 功能：
 * 1. 自动检测代码变更
 * 2. 智能生成 commit message
 * 3. 自动创建 branch
 * 4. 自动推送
 * 5. 可选创建 PR
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 配置
const config = {
    autoBranch: true,
    autoPush: true,
    autoPR: false,
    commitStyle: 'conventional', // conventional | simple
    maxMessageLength: 72
};

// Commit 类型
const commitTypes = {
    feat: '新功能',
    fix: 'Bug 修复',
    docs: '文档更新',
    style: '代码格式',
    refactor: '重构',
    test: '测试相关',
    chore: '构建/工具',
    perf: '性能优化',
    ci: 'CI 配置'
};

/**
 * 执行 git 命令
 */
function git(args, cwd = process.cwd()) {
    try {
        return execSync(`git ${args}`, { cwd, encoding: 'utf8' }).trim();
    } catch (error) {
        throw new Error(`Git 命令失败：${error.message}`);
    }
}

/**
 * 检测变更文件
 */
function detectChanges() {
    console.log('🔍 检测代码变更...');
    
    const status = git('status --porcelain');
    
    if (!status) {
        console.log('✅ 没有检测到变更');
        return null;
    }
    
    const files = status.split('\n').map(line => {
        const status = line.substring(0, 2).trim();
        const file = line.substring(3).trim();
        return { status, file };
    });
    
    console.log(`📁 检测到 ${files.length} 个变更文件:`);
    files.forEach(f => console.log(`   ${f.status} ${f.file}`));
    
    return files;
}

/**
 * 推断 commit 类型
 */
function inferCommitType(files) {
    const fileStr = files.map(f => f.file).join(' ');
    
    if (fileStr.includes('.test.') || fileStr.includes('test/')) return 'test';
    if (fileStr.includes('.md') || fileStr.includes('docs/')) return 'docs';
    if (fileStr.includes('package.json') || fileStr.includes('package-lock.json')) return 'chore';
    if (fileStr.includes('.github/') || fileStr.includes('.gitlab-ci.yml')) return 'ci';
    if (fileStr.includes('fix') || fileStr.includes('bug')) return 'fix';
    
    return 'feat';
}

/**
 * 推断 scope
 */
function inferScope(files) {
    const dirs = files.map(f => f.file.split('/')[0]);
    const uniqueDirs = [...new Set(dirs)];
    
    if (uniqueDirs.length === 1) return uniqueDirs[0];
    if (uniqueDirs.length > 3) return 'multiple';
    
    return uniqueDirs.join(',');
}

/**
 * 生成 commit message
 */
function generateCommitMessage(files, type, customMessage = null) {
    if (customMessage) {
        return `${type}: ${customMessage}`;
    }
    
    const scope = inferScope(files);
    
    // 分析变更内容
    const actions = [];
    const fileCount = files.length;
    
    // 简单描述
    if (fileCount === 1) {
        const file = files[0].file;
        const fileName = path.basename(file, path.extname(file));
        
        if (files[0].status.includes('A')) {
            actions.push(`添加 ${fileName}`);
        } else if (files[0].status.includes('D')) {
            actions.push(`删除 ${fileName}`);
        } else {
            actions.push(`更新 ${fileName}`);
        }
    } else {
        actions.push(`更新 ${fileCount} 个文件`);
    }
    
    const description = actions.join('; ');
    
    if (scope && scope !== 'multiple') {
        return `${type}(${scope}): ${description}`;
    }
    
    return `${type}: ${description}`;
}

/**
 * 创建 feature branch
 */
function createFeatureBranch(type) {
    const currentBranch = git('branch --show-current');
    
    if (['main', 'master'].includes(currentBranch)) {
        const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
        const shortHash = git('rev-parse --short HEAD');
        const branchName = `${type}/auto-${timestamp}-${shortHash}`;
        
        console.log(`🌿 创建新分支：${branchName}`);
        git(`checkout -b ${branchName}`);
        
        return branchName;
    }
    
    return currentBranch;
}

/**
 * 自动提交
 */
async function autoCommit(options = {}) {
    const {
        type: customType,
        message: customMessage,
        branch: customBranch,
        push = true,
        pr = false,
        dryRun = false
    } = options;
    
    console.log('🚀 Git 自动提交开始...\n');
    
    try {
        // 1. 检测变更
        const files = detectChanges();
        if (!files) return;
        
        // 2. 推断 commit 类型
        const type = customType || inferCommitType(files);
        console.log(`📝 推断类型：${type} (${commitTypes[type] || '未知'})`);
        
        // 3. 生成 commit message
        const commitMessage = generateCommitMessage(files, type, customMessage);
        console.log(`💬 Commit Message: ${commitMessage}`);
        
        if (dryRun) {
            console.log('\n⚠️  预览模式，不执行实际提交');
            return;
        }
        
        // 4. 创建 branch（如果需要）
        let branchName = customBranch;
        if (config.autoBranch && !customBranch) {
            branchName = createFeatureBranch(type);
        }
        
        // 5. 添加文件
        console.log('\n📦 添加文件...');
        git('add -A');
        
        // 6. 提交
        console.log('✏️  提交变更...');
        git(`commit -m "${commitMessage}"`);
        console.log('✅ 提交成功');
        
        // 7. 推送
        if (push && config.autoPush) {
            console.log('\n📤 推送到远程...');
            git(`push -u origin ${branchName || 'HEAD'}`);
            console.log('✅ 推送成功');
        }
        
        // 8. 创建 PR（如果需要）
        if (pr && config.autoPR) {
            console.log('\n🔗 创建 Pull Request...');
            try {
                git(`pr create --title "${commitMessage}" --body "自动创建的 PR"`);
                console.log('✅ PR 创建成功');
            } catch (error) {
                console.log('⚠️  PR 创建失败（可能需要安装 gh CLI）');
            }
        }
        
        console.log('\n🎉 Git 自动提交完成！\n');
        console.log(`📊 统计:`);
        console.log(`   类型：${type}`);
        console.log(`   分支：${branchName}`);
        console.log(`   文件：${files.length} 个`);
        console.log(`   Message: ${commitMessage}`);
        
    } catch (error) {
        console.error(`\n❌ 错误：${error.message}\n`);
        process.exit(1);
    }
}

// 命令行参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {};
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        
        if (arg === '-t' || arg === '--type') {
            options.type = args[++i];
        } else if (arg === '-m' || arg === '--message') {
            options.message = args[++i];
        } else if (arg === '-b' || arg === '--branch') {
            options.branch = args[++i];
        } else if (arg === '--no-push') {
            options.push = false;
        } else if (arg === '--pr') {
            options.pr = true;
        } else if (arg === '--dry-run') {
            options.dryRun = true;
        } else if (arg === '--help' || arg === '-h') {
            console.log(`
Git 自动提交工具 - 囡囡 🌿

用法：git-auto-commit [选项]

选项:
  -t, --type <type>      Commit 类型 (feat|fix|docs|style|refactor|test|chore|perf|ci)
  -m, --message <msg>    自定义提交消息
  -b, --branch <branch>  指定分支名
  --no-push              不自动推送
  --pr                   创建 Pull Request
  --dry-run              预览模式，不实际提交
  -h, --help             显示帮助

示例:
  git-auto-commit
  git-auto-commit -t fix -m "修复登录问题"
  git-auto-commit --dry-run
`);
            process.exit(0);
        }
    }
    
    return options;
}

// 主函数
if (require.main === module) {
    const options = parseArgs();
    autoCommit(options);
}

// 导出
module.exports = { autoCommit, detectChanges, generateCommitMessage };
