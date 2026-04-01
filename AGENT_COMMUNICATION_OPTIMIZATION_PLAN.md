# Agent 通信机制优化方案

## 问题分析

### 1. 会话生命周期机制

OpenClaw 的会话（Session）有以下关键状态：

| 状态 | 说明 | 触发条件 |
|------|------|---------|
| **active** | Agent 正在处理消息/运行 | 收到用户消息或 sessions_send |
| **idle** | 空闲，等待输入 | 一轮对话完成后 |
| **done** | 子Agent运行完成，结果待取 | sessions_spawn 的子 agent 完成任务 |

**关键发现：**
- 主会话 (`agent:main:main`) 完成一轮对话后进入 idle 状态
- 心跳会话 (`agent:main:main:heartbeat`) 是独立会话（`isolatedSession: true`），每 30 分钟触发一次
- 子 Agent 会话 (`agent:main:subagent:xxx`) 完成后标记为 done，需要 `reactivateCompletedSubagentSession` 重新激活

### 2. sessions_send 超时根因

通过源码分析，`sessions_send` 的工作流程：

```
sessions_send → handleSessionSend → chat.send → 创建新 Run → 队列执行
```

**超时原因有三个层面：**

1. **Run 队列等待**：如果主会话正在进行其他操作（如处理心跳），新 Run 需要排队
2. **子Agent Done 状态**：已完成的子 Agent 虽然可以通过 `reactivateCompletedSubagentSession` 重激活，但有额外开销
3. **timeoutMs 默认值问题**：`sessions_send` 工具没有显式传递 `timeoutMs`，使用全局默认值（2880 分钟 = 48 小时），但实际超时由 Run 执行决定

### 3. 当前配置状态

```json
// 心跳配置
{
  "heartbeat": {
    "every": "30m",           // 每30分钟触发
    "isolatedSession": true,  // 独立会话
    "activeHours": { "start": "08:00", "end": "23:00" }
  },
  "subagents": {
    "maxConcurrent": 8,       // 最大并发子Agent
    "runTimeoutSeconds": 600  // 子Agent运行超时10分钟
  },
  "maxConcurrent": 4          // 主Agent最大并发4
}
```

---

## 优化方案

### 方案 A：优先使用 sessions_spawn 代替 sessions_send（推荐）

**原理**：`sessions_spawn` 创建一个全新的子 Agent 会话，它是独立的、有明确生命周期的执行单元，不存在"done 状态等待唤醒"的问题。

**对比**：

| 特性 | sessions_send | sessions_spawn |
|------|--------------|----------------|
| 目标 | 已存在的会话（可能 idle/done） | 新建子会话（必定活跃） |
| 超时风险 | 高（目标可能不响应） | 低（新会话立即执行） |
| 上下文 | 共享目标会话历史 | 全新上下文（可继承） |
| 生命周期 | 依赖目标会话 | 独立生命周期 |

**实施步骤**：

1. **修改 AGENTS.md 中的分发原则**：
```markdown
## 分发原则（更新版）
1. **优先 sessions_spawn**：任务分发给子Agent时，优先使用 sessions_spawn
   - 每个任务独立会话，无状态耦合
   - 完成后通过 sessions_yield 接收结果
2. **sessions_send 仅用于**：
   - 向 main 会话汇报紧急事项
   - 需要共享完整上下文的长对话
3. **超时设置**：sessions_spawn 设置 runTimeoutSeconds: 900（15分钟）
```

2. **更新 SOUL.md 中的 Agent 通信规则**：
```markdown
## Agent 通信规则（更新版）
- 任务分发 → sessions_spawn（创建新子Agent）
- 结果回收 → sessions_yield（等待子Agent完成）
- 紧急通知 → sessions_send（仅限 main 会话）
- 常规汇报 → 写入文件（workspace/memory/）
```

### 方案 B：文件/共享内存通信介质

**原理**：不依赖会话间直接通信，而是通过共享文件系统作为消息队列。

**架构**：

```
Agent A 完成任务
    ↓
写入 workspace/inbox/{task_id}.json
    ↓
主 Agent 心跳检查 inbox/
    ↓
读取并处理完成的任务
    ↓
归档到 workspace/archive/
```

**实施步骤**：

1. **创建消息目录结构**：
```bash
mkdir -p workspace/inbox
mkdir -p workspace/outbox
mkdir -p workspace/archive
```

2. **定义消息格式** (`workspace/inbox/README.md`)：
```json
{
  "id": "task-uuid",
  "from": "agent_id",
  "to": "main",
  "type": "result|request|notification",
  "timestamp": "ISO-8601",
  "status": "pending|read|archived",
  "payload": {
    "summary": "任务摘要",
    "details": "详细结果",
    "files": ["相关文件路径"]
  }
}
```

3. **在 HEARTBEAT.md 中添加检查逻辑**：
```markdown
## 心跳任务
- [ ] 检查 workspace/inbox/ 中的待处理消息
- [ ] 处理并归档已读消息
- [ ] 检查子Agent是否超时
```

### 方案 C：调整超时和重试配置

**实施步骤**：

1. **增加子 Agent 超时时间**：
```bash
openclaw config set agents.defaults.subagents.runTimeoutSeconds 1800
# 从 600s (10分钟) → 1800s (30分钟)
```

2. **增加最大并发数**：
```bash
openclaw config set agents.defaults.maxConcurrent 6
openclaw config set agents.defaults.subagents.maxConcurrent 12
```

3. **配置 session 通信策略**（如果需要跨会话通信）：
```bash
openclaw config set session.sendPolicy.default allow
```

---

## 推荐实施路径

### 第一阶段（立即执行）：采用方案 A + C

```bash
# 1. 调整配置
openclaw config set agents.defaults.subagents.runTimeoutSeconds 1800
openclaw config set agents.defaults.maxConcurrent 6
openclaw config set agents.defaults.subagents.maxConcurrent 12

# 2. 更新 AGENTS.md（已完成在本方案中）
# 3. 更新 SOUL.md 中的通信规则
```

### 第二阶段（按需）：引入方案 B

如果 sessions_spawn 仍有可靠性问题，引入文件消息队列作为补充机制。

---

## 通信模式决策树

```
需要给子Agent分任务？
├── 是 → sessions_spawn（独立会话，无状态耦合）
│   ├── 需要结果？→ sessions_yield 等待
│   └── 火发不收？→ 不等待，让子Agent写文件汇报
│
├── 向 main 会话汇报紧急事？→ sessions_send
│   └── main 可能 idle？→ 写入 workspace/inbox/ 等心跳处理
│
└── 常规知识共享？→ 写入 SHARED_KNOWLEDGE.md / lessons.md
```

---

## 关键配置参考

| 配置项 | 当前值 | 建议值 | 说明 |
|--------|--------|--------|------|
| `subagents.runTimeoutSeconds` | 600 | 1800 | 子Agent超时30分钟 |
| `maxConcurrent` | 4 | 6 | 主Agent并发 |
| `subagents.maxConcurrent` | 8 | 12 | 子Agent并发 |
| `heartbeat.every` | 30m | 30m | 保持不变 |
| `heartbeat.isolatedSession` | true | true | 保持不变 |

---

## 验证方法

1. **测试 sessions_spawn 可靠性**：
```
- 创建子Agent执行一个2分钟任务
- 验证 sessions_yield 能正确接收结果
- 重复10次，统计成功率
```

2. **测试并发能力**：
```
- 同时 sessions_spawn 6个子Agent
- 验证都能正常完成
```

3. **测试文件通信**：
```
- 子Agent写入 inbox/ 文件
- 主Agent心跳检查并读取
- 验证消息完整性
```

---

*文档生成时间：2026-03-31*
*基于 OpenClaw 2026.3.24 源码分析*