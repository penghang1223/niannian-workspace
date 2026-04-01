# Agent 通信机制 v2 — 可靠通信架构设计

> 借鉴 Claude Code L8-L11 架构，解决 OpenClaw Agent 间通信可靠性问题
> 设计时间：2026-04-01
> 版本：v2.0

---

## 一、问题根因分析

### 1.1 OpenClaw 会话生命周期

```
┌─────────────────────────────────────────────────────┐
│              OpenClaw 会话状态机                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [新建] → [active] → [idle] → [done]               │
│              ↑          │         │                  │
│              │          ↓         ↓                  │
│         (新消息)    (心跳重启)  (需要reactivate)      │
│                                                     │
│  主会话: agent:main:main                            │
│    - active: 正在处理用户消息                        │
│    - idle: 完成一轮，等待下次消息                     │
│                                                     │
│  心跳会话: agent:main:main (isolatedSession: true)   │
│    - 每30分钟独立触发                                │
│    - 与主会话共享session key但独立run               │
│                                                     │
│  子Agent: agent:main:subagent:uuid                  │
│    - active → done（任务完成后）                     │
│    - done后需 reactivateCompletedSubagentSession     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 1.2 sessions_send 超时根因（三层）

| 层级 | 原因 | 表现 |
|------|------|------|
| **L1: Run队列阻塞** | 主会话正在执行其他Run（如心跳），新Run需排队 | 超时等待 |
| **L2: 子Agent Done状态** | 完成的子Agent需要reactivate，有额外开销 | 偶发超时 |
| **L3: 网络/模型延迟** | 模型推理慢、网络抖动 | 随机超时 |

### 1.3 Claude Code 架构对比

| Claude Code 层级 | 功能 | OpenClaw 对应 |
|-----------------|------|---------------|
| L8: 后台任务 | DreamTask/LocalShellTask, 完成后通知 | 无直接对应 (cron + sessions_spawn) |
| L9: 代理团队 | TeamCreate/InProcessTeammateTask, 独立邮箱 | 多Agent配置 + sessions |
| L10: 团队协议 | SendMessageTool 请求-响应模式 | sessions_send/sessions_yield |
| L11: 自治代理 | 空闲时自动claim任务 | 心跳 + HEARTBEAT.md |

**关键差异**：Claude Code 的 Agent 持久驻留 + 异步邮箱 vs OpenClaw 的 request-response 模型

---

## 二、三层通信架构设计

### 2.1 架构概览

```
┌───────────────────────────────────────────────────────────┐
│                    三层通信架构                              │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 1: 同步通道 (sessions_spawn + sessions_yield) │  │
│  │  - 任务分发: 每个任务独立子会话                        │  │
│  │  - 结果回收: sessions_yield 等待完成                   │  │
│  │  - 适用: 需要立即拿到结果的任务                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 2: 异步消息队列 (文件系统 inbox/outbox)        │  │
│  │  - 写入: Agent完成任务 → 写入 inbox/                  │  │
│  │  - 读取: 心跳检查 → 读取并处理                         │  │
│  │  - 适用: 不需要立即拿到结果的任务                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 3: 持久化通信 (飞书多维表格/文档)              │  │
│  │  - 任务状态: 多维表格跟踪所有任务                      │  │
│  │  - 知识共享: 文档/知识库存放共享知识                   │  │
│  │  - 适用: 跨天/跨会话的长期任务                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 2.2 Layer 1: 同步通道 (优先使用)

**原理**: `sessions_spawn` 创建全新子会话，不存在"done状态等待唤醒"问题

```
年年 (main)
    │
    ├── sessions_spawn(agent=玄机, task="实现登录API")
    │       │
    │       └── 新子会话立即执行 → 完成后 sessions_yield 接收
    │
    ├── sessions_spawn(agent=鉴微, task="写登录测试")
    │       │
    │       └── 新子会话立即执行 → 完成后 sessions_yield 接收
    │
    └── 等待所有子Agent完成
```

**vs sessions_send 的问题**:
```
年年 (main)
    │
    ├── sessions_send(sessionKey="agent:main:main", msg="做登录API")
    │       │
    │       └── ❌ 目标会话可能idle/done → 超时!
    │
    └── 需要等心跳重启才能通信
```

**适用规则**:
- ✅ 所有任务分发（新任务）
- ✅ 需要立即拿到结果
- ❌ 向已存在的长会话汇报（用Layer 2）

### 2.3 Layer 2: 异步消息队列 (文件系统)

**原理**: 不依赖会话间直接通信，用文件系统作为消息中间件

```
目录结构:
workspace/
├── inbox/           # Agent → 年年 的消息
│   ├── pending/     # 待处理
│   ├── processing/  # 处理中
│   └── done/        # 已完成
├── outbox/          # 年年 → Agent 的指令
│   ├── pending/     # 待分发
│   └── done/        # 已分发
├── tasks/           # 任务状态跟踪
│   └── {task_id}.json
└── archive/         # 历史归档
```

**消息格式** (`inbox/pending/{task_id}.json`):
```json
{
  "id": "task-20260401-001",
  "from": "dev_engineer",
  "to": "main",
  "type": "task_completed",
  "timestamp": "2026-04-01T09:30:00+08:00",
  "status": "completed",
  "task": {
    "name": "实现登录API",
    "wave": 2,
    "acceptance_criteria": ["AC-1", "AC-2"]
  },
  "result": {
    "summary": "登录API完成，支持邮箱+密码登录，JWT token生成",
    "files": ["src/api/auth.py", "tests/test_auth.py"],
    "test_status": "all_passed"
  },
  "metadata": {
    "session_key": "agent:main:subagent:xxx",
    "duration_seconds": 180,
    "tokens_used": 45000
  }
}
```

**心跳集成** (`HEARTBEAT.md`):
```markdown
## 心跳任务
- [ ] 检查 inbox/pending/ 中的消息
- [ ] 处理完成的任务通知
- [ ] 检查超时任务（tasks/ 中超过预期时间的）
- [ ] 归档已处理消息
```

### 2.4 Layer 3: 持久化通信 (飞书)

**适用场景**: 跨天任务、团队协作、需要人工干预

**任务跟踪多维表格结构**:
| 字段 | 类型 | 说明 |
|------|------|------|
| 任务ID | 文本 | task-xxx |
| 任务名称 | 文本 | 任务标题 |
| 负责Agent | 单选 | Agent ID |
| 状态 | 单选 | pending/running/completed/failed |
| 波次 | 数字 | 所属波次 |
| 开始时间 | 日期 | 任务开始 |
| 完成时间 | 日期 | 任务完成 |
| 验收标准 | 文本 | AC列表 |
| 结果摘要 | 文本 | 完成情况 |
| 关联文件 | 超链接 | 相关文件 |

---

## 三、通信决策树 (完整版)

```
需要与其他Agent通信？
│
├── 1. 分发新任务
│   ├── 需要立即拿到结果？
│   │   ├── 是 → sessions_spawn + sessions_yield (Layer 1)
│   │   └── 否 → sessions_spawn (不等待) + 写入 tasks/ (Layer 2)
│   │
│   └── 任务是长期的（跨天/需要跟踪）？
│       └── 是 → 飞书多维表格创建任务记录 (Layer 3)
│
├── 2. 获取已完成任务的结果
│   ├── 子Agent是sessions_spawn创建的？
│   │   ├── 是 → sessions_yield 接收
│   │   └── 否 → 检查 inbox/pending/ (Layer 2)
│   │
│   └── 任务跨天了？
│       └── 是 → 查询飞书多维表格 (Layer 3)
│
├── 3. 紧急通知
│   ├── 目标会话正在活跃？
│   │   ├── 是 → sessions_send (快速)
│   │   └── 否 → 写入 inbox/pending/ (异步)
│   │
│   └── 需要主人看到？
│       └── 是 → 直接通过 message 工具发飞书消息
│
└── 4. 知识共享
    ├── 即时共享 → 写入 SHARED_KNOWLEDGE.md
    ├── 经验教训 → 写入 lessons.md
    └── 项目文档 → 写入飞书文档/知识库
```

---

## 四、超时与重试策略

### 4.1 分级超时配置

```yaml
# Layer 1: 同步通信
sync:
  default_timeout_seconds: 900      # 15分钟
  max_timeout_seconds: 1800         # 30分钟
  retry_count: 1                    # 重试1次
  retry_delay_seconds: 5            # 重试间隔5秒

# Layer 2: 异步通信
async:
  check_interval_minutes: 5         # 每5分钟检查一次
  task_timeout_minutes: 60          # 任务超时1小时
  stale_threshold_minutes: 120      # 2小时未更新视为stale

# Layer 3: 持久化
persistent:
  sync_interval_minutes: 15         # 每15分钟同步状态
  cleanup_days: 30                  # 30天后归档
```

### 4.2 失败处理

```
sessions_spawn 失败？
├── 重试1次（等待5秒）
├── 仍失败 → 降级到 Layer 2（写入 outbox/）
└── 心跳时检查 outbox/ → 重新分发

子Agent超时？
├── 检查 tasks/{task_id}.json 的 last_updated
├── 超过预期时间50% → 发送催促
├── 超过预期时间100% → 标记stale，通知年年
└── 超过预期时间200% → 标记failed，启动备选方案
```

---

## 五、与现有配置集成

### 5.1 需要修改的配置

```bash
# 1. 增加子Agent超时时间
openclaw config set agents.defaults.subagents.runTimeoutSeconds 1800

# 2. 增加并发数
openclaw config set agents.defaults.maxConcurrent 6
openclaw config set agents.defaults.subagents.maxConcurrent 12

# 3. 配置session发送策略
openclaw config set session.sendPolicy.default allow
```

### 5.2 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `AGENTS.md` | 更新分发原则，优先sessions_spawn |
| `SOUL.md` | 更新Agent通信规则 |
| `WORKFLOW.md` | 更新波次执行使用sessions_spawn |
| `HEARTBEAT.md` | 添加inbox/outbox检查 |
| `TOOLS.md` | 添加消息队列使用说明 |

---

## 六、与 Claude Code 架构的映射

### 6.1 实现 Claude Code 的核心模式

| Claude Code 模式 | OpenClaw v2 实现 | 说明 |
|-----------------|-----------------|------|
| L8: 后台任务完成通知 | Layer 2: inbox/ 消息队列 | 任务完成后写入通知文件 |
| L9: 独立异步邮箱 | Layer 2: inbox/outbox 分离 | 每个Agent独立的消息通道 |
| L10: 请求-响应模式 | Layer 1: sessions_spawn + yield | 同步请求-响应 |
| L11: 空闲claim任务 | 心跳检查 outbox/ | Agent空闲时主动领取任务 |

### 6.2 关键差异与适配

| 差异点 | Claude Code | OpenClaw v2 适配 |
|--------|------------|-----------------|
| Agent驻留 | 持久驻留，实时监听 | 通过心跳定期激活 |
| 通信方式 | 内存邮箱 | 文件系统消息队列 |
| 任务调度 | 内置调度器 | 心跳 + cron 辅助 |
| 状态持久化 | 内存 + 数据库 | 文件系统 + 飞书表格 |

---

## 七、验证计划

### 7.1 测试场景

1. **基本通信**: sessions_spawn 创建子Agent → 完成 → sessions_yield 接收
2. **并发通信**: 同时 spawn 6个子Agent → 验证全部正常完成
3. **异步通信**: 子Agent写入 inbox/ → 心跳检查 → 验证消息处理
4. **失败恢复**: 模拟超时 → 验证重试和降级
5. **长期任务**: 创建跨天任务 → 飞书表格跟踪 → 验证状态同步

### 7.2 成功标准

- sessions_spawn 成功率 > 95%
- 消息处理延迟 < 5分钟（Layer 2）
- 任务状态同步延迟 < 15分钟（Layer 3）
- 无消息丢失（通过确认机制保证）

---

*设计完成时间: 2026-04-01*
*基于 OpenClaw 2026.3.24 + Claude Code L8-L11 架构*
