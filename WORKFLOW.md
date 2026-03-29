# WORKFLOW.md - 团队标准工作流

> 基于 GSD + Superpowers 方法论，适配 OpenClaw 多 Agent 团队
> 创建时间：2026-03-25
> 维护者：年年 🎀

---

## 📋 6 步标准化项目流程

### Step 1: 需求理解（年年）
**对标 GSD：** `/gsd:new-project`

- 年年接收主人任务
- 追问澄清模糊需求（不假设，不瞎猜）
- 输出：**需求摘要**（一句话说清楚要做什么）

### Step 2: 深入讨论（望舒 - 望舒）
**对标 GSD：** `/gsd:discuss-phase`

- 望舒细化需求，消除灰色地带
- 明确边界条件、异常场景
- 输出：**PRD / 需求文档**

### Step 3: 方案规划（玄机 / 太一）
**对标 GSD：** `/gsd:plan-phase`

- 技术方案设计
- **任务拆解 + 依赖分析**
- **波次规划**（见下方波次并行机制）
- 输出：**技术方案 + 波次执行计划**

### Step 3.5: 前置约束检查（年年）🆕 学自惊鸿
**核心理念：质量不是评估出来的，是约束出来的**

每个任务执行前，年年先过一遍前置约束checklist：

**通用约束（所有任务）：**
- [ ] 目标是否一句话说清楚了？
- [ ] 验收标准是否在执行前就定义好了？（TDD前置）
- [ ] 任务边界是否明确——做什么、不做什么？
- [ ] 依赖关系是否分析清楚了？

**产出物约束（文档/代码/设计）：**
- [ ] 产出物有明确的格式要求吗？
- [ ] 有禁止事项吗？（比如：不要AI味、不要废话）
- [ ] 风格一致性有保证吗？（禁词表/必含元素）

**不过约束checklist的任务，不允许进入执行阶段。**

### Step 4: 波次并行执行（全团队）
**对标 GSD：** `/gsd:execute-phase`

- 年年按波次分发任务（见下方机制）
- 每个任务在**独立子会话**中执行（防 Context Rot）
- 每个任务完成后自动 git commit
- 输出：**代码/文档/产出物**

### Step 5: 验证验收（鉴微 - 鉴微）
**对标 GSD：** `/gsd:verify-work`

- 鉴微按**预定义验收标准**走查（TDD 前置）
- 自动化测试 + 人工走查
- 失败任务自动打回重做
- 输出：**测试报告**

### Step 6: 归档收尾（年年）
**对标 GSD：** `/gsd:complete-milestone`

- 年年汇总所有产出物
- 更新 STATE.yaml 任务状态
- 同步到飞书知识库
- 更新 memory 日志
- 输出：**完成报告 + 知识库归档**

---

## 🎭 四角色分离原则（学自惊鸿）

复杂任务拆成4个独立角色，每个角色只能做自己的事：

| 角色 | 职责 | 限制 |
|------|------|------|
| **规划者** | 任务拆解、方案设计、依赖分析 | 不写代码/不做产出 |
| **执行者** | 具体产出（代码/文档/设计） | 不审查自己，只管产出 |
| **审查者** | 质量检查、问题分级、修改建议 | 不直接改产出，有否决权 |
| **整合者** | 汇总各产出、组装交付、归档 | 不做具体任务 |

**适用场景：** 重要项目、多Agent协作、高风险任务
**不适用：** 简单任务、日常对话、即时查询

---

## 🌊 波次并行执行机制

### 核心原则
```
Wave N 中的所有任务互相独立，可以并行执行
Wave N+1 的任务依赖 Wave N 的产出
```

### 年年分发任务时的标注格式
```yaml
project: 用户登录系统
waves:
  - wave: 1
    tasks:
      - name: 数据库模型设计
        agent: dev_engineer
        depends_on: []
      - name: JWT 配置方案
        agent: dev_engineer  
        depends_on: []
      - name: 测试用例框架
        agent: qa_engineer
        depends_on: []
    parallel: true  # Wave 1 全部并行

  - wave: 2
    tasks:
      - name: 认证 API 开发
        agent: dev_engineer
        depends_on: [数据库模型设计, JWT 配置方案]
      - name: 登录页 UI
        agent: frontend_dev
        depends_on: []
    parallel: true  # Wave 2 内部并行

  - wave: 3
    tasks:
      - name: 集成测试
        agent: qa_engineer
        depends_on: [认证 API 开发, 登录页 UI]
    parallel: false
```

### 年年执行波次的代码逻辑
```
for each wave in waves:
    # 同一波次内的任务同时发出
    for each task in wave.tasks:
        sessions_send(agentId=task.agent, message=task.description)
    
    # 等待本波次全部完成
    wait_all(wave.tasks)
    
    # 进入下一波次
```

### 关键规则
1. **无依赖 = 同波并行** — 能并行的绝不串行
2. **有依赖 = 后波执行** — 严格等前置完成
3. **每任务独立上下文** — 用 `sessions_spawn` 创建子会话，防 Context Rot
4. **原子提交** — 每个任务完成后独立 git commit，标注任务 ID

---

## 🔴🟢🔵 TDD 验收标准前置机制

### 核心原则
```
先定义"什么是成功" → 再去实现 → 最后验证
```

### 工作流
```
Step 1: 年年接收任务
    ↓
Step 2: 年年 + 鉴微 定义验收标准
    ↓ （验收标准前置，开发前就写好）
Step 3: 玄机按标准实现
    ↓
Step 4: 鉴微按预定义标准验收
    ↓
    ├── ✅ 通过 → 归档
    └── ❌ 不通过 → 打回重做（附失败原因）
```

### 验收标准模板
```yaml
task: TASK-XXX 任务名称
acceptance_criteria:
  - id: AC-1
    description: "用户可以通过邮箱+密码登录"
    type: functional
    priority: must-have
    
  - id: AC-2
    description: "登录失败返回明确错误信息"
    type: functional
    priority: must-have
    
  - id: AC-3
    description: "API 响应时间 < 500ms"
    type: performance
    priority: should-have

  - id: AC-4
    description: "密码错误 5 次后锁定账户"
    type: security
    priority: must-have

test_cases:
  - AC-1: "输入正确邮箱密码 → 返回 token"
  - AC-1: "输入未注册邮箱 → 返回用户不存在"
  - AC-2: "密码错误 → 返回密码错误提示"
  - AC-3: "并发 100 请求 → 平均响应 < 500ms"
  - AC-4: "连续 5 次错误密码 → 账户锁定 30 分钟"
```

### 关键规则
1. **验收标准必须在开发前确定** — 不是做完了再想怎么测
2. **must-have 必须 100% 通过** — 任何一条不过就打回
3. **鉴微在 Step 2 就介入** — 不是最后才出场
4. **验收标准写入任务描述** — 玄机能看到要达到什么标准

---

## 🧹 Context Rot 防治

### 问题
长会话中 Agent 的输出质量会逐渐下降（上下文堆积、注意力分散）

### 解决方案
1. **复杂任务用 `sessions_spawn`** — 每个任务独立子会话
2. **子会话只关注当前任务** — 不带历史包袱
3. **任务完成后子会话结束** — 干净利落
4. **主会话只做协调** — 年年只分发和汇总，不做具体实现

### 适用场景
| 场景 | 方式 |
|------|------|
| 简单查询/回答 | 主会话直接处理 |
| 单个开发任务 | `sessions_send` 给对应 Agent |
| 复杂多步骤任务 | `sessions_spawn` 创建独立子会话 |
| 多 Agent 协作项目 | 波次并行 + 每任务独立子会话 |

---

## 📊 Git 原子提交规范

### Commit Message 格式
```
[TASK-XXX] <type>: <简述>

<详细描述>

Wave: <波次号>
Agent: <执行 Agent>
AC: <通过的验收标准 ID>
```

### Type 类型
| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| test | 测试用例 |
| refactor | 重构 |
| chore | 杂项 |

### 示例
```
[TASK-014] feat: 实现用户登录 API

- JWT token 生成和验证
- 密码加密存储
- 登录失败错误处理

Wave: 2
Agent: dev_engineer
AC: AC-1, AC-2, AC-4
```

---

## 🔄 快速启动模板

### 主人说："帮我做 XXX"

年年立即执行：
```
1. 📝 需求理解 — 确认主人要什么（有疑问就追问）
2. 📋 定义验收标准 — 和鉴微一起写 AC
3. 🔧 任务拆解 — 拆成可并行的波次
4. 🚀 波次执行 — sessions_send/spawn 分发
5. ✅ 验收 — 鉴微按 AC 走查
6. 📦 归档 — 更新 STATE.yaml + 知识库
```

---

**版本：** v1.0
**创建时间：** 2026-03-25
**灵感来源：** GSD (Get Shit Done) + Superpowers (TDD Framework)
