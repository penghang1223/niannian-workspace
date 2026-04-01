# Agent Architecture Reference — 12层递进机制

> 基于 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 对 Claude Code 512K 行源码的逆向分析，逐层拆解 Agent Harness 工程设计原理，并对标 OpenClaw 当前实现，找出差距与可优化点。
>
> **核心理念：Agent = Model（模型）+ Harness（缰绳）。模型决定智商，Harness 决定边界。**

---

## 📐 架构总览

```
Phase 1: THE LOOP          Phase 2: PLANNING & KNOWLEDGE
==================         =============================
L1 核心循环 [1 tool]       L3 规划模式 [5 tools]
  |                          |
L2 工具调度 [4 tools]      L4 子代理机制 [5 tools]
                             |
                           L5 知识按需加载 [5 tools]
                             |
                           L6 上下文压缩 [5 tools]

Phase 3: PERSISTENCE       Phase 4: TEAMS
==================         =====================
L7 持久化任务 [8 tools]    L9 代理团队 [9 tools]
  |                          |
L8 后台任务 [6 tools]      L10 团队协议 [12 tools]
                             |
                           L11 自治代理 [14 tools]
                             |
                           L12 工作树隔离 [16 tools]
```

**设计哲学**：每一层都在上一层基础上添加一个 Harness 机制，Agent Loop 本身从不改变。Loop 属于 Agent，机制属于 Harness。

---

## L1: 核心循环 — The Agent Loop

### 设计原理

最小可行 Agent 只需一个循环 + 一个工具：

```python
def agent_loop(query):
    messages = [{"role": "user", "content": "query"}]
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM,
            messages=messages, tools=TOOLS,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return  # 模型决定停止 = 任务完成
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS[block.name](**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})
```

**关键洞察**：退出条件完全由模型的 `stop_reason` 决定。代码不判断"任务是否完成"，模型自己说了算。这是 Trust the Model 哲学的根基。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 循环实现 | 单进程 while 循环 | Gateway runtime 事件循环 |
| 消息格式 | Anthropic Messages API | 抽象适配多 Provider (OpenRouter/Anthropic/OpenAI) |
| 停止条件 | `stop_reason != "tool_use"` | Provider 返回 finish_reason |
| 工具执行 | 同步阻塞 | 支持同步 + 异步（background exec） |

**OpenClaw 状态**：✅ 已实现。核心循环稳固，多 Provider 适配是额外优势。

### 差距与优化

- 🟡 OpenClaw 的 Provider 抽象层增加了复杂度，但换来了模型无关性 — 这是正确的取舍
- 🔴 缺少 `stop_reason` 级别的精细控制（如区分 `end_turn` vs `max_tokens` vs `stop_sequence`）

---

## L2: 工具调度 — Tool Dispatch

### 设计原理

工具注册用字典映射，添加工具 = 添加一个 handler + 一个 schema，循环完全不变：

```python
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}
```

Claude Code 有 40+ 内置工具，通过 `buildTool()` 工厂统一注册。路径沙箱在工具层强制执行，不依赖模型判断。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 工具数量 | 40+ 内置 | 20+ 内置 + 无限 Skill 扩展 |
| 注册方式 | buildTool() 工厂 | 声明式 JSON Schema + 工厂 |
| 沙箱 | 路径级 sandbox | exec sandbox + 浏览器 sandbox |
| 扩展性 | 内置固定 | Skill 系统动态加载 |

**OpenClaw 状态**：✅ 已实现，且 Skill 系统提供了更强的扩展性。OpenClaw 的 `exec/read/write/edit` 工具与 Claude Code 的核心工具几乎一一对应。

### 差距与优化

- 🟡 Claude Code 的 `Glob` 和 `Grep` 是独立工具（高效文件搜索），OpenClaw 依赖 `exec + find/rg`，性能和易用性略差
- 🔴 缺少工具级别的细粒度权限控制（如 "允许 read 但禁止 write" 的 per-tool 策略）
- 🟢 OpenClaw 的 Skill 系统（SKILL.md + 动态加载）比 Claude Code 的静态工具集更灵活

---

## L3: 规划模式 — Planning Mode

### 设计原理

"没有计划的 Agent 会漂移。" 10 步重构可能完成 1-3 步后模型开始即兴发挥。

```python
class TodoManager:
    def update(self, items: list) -> str:
        # 同时只能有一个 in_progress — 强制串行聚焦
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_progress")
```

**Nag Reminder 机制**：如果模型 3+ 轮没调用 todo 工具，自动在 tool_result 前插入 `<reminder>Update your todos.</reminder>`。这是软约束 — 提醒而非强制。

**效果**：先规划后执行，任务完成率提升 2 倍。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 规划工具 | TodoWrite | GSD 6步工作流（AGENTS.md + WORKFLOW.md） |
| 任务格式 | 内存状态 + nag reminder | 波次规划 + 文件持久化 |
| 执行约束 | 单 in_progress 强制 | Agent 角色分工约束 |
| 提醒机制 | `<reminder>` 注入 | 心跳检查 + INSTINCTS 提醒 |

**OpenClaw 状态**：🟡 部分实现。GSD 工作流提供了更丰富的规划框架（需求→PRD→波次→执行→验收），但缺少 Claude Code 那种**工具级别的强制约束**。OpenClaw 的规划是"建议性的"，Claude Code 是"强制性的"。

### 差距与优化

- 🔴 缺少 `TodoWrite` 类的工具级规划工具（当前规划在 system prompt 中描述，不是工具调用）
- 🔴 没有 nag reminder 自动注入机制（OpenClaw 依赖模型自律 + 心跳提醒）
- 🟢 GSD 波次规划在复杂度上超越了 Claude Code 的扁平 TodoList

---

## L4: 子代理机制 — Subagent

### 设计原理

子代理解决上下文污染问题。"这个项目用什么测试框架？"可能需要读 5 个文件，但父代理只需要答案："pytest。"

```
Parent: messages=[...] → task("find testing framework") → 结果: "pytest"
Subagent: messages=[] (全新) → 读文件 → 查配置 → 返回摘要
         ↑ 子代理的 30+ 轮工具调用全部丢弃，父代理上下文干净
```

- 子代理不能递归 spawn（`task` 工具不在 CHILD_TOOLS 中）
- 有安全限制（最多 30 轮迭代）
- 只返回最终文本摘要，不返回中间过程

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| Spawn 机制 | task tool → run_subagent() | sessions_spawn() |
| 上下文隔离 | 全新 messages[] | 独立 session（独立上下文） |
| 递归限制 | 禁止递归 spawn | depth 限制（默认 1/1） |
| 返回值 | 文本摘要 | push-based 自动汇报 |
| 身份传递 | 无 | agentId 可指定特定 Agent 角色 |

**OpenClaw 状态**：✅ 已实现，且功能更强。OpenClaw 的 `sessions_spawn` 支持指定 `agentId`（不同角色 Agent）和 `depth` 限制，比 Claude Code 的匿名子代理更丰富。

### 差距与优化

- 🟢 OpenClaw 的 Agent 角色系统（main/frontend_dev/qa_engineer 等）远超 Claude Code 的匿名子代理
- 🟡 缺少子代理的"安全轮次限制"配置（Claude Code 有 30 轮上限）
- 🟡 子代理结果通过 push-based 通知，但缺少中间状态查询能力

---

## L5: 知识按需加载 — Skill Loading

### 设计原理

把所有知识塞进 system prompt 是浪费 token。10 个 skill × 2000 token = 20,000 token，大部分永远用不到。

**两层架构**：
- **Layer 1**（system prompt）：skill 名称 + 一句话描述（~100 token/skill）— 告诉模型"有什么可用"
- **Layer 2**（tool_result）：skill 完整内容（~2000 token）— 模型按需调用 `load_skill("git")` 时注入

```
System Prompt: "Skills: git (Git workflow), test (Testing practices)" ← 廉贵
↓ 模型判断需要 git
tool_result: <skill name="git">完整的 git 工作流指令...</skill>   ← 按需
```

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 发现机制 | 扫描 SKILL.md | 扫描 SKILL.md（完全一致） |
| 注入方式 | load_skill tool → tool_result | read tool → 读 SKILL.md 内容 |
| 目录结构 | skills/*/SKILL.md | skills/*/SKILL.md（完全一致） |
| 描述层 | system prompt 中列出 | `<available_skills>` 注入 |
| 触发方式 | 模型主动调 load_skill | 模型用 read 工具读取 |

**OpenClaw 状态**：✅ 已实现，设计几乎完全一致。OpenClaw 的 SKILL.md 格式（YAML frontmatter + Markdown body）与 Claude Code 的 skill 系统同源。

### 差距与优化

- 🟢 OpenClaw 的 Skill 系统在功能上与 Claude Code 对等
- 🟡 Claude Code 的 `load_skill` 是专用工具，语义更清晰；OpenClaw 用通用 `read` 工具加载，缺少 "这是 skill 加载" 的语义标记
- 🟡 缺少 skill 版本管理和依赖声明（skill A 依赖 skill B？）

---

## L6: 上下文压缩 — Context Compression

### 设计原理

上下文窗口是有限的。读 30 个文件 + 跑 20 个 bash 命令 = 100K+ token。三层压缩策略：

```
Layer 1: micro_compact（静默，每轮）
  3 轮以上的 tool_result 替换为 "[Previous: used read_file]"
  ↓
Layer 2: auto_compact（阈值触发，>50K token）
  保存完整 transcript 到 .transcripts/
  调用 LLM 总结对话 → 替换所有消息为 [summary]
  ↓
Layer 3: manual compact（模型主动调用）
  与 Layer 2 相同的总结逻辑，但由模型决定何时触发
```

**关键洞察**：Transcript 保存到磁盘 = 没有真正丢失信息，只是移出了活跃上下文。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| Layer 1 微压缩 | 旧 tool_result → placeholder | 无明确实现 |
| Layer 2 自动压缩 | Token 阈值触发 + LLM 总结 | Provider context window 管理 |
| Layer 3 手动压缩 | compact tool | 无专用工具 |
| Transcript 保存 | .transcripts/ 目录 | session 历史（自动保留） |
| 压缩策略 | 三层渐进 | 依赖 Provider 的 truncation |

**OpenClaw 状态**：🔴 部分实现。OpenClaw 依赖底层 Provider 的上下文管理（如 Anthropic 的 auto-truncation），但缺少 Claude Code 的三层精细化压缩策略。

### 差距与优化

- 🔴 **最大差距之一**：缺少 micro_compact（旧结果替换为占位符）。在长对话中，早期的文件读取结果仍然占据大量 token
- 🔴 缺少 LLM 驱动的自动总结压缩（auto_compact）
- 🟡 session 历史的持久化提供了类似 transcript 的功能，但缺少主动压缩触发
- 💡 **优化建议**：实现一个 `compact` 工具，支持三种模式：
  1. `compact: micro` — 旧结果占位化
  2. `compact: auto` — LLM 总结 + transcript 保存
  3. `compact: manual` — 由模型主动触发

---

## L7: 持久化任务 — Persistent Task System

### 设计原理

L3 的 TodoManager 是内存中的扁平 checklist，上下文压缩后就被清除了。升级为**文件系统任务图**：

```
.tasks/
  task_1.json  {"id":1, "status":"completed"}
  task_2.json  {"id":2, "blockedBy":[1], "status":"pending"}
  task_3.json  {"id":3, "blockedBy":[1], "status":"pending"}
  task_4.json  {"id":4, "blockedBy":[2,3], "status":"pending"}
```

**DAG（有向无环图）**：
- **What's ready?** — `status=pending` + `blockedBy=[]`
- **What's blocked?** — 等待未完成的依赖
- **What's done?** — 完成后自动从依赖它的任务的 `blockedBy` 中移除

这是后续所有多 Agent 协作的基础骨架。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 存储 | .tasks/*.json 文件 | 飞书任务系统（feishu_task_task） |
| 依赖关系 | blockedBy 列表 | 无显式依赖图 |
| 状态流转 | pending → in_progress → completed | 飞书任务状态 |
| 并行判断 | blockedBy 为空 = 可执行 | 人工判断 |
| 持久化 | 文件系统（survives 压缩） | 飞书云端（survives 重启） |

**OpenClaw 状态**：🟡 部分实现。OpenClaw 有飞书任务集成（feishu_task_task），但缺少：
1. **依赖图**（blockedBy）
2. **自动状态流转**（完成 A → 自动解除 B 的阻塞）
3. **并行任务识别**（哪些任务可以同时执行）

GSD 波次规划在规划阶段体现了依赖关系，但没有持久化为可查询的任务图。

### 差距与优化

- 🔴 缺少文件系统级的任务图（.tasks/*.json with blockedBy）
- 🔴 缺少"完成 A 后自动解除 B 阻塞"的自动流转
- 🟡 飞书任务系统提供了 UI 友好的任务管理，但缺少编程化的依赖图
- 💡 **优化建议**：在 workspace 中实现 `.tasks/` 目录，每个任务一个 JSON，支持 blockedBy 依赖图，与飞书任务双向同步

---

## L8: 后台任务 — Background Tasks

### 设计原理

`npm install`、`pytest`、`docker build` 可能需要几分钟。阻塞循环意味着模型干等。

```
Main thread                Background thread
agent loop ...             subprocess runs
  [LLM call] ←────────── enqueue(result)
  ↑ drain queue
```

- 后台任务用 daemon thread 执行
- 完成后结果进入通知队列
- Agent Loop 在每次 LLM 调用前 drain 队列，注入 `<background-results>`
- Loop 保持单线程，只并行化 subprocess I/O

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 执行方式 | daemon thread + subprocess | exec with background:true |
| 通知机制 | 队列 drain → 注入消息 | process tool (poll/log/kill) |
| 状态查询 | check tool | process(action=poll) |
| 并发模型 | 单线程 loop + 后台 subprocess | 类似（事件驱动 + background exec） |

**OpenClaw 状态**：✅ 已实现。`exec` 工具的 `background:true` 模式 + `process` 工具的管理能力与 Claude Code 的后台任务系统对等。

### 差距与优化

- 🟢 OpenClaw 的 background exec + process 管理在功能上与 Claude Code 对等
- 🟡 缺少"自动 drain + 注入"机制（Claude Code 自动在下一轮 LLM 调用前注入完成结果，OpenClaw 需要模型主动调 process(action=poll)）
- 💡 优化：在 Agent Loop 中添加自动 drain 逻辑，后台任务完成后自动注入结果

---

## L9: 代理团队 — Agent Teams

### 设计原理

子代理（L4）是一次性的：spawn → 工作 → 返回摘要 → 死亡。真正的团队协作需要：

1. **持久化 Agent** — 活过单次 prompt
2. **身份管理** — name + role
3. **Agent 间通信** — 异步邮箱

```
.team/
  config.json           ← 团队花名册 + 状态
  inbox/
    alice.jsonl         ← append-only, drain-on-read
    bob.jsonl
    lead.jsonl
```

通信协议：`send("alice", "bob", "...")` → 追加 JSON line → `read_inbox("bob")` → 读取 + 清空。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| Agent 持久化 | 线程内循环 | 独立 session |
| 身份管理 | config.json 花名册 | AGENTS.md 角色定义 |
| 通信机制 | JSONL 文件邮箱 | sessions_send / sessions_yield |
| 生命周期 | spawn → WORKING → IDLE → SHUTDOWN | session 生命周期 |
| 团队配置 | .team/config.json | AGENTS.md（13 个 Agent 角色） |

**OpenClaw 状态**：✅ 已实现，且架构更成熟。OpenClaw 的 Agent 团队有 13 个预定义角色（main/frontend_dev/dev_engineer/qa_engineer 等），通过 `sessions_send` 进行内部通信。

### 差距与优化

- 🟢 OpenClaw 的 Agent 角色系统和 AGENTS.md 定义远超 Claude Code 的匿名 teammate
- 🟡 Claude Code 的 JSONL 邮箱提供了文件级持久化通信（跨 session 重启）；OpenClaw 的 `sessions_send` 是内存级的
- 🔴 OpenClaw 缺少"团队状态面板"（谁在工作、谁空闲、邮箱有没有新消息）
- 💡 优化：实现 `.team/` 目录持久化团队状态 + JSONL 通信协议

---

## L10: 团队协议 — Team Protocols

### 设计原理

有了团队（L9），需要通信规则。一个请求-响应 FSM 驱动所有协调：

```
Shutdown Protocol:            Plan Approval Protocol:
Lead → shutdown_req → Team    Teammate → plan_req → Lead
Lead ← shutdown_resp ← Team   Teammate ← plan_resp ← Lead

共享 FSM: [pending] → approve → [approved]
          [pending] → reject  → [rejected]
```

每条消息带 `request_id` 做关联。同一 FSM 应用于 shutdown、plan approval、未来任何需要协商的场景。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 协议类型 | shutdown + plan approval | 无显式协议 |
| FSM | pending → approved/rejected | 无 |
| 关联机制 | request_id | message_id（弱关联） |
| 人工介入 | plan approval = 人工审查 | 依赖 system prompt 描述 |

**OpenClaw 状态**：🔴 未实现。OpenClaw 的 Agent 间协作依赖 `sessions_send` 的自由格式消息，没有结构化的请求-响应协议。

### 差距与优化

- 🔴 **关键差距**：缺少请求-响应协议框架
- 🔴 缺少 plan approval 机制（高风险操作前的人工/Agent 审查）
- 🔴 缺少优雅 shutdown 协议（当前直接 kill session）
- 💡 **优化建议**：实现 `protocol` 工具，支持注册自定义请求-响应协议，自动关联 request_id

---

## L11: 自治代理 — Autonomous Agents

### 设计原理

L9-L10 的 teammate 只在被明确指定时工作。10 个未完成任务？Lead 要手动分配每个。

**真正的自治**：teammate 自己扫描任务板，认领未分配任务，完成后继续寻找。

```
Teammate lifecycle:
  spawn → WORKING → IDLE → (poll inbox + scan tasks) → WORKING → ...
                          ↓ 60s 超时
                        SHUTDOWN
```

**身份重注入**：上下文压缩后 Agent 可能忘记自己是谁。当 `len(messages) <= 3` 时，插入 `<identity>You are 'alice', role: coder</identity>`。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 空闲轮询 | poll inbox + scan .tasks/ every 5s | 无（session 无空闲轮询） |
| 自动认领 | claim_task() 自动认领 | 无 |
| 身份重注入 | 压缩后自动注入 | AGENTS.md 每次读取 |
| 超时退出 | 60s idle → SHUTDOWN | 无自动退出 |

**OpenClaw 状态**：🔴 未实现。OpenClaw 的 Agent 由 main agent（年年）显式调度，没有"空闲时自动寻找工作"的自治能力。

### 差距与优化

- 🔴 **关键差距**：Agent 没有空闲轮询和自动认领能力
- 🔴 缺少 idle 状态管理（当前 session 要么活跃要么不存在）
- 🟡 AGENTS.md 中的"心跳"机制提供了某种形式的"空闲检查"，但不是任务驱动的
- 💡 **优化建议**：
  1. Agent session 完成任务后进入 idle 状态
  2. Idle 时定期扫描 `.tasks/` 找未认领任务
  3. 60s 无工作自动 shutdown

---

## L12: 工作树隔离 — Worktree Isolation

### 设计原理

L11 的 Agent 可以自主认领任务，但所有任务共享一个目录。两个 Agent 同时改 `config.py`？灾难。

**解决方案**：每个 task 绑定一个 git worktree。Task 管目标，worktree 管目录，用 task_id 绑定。

```
Control plane (.tasks/)         Execution plane (.worktrees/)
task_1.json ←──────────────→ auth-refactor/
  worktree: "auth-refactor"     branch: wt/auth-refactor
task_2.json ←──────────────→ ui-login/
  worktree: "ui-login"          branch: wt/ui-login
```

**状态机**：
- Task: `pending → in_progress → completed`
- Worktree: `absent → active → removed | kept`

**Event Stream**：每个生命周期事件写入 `.worktrees/events.jsonl`，崩溃后可从磁盘恢复状态。

### OpenClaw 实现

| 维度 | Claude Code | OpenClaw |
|------|------------|----------|
| 目录隔离 | git worktree | 无（WORKFLOW.md 建议但未强制） |
| 任务绑定 | task_id ↔ worktree name | 无 |
| 事件流 | events.jsonl | 无 |
| 崩溃恢复 | 磁盘状态重建 | 依赖 session 历史 |

**OpenClaw 状态**：🟡 部分实现。WORKFLOW.md 的 Step 3.5 提到了 Git Worktree 隔离，但：
1. 是建议性的，不是强制性的
2. 没有 task-worktree 绑定机制
3. 没有生命周期事件流
4. 没有自动清理

### 差距与优化

- 🔴 缺少 task-worktree 自动绑定（创建任务时自动创建 worktree）
- 🔴 缺少 worktree 生命周期管理（创建/绑定/移除/保留）
- 🔴 缺少事件流（.worktrees/events.jsonl）
- 💡 **优化建议**：实现 `worktree` 工具，支持 create/remove/keep/bind/list，自动与 `.tasks/` 联动

---

## 📊 OpenClaw vs Claude Code 对标总览

| 层级 | 机制 | Claude Code | OpenClaw | 差距等级 |
|------|------|:-----------:|:--------:|:-------:|
| L1 | 核心循环 | ✅ | ✅ | 🟢 对等 |
| L2 | 工具调度 | ✅ | ✅ | 🟢 基本对等 |
| L3 | 规划模式 | ✅ 强制 | 🟡 建议 | 🟡 缺工具级约束 |
| L4 | 子代理机制 | ✅ | ✅+ | 🟢 OpenClaw 更强 |
| L5 | 知识按需加载 | ✅ | ✅ | 🟢 对等 |
| L6 | 上下文压缩 | ✅ 三层 | 🔴 弱 | 🔴 **最大差距** |
| L7 | 持久化任务 | ✅ DAG | 🟡 飞书 | 🟡 缺依赖图 |
| L8 | 后台任务 | ✅ | ✅ | 🟢 对等 |
| L9 | 代理团队 | ✅ | ✅+ | 🟢 OpenClaw 更强 |
| L10 | 团队协议 | ✅ FSM | 🔴 无 | 🔴 **关键差距** |
| L11 | 自治代理 | ✅ | 🔴 无 | 🔴 **关键差距** |
| L12 | 工作树隔离 | ✅ | 🟡 建议 | 🟡 缺自动化 |

---

## 🎯 优先优化建议

### P0 — 必须做

1. **L6 上下文压缩**：实现 micro_compact（旧结果占位化）+ auto_compact（LLM 总结）。这是长对话性能的最大瓶颈。
2. **L10 团队协议**：实现请求-响应协议框架。没有协议的多 Agent 协作就是混乱的自由格式消息。

### P1 — 应该做

3. **L11 自治代理**：Agent 空闲时自动扫描任务板认领工作。这将释放多 Agent 并行的真正潜力。
4. **L3 规划工具**：实现 `TodoWrite` 类工具级规划工具，支持 nag reminder 自动注入。
5. **L7 任务依赖图**：在 `.tasks/` 目录实现 DAG，支持 blockedBy 自动流转。

### P2 — 可以做

6. **L12 工作树隔离自动化**：实现 task-worktree 绑定 + 生命周期管理。
7. **L2 工具级权限**：per-tool 策略（如 read-only mode）。
8. **L9 团队状态面板**：`.team/` 目录持久化 + 状态查询。

---

## 🔗 参考资料

- [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) — 12 层递进学习项目
- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [OpenClaw Workspace AGENTS.md](../AGENTS.md) — 多 Agent 团队配置
- [OpenClaw WORKFLOW.md](../WORKFLOW.md) — GSD 6 步工作流
- [OpenClaw INSTINCTS.md](../INSTINCTS.md) — 直觉经验系统

---

*最后更新：2026-04-01 | 维护者：年年 🎀 | 基于 Claude Code 512K 行源码逆向分析*
