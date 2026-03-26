#!/usr/bin/env node

/**
 * 囡囡的代码沙箱
 * 
 * 功能：
 * 1. Docker 容器隔离执行
 * 2. 多语言支持
 * 3. 资源限制
 * 4. 超时控制
 * 5. 输出捕获
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 配置
const config = {
    defaultTimeout: 30000, // 30 秒
    defaultMemory: '512m',
    defaultCpu: 1.0,
    workDir: '/tmp/code-sandbox',
    languages: {
        python3: {
            image: 'python:3.11-slim',
            command: 'python',
            extension: '.py'
        },
        node: {
            image: 'node:20-slim',
            command: 'node',
            extension: '.js'
        },
        go: {
            image: 'golang:1.21-alpine',
            command: 'go run',
            extension: '.go'
        }
    }
};

/**
 * 生成唯一 ID
 */
function generateId() {
    return crypto.randomBytes(8).toString('hex');
}

/**
 * 执行 shell 命令
 */
function exec(command, options = {}) {
    try {
        return execSync(command, {
            encoding: 'utf8',
            timeout: options.timeout || 60000,
            ...options
        });
    } catch (error) {
        throw new Error(`命令执行失败：${error.message}`);
    }
}

/**
 * 检查 Docker 是否可用
 */
function checkDocker() {
    try {
        execSync('docker --version', { encoding: 'utf8' });
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * 创建沙箱环境
 */
async function createSandbox(language) {
    const langConfig = config.languages[language];
    if (!langConfig) {
        throw new Error(`不支持的语言：${language}`);
    }
    
    const containerId = `sandbox-${generateId()}`;
    const workDir = path.join(config.workDir, containerId);
    
    // 创建工作目录
    if (!fs.existsSync(workDir)) {
        fs.mkdirSync(workDir, { recursive: true });
    }
    
    return {
        containerId,
        workDir,
        langConfig
    };
}

/**
 * 执行代码
 */
async function execute(code, options = {}) {
    const {
        language = 'python3',
        timeout = config.defaultTimeout,
        memory = config.defaultMemory,
        cpu = config.defaultCpu,
        network = false
    } = options;
    
    console.log('🔒 代码沙箱执行开始...\n');
    
    // 检查 Docker
    if (!checkDocker()) {
        console.log('❌ Docker 不可用，使用本地执行模式');
        return executeLocal(code, { language, timeout });
    }
    
    try {
        // 创建沙箱
        const sandbox = await createSandbox(language);
        const { containerId, workDir, langConfig } = sandbox;
        
        console.log(`📦 语言：${language}`);
        console.log(`⏱️  超时：${timeout}ms`);
        console.log(`💾 内存：${memory}`);
        console.log(`🔌 网络：${network ? '启用' : '禁用'}`);
        
        // 写入代码文件
        const codeFile = path.join(workDir, `code${langConfig.extension}`);
        fs.writeFileSync(codeFile, code);
        console.log(`\n📝 代码文件：${codeFile}`);
        
        // 构建 Docker 命令
        const dockerArgs = [
            'docker run --rm',
            `--name ${containerId}`,
            `--memory ${memory}`,
            `--cpus ${cpu}`,
            `--pids-limit 50`,
            '--cap-drop=ALL',
            '--security-opt=no-new-privileges',
            `--mount type=bind,source=${workDir},target=/code,readonly`,
            `--mount type=tmpfs,destination=/tmp`,
            network ? '' : '--network none',
            langConfig.image,
            `${langConfig.command} /code/code${langConfig.extension}`
        ].filter(arg => arg).join(' ');
        
        console.log(`\n🚀 执行命令：${dockerArgs}\n`);
        
        // 执行
        const startTime = Date.now();
        let stdout = '';
        let stderr = '';
        let exitCode = 0;
        
        try {
            const result = execSync(dockerArgs, {
                encoding: 'utf8',
                timeout: timeout,
                stdio: ['pipe', 'pipe', 'pipe']
            });
            stdout = result;
        } catch (error) {
            if (error.signal === 'SIGKILL' || error.message.includes('OOM')) {
                stderr = '内存超出限制';
                exitCode = 137;
            } else if (error.message.includes('timeout')) {
                stderr = '执行超时';
                exitCode = 124;
            } else {
                stderr = error.stderr || error.message;
                exitCode = error.status || 1;
            }
        }
        
        const executionTime = Date.now() - startTime;
        
        // 结果
        const result = {
            success: exitCode === 0,
            exitCode,
            stdout,
            stderr,
            executionTime,
            language,
            timestamp: new Date().toISOString()
        };
        
        // 输出结果
        console.log('📊 执行结果:\n');
        if (result.stdout) {
            console.log('✅ 输出:');
            console.log(result.stdout);
        }
        if (result.stderr) {
            console.log('❌ 错误:');
            console.log(result.stderr);
        }
        console.log(`\n⏱️  执行时间：${executionTime}ms`);
        console.log(`🔚 退出码：${exitCode}`);
        
        return result;
        
    } catch (error) {
        console.error(`\n❌ 沙箱执行失败：${error.message}`);
        return {
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * 本地执行（Docker 不可用时）
 */
function executeLocal(code, options = {}) {
    const { language = 'python3', timeout = 30000 } = options;
    
    console.log('⚠️  使用本地执行模式（无沙箱隔离）\n');
    
    const workDir = path.join(config.workDir, 'local', generateId());
    fs.mkdirSync(workDir, { recursive: true });
    
    try {
        let command;
        let codeFile;
        
        if (language === 'python3') {
            codeFile = path.join(workDir, 'code.py');
            fs.writeFileSync(codeFile, code);
            command = `python3 ${codeFile}`;
        } else if (language === 'node') {
            codeFile = path.join(workDir, 'code.js');
            fs.writeFileSync(codeFile, code);
            command = `node ${codeFile}`;
        } else {
            throw new Error(`本地模式不支持：${language}`);
        }
        
        const startTime = Date.now();
        let stdout = '';
        let stderr = '';
        let exitCode = 0;
        
        try {
            stdout = execSync(command, {
                encoding: 'utf8',
                timeout,
                cwd: workDir
            });
        } catch (error) {
            stderr = error.stderr || error.message;
            exitCode = error.status || 1;
        }
        
        const executionTime = Date.now() - startTime;
        
        // 清理
        try {
            fs.rmSync(workDir, { recursive: true, force: true });
        } catch (e) {}
        
        const result = {
            success: exitCode === 0,
            exitCode,
            stdout,
            stderr,
            executionTime,
            language,
            mode: 'local',
            timestamp: new Date().toISOString()
        };
        
        console.log('📊 执行结果:\n');
        if (result.stdout) console.log('✅ 输出:', result.stdout);
        if (result.stderr) console.log('❌ 错误:', result.stderr);
        console.log(`⏱️  执行时间：${executionTime}ms`);
        
        return result;
        
    } catch (error) {
        console.error(`❌ 执行失败：${error.message}`);
        return {
            success: false,
            error: error.message
        };
    }
}

// 命令行参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {};
    let code = '';
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        
        if (arg === '-l' || arg === '--lang') {
            options.language = args[++i];
        } else if (arg === '-t' || arg === '--timeout') {
            options.timeout = parseInt(args[++i]);
        } else if (arg === '-m' || arg === '--memory') {
            options.memory = args[++i];
        } else if (arg === '-c' || arg === '--code') {
            code = args[++i];
        } else if (arg === '-f' || arg === '--file') {
            code = fs.readFileSync(args[++i], 'utf8');
        } else if (arg === '--network') {
            options.network = true;
        } else if (arg === '--help' || arg === '-h') {
            console.log(`
代码沙箱 - 囡囡 🔒

用法：code-sandbox [选项]

选项:
  -l, --lang <lang>      编程语言 (python3|node|go)
  -t, --timeout <ms>     超时时间 (毫秒)
  -m, --memory <size>    内存限制 (如 512m)
  -c, --code <code>      直接执行代码
  -f, --file <file>      执行文件
  --network              启用网络访问
  -h, --help             显示帮助

示例:
  code-sandbox -l python3 -c "print('Hello')"
  code-sandbox -l node -f script.js
  code-sandbox -l python3 --timeout 5000 script.py
`);
            process.exit(0);
        }
    }
    
    return { options, code };
}

// 主函数
if (require.main === module) {
    const { options, code } = parseArgs();
    
    if (!code) {
        console.log('❌ 请提供代码（使用 -c 或 -f 选项）');
        process.exit(1);
    }
    
    execute(code, options).then(result => {
        process.exit(result.success ? 0 : 1);
    });
}

// 导出
module.exports = { execute, executeLocal, config };
