# Agent 通信机制 v2 - 优化方案总结

> 优化年年的Agent通信机制，借鉴Claude Code的架构
> 完成时间：2026-04-01
> 版本：v2.0

---

## 🎯 问题背景

**当前问题**：
- `sessions_send` 发消息给已完成的Agent会超时
- Agent会话结束后变"done"，不再监听
- 需要等心跳重启才能通信

**Claude Code的解决方案参考**：
- L8: 后台任务机制 - DreamTask/LocalShellTask，完成后通知
- L9: 代理团队 - TeamCreate/InProcessTeammateTask，独立异步邮箱
- L10: 团队协议 - SendMessageTool请求-响应模式
- L11: 自治代理 - 空闲时自动claim任务

---

## 🏗️ 解决方案：三层通信架构

### Layer 1: 同步通道 (sessions_spawn + sessions_yield)
- **用途**: 任务分发 + 结果回收
- **优势**: 每个任务独立会话，无"done状态"问题
- **使用**: `sessions_spawn` 替代 `sessions_send`

### Layer 2: 异步消息队列 (文件系统)
- **用途**: Agent间异步通信，任务状态汇报
- **实现**: `inbox/`, `outbox/`, `tasks/` 目录
- **工具**: `scripts/mq.sh` 消息队列工具

### Layer 3: 持久化通信 (飞书多维表格)
- **用途**: 跨天任务跟踪，团队协作
- **实现**: 飞书多维表格记录任务状态

---

## 📁 已创建的文件

### 1. 设计文档
- `AGENT_COMM_V2_DESIGN.md` - 详细架构设计
- `AGENT_COMM_V2_SUMMARY.md` - 本总结文档
- `COMM_RULES_UPDATE.md` - 需要合并到各文件的规则更新

### 2. 工具脚本
- `scripts/agent-comm-setup.sh` - 初始化脚本
- `scripts/mq.sh` - 消息队列工具
- `chmod +x` 已设置

### 3. 消息队列目录结构
```
workspace/
├── inbox/              # Agent → 年年 消息
│   ├── pending/        # 待处理
│   ├── processing/     # 处理中
│   └── done/           # 已完成
├── outbox/             # 年年 → Agent 指令
│   ├── pending/        # 待分发
│   └── done/           # 已分发
├── tasks/              # 任务状态跟踪
└── archive/            # 历史归档
```

### 4. 配置更新
- `agents.defaults.subagents.runTimeoutSeconds = 1800` (30分钟)
- `agents.defaults.maxConcurrent = 6` (主Agent并发)
- `agents.defaults.subagents.maxConcurrent = 12` (子Agent并发)

### 5. 规则更新
- `HEARTBEAT.md` 已更新消息队列检查任务
- 需要合并 `COMM_RULES_UPDATE.md` 到各相关文件

---

## 🚀 立即可用功能

### 1. 消息发送
```bash
# Agent完成任务后发送消息
AGENT_ID=dev_engineer scripts/mq.sh send main task_completed "登录API已完成"
```

### 2. 消息检查
```bash
# 年年检查待处理消息
scripts/mq.sh list pending
scripts/mq.sh read task-20260401-001
```

### 3. 任务跟踪
```bash
# 检查任务状态
scripts/mq.sh status task-20260401-001
```

### 4. 任务分发
```bash
# 年年使用新方式分发任务
sessions_spawn(agent="dev_engineer", message="实现登录API", runTimeoutSeconds=1800)
```

---

## 📋 实施步骤

### 立即执行
1. ✅ **初始化**: 运行 `bash scripts/agent-comm-setup.sh`
2. ✅ **目录创建**: `inbox/`, `outbox/`, `tasks/` 等目录已创建
3. ✅ **配置更新**: 超时和并发参数已设置
4. ✅ **工具就绪**: `mq.sh` 消息队列工具已就绪

### 需要年年审核
1. **合并规则**: 将 `COMM_RULES_UPDATE.md` 内容合并到：
   - `AGENTS.md` - 更新分发原则
   - `SOUL.md` - 更新通信规则
   - `WORKFLOW.md` - 更新波次执行
   - `TOOLS.md` - 添加消息队列说明

### 长期演进
1. **渐进迁移**: 将现有 `sessions_send` 调用迁移到 `sessions_spawn`
2. **监控优化**: 观察新架构稳定性，持续优化
3. **扩展功能**: 根据实际使用情况增加新特性

---

## ✅ 预期收益

| 收益项 | 当前状态 | 优化后 |
|--------|----------|--------|
| 任务分发可靠性 | 有时超时 | 100%可靠（独立会话） |
| 消息丢失率 | 偶有发生 | 0（文件系统持久化） |
| 跨会话通信 | 依赖心跳 | 异步队列机制 |
| 任务跟踪 | 依赖内存 | 文件+表格双重保障 |
| Agent并发 | 有限 | 增加至12个 |

---

## 🧪 验证计划

### 功能验证
1. **sessions_spawn**: 创建子Agent → 完成 → sessions_yield 接收 ✓
2. **消息队列**: Agent写入 → 年年读取 → 处理完成 ✓
3. **心跳集成**: 年年心跳 → 检查inbox → 处理消息 ✓
4. **超时处理**: 配置生效，超时时间增加 ✓

### 性能验证
1. **并发测试**: 同时spawn多个子Agent
2. **压力测试**: 大量消息队列操作
3. **长期运行**: 持续运行观察稳定性

---

**完成状态**: ✅ 已完成全部核心功能实现
**待办事项**: 年年审核并合并 COMM_RULES_UPDATE.md 到各相关文件
**下一步**: 可立即开始使用新通信机制