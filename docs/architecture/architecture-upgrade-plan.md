# 🏗️ 全团队架构升级学习方案

> 创建时间：2026-03-27
> 维护者：年年 🎀
> 目标：让每个 Agent 都能自主学习、持续进化、高效协作

---

## 📊 现状盘点

### 当前团队

| Agent | 角色 | 模型 | 现有能力 | 欠缺 |
|-------|------|------|---------|------|
| **年年** (main) | 协调员 | Qwen3.5-Plus | 记忆、进化、任务调度 | 跨Agent学习协调弱 |
| **望舒** (product_manager) | 产品 | Qwen3.5-Plus | 需求分析、PRD | 无独立记忆/进化 |
| **玄机** (dev_engineer) | 后端 | Qwen-Coder-Next | 代码实现 | 无独立知识库 |
| **鉴微** (qa_engineer) | 测试 | Qwen3.5-Plus | 测试分析 | 无测试用例库 |
| **霓裳** (frontend_dev) | 前端 | Qwen-Coder-Next | UI实现 | 无设计模式库 |
| **岁岁** (chief_cute_officer) | 气氛 | GLM-4.5-Air | 互动/可爱 | 无 |

### 当前系统

| 系统 | 状态 | 覆盖范围 |
|------|------|---------|
| 记忆系统 | ✅ 运行中 | 仅 main agent |
| 进化系统 | ✅ 223周期 | 仅 main agent |
| Skill系统 | ✅ 119个 | 全团队可用 |
| 模型路由 | ✅ 已配置 | 全团队 |
| 工作流 | ✅ 6步标准化 | 全团队 |
| 心跳系统 | ✅ 30分钟 | 仅 main agent |

### 核心问题

```
┌─────────────────────────────────────────────────┐
│ 1. 能力集中在 main，子Agent 是"执行工具"          │
│    → 子Agent不会从经验中学习                      │
│                                                 │
│ 2. 记忆/进化不共享                                │
│    → 鉴微发现的bug模式，望舒不知道                │
│    → 开发踩的坑，下次还会踩                       │
│                                                 │
│ 3. Agent间通信靠年年中转                          │
│    → 年年成为瓶颈                                │
│    → Agent间没有直接知识交换                      │
│                                                 │
│ 4. 没有Agent级别的能力评估                        │
│    → 不知道谁擅长什么，谁需要补课                  │
└─────────────────────────────────────────────────┘
```

---

## 🎯 升级目标

```
现状：  main (全知) → 分配 → 子Agent (执行) → 汇报 → main
目标：  每个Agent自主学习 + 共享知识 + 协作进化
```

---

## 📋 升级方案（4个阶段）

---

### Phase 1：Agent 专属记忆（基础建设）

**目标：** 每个Agent有自己的"大脑"，不再只靠main的记忆

#### 1.1 Agent 专属记忆目录

```
memory/
├── agents/
│   ├── main/              ← 年年的私人笔记
│   │   ├── INSTINCTS.md   ← 已有
│   │   ├── decisions.md   ← 决策日志
│   │   └── lessons.md     ← 经验教训
│   │
│   ├── product_manager/   ← 望舒的产品知识
│   │   ├── domain.md      ← 业务领域知识
│   │   ├── patterns.md    ← 需求分析模式
│   │   └── prd-templates.md ← PRD模板库
│   │
│   ├── dev_engineer/      ← 玄机的技术库
│   │   ├── code-patterns.md ← 代码模式库
│   │   ├── bug-fixes.md   ← 修复记录
│   │   ├── tech-decisions.md ← 技术选型记录
│   │   └── architecture.md ← 架构决策
│   │
│   ├── qa_engineer/       ← 鉴微的测试知识
│   │   ├── test-patterns.md ← 测试模式库
│   │   ├── bug-analysis.md ← Bug分析模板
│   │   ├── coverage-maps.md ← 覆盖率地图
│   │   └── edge-cases.md  ← 边界case库
│   │
│   ├── frontend_dev/      ← 霓裳的前端知识
│   │   ├── ui-patterns.md ← UI模式库
│   │   ├── component-lib.md ← 组件知识库
│   │   └── accessibility.md ← 无障碍知识
│   │
│   └── chief_cute_officer/ ← 岁岁的互动库
│       ├── greetings.md   ← 问候模板
│       └── reactions.md   ← 互动反应库
```

#### 1.2 Agent 记忆同步机制

```
Agent完成任务
    ↓
写入自己的 memory/agents/{agent_id}/lessons.md
    ↓
main 心跳时检查所有 agent 的 lessons.md
    ↓
提取有价值的条目
    ↓
同步到 SHARED_KNOWLEDGE.md（全团队共享）
    ↓
各 Agent 下次启动时加载 SHARED_KNOWLEDGE.md
```

#### 1.3 共享知识库

```markdown
# SHARED_KNOWLEDGE.md - 团队共享知识

## 技术共识
- xxx

## 已知坑点
- xxx

## 最佳实践
- xxx

## 最近更新
- 2026-03-27: xxx
```

---

### Phase 2：Agent 专属进化（能力成长）

**目标：** 每个Agent有自己的"进化曲线"，不只是main在进化

#### 2.1 Agent 能力评估矩阵

```yaml
# memory/agents/{agent_id}/capability.json
{
  "agent_id": "qa_engineer",
  "name": "鉴微",
  "version": "1.0",
  "last_evaluated": "2026-03-27",
  "capabilities": {
    "test_design": {
      "level": 3,           # 1-5
      "evidence": ["测试用例质量评分85%", "边界case覆盖率70%"],
      "weaknesses": ["权限类测试覆盖不足"],
      "improvement_plan": "增加权限测试模式库"
    },
    "bug_analysis": {
      "level": 4,
      "evidence": ["根因定位准确率90%", "分类完整度85%"],
      "weaknesses": ["性能类bug分析较弱"],
      "improvement_plan": "补充性能分析模板"
    },
    "automation": {
      "level": 2,
      "evidence": ["能写简单测试脚本"],
      "weaknesses": ["自动化框架搭建不熟"],
      "improvement_plan": "学习pytest/playwright"
    }
  },
  "total_tasks_completed": 45,
  "success_rate": 0.87,
  "avg_quality_score": 4.2
}
```

#### 2.2 Agent 专属进化循环

```
Agent执行任务
    ↓
任务完成后自评（质量/效率/学习点）
    ↓
写入 capability.json
    ↓
发现弱项 → 生成学习任务
    ↓
main 分配学习资源（skill/文档/示例）
    ↓
Agent消化后写入 lessons.md
    ↓
下次任务验证是否提升
```

#### 2.3 各 Agent 专属进化重点

| Agent | 优先进化方向 | 学习资源 |
|-------|------------|---------|
| **望舒** | 需求拆解精度、用户故事编写 | PRD模板、竞品分析案例 |
| **玄机** | 代码模式库、架构决策能力 | 设计模式、最佳实践 |
| **鉴微** | 测试策略、自动化能力 | 测试框架、边界case库 |
| **霓裳** | 组件设计、响应式布局 | UI库、设计系统 |
| **岁岁** | 互动创意、氛围营造 | 表情包库、话术库 |

---

### Phase 3：Agent 间知识流动（协作增强）

**目标：** Agent间可以互相学习，不只靠main中转

#### 3.1 知识流动通道

```
┌──────────┐     写lessons.md     ┌──────────────┐
│ Agent A  │ ──────────────────→ │ SHARED_       │
└──────────┘                     │ KNOWLEDGE.md  │
                                 └──────┬────────┘
                                        │ 心跳同步
┌──────────┐     读SHARED_       ┌──────┴────────┐
│ Agent B  │ ←────────────────── │               │
└──────────┘     KNOWLEDGE.md    └───────────────┘
```

#### 3.2 Agent 间知识交换协议

```markdown
## 知识交换规则

### 谁可以写入共享知识？
- 所有 Agent 完成任务后都可以写入
- 格式：`[Agent名] [日期] 知识内容`

### 谁应该读取？
- 所有 Agent 每次任务前读取 SHARED_KNOWLEDGE.md
- 特别关注自己领域的更新

### 知识冲突处理？
- 以 main agent 的最终决定为准
- 有争议的知识标注 "⚠️ 待确认"

### 知识过期？
- 超过30天未被引用的知识标记为 "💤 可能过期"
- 超过90天未被引用的移入 archive/
```

#### 3.3 跨Agent协作增强

| 协作模式 | 现状 | 升级后 |
|---------|------|--------|
| Bug→用例 | main中转 | 鉴微直接读望舒的PRD写用例 |
| 代码审查 | main分配 | 玄机和霓裳直接互审 |
| 需求澄清 | main传话 | 望舒直接问开发可行性 |
| 测试反馈 | main汇总 | 鉴微直接写review给开发 |

---

### Phase 4：智能调度（效率革命）

**目标：** main agent 从"手动分配"升级为"智能调度"

#### 4.1 Agent 能力匹配

```yaml
# main agent 内部调度逻辑
task_assignment:
  - 读取任务类型和复杂度
  - 查询各 Agent capability.json
  - 匹配最佳 Agent（能力得分 + 负载 + 经验）
  - 分配任务
  - 跟踪执行质量
```

#### 4.2 动态负载均衡

```
┌─────────────────────────────────────────┐
│            Main Agent 调度中心           │
├─────────────────────────────────────────┤
│  Agent   │ 状态    │ 负载  │ 擅长领域    │
│  望舒     │ 空闲    │ 低    │ 需求分析    │
│  开发     │ 执行中  │ 高    │ 后端代码    │
│  鉴微     │ 空闲    │ 低    │ 测试设计    │
│  霓裳     │ 执行中  │ 中    │ 前端UI      │
│  岁岁     │ 空闲    │ 低    │ 氛围/内容   │
├─────────────────────────────────────────┤
│  新任务：写API文档                      │
│  → 匹配：玄机（最近刚写过类似）     │
│  → 但负载高 → 改分配给鉴微（逻辑清晰）   │
└─────────────────────────────────────────┘
```

#### 4.3 学习路径自动规划

```
main 分析 Agent 能力评估
    ↓
发现鉴微的自动化能力只有 Level 2
    ↓
自动生成学习任务：
  1. 阅读 pytest 官方文档
  2. 分析3个优秀测试框架案例
  3. 完成一个小测试项目
    ↓
分配给鉴微在空闲时完成
    ↓
完成后更新 capability.json
```

---

## 📊 实施路线图

```
Phase 1（基础建设）     Phase 2（能力成长）     Phase 3（协作增强）     Phase 4（智能调度）
    1-2周                  2-3周                  2-3周                  持续迭代
       │                      │                      │                      │
       ▼                      ▼                      ▼                      ▼
  ┌─────────┐           ┌─────────┐           ┌─────────┐           ┌─────────┐
  │ Agent   │           │ 能力评估 │           │ 知识流动 │           │ 智能匹配 │
  │ 专属记忆 │    →      │ 矩阵    │    →      │ 协议    │    →      │ 负载均衡 │
  │ 目录    │           │ 进化循环 │           │ 跨Agent │           │ 学习规划 │
  └─────────┘           └─────────┘           │ 协作    │           └─────────┘
                                              └─────────┘
```

---

## 🔧 实施细节

### Step 1：创建目录结构（立即可做）

```bash
mkdir -p memory/agents/{main,product_manager,dev_engineer,qa_engineer,frontend_dev,chief_cute_officer}
```

### Step 2：初始化各 Agent 能力文件（1天）

每个 Agent 目录下创建：
- `capability.json` — 能力评估
- `lessons.md` — 经验记录
- `patterns.md` — 专属模式库

### Step 3：创建共享知识库（1天）

```bash
touch SHARED_KNOWLEDGE.md
touch KNOWLEDGE_SYNC_LOG.md
```

### Step 4：更新心跳任务（2天）

在 HEARTBEAT.md 中新增：
- [ ] 检查各 Agent 的 lessons.md 更新
- [ ] 同步有价值的条目到 SHARED_KNOWLEDGE.md
- [ ] 检查 Agent 能力评估是否需要更新

### Step 5：更新 SOUL.md（1天）

在年年的角色描述中加入：
- 知识协调职责
- Agent 能力评估职责
- 学习路径规划职责

---

## 📈 预期收益

| 维度 | 现状 | 升级后预期 |
|------|------|-----------|
| **Agent独立性** | 低（依赖main） | 高（自主学习） |
| **知识复用** | 单点（main记忆） | 网状（全团队共享） |
| **协作效率** | 串行（main中转） | 并行（Agent直连） |
| **能力成长** | 仅main进化 | 全团队进化 |
| **任务质量** | 取决于main调度 | 取决于能力匹配 |

---

## ⚠️ 风险和对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 知识冲突 | Agent间结论矛盾 | main有最终决定权 |
| 信息过载 | 共享知识太多读不完 | 按Agent角色过滤，只读相关的 |
| 进化失控 | Agent改变核心行为 | 进化边界明确，只改策略不改规则 |
| 同步延迟 | 知识更新不同步 | 心跳周期内同步，最长30分钟 |

---

**一句话总结：让每个Agent从"执行工具"升级为"自主学习者"，通过共享知识和能力匹配实现团队级智能。** 🎀

---

*文档维护者：鉴微 🛡️*
*更新频率：每次架构调整后更新*
