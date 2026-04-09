# 多 Agent 协作进度控制与流程规划

> 研究时间：2026-04-08 15:07  
> 理论基础：忘忧并行调度 + OpenClaw 多 Agent + Karpathy 进度驱动  
> 实践案例：13 Agent 协作系统  
> 作者：年年 🎀

---

## 🎯 核心理念

### 时间驱动 vs 进度驱动

| 维度 | 时间驱动 ❌ | 进度驱动 ✅ |
|------|-----------|-----------|
| **触发条件** | "每 30 分钟执行" | "完成 10 个任务后执行" |
| **完成标准** | "运行 30 分钟" | "处理 50 条消息" |
| **汇报时机** | "每小时汇报" | "每波次完成后汇报" |
| **资源利用** | 可能浪费时间 | 按需使用 |
| **结果可比性** | 样本量不同 | 样本量一致 |

### 进度驱动的核心公式

```
进度 = 已完成任务数 / 总任务数

触发条件 = 进度达到阈值（如 25%/50%/75%/100%）
汇报时机 = 每个波次完成后
资源分配 = 根据进度动态调整
```

---

## 🏗️ 多 Agent 进度控制架构

### 三层架构

```
┌─────────────────────────────────────────────────┐
│              战略规划层（年年）                   │
│  • 定义总体进度目标（100%）                      │
│  • 分解为波次（Wave-1/2/3...）                  │
│  • 分配 Agent 角色（望舒/玄机/惊鸿...）           │
│  • 定义进度阈值（25%/50%/75%/100%）             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│              波次协调层（sessions_send）          │
│  • 波次任务分解（Wave-1: 选题→大纲→人设）        │
│  • Agent 任务分配（望舒→灵犀→惊鸿）              │
│  • 进度追踪（0/10→5/10→10/10）                  │
│  • 依赖管理（大纲完成→启动人设）                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│              任务执行层（各 Agent）               │
│  • 执行具体任务（望舒：分析 10 个竞品）           │
│  • 报告进度（5/10→8/10→10/10）                  │
│  • 触发汇报（完成 10/10→通知年年）               │
│  • 异常处理（超时/失败→请求支援）                │
└─────────────────────────────────────────────────┘
```

---

## 📊 进度指标设计

### 三级进度指标

#### L1：总体进度（主人可见）

```
小说创作项目总体进度：45%
├── 第 1 阶段：选题定方向 ✅ 100%
├── 第 2 阶段：大纲 + 人设 ✅ 100%
├── 第 3 阶段：章节创作 🟡 45%
├── 第 4 阶段：发布准备 ⏳ 0%
└── 第 5 阶段：数据追踪 ⏳ 0%
```

**汇报时机**：每个阶段完成后

---

#### L2：波次进度（年年可见）

```
Wave-3（章节创作）进度：45%
├── 第 1 章 ✅ 100%
├── 第 2 章 ✅ 100%
├── 第 3 章 ✅ 100%
├── 第 4 章 ✅ 100%
├── 第 5 章 ✅ 100%
├── 第 6 章 ✅ 100%
├── 第 7 章 ✅ 100%
├── 第 8 章 ✅ 100%
├── 第 9 章 ✅ 100%
├── 第 10 章 ⏳ 45%
├── 第 11 章 ⏳ 0%
└── 第 12 章 ⏳ 0%
```

**汇报时机**：每章完成后

---

#### L3：任务进度（Agent 可见）

```
惊鸿 - 第 10 章创作进度：45%
├── 大纲细读 ✅ 100%
├── 场景设计 ✅ 100%
├── 对话撰写 ✅ 100%
├── 正文创作 🟡 45% (1350/3000 字)
├── 爽点植入 ⏳ 0%
└── 伏笔检查 ⏳ 0%
```

**汇报时机**：每 25% 进度汇报一次

---

## 🔄 流程规划方法

### 方法 1：波次规划法（推荐）

**核心思想**：将大任务分解为多个波次，每个波次独立完整

**示例：小说创作 12 章**

```
总体目标：12 章小说（3-4 万字）

Wave-1（第 1-4 章）：开篇定基调
├── 目标：4 章 1 万字
├── Agent：惊鸿（创作）+ 鉴微（审查）
├── 进度指标：4/4 章
├── 完成触发：第 4 章审查通过
└── 汇报：Wave-1 完成报告

Wave-2（第 5-8 章）：发展 + 冲突
├── 目标：4 章 1 万字
├── Agent：惊鸿（创作）+ 鉴微（审查）
├── 进度指标：4/4 章
├── 完成触发：第 8 章审查通过
└── 汇报：Wave-2 完成报告

Wave-3（第 9-12 章）：高潮 + 结局
├── 目标：4 章 1 万字
├── Agent：惊鸿（创作）+ 鉴微（审查）
├── 进度指标：4/4 章
├── 完成触发：第 12 章审查通过
└── 汇报：Wave-3 完成报告 + 总体完成
```

**优势**：
- ✅ 每个波次独立，可并行
- ✅ 进度清晰（25%/50%/75%/100%）
- ✅ 风险分散（Wave-1 失败不影响 Wave-2）

---

### 方法 2：流水线规划法

**核心思想**：多 Agent 流水线作业，前后依赖

**示例：小说创作流水线**

```
望舒（产品）     灵犀（创意）     惊鸿（内容）     鉴微（测试）
    ↓              ↓              ↓              ↓
选题分析   →   脑洞生成   →   正文创作   →   审查过稿
(2 小时)       (2 小时)       (4 小时)       (1 小时)

进度追踪：
T+0h: 望舒开始选题分析
T+2h: 望舒完成→灵犀开始
T+4h: 灵犀完成→惊鸿开始
T+8h: 惊鸿完成→鉴微开始
T+9h: 鉴微完成→发布

进度指标：
- 望舒：0/1→1/1（触发灵犀）
- 灵犀：0/1→1/1（触发惊鸿）
- 惊鸿：0/1→1/1（触发鉴微）
- 鉴微：0/1→1/1（触发发布）
```

**优势**：
- ✅ 专业化分工
- ✅ 质量可控
- ✅ 责任清晰

**劣势**：
- ❌ 串行执行，耗时长
- ❌ 瓶颈效应（最慢环节决定总速度）

---

### 方法 3：混合规划法（最优）

**核心思想**：波次内流水线，波次间并行

**示例：12 章小说创作**

```
总体目标：12 章（3-4 万字）

Wave-1（第 1-4 章）：
┌─────────────────────────────────────────┐
│ 望舒→灵犀→惊鸿→鉴微（流水线）            │
│ 第 1 章：T+0h→T+2h→T+6h→T+7h            │
│ 第 2 章：T+2h→T+4h→T+8h→T+9h            │
│ 第 3 章：T+4h→T+6h→T+10h→T+11h          │
│ 第 4 章：T+6h→T+8h→T+12h→T+13h          │
└─────────────────────────────────────────┘
Wave-1 完成：T+13h（4 章 1 万字）

Wave-2（第 5-8 章）：
┌─────────────────────────────────────────┐
│ 望舒→灵犀→惊鸿→鉴微（流水线）            │
│ ...（与 Wave-1 并行）                    │
└─────────────────────────────────────────┘
Wave-2 完成：T+13h（4 章 1 万字）

Wave-3（第 9-12 章）：
┌─────────────────────────────────────────┐
│ 望舒→灵犀→惊鸿→鉴微（流水线）            │
│ ...（与 Wave-1/2 并行）                  │
└─────────────────────────────────────────┘
Wave-3 完成：T+13h（4 章 1 万字）

总体完成：T+13h（12 章 3 万字）
```

**优势**：
- ✅ 波次间并行（加速 3 倍）
- ✅ 波次内流水线（质量可控）
- ✅ 进度清晰（3 波次×4 章）

---

## 📋 进度控制实现

### 实现 1：进度追踪器

```python
class ProgressTracker:
    def __init__(self, total_tasks, wave_size=4):
        self.total_tasks = total_tasks
        self.wave_size = wave_size
        self.completed = 0
        self.current_wave = 1
        self.agent_progress = {}  # {agent_id: completed/total}
    
    def update(self, agent_id, completed, total):
        self.agent_progress[agent_id] = (completed, total)
        self.completed = sum(c for c, t in self.agent_progress.values())
        
        # 检查波次完成
        if self.completed % self.wave_size == 0:
            self.on_wave_complete(self.current_wave)
            self.current_wave += 1
        
        # 检查总体完成
        if self.completed == self.total_tasks:
            self.on_project_complete()
    
    def on_wave_complete(self, wave_num):
        """波次完成回调"""
        # 触发汇报
        send_card(
            template="wave_completion",
            wave_num=wave_num,
            progress=f"{wave_num * self.wave_size}/{self.total_tasks}"
        )
        
        # 触发下一波次
        start_next_wave(wave_num + 1)
    
    def on_project_complete(self):
        """项目完成回调"""
        send_card(
            template="project_completion",
            total_tasks=self.total_tasks,
            total_time=self.elapsed_time
        )
```

---

### 实现 2：进度驱动触发器

```python
class ProgressTrigger:
    """进度驱动触发器"""
    
    TRIGGERS = {
        "wave_start": {"condition": "progress % 4 == 0"},
        "wave_complete": {"condition": "progress % 4 == 0 and progress > 0"},
        "halfway": {"condition": "progress == total / 2"},
        "project_complete": {"condition": "progress == total"},
    }
    
    def check_triggers(self, progress, total):
        """检查触发条件"""
        triggered = []
        
        for trigger_name, config in self.TRIGGERS.items():
            if eval(config["condition"]):
                triggered.append(trigger_name)
        
        return triggered
    
    def on_trigger(self, trigger_name, context):
        """触发处理"""
        if trigger_name == "wave_start":
            self.start_wave(context["wave_num"])
        elif trigger_name == "wave_complete":
            self.report_wave_complete(context["wave_num"])
        elif trigger_name == "halfway":
            self.report_halfway()
        elif trigger_name == "project_complete":
            self.report_project_complete()
```

---

### 实现 3：多 Agent 进度同步

```python
class MultiAgentSync:
    """多 Agent 进度同步"""
    
    def __init__(self, agents):
        self.agents = agents  # [望舒，灵犀，惊鸿，鉴微]
        self.progress = {agent: 0 for agent in agents}
        self.dependencies = {
            "灵犀": ["望舒"],  # 灵犀依赖望舒
            "惊鸿": ["灵犀"],  # 惊鸿依赖灵犀
            "鉴微": ["惊鸿"],  # 鉴微依赖惊鸿
        }
    
    def can_start(self, agent):
        """检查 Agent 是否可以开始"""
        deps = self.dependencies.get(agent, [])
        return all(self.progress[dep] == 100 for dep in deps)
    
    def update_progress(self, agent, progress):
        """更新进度"""
        self.progress[agent] = progress
        
        # 检查是否可以触发下一个 Agent
        for next_agent, deps in self.dependencies.items():
            if agent in deps and self.can_start(next_agent):
                self.start_agent(next_agent)
    
    def start_agent(self, agent):
        """启动 Agent"""
        sessions_send(
            sessionKey=f"agent:{agent}:main",
            message=f"[进度驱动] {agent} 可以开始了！前置依赖已完成。"
        )
```

---

## 🎯 实际案例：OpenClaw 13 Agent 协作

### 案例 1：小说创作流程

```
总体目标：12 章小说（3-4 万字）

第 1 阶段：选题定方向（Wave-1）
├── 望舒：分析知乎盐选热门题材（10 个竞品）
│   进度：0/10→5/10→10/10 ✅
│   触发：完成 10/10→通知年年
│
├── 灵犀：提供 3-5 个创意脑洞
│   依赖：望舒完成
│   进度：0/5→3/5→5/5 ✅
│   触发：完成 5/5→通知年年
│
└── 年年：汇总汇报主人
    依赖：望舒 + 灵犀完成
    触发：主人确认→启动第 2 阶段

第 2 阶段：大纲 + 人设（Wave-2）
├── 望舒：PRD 文档（1 份）
├── 灵犀：角色卡创意（5 个角色）
├── 惊鸿：大纲初稿（12 章）
├── 鉴微：审查过稿（1 次）
└── 年年：汇总汇报主人

第 3 阶段：章节创作（Wave-3 到 Wave-6）
├── Wave-3：第 1-4 章（惊鸿 + 鉴微）
├── Wave-4：第 5-8 章（惊鸿 + 鉴微）
├── Wave-5：第 9-12 章（惊鸿 + 鉴微）
└── 年年：每波次汇报

第 4 阶段：发布（Wave-7）
├── 霓裳：封面设计（1 张）
├── 岁岁：营销文案（3 版）
└── 年年：发布汇报
```

**进度汇报卡片**：

```
┌─────────────────────────────────────────┐
│  **小说创作进度汇报（Wave-3 完成）** 🎉    │
│                                         │
│  **总体进度：**25% → 50%                │
│                                         │
│  **Wave-3（第 1-4 章）：**                │
│  | 章节 | 创作 | 审查 | 状态 |          │
│  |------|------|------|------|          │
│  | 第 1 章 | ✅ | ✅ | 已完成 |          │
│  | 第 2 章 | ✅ | ✅ | 已完成 |          │
│  | 第 3 章 | ✅ | ✅ | 已完成 |          │
│  | 第 4 章 | ✅ | ✅ | 已完成 |          │
│                                         │
│  **下一步：**启动 Wave-4（第 5-8 章）      │
│  **预计完成：**T+12h                     │
└─────────────────────────────────────────┘
```

---

### 案例 2：Cron 系统修复（已完成）

```
总体目标：修复 8 个 timeout 错误的 Cron 任务

Wave-1（P0 任务）：
├── 09:00 指标分析：300s→600s ✅
├── 20:00 每日复盘：300s→600s ✅
└── 06:00 隔夜成果：300s→600s ✅
进度：3/3 ✅ 完成

Wave-2（P1 任务 - 太一系）：
├── 技术扫描：120s→300s ✅
├── Prompt 工程：180s→300s ✅
├── 知识沉淀：180s→300s ✅
├── AI 工具探索：180s→300s ✅
└── 代码实战：180s→300s ✅
进度：5/5 ✅ 完成

总体完成：8/8 ✅ 100%
```

**进度汇报卡片**：

```
┌─────────────────────────────────────────┐
│  **Cron 系统健康度修复完成！** 🎉          │
│                                         │
│  **总体进度：**0% → 100%                │
│                                         │
│  **Wave-1（P0 任务）：**3/3 ✅           │
│  **Wave-2（P1 任务）：**5/5 ✅           │
│                                         │
│  **修复结果：**                          │
│  - 错误 Cron 数量：5→0                   │
│  - 系统健康度：0% → 100%                │
│  - 提交文件：56 个                       │
│                                         │
│  **下一步：**推送 Git 触发 CI/CD 验证      │
└─────────────────────────────────────────┘
```

---

## 📊 进度可视化设计

### 卡片模板：进度汇报

```json
{
  "type": "progress_report",
  "elements": [
    {
      "type": "header",
      "content": "**{项目名称}进度汇报（{wave_name}）** {emoji}"
    },
    {
      "type": "progress_bar",
      "overall": "{overall_progress}%",
      "wave": "{wave_progress}%"
    },
    {
      "type": "table",
      "columns": ["任务", "进度", "状态"],
      "rows": [
        ["第 1 章", "100%", "✅ 已完成"],
        ["第 2 章", "100%", "✅ 已完成"],
        ["第 3 章", "45%", "🟡 进行中"],
        ["第 4 章", "0%", "⏳ 待开始"]
      ]
    },
    {
      "type": "section",
      "title": "**下一步：**",
      "content": "{next_action}"
    },
    {
      "type": "footer",
      "content": "预计完成：{estimated_time}"
    }
  ]
}
```

---

### 卡片模板：波次完成

```json
{
  "type": "wave_completion",
  "elements": [
    {
      "type": "header",
      "content": "**{wave_name}完成！** {emoji}"
    },
    {
      "type": "section",
      "content": "**总体进度：**{previous}% → {current}%"
    },
    {
      "type": "table",
      "columns": ["任务", "负责 Agent", "状态"],
      "rows": [
        ["任务 1", "望舒", "✅"],
        ["任务 2", "灵犀", "✅"],
        ["任务 3", "惊鸿", "✅"],
        ["任务 4", "鉴微", "✅"]
      ]
    },
    {
      "type": "section",
      "title": "**下一步：**",
      "content": "启动{next_wave_name}"
    },
    {
      "type": "footer",
      "content": "本波次耗时：{elapsed_time}"
    }
  ]
}
```

---

## 🚀 年年实施方案

### 短期（立即执行）

**创建进度追踪器**：

```python
# progress_tracker.py
class NiannianProgressTracker:
    def __init__(self):
        self.projects = {}  # {project_id: ProgressTracker}
    
    def create_project(self, project_id, total_tasks, wave_size=4):
        self.projects[project_id] = ProgressTracker(total_tasks, wave_size)
    
    def update(self, project_id, agent_id, completed, total):
        tracker = self.projects[project_id]
        tracker.update(agent_id, completed, total)
        
        # 自动触发汇报
        if tracker.completed % tracker.wave_size == 0:
            self.send_wave_report(project_id, tracker.current_wave)
```

### 中期（1 周）

**集成到所有 Agent**：

| Agent | 进度汇报频率 | 触发条件 |
|-------|------------|---------|
| 望舒 | 每 10 个竞品 | 完成 10/10 |
| 灵犀 | 每 5 个创意 | 完成 5/5 |
| 惊鸿 | 每章完成 | 完成 1/1 |
| 鉴微 | 每章审查 | 完成 1/1 |
| 太一 | 每 50 个网站 | 完成 50/50 |

### 长期（1 月）

**进度驱动标准化**：

```
所有 Agent 统一使用：
- ProgressTracker 类
- 进度汇报卡片模板
- 波次完成触发器
- 异常处理流程
```

---

## 📋 总结

### 进度控制核心原则

1. **进度驱动，非时间驱动**
   - 触发条件 = 完成任务数，非经过时间
   - 汇报时机 = 波次完成，非固定时间

2. **波次分解，独立完整**
   - 每个波次有明确目标
   - 波次间可并行

3. **三级进度，分层汇报**
   - L1：总体进度（主人可见）
   - L2：波次进度（年年可见）
   - L3：任务进度（Agent 可见）

4. **依赖管理，流水线作业**
   - 明确前后依赖
   - 自动触发下一环节

### 最佳实践

| 场景 | 推荐方法 | 理由 |
|------|---------|------|
| 小说创作 | 混合规划法 | 波次并行 + 流水线质量 |
| 技术修复 | 波次规划法 | 任务独立，可并行 |
| 数据分析 | 流水线规划法 | 前后依赖强 |
| 技能开发 | 波次规划法 | 每个 Skill 独立 |

---

**作者**：年年 🎀  
**创建时间**：2026-04-08 15:07  
**理论基础**：忘忧并行调度 + OpenClaw 多 Agent + Karpathy 进度驱动
