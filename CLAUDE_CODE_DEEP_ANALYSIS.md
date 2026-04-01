# Claude Code 深度架构分析

> 源代码路径: `/Users/narain/Desktop/claude-code-main/src/`
> 规模: ~1884个 TypeScript/TSX 文件, ~512K 行代码
> 分析日期: 2026-04-01

---

## 目录

1. [核心循环 (Query Engine)](#1-核心循环-query-engine)
2. [工具系统 (Tool System)](#2-工具系统-tool-system)
3. [子代理机制 (Agent Tool)](#3-子代理机制-agent-tool)
4. [上下文管理 (Context Management)](#4-上下文管理-context-management)
5. [任务系统 (Task System)](#5-任务系统-task-system)
6. [协调器模式 (Coordinator Mode)](#6-协调器模式-coordinator-mode)
7. [权限系统 (Permission System)](#7-权限系统-permission-system)
8. [遥测系统 (Telemetry)](#8-遥测系统-telemetry)
9. [核心设计模式总结](#9-核心设计模式总结)
10. [与 OpenClaw 对比分析](#10-与-openclaw-对比分析)
11. [具体优化建议](#11-具体优化建议)

---

## 1. 核心循环 (Query Engine)

### 1.1 架构概述

Claude Code 的核心循环是一个**无限 while-true 生成器**，定义在 `query.ts` 中。整体结构是:

```
query() → queryLoop() → while(true) { ... yield message; continue; }
```

关键组件:
- **`QueryEngine` 类** (`QueryEngine.ts`): 将核心逻辑从 `ask()` 提取为独立类, 可复用于 SDK 消费者
- **`query()` 生成器** (`query.ts`): 主循环，产出 `StreamEvent | Message | Terminal`

### 1.2 消息循环驱动机制

```
while (true) {
  // 1. 从 state 解构循环迭代状态
  // 2. 启动 prefetch (skill discovery, memory)
  // 3. yield { type: 'stream_request_start' }
  
  // 4. 上下文压缩管道 (按顺序):
  //    a. applyToolResultBudget() - 工具结果大小限制
  //    b. snipCompactIfNeeded() - 历史裁剪
  //    c. microcompact() - 微压缩 (prompt cache 优化)
  //    d. contextCollapse.applyCollapsesIfNeeded() - 上下文折叠
  //    e. autocompact() - 全量压缩 (调用 LLM 生成摘要)
  
  // 5. 流式 API 调用: deps.callModel()
  //    - 流式接收 assistant 消息块
  //    - 检测 tool_use blocks
  //    - StreamingToolExecutor 并行执行工具
  
  // 6. stop_reason 路由:
  //    - 'end_turn' → 完成, 返回 Terminal
  //    - 'tool_use' → 执行工具, 继续循环
  //    - 'max_tokens' → 输出截断恢复
  
  // 7. state = { ...newState } → continue 到下一轮
}
```

### 1.3 stop_reason 处理

Claude Code 不完全信任 API 的 `stop_reason` 字段，注释明确指出:

> "stop_reason === 'tool_use' is unreliable -- it's not always set correctly."

实际的循环退出信号是检测 `tool_use` blocks 的存在:

```typescript
const toolUseBlocks: ToolUseBlock[] = []
let needsFollowUp = false

// 流式接收中
if (msgToolUseBlocks.length > 0) {
  toolUseBlocks.push(...msgToolUseBlocks)
  needsFollowUp = true  // ← 这才是真正的循环继续信号
}
```

**恢复机制**:
- `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT = 3`: 最大输出 token 恢复次数
- 遇到 `max_output_tokens` 时，流式内容被 **withhold** (暂不 yield)，等待 reactive compact 恢复
- StreamingFallback: 如果流式失败，tombstone 已产出的消息，切换 fallback model 重试

### 1.4 工具调用流程

```
1. 流式接收 tool_use block
2. StreamingToolExecutor.addTool(block, assistantMessage)
3. 并发控制:
   - isConcurrencySafe → 并行执行 (read-only tools)
   - !isConcurrencySafe → 串行执行 (write tools)
4. runToolUse() 执行每个工具
5. canUseTool 权限检查 (5层)
6. 结果 yield 回循环
```

### 1.5 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **生成器驱动循环** | `async function* query()` | 惰性求值, 内存高效, 可组合 |
| **State 容器模式** | `let state: State = { ... }` + continue sites | 避免9个独立赋值, 清晰的状态转移 |
| **Withhold-then-Recover** | 流式错误暂存 → 恢复循环 | 对 SDK 消费者透明的错误恢复 |
| **管道压缩** | snip → microcompact → collapse → autocompact | 分层渐进, 前置层减轻后置层负担 |
| **StreamingToolExecutor** | 流式接收 + 即时执行 | 不等完整响应就开始执行工具 |

---

## 2. 工具系统 (Tool System)

### 2.1 buildTool() 工厂模式

定义在 `Tool.ts` 的核心函数:

```typescript
export function buildTool<D extends AnyToolDef>(def: D): BuiltTool<D> {
  return {
    ...TOOL_DEFAULTS,     // 安全默认值
    userFacingName: () => def.name,
    ...def,               // 工具特定实现覆盖
  } as BuiltTool<D>
}
```

**默认值策略 (fail-closed)**:
```typescript
const TOOL_DEFAULTS = {
  isEnabled: () => true,
  isConcurrencySafe: () => false,     // ← 保守: 假设不安全
  isReadOnly: () => false,            // ← 保守: 假设有写操作
  isDestructive: () => false,
  checkPermissions: () => ({ behavior: 'allow', updatedInput }),
  toAutoClassifierInput: () => '',    // ← 跳过安全分类器
  userFacingName: () => '',
}
```

### 2.2 Tool 类型接口 (核心字段)

每个工具必须实现:
- **`name`**: 唯一名称
- **`inputSchema`**: Zod schema，用于输入验证
- **`call()`**: 异步执行函数
- **`prompt()`**: 生成系统提示中的工具描述
- **`description()`**: 动态描述
- **`mapToolResultToToolResultBlockParam()`**: 结果 → API 块

关键可选字段:
- **`isConcurrencySafe(input)`**: 是否可并行执行
- **`isReadOnly(input)`**: 是否只读
- **`isDestructive(input)`**: 是否不可逆 (delete/overwrite/send)
- **`validateInput(input, ctx)`**: 输入验证
- **`checkPermissions(input, ctx)`**: 工具级权限检查
- **`backfillObservableInput(input)`**: 观察者输入补全
- **`maxResultSizeChars`**: 结果持久化阈值
- **`shouldDefer`**: 延迟加载 (需 ToolSearch 先触发)
- **`alwaysLoad`**: 始终出现在初始 prompt (不延迟)
- **`interruptBehavior()`**: 用户中断时的行为 ('cancel' | 'block')
- **`toAutoClassifierInput()`**: 安全分类器输入

### 2.3 工具注册机制

工具通过 `tools.ts` 的 `getAllBaseTools()` 静态注册:

```typescript
export function getAllBaseTools(): Tools {
  return [
    AgentTool, BashTool, FileEditTool, FileReadTool, FileWriteTool,
    GlobTool, GrepTool, NotebookEditTool, WebFetchTool, TaskStopTool,
    BriefTool, SkillTool, TodoWriteTool, WebSearchTool, ToolSearchTool,
    EnterPlanModeTool, ExitPlanModeV2Tool, AskUserQuestionTool, LSPTool,
    // 条件加载:
    ...(feature('KAIROS') ? [PushNotificationTool] : []),
    ...(feature('COORDINATOR_MODE') ? [TeamCreateTool, TeamDeleteTool] : []),
    // ...
  ]
}
```

**条件加载模式**: 通过 `feature()` 标志实现 dead code elimination。每个 feature gate 在编译时就被 bun bundler 移除。

### 2.4 40+ 内置工具

| 类别 | 工具 |
|------|------|
| 文件操作 | FileRead, FileWrite, FileEdit, Glob, Grep |
| Shell | Bash, PowerShell |
| Agent | Agent, SendMessage, TaskStop, TaskOutput |
| 任务 | TaskCreate, TaskGet, TaskUpdate, TaskList |
| 团队 | TeamCreate, TeamDelete |
| Web | WebFetch, WebSearch |
| 元 | ToolSearch, SkillTool, TodoWrite, BriefTool, ConfigTool |
| 计划 | EnterPlanMode, ExitPlanModeV2 |
| MCP | MCPTool, ListMcpResources, ReadMcpResource |
| 实验 | SleepTool, MonitorTool, WebBrowserTool, REPLTool |

### 2.5 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **工厂 + 安全默认** | `buildTool()` + TOOL_DEFAULTS | 新工具只需最少字段，安全属性 opt-in |
| **Zod Schema 驱动** | `inputSchema: z.object({...})` | 类型安全 + 运行时验证 + API schema 生成统一 |
| **Feature Gate + Dead Code Elimination** | `feature('X') && require(...)` | 零运行时开销的条件加载 |
| **并发安全标记** | `isConcurrencySafe(input)` per-input | 精确到输入级别的并行化决策 |
| **Tool Deferral** | `shouldDefer` + `ToolSearchTool` | 大量工具时不膨胀 prompt |

---

## 3. 子代理机制 (Agent Tool)

### 3.1 架构概述

子代理系统围绕 `AgentTool` (`tools/AgentTool/AgentTool.tsx`) 构建，支持多种任务类型:

```
AgentTool.call()
├── 普通模式 → runAgent() → query() 子循环
├── Fork 模式 → buildForkedMessages() → 隐式 fork
├── 异步模式 → registerAsyncAgent() → 后台运行
├── 团队模式 → spawnTeammate() → tmux session
└── 隔离模式 → createAgentWorktree() → git worktree
```

### 3.2 子代理创建流程

```typescript
// 1. 构建子代理上下文
const subagentContext = createSubagentContext(
  agentDefinition, parentContext, ...
);

// 2. 选择模型
const model = getAgentModel(agentDefinition, parentModel);

// 3. 获取系统提示
const systemPrompt = agentDefinition.getSystemPrompt();

// 4. 初始化 MCP (代理级 MCP 服务器)
const { clients, tools, cleanup } = await initializeAgentMcpServers(
  agentDefinition, parentClients
);

// 5. 运行 query() 循环
const result = query({
  messages, systemPrompt, userContext, systemContext,
  canUseTool, toolUseContext, ...
});
```

### 3.3 Fork 子代理 (实验性)

当 `FORK_SUBAGENT` feature gate 开启且未指定 `subagent_type` 时触发:

```typescript
// forkSubagent.ts
export function buildForkedMessages(
  directive: string,
  assistantMessage: AssistantMessage,
): MessageType[] {
  // 保留父代理的完整 assistant 消息 (所有 tool_use blocks)
  // 构造占位符 tool_results → 最大化 prompt cache 命中
  // 附加 <fork-boilerplate> 指令
  return [fullAssistantMessage, toolResultMessage];
}
```

**Cache 策略**: 所有 fork 子代理使用相同的占位符 `FORK_PLACEHOLDER_RESULT`，保证 `[..., assistant(all_tool_uses), user(placeholder_results..., directive)]` 前缀的 byte 完全一致。

### 3.4 上下文隔离机制

| 隔离级别 | 机制 | 说明 |
|----------|------|------|
| **消息隔离** | 子代理有独立消息数组 | 不继承父代理对话历史 |
| **系统提示隔离** | AgentDefinition.getSystemPrompt() | 每种代理类型有独立系统提示 |
| **工具隔离** | resolveAgentTools() | 按代理类型过滤可用工具 |
| **MCP 隔离** | initializeAgentMcpServers() | 代理可定义自己的 MCP 服务器 |
| **文件系统隔离** | git worktree | 物理文件副本 |
| **Session 隔离** | 独立 sessionId + transcript | 独立的 session 存储 |

### 3.5 代理间通信

```
父代理 → 子代理: 通过 prompt 参数传入指令
子代理 → 父代理: 通过 <task-notification> XML 回传结果

<task-notification>
  <task-id>agent-xxx</task-id>
  <status>completed|failed|killed</status>
  <summary>...</summary>
  <result>...</result>
  <usage>
    <total_tokens>N</total_tokens>
    <tool_uses>N</tool_uses>
    <duration_ms>N</duration_ms>
  </usage>
</task-notification>
```

**Coordinator 模式下的通信**:
- `SendMessageTool`: 父代理向已有子代理发送后续指令
- `TaskStopTool`: 停止运行中的子代理
- 子代理结果到达时自动注入为 user-role 消息

### 3.6 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **统一 Agent 定义** | `AgentDefinition` 接口 | 一致的代理创建/管理 |
| **Cache-Identical Fork** | 占位符 + byte 完全一致前缀 | 多 fork 共享 prompt cache |
| **异步生命周期** | `registerAsyncAgent` / `killAsyncAgent` | 后台任务管理 |
| **层级工具过滤** | `resolveAgentTools()` | 按角色限制工具访问 |
| **XML 通知协议** | `<task-notification>` 结构化结果 | 机器可解析的代理间通信 |

---

## 4. 上下文管理 (Context Management)

### 4.1 多层压缩架构

Claude Code 使用 **4 层渐进式上下文压缩**，每层在前层不足时触发:

```
Layer 0: applyToolResultBudget()    ← 工具结果大小限制 (最先执行)
Layer 1: snipCompactIfNeeded()      ← 历史裁剪 (HISTORY_SNIP feature)
Layer 2: microcompact()             ← 微压缩 (prompt cache 优化)
Layer 3: contextCollapse            ← 上下文折叠 (CONTEXT_COLLAPSE feature)
Layer 4: autocompact()              ← 全量压缩 (调用 LLM 生成摘要)
```

### 4.2 自动压缩 (autocompact)

定义在 `services/compact/autoCompact.ts`:

```typescript
// 阈值计算
const AUTOCOMPACT_BUFFER_TOKENS = 13_000;
const effectiveContextWindow = contextWindow - MAX_OUTPUT_TOKENS_FOR_SUMMARY;
const autocompactThreshold = effectiveContextWindow - AUTOCOMPACT_BUFFER_TOKENS;

// 熔断器
const MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3;
```

**压缩流程** (`compact.ts`):
1. strip images from messages (避免图片导致压缩本身 prompt 过长)
2. group messages by API round (将 tool_use + tool_result 分组)
3. 调用 LLM 生成摘要 (独立 API 调用)
4. 构建 post-compact messages (摘要 + 保留的关键文件 + hooks)
5. POST_COMPACT_MAX_FILES_TO_RESTORE = 5 (最多恢复5个关键文件)

### 4.3 微压缩 (microcompact)

定义在 `services/compact/microCompact.ts`:
- 不调用 LLM，纯客户端侧优化
- 压缩早期工具结果，保留最近的
- 优化 prompt cache 命中率

### 4.4 Token 预算系统

```typescript
// query/tokenBudget.ts
const TOKEN_BUDGET = 500_000;  // 总预算
// 预算耗尽 → 自动继续 (incrementBudgetContinuationCount)
```

### 4.5 MEMORY.md 管理

定义在 `memdir/memdir.ts`:

```typescript
const MAX_ENTRYPOINT_LINES = 200;   // MEMORY.md 最大行数
const MAX_ENTRYPOINT_BYTES = 25_000; // MEMORY.md 最大字节数

// 截断策略: 先按行截断, 再按字节截断
// 附加警告提示
```

**按需加载**: CLAUDE.md 和 MEMORY.md 通过 `getUserContext()` 懒加载 (memoized)，在每个 session 中只读取一次。

### 4.6 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **渐进式压缩** | 4层管道, 前置层减轻后置层 | 最大化保留精细上下文 |
| **熔断器** | `MAX_CONSECUTIVE_FAILURES = 3` | 防止不可恢复场景的无限重试 |
| **Budget 缓冲** | `AUTOCOMPACT_BUFFER_TOKENS = 13K` | 给 output 预留空间 |
| **Memoized Context** | `memoize(getSystemContext)` | 避免重复 I/O |
| **文件恢复** | post-compact 最多恢复5个关键文件 | 压缩后保留关键上下文 |

---

## 5. 任务系统 (Task System)

### 5.1 任务类型

定义在 `tasks/types.ts`:

```typescript
type TaskState =
  | LocalShellTaskState      // 本地 shell 后台任务
  | LocalAgentTaskState      // 本地 agent 异步任务
  | RemoteAgentTaskState     // 远程 agent 任务 (CCR)
  | InProcessTeammateTaskState  // 进程内 teammate
  | LocalWorkflowTaskState   // 工作流任务
  | MonitorMcpTaskState      // MCP 监控任务
  | DreamTaskState           // Dream 任务 (KAIROS)
```

### 5.2 LocalAgentTask

```typescript
// 任务注册
registerAsyncAgent(agentId, description, prompt, outputFile, ...)

// 任务生命周期
runAsyncAgentLifecycle(agentId, ...) // 运行
updateAsyncAgentProgress(agentId, ...) // 更新进度
completeAsyncAgent(agentId, ...) // 完成
failAsyncAgent(agentId, ...) // 失败
killAsyncAgent(agentId) // 杀死

// 前台/后台切换
registerAgentForeground(agentId) // 前台
unregisterAgentForeground(agentId) // 后台
isBackgroundTask(task) // 检查是否为后台任务
```

### 5.3 后台任务机制

```typescript
// 自动后台化 (GrowthBook 控制)
const AUTO_BACKGROUND_MS = 120_000; // 2分钟后自动后台化

// 通知
enqueueAgentNotification(agentId, ...)

// 输出持久化
getTaskOutputPath(agentId) // 输出文件路径
```

### 5.4 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **统一任务接口** | `TaskState` 联合类型 | UI 一致处理所有任务类型 |
| **自动后台化** | 超时自动转后台 | 不阻塞用户交互 |
| **输出持久化** | `outputFile` | 任务结果可异步获取 |
| **前台/后台切换** | register/unregister Foreground | 灵活的任务展示控制 |

---

## 6. 协调器模式 (Coordinator Mode)

### 6.1 架构概述

协调器模式 (`coordinator/coordinatorMode.ts`) 将 Claude Code 转变为一个**多 worker 编排器**:

```
用户 ↔ Coordinator (Claude)
  ├── Worker 1 (Agent)
  ├── Worker 2 (Agent)
  └── Worker N (Agent)
```

### 6.2 协调器规则

```typescript
// 工具限制: 协调器只能使用这些工具
const COORDINATOR_MODE_ALLOWED_TOOLS = [
  'Agent', 'SendMessage', 'TaskStop',
  'TeamCreate', 'TeamDelete',
  'Bash', 'Read', 'Edit'  // 简单模式
];

// Worker 可用工具
const ASYNC_AGENT_ALLOWED_TOOLS = [
  'Bash', 'Read', 'Edit', 'Glob', 'Grep',
  'WebFetch', 'WebSearch', 'TodoWrite', ...
];
```

### 6.3 通信协议

```xml
<!-- Worker → Coordinator -->
<task-notification>
  <task-id>agent-xxx</task-id>
  <status>completed</status>
  <result>...</result>
</task-notification>

<!-- Coordinator → Worker (via SendMessageTool) -->
SendMessageTool({ to: "agent-xxx", message: "下一步指令" })
```

### 6.4 Scratchpad 共享

```typescript
// 协调器为 workers 提供共享 scratchpad 目录
const content = `Scratchpad directory: ${scratchpadDir}
Workers can read and write here without permission prompts.`;
```

### 6.5 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **受限工具集** | 协调器只用编排工具 | 强制关注点分离 |
| **XML 通知** | `<task-notification>` 结构 | 结构化异步通信 |
| **共享 Scratchpad** | 跨 worker 文件系统 | 知识传递无需 API |

---

## 7. 权限系统 (Permission System)

### 7.1 5 层权限检查

Claude Code 的权限检查是**级联决策系统**:

```
Layer 1: Tool.validateInput()       ← 工具级输入验证
Layer 2: Tool.checkPermissions()    ← 工具级权限检查
Layer 3: Permission Rules           ← 用户定义规则匹配
Layer 4: PreToolUse Hooks           ← 用户/插件 hooks
Layer 5: Bash Classifier            ← AI 分类器 (仅 Bash)
```

**决策流**:
```typescript
// permissions.ts
export async function hasPermissionsToUseTool(
  tool, input, context, assistantMessage, toolUseID, canUseTool
): Promise<PermissionResult> {
  // 1. 工具级 validateInput
  // 2. 工具级 checkPermissions
  // 3. 规则匹配 (alwaysAllowRules / denyRules)
  // 4. 权限 hooks (executePermissionRequestHooks)
  // 5. Bash classifier (TRANSCRIPT_CLASSIFIER feature)
  // → { behavior: 'allow' | 'deny' | 'ask', ... }
}
```

### 7.2 权限规则源

```typescript
const PERMISSION_RULE_SOURCES = [
  'userSettings',    // ~/.claude/settings.json
  'projectSettings', // .claude/settings.json
  'cliArg',          // --allowedTools
  'command',         // /allowed-tools 命令
  'session',         // 当前 session
];
```

### 7.3 交互式处理

```typescript
// interactiveHandler.ts - 主代理交互式权限流程
function handleInteractivePermission(params, resolve) {
  // 1. 推送 ToolUseConfirm 到 UI 队列
  // 2. 异步运行 hooks + classifier
  // 3. 回调: onAllow / onReject / onAbort
  // 4. resolveOnce 保证只 resolve 一次
  // 5. 桥接远程权限请求 (bridgeCallbacks)
}
```

### 7.4 Coordinator Worker 权限

```typescript
// coordinatorHandler.ts - worker 权限流程
async function handleCoordinatorPermission(params) {
  // 1. 顺序运行 hooks
  // 2. 运行 classifier
  // 3. 都未决 → 返回 null (降级到交互式)
}
```

### 7.5 权限持久化

```typescript
// PermissionUpdate.ts
persistPermissionUpdates(updates) // 写入 settings.json
applyPermissionUpdates(context, updates) // 更新内存中上下文
```

### 7.6 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **分级权限** | 5层级联检查 | 粗粒度 → 细粒度逐级过滤 |
| **规则引擎** | 多源规则 + 合并策略 | 灵活的权限配置 |
| **ResolveOnce** | `createResolveOnce()` | 防止并发 callback 竞争 |
| **分类器旁路** | Bash classifier 异步 + 用户交互 race | 不阻塞的 AI 安全检查 |
| **权限持久化** | 自动写入 settings.json | "always allow" 选项真正持久 |

---

## 8. 遥测系统 (Telemetry)

### 8.1 架构

```typescript
// services/analytics/index.ts
// 零依赖设计 — 避免循环导入

// 事件队列 (sink 未就绪前)
const eventQueue: QueuedEvent[] = [];

// Sink 接口
type AnalyticsSink = {
  logEvent: (eventName, metadata) => void;
  logEventAsync: (eventName, metadata) => Promise<void>;
};

// 公共 API
logEvent('tengu_auto_compact_succeeded', { ... });
logEventAsync('tengu_event', { ... });
```

### 8.2 隐私保护

```typescript
// 防止代码/文件路径泄露的标记类型
type AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS = never;

// PII 标记类型 (仅 1P 可见)
type AnalyticsMetadata_I_VERIFIED_THIS_IS_PII_TAGGED = never;

// PII 字段过滤
function stripProtoFields(metadata) {
  // 移除 _PROTO_* keys (Datadog 不可见)
}
```

### 8.3 事件采样

```typescript
// GrowthBook 动态配置采样率
// tengu_event_sampling_config
// 被采样的事件附带 sample_rate 元数据
```

### 8.4 事件命名规范

所有事件以 `tengu_` 前缀命名:
- `tengu_auto_compact_succeeded`
- `tengu_tool_use_cancelled`
- `tengu_coordinator_mode_switched`
- `tengu_memdir_loaded`
- `tengu_orphaned_messages_tombstoned`

### 8.5 可复用模式

| 模式 | 实现 | 价值 |
|------|------|------|
| **零依赖队列** | eventQueue + attachAnalyticsSink | 避免循环导入, 启动时无阻塞 |
| **标记类型** | `I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS` | 编译时强制隐私审查 |
| **PII 分离** | `_PROTO_*` keys + stripProtoFields | 不同后件看到不同粒度 |
| **异步 drain** | queueMicrotask 批量 flush | 不阻塞启动路径 |

---

## 9. 核心设计模式总结

### 9.1 架构级模式

| 模式 | 用途 | Claude Code 实现 |
|------|------|------------------|
| **Generator 驱动** | 主循环 | `async function* query()` |
| **渐进式管道** | 上下文压缩 | 4 层压缩, 每层独立 |
| **Feature Gate + Tree Shaking** | 条件功能 | `feature('X')` + bun:bundle |
| **Builder/Factory** | 工具创建 | `buildTool()` + defaults |
| **Async Iterator** | 流式处理 | `for await (const msg of callModel(...))` |
| **State Container** | 循环状态 | `let state: State` + spread |
| **Circuit Breaker** | 容错 | consecutiveFailures 熔断 |
| **ResolveOnce** | 竞态控制 | `createResolveOnce()` |
| **Capability-based Security** | 权限 | 5 层级联检查 |
| **XML Protocol** | 代理通信 | `<task-notification>` |

### 9.2 代码级模式

- **Zod Schema 统一**: 输入验证、API schema、类型定义三合一
- **Memoize**: `memoize(getSystemContext)` 避免重复 I/O
- **Lazy Require**: 条件模块 `feature('X') ? require(...) : null`
- **Type-level Factory**: `BuiltTool<D>` 类型级 spread 合并
- **Marker Types**: `as AnalyticsMetadata_I_VERIFIED_...` 编译时标记
- **AbortController 层级**: parent → child abort signal 链

---

## 10. 与 OpenClaw 对比分析

### 10.1 核心循环对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **循环结构** | Generator + state container | sessions_spawn/send | CC 更精细的单循环控制 |
| **压缩管道** | 4层渐进 (snip→micro→collapse→auto) | 简单 token 计数 | **重大差距** — OpenClaw 无分层压缩 |
| **流式工具执行** | StreamingToolExecutor | 等待完整响应 | CC 并行执行更快 |
| **错误恢复** | Withhold + reactive compact | 基础重试 | CC 有更复杂的恢复策略 |
| **Token 预算** | 500K 自动继续 | 无 | CC 有自动预算管理 |

### 10.2 工具系统对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **工具定义** | `buildTool()` + Zod | 函数描述 JSON schema | CC 类型安全更好 |
| **并发控制** | per-input `isConcurrencySafe` | 无 | **差距** — 无并行工具执行 |
| **工具延迟加载** | `shouldDefer` + ToolSearch | 全量加载 | CC prompt 更紧凑 |
| **结果截断** | `maxResultSizeChars` 自动持久化 | 无 | CC 大结果自动降级 |
| **工具数量** | 40+ | ~20+ | CC 更丰富的工具生态 |

### 10.3 子代理对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **代理定义** | AgentDefinition (YAML frontmatter) | 简单配置 | CC 更灵活 |
| **上下文隔离** | 多层 (消息/MCP/文件系统/Session) | 基于 session | CC 更严格 |
| **Fork 模式** | cache-identical fork | 无 | **差距** — CC 有共享 cache 的隐式 fork |
| **异步任务** | registerAsyncAgent + 自动后台 | sessions_spawn | CC 有更完善的任务生命周期 |
| **协调器模式** | 专职编排器 + XML 协议 | 无专职编排 | CC 更成熟的多代理编排 |
| **代理通信** | XML 通知 + SendMessageTool | sessions_send | 通信协议更结构化 |

### 10.4 权限系统对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **检查层数** | 5层 | 5层 (见 TOOLS.md) | 相当 |
| **规则匹配** | 多源规则 + 合并 | rules.json | CC 更灵活 |
| **Bash 分类器** | AI 分类器 | 无 | **差距** — CC 有 AI 辅助权限判断 |
| **权限持久化** | 自动写入 settings.json | 手动配置 | CC 更方便 |
| **交互式处理** | UI 队列 + 远程桥接 | 基础确认 | CC 更丰富的交互方式 |

### 10.5 上下文管理对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **压缩策略** | 4层渐进式 | 无分层压缩 | **重大差距** |
| **MEMORY.md** | 200行/25KB 截断 + 按需加载 | 无限制 | CC 有更严格的控制 |
| **Memoization** | context/SystemPrompt memoized | 部分 | CC 更系统化 |
| **Prompt Cache** | 微压缩优化 cache 命中 | 无意识 | **差距** — CC 有 cache 优化策略 |

### 10.6 遥测对比

| 维度 | Claude Code | OpenClaw | 差距 |
|------|-------------|----------|------|
| **隐私保护** | 标记类型 + PII 分离 | 基础审计日志 | CC 更严谨 |
| **事件队列** | 零依赖 + 异步 drain | 直接写入 | CC 更可靠 |
| **采样** | 动态采样率 | 无 | CC 更高效 |

---

## 11. 具体优化建议

### 11.1 🔴 高优先级 (架构级)

#### 1. 实现分层上下文压缩管道

```typescript
// 建议: OpenClaw 可实现 3 层压缩 (比 CC 简化)
interface CompressionPipeline {
  // Layer 0: 工具结果截断 (最廉价)
  applyToolResultBudget(messages: Message[]): Message[];
  
  // Layer 1: 历史裁剪 (无需 LLM)
  snipOldMessages(messages: Message[], preserveTail: number): Message[];
  
  // Layer 2: 全量压缩 (调用 LLM 生成摘要)
  autocompact(messages: Message[]): CompactionResult;
}
```

**预期收益**: 大幅减少 token 浪费, 支持更长的 session

#### 2. 实现流式工具执行器

```typescript
// 建议: 不等 API 完整响应就开始执行工具
class StreamingToolExecutor {
  addTool(block: ToolUseBlock): void;  // 流式接收即添加
  getCompletedResults(): ToolResult[];  // 非阻塞获取结果
  
  // 并发控制
  private canExecute(isConcurrencySafe: boolean): boolean;
}
```

**预期收益**: 减少用户等待时间 30-50%

#### 3. 实现 buildTool() 工厂模式

```typescript
// 建议: 统一工具定义, 安全默认值
function buildTool(def: Partial<Tool>): Tool {
  return {
    isConcurrencySafe: () => false,  // 保守默认
    isReadOnly: () => false,
    isEnabled: () => true,
    checkPermissions: () => allow,
    ...def,
  };
}
```

**预期收益**: 减少工具定义代码量, 统一安全策略

### 11.2 🟡 中优先级 (功能级)

#### 4. 实现 Token 预算管理

```typescript
// 建议: 自动预算追踪 + 自动继续
const TOKEN_BUDGET = 500_000;
function checkTokenBudget(usage: number): BudgetStatus;
function incrementBudgetContinuationCount(): void;
```

**预期收益**: 避免用户手动管理长 session

#### 5. 实现 Tool Deferral (工具延迟加载)

```typescript
// 建议: 大量工具时不膨胀 prompt
interface Tool {
  shouldDefer?: boolean;  // 需要 ToolSearch 先触发
  alwaysLoad?: boolean;   // 始终在初始 prompt
}

// ToolSearchTool: 按关键词搜索可用工具
class ToolSearchTool {
  call({ query: string }): ToolDefinition[];
}
```

**预期收益**: 工具数量超过 20 时显著减少 prompt 大小

#### 6. 实现 Feature Gate + Dead Code Elimination

```typescript
// 建议: 编译时移除未启用功能
const feature = (name: string) => process.env[`FEATURE_${name}`] === 'true';

// 条件导入
const SleepTool = feature('PROACTIVE') 
  ? require('./tools/SleepTool').SleepTool 
  : null;
```

**预期收益**: 减少运行时内存, 支持不同版本的精简构建

### 11.3 🟢 低优先级 (优化级)

#### 7. 实现 Memoized Context

```typescript
// 建议: 避免重复 I/O
const getSystemContext = memoize(async () => {
  const gitStatus = await getGitStatus();
  return { gitStatus, currentDate: getLocalISODate() };
});
```

**预期收益**: 减少重复计算

#### 8. 实现 BASH 分类器

```typescript
// 建议: AI 辅助权限判断
async function executeClassifierCheck(
  command: string,
): Promise<'allow' | 'deny' | 'ask'> {
  // 调用小型模型判断命令安全性
}
```

**预期收益**: 减少用户确认次数, 提高自动批准率

#### 9. 实现 XML 代理间通信协议

```typescript
// 建议: 结构化的代理间通信
interface TaskNotification {
  taskId: string;
  status: 'completed' | 'failed' | 'killed';
  summary: string;
  result?: string;
  usage?: { totalTokens: number; toolUses: number; durationMs: number };
}
```

**预期收益**: 机器可解析的代理结果, 支持更复杂的编排

#### 10. 实现 Output 持久化

```typescript
// 建议: 大结果自动持久化到文件
interface Tool {
  maxResultSizeChars: number;  // 超过此阈值持久化
}

// 超过阈值时:
// 1. 结果写入文件
// 2. 向模型返回预览 + 文件路径
```

**预期收益**: 避免大结果淹没上下文

---

## 附录 A: 关键文件速查

| 文件 | 行数 | 职责 |
|------|------|------|
| `query.ts` | ~1200 | 主循环, 状态机, 压缩管道 |
| `QueryEngine.ts` | ~960 | SDK 封装, 流式事件处理 |
| `Tool.ts` | ~800 | Tool 类型定义, buildTool 工厂 |
| `tools.ts` | ~250 | 工具注册, getAllBaseTools() |
| `AgentTool/AgentTool.tsx` | ~500+ | 子代理工具, UI 渲染 |
| `AgentTool/forkSubagent.ts` | ~200 | Fork 子代理, cache-identical |
| `AgentTool/runAgent.ts` | ~300 | 子代理运行时, MCP 初始化 |
| `coordinator/coordinatorMode.ts` | ~200 | 协调器模式, worker 限制 |
| `hooks/toolPermission/PermissionContext.ts` | ~300 | 权限上下文, 决策流程 |
| `utils/permissions/permissions.ts` | ~300+ | 规则匹配, 5层检查 |
| `services/compact/compact.ts` | ~200+ | LLM 压缩, 图片剥离 |
| `services/compact/autoCompact.ts` | ~200+ | 自动压缩阈值, 熔断器 |
| `context.ts` | ~200 | 系统上下文, CLAUDE.md 加载 |
| `memdir/memdir.ts` | ~200+ | MEMORY.md 管理, 截断策略 |
| `services/analytics/index.ts` | ~150 | 遥测 API, 隐私保护 |
| `tasks/types.ts` | ~30 | 任务类型定义 |
| `buddy/companion.ts` | ~100 | 虚拟伙伴系统 |

## 附录 B: Feature Gates 一览

| Gate | 用途 |
|------|------|
| `FORK_SUBAGENT` | 隐式 fork 子代理 |
| `COORDINATOR_MODE` | 协调器模式 |
| `HISTORY_SNIP` | 历史裁剪 |
| `CONTEXT_COLLAPSE` | 上下文折叠 |
| `REACTIVE_COMPACT` | 反应式压缩 |
| `CACHED_MICROCOMPACT` | 缓存微压缩 |
| `TOKEN_BUDGET` | Token 预算 |
| `BASH_CLASSIFIER` | Bash AI 分类器 |
| `TRANSCRIPT_CLASSIFIER` | 转录分类器 |
| `PROACTIVE` / `KAIROS` | 主动代理功能 |
| `TEAMMEM` | 团队记忆 |
| `EXPERIMENTAL_SKILL_SEARCH` | 技能搜索 |
| `BG_SESSIONS` | 后台 session |
| `WORKFLOW_SCRIPTS` | 工作流脚本 |
| `AGENT_TRIGGERS` | 代理触发器 |

---

*分析完成。本报告基于对 Claude Code 源代码的深度阅读，每个结论都基于实际代码证据。*
