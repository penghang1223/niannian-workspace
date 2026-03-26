# 学习笔记

## [2026-03-27] 技能开发进阶

### 核心概念
- **技能本质**：SKILL.md 是一个带 YAML 前置元数据的 Markdown 文件，告诉 Agent 如何使用工具
- **三个加载层级**：`<workspace>/skills/`（最高优先级）→ `~/.openclaw/skills/`（共享）→ 捆绑技能（最低）
- **AgentSkills 规范**：OpenClaw 遵循 AgentSkills 规范，名称必须 snake_case，description 用于模型匹配

### 关键知识点
- **环境变量注入**：`skills.entries.<key>.env` 仅在 Agent 运行时注入，不污染全局环境；`apiKey` 是 `primaryEnv` 的便捷方式
- **Gating 机制**：`metadata.openclaw` 支持 OS 过滤、二进制依赖检查（`requires.bins`）、环境变量检查（`requires.env`）、配置检查（`requires.config`）
- **安装器配置**：`metadata.openclaw.install` 支持 brew/node/go/uv/download，macOS UI 自动展示安装按钮
- **会话快照**：技能列表在会话启动时快照，后续轮次复用；watcher 模式支持热重载
- **Token 成本**：每个技能 ≈ 97 字符 + 名称/描述/位置长度，可用公式计算

### 实践要点
- **脚本型技能**：技能可以引导 Agent 使用 `exec` 运行脚本，通过 `{baseDir}` 引用技能目录
- **调试技巧**：`openclaw agent --message "测试消息"` 测试技能触发；`/new` 或重启 Gateway 加载新技能
- **发布流程**：`clawhub publish ./my-skill --slug my-skill --name "My Skill" --version 1.2.0`
- **安全要点**：第三方技能视为不可信代码；`env` 和 `apiKey` 只注入到 host 进程，沙箱中需单独配置
- **自定义配置**：`skills.entries.<key>.config` 可存储任意自定义字段

### 学习时间
- 01:11 - 01:18 (7 分钟)

---

## [2026-03-27] 多 Agent 编排

### 核心概念
- **四个核心工具**：`sessions_list`（列出会话）、`sessions_history`（获取历史）、`sessions_send`（跨会话消息）、`sessions_spawn`（启动子 Agent）
- **子 Agent 隔离**：子 Agent 运行在独立会话 `agent:<agentId>:subagent:<uuid>`，有自己的上下文和 token 消耗
- **层级深度**：depth 0（主 Agent）→ depth 1（子 Agent/编排者）→ depth 2（叶子工作者），最多 5 层

### 关键知识点
- **sessions_spawn 参数**：`task`（必填）、`label`、`model`（覆盖模型）、`thinking`（覆盖思考级别）、`runTimeoutSeconds`（超时）、`thread`（线程绑定）、`mode`（run/session）、`cleanup`（delete/keep）
- **sessions_send 模式**：`timeoutSeconds=0` 是 fire-and-forget；`>0` 等待完成并返回回复
- **Announce 机制**：子 Agent 完成后自动 announce 结果回请求者；回复 `ANNOUNCE_SKIP` 静默
- **嵌套编排**：`maxSpawnDepth=2` 允许 depth-1 作为编排者，获得 `sessions_spawn`/`sessions_list` 等工具
- **工具策略**：默认子 Agent 无会话工具；depth-1 编排者有 spawn/list/history/send
- **并发控制**：`maxConcurrent=8`（全局），`maxChildrenPerAgent=5`（每个 Agent）

### 实践要点
- **波次并行**：无依赖任务同时 `sessions_send`，有依赖分波执行
- **超时管理**：设置 `runTimeoutSeconds` 防止子 Agent 卡死；auto-archive 默认 60 分钟
- **级联停止**：`/stop` 会级联停止所有 depth-1 和 depth-2 子 Agent
- **认证继承**：子 Agent 按 agentId 解析 auth，主 Agent 的 auth profiles 作为 fallback
- **上下文限制**：子 Agent 只注入 AGENTS.md + TOOLS.md，不注入 SOUL.md/USER.md 等

### 学习时间
- 01:18 - 01:23 (5 分钟)

---

## [2026-03-27] Cron 高级用法

### 核心概念
- **Cron 是 Gateway 内置调度器**，持久化到 `~/.openclaw/cron/jobs.json`，重启不丢失
- **四种执行模式**：`main`（主会话系统事件）、`isolated`（独立 cron 会话）、`current`（绑定当前会话）、`session:custom-id`（持久命名会话）
- **三种调度方式**：`at`（一次性）、`every`（固定间隔）、`cron`（cron 表达式 + 时区）

### 关键知识点
- **Main vs Isolated**：Main 通过 heartbeat 执行（共享上下文），Isolated 独立运行（不污染主会话历史）
- **投递模式**：`announce`（投递到频道 + 主会话摘要）、`webhook`（HTTP POST）、`none`（内部）
- **重试策略**：一次性任务 transient 错误重试 3 次（指数退避 30s→1m→5m）；循环任务退避 30s→1m→5m→15m→60m
- **Stagger 防抖**：整点 cron 表达式自动加最多 5 分钟随机延迟；可用 `--exact` 或 `--stagger 30s` 控制
- **自定义会话**：`session:xxx` 模式跨运行保持上下文，适合每日站会等连续性任务
- **模型覆盖**：isolated 任务可单独指定 `model` 和 `thinking` 级别

### 实践要点
- **一次性提醒**：`openclaw cron add --name "提醒" --at "20m" --session main --system-event "..." --wake now`
- **每日任务**：`openclaw cron add --name "日报" --cron "0 9 * * *" --tz "Asia/Shanghai" --session isolated --message "..." --announce`
- **维护配置**：`cron.sessionRetention`（默认 24h）控制运行会话保留；`runLog.maxBytes/keepLines` 控制日志大小
- **轻量上下文**：`lightContext: true` 适合不需要工作区文件的简单定时任务
- **调试命令**：`openclaw cron list` / `openclaw cron runs --id <jobId>` / `openclaw cron run <jobId>`

### 学习时间
- 01:23 - 01:28 (5 分钟)

---

## [2026-03-27] 模型路由

### 核心概念
- **多层路由**：全局默认 → 每个 Agent 默认 → 会话覆盖 → 消息内联指令（`/think:medium`）
- **Per-Agent 模型**：`agents.list[].model` 设置每个 Agent 的默认模型
- **Sub-Agent 模型**：`agents.defaults.subagents.model` 或 `sessions_spawn.model` 覆盖

### 关键知识点
- **思考级别**：off → minimal(Think) → low(Think hard) → medium(Think harder) → high(Ultrathink) → xhigh(Ultrathink+)
- **Fast 模式**：`/fast on` 启用低延迟模式；OpenAI 用 `service_tier=priority` + 低推理努力；Anthropic 用 `service_tier=auto`
- **Thinking 降级链**：内联指令 → 会话覆盖 → `agents.list[].thinkingDefault` → `agents.defaults.thinkingDefault` → 自适应 fallback
- **多 Agent 模型分离**：不同 Agent 可用不同模型（如 WhatsApp 用 Sonnet 快速响应，Telegram 用 Opus 深度分析）
- **Cron 模型覆盖**：isolated cron 任务可指定 `model: "opus"` 和 `thinking: high`

### 实践要点
- **省钱策略**：简单查询/闲聊用 GLM-4.5-Air，日常任务用默认模型，复杂架构用 GPT-4.1/O3
- **降级策略**：Cron 任务遇到 429/5xx 自动退避；provider overload 触发 fallback
- **会话级切换**：发送 `/think:high` 只影响当前会话；发送 `/fast on` 启用快速模式
- **Verbose 调试**：`/verbose on` 展示工具调用摘要，`/verbose full` 展示完整输出
- **推理可见性**：`/reasoning on` 展示思考过程，`stream` 模式（Telegram）流式展示

### 学习时间
- 01:28 - 01:32 (4 分钟)

---

## [2026-03-27] 飞书 API 深入

### 核心概念
- **多维表格 (Bitable)**：类似 Airtable 的结构化数据库，支持 27 种字段类型
- **日历**：飞书日历事件管理，支持重复事件、忙闲查询
- **任务**：飞书任务管理，支持清单、子任务、评论

### 关键知识点
- **Bitable 字段类型**：文本(1)、数字(2)、单选(3)、多选(4)、日期(5)、复选框(7)、人员(11)、超链接(15)、附件(17) 等
- **日期字段**：毫秒时间戳（如 1674206443000），不是秒
- **人员字段**：`[{id:"ou_xxx"}]` 数组格式
- **批量上限**：单次 ≤ 500 条，同一数据表不支持并发写
- **日历事件**：ISO 8601/RFC 3339 格式（含时区），`user_open_id` 必填
- **任务成员**：assignee=负责人，follower=关注人

### 实践要点
- **创建 Bitable 流程**：`app.create` → 删除默认空行 → `table.create` 或使用默认表 → `field.create` 定义字段 → `record.create` 写入
- **筛选查询**：`filter: {conjunction: 'and', conditions: [{field_name: '状态', operator: 'is', value: ['完成']}]}`
- **视图管理**：支持 grid/kanban/gallery/gantt/form 视图类型
- **日历忙闲查询**：`feishu_calendar_freebusy` 支持批量查询 1-10 个用户
- **技能触发**：飞书技能通过描述关键词匹配（如"多维表格"、"bitable"、"数据表"）

### 学习时间
- 01:32 - 01:37 (5 分钟)

---

## [2026-03-27] 浏览器自动化

### 核心概念
- **两种浏览器模式**：`openclaw`（Agent 专用隔离浏览器）和 `user`（挂载到真实 Chrome 的已有会话）
- **控制方式**：通过 Gateway 内置的控制服务（loopback only）控制 Chrome/Brave/Edge/Chromium
- **SSRF 策略**：默认阻止私有网络访问，可通过 `ssrfPolicy.dangerouslyAllowPrivateNetwork` 放开

### 关键知识点
- **核心操作**：status/start/stop/open/navigate/snapshot/screenshot/console/pdf/upload/dialog/act
- **Snapshot vs Screenshot**：snapshot 返回可交互的 DOM 结构（含 ref），screenshot 返回图片
- **操作类型**：click/type/press/hover/drag/select/fill/resize/wait/evaluate/close
- **Refs 系统**：`refs="role"`（角色+名称）或 `refs="aria"`（Playwright aria-ref id，更稳定）
- **Profile 切换**：默认 `openclaw`，需要登录态时用 `profile="user"`

### 实践要点
- **基本流程**：`snapshot` 获取页面结构 → `act` 操作元素 → `snapshot` 验证结果
- **多 Profile**：可配置多个浏览器 profile（openclaw/work/brave/remote），各有独立 CDP 端口
- **远程浏览器**：`cdpUrl: "http://10.0.0.42:9222"` 支持远程 Chrome DevTools Protocol
- **沙箱中使用**：沙箱中的浏览器需要在容器内安装 Chrome；`setupCommand` 在容器创建后运行一次
- **Frame 支持**：`frame` 参数可在 iframe 内操作

### 学习时间
- 01:37 - 01:41 (4 分钟)

---

## [2026-03-27] 文件操作

### 核心概念
- **read**：读取文件内容，支持 offset/limit 分页，也支持图片分析
- **write**：创建或覆盖文件，自动创建父目录
- **edit**：精确文本替换（old_string 必须完全匹配）
- **exec**：执行 shell 命令，支持 pty/background/elevated 模式

### 关键知识点
- **read 大文件**：超过 2000 行或 50KB 自动截断，用 offset/limit 分段读取
- **write 危险**：会覆盖已有文件，优先用 edit 做精确修改
- **edit 精确匹配**：old_string 必须完全匹配（包括空白），适合小范围修改
- **exec 模式**：默认阻塞；`background: true` 后台执行；`pty: true` 用于 TTY 交互程序
- **exec 安全**：`elevated: true` 需要审批；沙箱中的 exec 在容器内运行

### 实践要点
- **组合技巧 1：读取→修改→写入**：read 文件 → 分析内容 → edit 精确替换
- **组合技巧 2：搜索→批量修改**：exec `rg`/`grep` 搜索 → edit 逐个替换 或 exec `sed` 批量替换
- **组合技巧 3：创建项目结构**：write 创建目录结构 → exec 安装依赖 → write 写入代码
- **进程管理**：`exec background` 启动 → `process` 工具管理（poll/log/kill/write）
- **安全习惯**：优先 `trash` > `rm`；不确定时问；敏感操作前确认

### 学习时间
- 01:41 - 01:45 (4 分钟)

---

## [2026-03-27] 创建一个完整技能

### 核心概念
- **技能目录结构**：`skills/<name>/SKILL.md`（必选）+ 可选脚本/引用文件
- **SKILL.md 结构**：YAML 前置元数据（name/description/metadata）+ Markdown 指令体
- **ClawHub 发布**：`clawhub publish` 发布到公共注册表

### 关键知识点
- **完整技能包含**：
  1. 唯一名称（snake_case）
  2. 清晰描述（用于模型匹配）
  3. 前置元数据（OS 限制、依赖检查、安装器）
  4. Markdown 指令（告诉 Agent 何时触发、如何执行）
  5. 可选：引用文件（references/）、脚本（scripts/）
- **描述设计**：描述决定触发精准度，写清楚"当用户提到 X 时使用"
- **指令编写**：简洁、具体、面向 Agent（告诉它"做什么"而非"怎么做"）

### 实践要点
- **完整流程**：
  1. `mkdir -p ~/.openclaw/workspace/skills/my-skill`
  2. 编写 SKILL.md（含 metadata + 指令）
  3. 添加引用文件/脚本
  4. `/new` 或 `openclaw gateway restart` 加载
  5. `openclaw skills list` 验证
  6. 测试触发
  7. `clawhub publish` 发布
- **最佳实践**：
  - 指令要简洁，不要教模型"怎么当 AI"
  - `exec` 类技能要防止命令注入
  - 本地测试后再发布
  - 用 ClawHub 分享和发现技能
- **故障排除**：技能不触发检查描述是否匹配；依赖缺失检查 `requires.bins/env`

### 学习时间
- 01:45 - 01:49 (4 分钟)

---

## [2026-03-27] 优化 Agent 协作

### 核心概念
- **编排模式**：main → 编排者(depth-1) → 工作者(depth-2)，结果逐级 announce 回来
- **工具策略**：按 depth 分配工具权限，depth-1 编排者获得 sessions_spawn 等管理工具
- **并发管理**：`maxConcurrent` 全局上限 + `maxChildrenPerAgent` 单 Agent 上限

### 关键知识点
- **波次执行**：
  - 波次 1：并行 dispatch 无依赖任务（`sessions_send` timeout=0）
  - 波次 2：等待波次 1 完成后 dispatch 有依赖的任务
  - 最终：汇总所有结果
- **能力匹配**：根据 `capability.json` 匹配最佳 Agent（按评分排序）
- **超时催促**：Agent 10 分钟未响应则催促（`sessions_send` 发提醒消息）
- **结果聚合**：announce 回来的结果标准化为 Status/Result/Notes 格式
- **级联管理**：停止编排者自动停止所有工作者

### 实践要点
- **调度原则**：
  1. 单一职责 — 每任务只给最相关 Agent
  2. 波次并行 — 独立任务同时 dispatch
  3. 超时催促 — 10 分钟未响应则提醒
  4. 结果汇总 — 统一整理报告
  5. Instinct 提取 — 完成后记录经验教训
- **性能优化**：
  - 子 Agent 用更便宜的模型
  - `lightContext: true` 减少 bootstrap 开销
  - `cleanup: "delete"` 及时清理临时会话
  - 避免不必要的嵌套（maxSpawnDepth=2 足够大多数场景）
- **调试技巧**：
  - `/subagents list` 查看运行状态
  - `/subagents log <id>` 查看输出
  - `sessions_history` 获取完整历史

### 学习时间
- 01:49 - 01:53 (4 分钟)

---

## [2026-03-27] 学习笔记整理

### 核心概念
- **记忆系统**：daily notes（`memory/YYYY-MM-DD.md`）+ long-term（`MEMORY.md`）+ 专属记忆（`memory/agents/<id>/`）
- **知识流动**：Agent 完成任务写入 `lessons.md` → 心跳同步到 `SHARED_KNOWLEDGE.md` → 全团队可读
- **Instinct 提取**：每次任务完成后记录经验教训，避免重复犯错

### 关键知识点
- **文件组织**：
  - `AGENTS.md` — 工作区规则（团队协作、记忆系统、安全约束）
  - `SOUL.md` — 人格定义（身份、风格、核心工作流）
  - `WORKFLOW.md` — GSD 6 步工作流
  - `MODEL_ROUTING.md` — 模型选择策略
  - `TOOLS.md` — 环境特定配置
- **编写规范**：
  - 写清楚什么可以做、什么不能做
  - 用实际案例说明
  - 定期 review 和更新
  - 按优先级排序

### 实践要点
- **笔记模板**：
  ```
  ## [日期] [主题名称]
  ### 核心概念
  ### 关键知识点
  ### 实践要点
  ### 学习时间
  ```
- **定期整理**：
  - 每天清理 daily notes 中的噪音
  - 每周将重要经验提升到 MEMORY.md
  - 每月 review AGENTS.md/SOUL.md 的适用性
- **知识共享**：
  - SHARED_KNOWLEDGE.md 放团队通用知识
  - 按 Agent 角色过滤读取
  - 有争议的知识由 main agent 仲裁

### 学习时间
- 01:53 - 01:56 (3 分钟)
