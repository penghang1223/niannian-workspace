# 年年权限系统设计文档

> 版本：1.0 | 日期：2026-04-01
> 参考：Claude Code 5层权限系统

---

## 1. 当前权限现状分析

### 1.1 现有组件

| 组件 | 功能 | 不足 |
|------|------|------|
| `permission_manager.js` | 用户角色验证（admin/beta_user/user） | 只管用户角色，不管Agent/工具 |
| `privacy_filter.js` | 群聊隐私脱敏 | 只过滤输出，不拦截工具调用 |
| `NIANNIAN_RULES.md` | 行为准则 | 只是文档，无强制执行 |

### 1.2 关键缺陷

1. **无工具调用审批** — Agent可以直接执行任何工具，无拦截机制
2. **无输入验证** — prompt注入、恶意指令无防护
3. **无沙箱限制** — 文件操作无路径白名单
4. **无审计日志** — 谁做了什么无记录
5. **Agent权限同质化** — 所有Agent权限相同，无细粒度控制

---

## 2. 权限系统架构（5层设计）

```
┌─────────────────────────────────────────────────┐
│                  用户输入                         │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Layer 1: 输入验证 (InputValidator)              │
│  - prompt注入检测                                 │
│  - 敏感关键词过滤                                  │
│  - 输入长度/格式校验                               │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Layer 2: 规则匹配 (RuleEngine)                  │
│  - alwaysAllowRules → 直接放行                   │
│  - alwaysDenyRules  → 直接拒绝                   │
│  - alwaysAskRules   → 转交互确认                 │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Layer 3: Agent权限检查 (AgentPermissionCheck)   │
│  - Agent→工具白名单                               │
│  - Agent→资源权限                                 │
│  - Agent→敏感操作审批                             │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Layer 4: 工具特定检查 (ToolSpecificCheck)       │
│  - 文件操作：路径沙箱检查                          │
│  - 网络操作：域名白名单                            │
│  - 代码执行：超时+资源限制                         │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Layer 5: 审计日志 (AuditLogger)                 │
│  - 记录所有工具调用                               │
│  - 记录拒绝/允许决策                              │
│  - 异常检测+告警                                  │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│                  实际执行                         │
└─────────────────────────────────────────────────┘
```

---

## 3. 核心组件设计

### 3.1 输入验证器 (InputValidator)

**职责**：第一道防线，拒绝非法输入

```javascript
// 检测规则
const BLOCKED_PATTERNS = [
  /ignore\s+(all\s+)?previous\s+instructions/i,  // prompt注入
  /you\s+are\s+now\s+(a|an|the)/i,               // 角色劫持
  /system\s*:\s*/i,                               // 伪系统指令
  /<\s*system\s*>/i,                              // XML注入
  /\[INST\]|\[\/INST\]/i,                         // 指令标签
  /jailbreak/i,                                   // 越狱尝试
];

// 输出：{ valid: boolean, reason?: string, risk_level: 'low'|'medium'|'high' }
```

### 3.2 规则匹配引擎 (RuleEngine)

**配置文件**：`permissions/rules.json`

```json
{
  "alwaysAllowRules": [
    { "tool": "read", "pathPattern": "/Users/narain/.openclaw/workspace/**" },
    { "tool": "web_search", "action": "*" },
    { "tool": "feishu_search_doc_wiki", "action": "search" }
  ],
  "alwaysDenyRules": [
    { "tool": "exec", "commandPattern": "rm -rf /" },
    { "tool": "exec", "commandPattern": "curl * | bash" },
    { "tool": "write", "pathPattern": "/etc/**" },
    { "tool": "write", "pathPattern": "~/.ssh/**" },
    { "tool": "exec", "commandPattern": "sudo *" },
    { "tool": "feishu_oauth", "action": "revoke" }
  ],
  "alwaysAskRules": [
    { "tool": "exec", "commandPattern": "git push *" },
    { "tool": "feishu_im_user_message", "action": "send" },
    { "tool": "feishu_create_doc", "action": "*" },
    { "tool": "feishu_calendar_event", "action": "create" },
    { "tool": "delete", "pathPattern": "*" }
  ]
}
```

### 3.3 Agent权限配置 (AgentPermissions)

**配置文件**：`permissions/agent_permissions.json`

```json
{
  "agentProfiles": {
    "main": {
      "description": "年年主Agent - 最高权限",
      "allowedTools": ["*"],
      "deniedTools": [],
      "maxConcurrentCalls": 5,
      "requireApproval": false
    },
    "frontend_dev": {
      "description": "霓裳 - 前端Agent",
      "allowedTools": ["read", "write", "exec", "browser", "web_fetch"],
      "deniedTools": ["feishu_im_user_message", "feishu_oauth", "feishu_calendar_event"],
      "maxConcurrentCalls": 3,
      "requireApproval": ["exec:git push *", "exec:npm publish *"]
    },
    "qa_engineer": {
      "description": "鉴微 - 测试Agent",
      "allowedTools": ["read", "exec", "web_search", "web_fetch"],
      "deniedTools": ["feishu_*", "write", "edit", "delete"],
      "maxConcurrentCalls": 3,
      "requireApproval": []
    },
    "default": {
      "description": "未配置Agent的默认权限",
      "allowedTools": ["read", "web_search", "web_fetch"],
      "deniedTools": ["exec", "feishu_*", "write", "edit", "delete"],
      "maxConcurrentCalls": 2,
      "requireApproval": ["*"]
    }
  }
}
```

### 3.4 工具特定检查

**文件操作沙箱**：
- 工作目录：`/Users/narain/.openclaw/workspace/**` (读写)
- 临时目录：`/tmp/openclaw/**` (读写)
- 主目录：`~/**` (只读)
- 系统目录：`/etc/**`, `/usr/**` (禁止)

**网络操作白名单**：
- 搜索引擎：google.com, bing.com, brave.com
- 飞书：*.feishu.cn, *.larksuite.com
- GitHub：github.com, api.github.com
- 其他需逐项添加

### 3.5 审计日志 (AuditLogger)

**日志格式**：
```json
{
  "timestamp": "2026-04-01T09:00:00+08:00",
  "agent_id": "frontend_dev",
  "tool": "exec",
  "action": "read",
  "params_hash": "sha256:...",
  "decision": "allow|deny|ask",
  "reason": "匹配alwaysAllowRules",
  "risk_level": "low",
  "execution_time_ms": 1200,
  "success": true
}
```

**日志存储**：`/Users/narain/.openclaw/workspace/logs/audit/YYYY-MM-DD.jsonl`

**告警条件**：
- 同一Agent 1分钟内被拒绝3次 → 告警
- 高风险操作被允许 → 告警
- 非白名单路径访问 → 告警

---

## 4. 与OpenClaw的集成方式

由于OpenClaw是黑盒运行时（我们无法修改其内部），权限系统采用**外部包装器**模式：

```
用户请求 → OpenClaw运行时 → 年年Agent
                                  │
                                  ▼
                          permission_wrapper.js
                          (在Agent的指令中加载)
                                  │
                          ┌───────┴───────┐
                          ▼               ▼
                      允许执行         拒绝/询问
```

**集成点**：
1. **SOUL.md / AGENTS.md** — 添加权限检查指令
2. **每个Agent的capability.json** — 定义权限配置
3. **脚本层** — 提供 `scripts/permission_wrapper.js` 供exec调用
4. **审计层** — 心跳时检查审计日志

---

## 5. 文件清单

| 文件 | 说明 |
|------|------|
| `permissions/rules.json` | 规则配置 |
| `permissions/agent_permissions.json` | Agent权限配置 |
| `scripts/permission_wrapper.js` | 权限检查主引擎 |
| `scripts/input_validator.js` | 输入验证器 |
| `scripts/audit_logger.js` | 审计日志 |
| `scripts/rule_engine.js` | 规则匹配引擎 |
| `PERMISSION_SYSTEM.md` | 本文档 |

---

## 6. 使用指南

### 主人如何管理权限

1. **编辑规则**：直接修改 `permissions/rules.json`
2. **查看审计日志**：`cat logs/audit/YYYY-MM-DD.jsonl | jq .`
3. **紧急禁用Agent**：在 `agent_permissions.json` 中设 `"deniedTools": ["*"]`
4. **添加新Agent权限**：在 `agent_permissions.json` 添加配置

### Agent如何使用

在执行工具调用前，运行权限检查：

```javascript
const checker = require('./scripts/permission_wrapper');
const result = checker.checkPermission({
  agent_id: 'frontend_dev',
  tool: 'exec',
  command: 'git push origin main'
});
if (result.allowed) { /* 执行 */ } else { /* 拒绝/询问 */ }
```
