# Agent 通信规则更新 (v2)

> 此文件包含需要合并到 AGENTS.md / SOUL.md / HEARTBEAT.md 的更新内容
> 状态：待年年审核后合并

---

## 1. AGENTS.md 更新 - 分发原则

**替换现有分发原则为：**

```markdown
## 分发原则（v2 - 三层通信架构）
1. **优先 sessions_spawn**：任务分发给子Agent时，优先使用 sessions_spawn
   - 每个任务独立会话，无状态耦合，不存在"done状态等唤醒"问题
   - 需要结果 → sessions_yield 等待
   - 火发不收 → sessions_spawn（不等待）+ 写入 tasks/ 跟踪
2. **sessions_send 仅用于**：
   - 向 main 会话汇报紧急事项（且目标确实在活跃状态）
   - 需要共享完整上下文的长对话（极少场景）
3. **异步消息队列**：Agent 完成任务后写入 inbox/pending/{task_id}.json
   - 年年心跳检查时读取并处理
   - 跨天任务用飞书多维表格跟踪
4. **超时设置**：sessions_spawn 默认 runTimeoutSeconds: 1800（30分钟）
5. **失败降级**：sessions_spawn 失败 → 重试1次 → 降级到写文件
```

**通信决策树：**
```markdown
### 通信决策树
给子Agent分任务？
├── 是 → sessions_spawn（独立会话，无状态耦合）
│   ├── 需要结果？→ sessions_yield 等待
│   └── 火发不收？→ 不等待，让子Agent写 inbox/ 汇报
│
├── 向 main 会话汇报紧急事？→ 检查main是否活跃
│   ├── 活跃 → sessions_send
│   └── 不活跃 → 写入 inbox/pending/ 等心跳处理
│
└── 常规知识共享？→ 写入 SHARED_KNOWLEDGE.md / lessons.md
```

---

## 2. SOUL.md 更新 - 通信规则

**在核心工作流部分替换通信相关内容：**

```markdown
## Agent 通信规则（v2）
- **任务分发** → sessions_spawn（创建新子Agent，每个任务独立会话）
- **结果回收** → sessions_yield（等待子Agent完成）或检查 inbox/
- **紧急通知** → sessions_send（仅限 main 会话活跃时）
- **异步汇报** → Agent写入 inbox/pending/，年年心跳处理
- **知识共享** → 写入文件（SHARED_KNOWLEDGE.md / lessons.md）
- **长期跟踪** → 飞书多维表格记录任务状态
```

---

## 3. HEARTBEAT.md 更新

**添加以下检查项到心跳任务：**

```markdown
## 📬 消息队列检查
- [ ] 检查 inbox/pending/ 中的消息（ls -la inbox/pending/*.json）
- [ ] 对pending消息逐个处理：读取 → 执行 → 移到 done/
- [ ] 检查 tasks/ 中超过预期时间的任务（标记stale/failed）
- [ ] 检查 outbox/pending/ 中是否有待分发给子Agent的指令
- [ ] 清理 inbox/done/ 中超过7天的消息（归档到 archive/）

## 🔍 超时任务检查
- [ ] 读取 tasks/ 目录中的所有 .json 文件
- [ ] 检查 last_updated 是否超过预期完成时间
- [ ] 超过预期时间50% → 发送催促
- [ ] 超过预期时间100% → 标记stale，通知主人
```

---

## 4. WORKFLOW.md 更新 - 波次执行

**替换波次执行代码逻辑为：**

```markdown
### 年年执行波次的代码逻辑（v2）
```
for each wave in waves:
    spawned_sessions = []
    
    # 同一波次内的任务同时发出 (sessions_spawn)
    for each task in wave.tasks:
        session = sessions_spawn(
            agent=task.agent,
            message=task.description,
            runTimeoutSeconds=1800
        )
        spawned_sessions.append(session)
        
        # 同时写入 tasks/ 跟踪
        write_task_file(task.id, {
            "status": "running",
            "session_key": session.key,
            "wave": wave.number,
            "expected_completion": now + task.estimated_duration
        })
    
    # 等待本波次全部完成
    for session in spawned_sessions:
        result = sessions_yield()  # 等待任一子Agent完成
    
    # 检查 inbox/ 确认所有任务完成
    for task in wave.tasks:
        if not exists(f"inbox/done/{task.id}.json"):
            # 可能子Agent通过文件汇报，检查 tasks/
            check_task_completion(task.id)
    
    # 进入下一波次
```
```

---

## 5. TOOLS.md 更新 - 消息队列使用

**添加以下内容：**

```markdown
## 📬 消息队列工具 (mq.sh)

Agent 间通过文件系统通信的工具。位于 `scripts/mq.sh`。

### 常用命令
```bash
# 发送消息 (Agent完成任务后)
scripts/mq.sh send main task_completed "登录API已完成"

# 列出待处理消息 (年年心跳时检查)
scripts/mq.sh list pending

# 读取消息详情
scripts/mq.sh read task-20260401-001

# 标记消息为处理中
scripts/mq.sh process task-20260401-001

# 标记消息为已完成
scripts/mq.sh done task-20260401-001 "已确认"

# Agent领取任务
scripts/mq.sh claim dev_engineer

# 清理旧消息
scripts/mq.sh cleanup 30
```

### 消息流程
```
Agent完成 → send到inbox/pending → 年年心跳检查 → process → done → archive
```
```

---

*更新时间: 2026-04-01*
*待年年审核后合并到各文件*
