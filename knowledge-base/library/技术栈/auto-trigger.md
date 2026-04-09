# 自动触发器（Auto Trigger）

> 创建时间：2026-04-08 15:10  
> 目的：解决多 Agent 协作需要人工催促的问题  
> 状态：🔴 待实施

---

## 🎯 核心功能

### 1. 自动触发下一环节

```python
def on_agent_complete(agent, task):
    """Agent 完成任务后自动触发下一环节"""
    next_agent = WORKFLOW[agent]["next"]
    
    if next_agent:
        sessions_send(
            sessionKey=f"agent:{next_agent}:main",
            message=f"[自动触发] {agent} 已完成{task}，你可以开始了！"
        )
```

### 2. 自动进度监控

```python
async def monitor_progress():
    """每分钟检查进度"""
    for agent, status in agent_status.items():
        if status["status"] == "running":
            elapsed = now() - status["start_time"]
            
            if elapsed == timeout * 0.5:
                send_reminder(agent)  # 50% 提醒
            elif elapsed == timeout * 0.8:
                send_urge(agent)  # 80% 催促
            elif elapsed >= timeout:
                escalate(agent)  # 超时升级
```

### 3. 自动汇报主人

```python
def on_wave_complete(wave_num):
    """波次完成自动汇报"""
    send_card(
        template="wave_completion",
        wave_num=wave_num,
        progress=f"{wave_num * 4}/12"
    )
```

---

## 📋 工作流定义

### 小说创作工作流

```python
NOVEL_WORKFLOW = {
    "wave_1": {
        "name": "选题定方向",
        "steps": [
            {"agent": "望舒", "task": "分析竞品", "timeout": 1800, "next": "灵犀"},
            {"agent": "灵犀", "task": "提供创意", "timeout": 1800, "next": "年年"},
        ]
    },
    "wave_2": {
        "name": "大纲 + 人设",
        "steps": [
            {"agent": "望舒", "task": "PRD 文档", "timeout": 3600, "next": "灵犀"},
            {"agent": "灵犀", "task": "角色卡", "timeout": 3600, "next": "惊鸿"},
            {"agent": "惊鸿", "task": "大纲", "timeout": 7200, "next": "鉴微"},
            {"agent": "鉴微", "task": "审查", "timeout": 1800, "next": "年年"},
        ]
    },
    "wave_3": {
        "name": "章节创作（第 1-4 章）",
        "steps": [
            {"agent": "惊鸿", "task": "第 1 章", "timeout": 7200, "next": "鉴微"},
            {"agent": "鉴微", "task": "审查", "timeout": 1800, "next": "惊鸿"},
            {"agent": "惊鸿", "task": "第 2 章", "timeout": 7200, "next": "鉴微"},
            {"agent": "鉴微", "task": "审查", "timeout": 1800, "next": "惊鸿"},
            {"agent": "惊鸿", "task": "第 3 章", "timeout": 7200, "next": "鉴微"},
            {"agent": "鉴微", "task": "审查", "timeout": 1800, "next": "惊鸿"},
            {"agent": "惊鸿", "task": "第 4 章", "timeout": 7200, "next": "鉴微"},
            {"agent": "鉴微", "task": "审查", "timeout": 1800, "next": "年年"},
        ]
    }
}
```

---

## 🔧 实施步骤

### 第 1 步：创建自动触发器模块

```python
# auto_trigger.py
class AutoTrigger:
    def __init__(self):
        self.workflow = NOVEL_WORKFLOW
        self.agent_status = {}
    
    def register_agent_start(self, agent, task):
        """注册 Agent 开始任务"""
        self.agent_status[agent] = {
            "task": task,
            "status": "running",
            "start_time": time.now()
        }
        
        # 启动监控
        asyncio.create_task(self.monitor(agent))
    
    def register_agent_complete(self, agent, task):
        """注册 Agent 完成任务"""
        self.agent_status[agent]["status"] = "completed"
        
        # 自动触发下一环节
        next_agent = self.get_next_agent(agent)
        if next_agent:
            self.trigger(next_agent)
    
    def trigger(self, agent):
        """触发 Agent"""
        task = self.get_task(agent)
        sessions_send(
            sessionKey=f"agent:{agent}:main",
            message=f"[自动触发] 上一环节已完成，你可以开始{task}了！"
        )
    
    async def monitor(self, agent):
        """监控进度"""
        while self.agent_status[agent]["status"] == "running":
            await asyncio.sleep(60)
            
            elapsed = time.now() - self.agent_status[agent]["start_time"]
            timeout = self.get_timeout(agent)
            
            if elapsed >= timeout * 0.5 and elapsed < timeout * 0.8:
                self.send_reminder(agent)
            elif elapsed >= timeout * 0.8 and elapsed < timeout:
                self.send_urge(agent)
            elif elapsed >= timeout:
                self.escalate(agent)
                break
```

### 第 2 步：集成到所有 Agent

修改每个 Agent 的心跳回调：

```python
# 在每个 Agent 的回调中
def on_heartbeat():
    # 报告进度
    progress = get_progress()
    auto_trigger.register_agent_start(agent_id, current_task)
    
    if task_complete:
        auto_trigger.register_agent_complete(agent_id, current_task)
```

### 第 3 步：创建进度追踪器

```python
# progress_tracker.py
class ProgressTracker:
    def __init__(self):
        self.projects = {}
    
    def create_project(self, project_id, workflow):
        self.projects[project_id] = {
            "workflow": workflow,
            "current_wave": 1,
            "current_step": 0,
            "progress": 0
        }
    
    def update_progress(self, project_id, agent, completed):
        project = self.projects[project_id]
        project["progress"] = completed
        
        # 检查波次完成
        if completed % 4 == 0:
            self.on_wave_complete(project_id, project["current_wave"])
            project["current_wave"] += 1
```

### 第 4 步：创建卡片模板

```python
# card_templates.py
CARD_TEMPLATES = {
    "auto_trigger": """
┌─────────────────────────────────────────┐
│  **自动触发通知** 🔔                     │
│                                         │
│  {from_agent} 已完成 {task}              │
│                                         │
│  下一环节：{to_agent} → {next_task}     │
│                                         │
│  已自动触发，请开始执行～                │
└─────────────────────────────────────────┘
""",
    "progress_reminder": """
┌─────────────────────────────────────────┐
│  **进度提醒** ⏰                         │
│                                         │
│  任务：{task}                           │
│  进度：{progress}%                      │
│  已用时间：{elapsed}                    │
│                                         │
│  请加油～                               │
└─────────────────────────────────────────┘
""",
    "timeout_escalation": """
┌─────────────────────────────────────────┐
│  **超时升级汇报** 🔴                     │
│                                         │
│  Agent：{agent}                         │
│  任务：{task}                           │
│  超时：{elapsed} / {threshold}          │
│                                         │
│  请主人指示下一步行动！                  │
└─────────────────────────────────────────┘
"""
}
```

---

## 📊 预期效果

### 当前状态（需要催促）

```
T+0h: 主人："望舒，分析竞品"
T+2h: 望舒完成
T+2h: ❌ 等待主人催促灵犀
T+3h: 主人："灵犀，提供创意"
T+5h: 灵犀完成
T+5h: ❌ 等待主人催促惊鸿
T+6h: 主人："惊鸿，开始创作"
```

**主人操作**：3 次催促

---

### 实施后状态（自动执行）

```
T+0h: 主人："启动小说创作工作流"
T+0h: ✅ 自动触发望舒
T+2h: 望舒完成
T+2h: ✅ 自动触发灵犀
T+4h: 灵犀完成
T+4h: ✅ 自动触发惊鸿
T+8h: 惊鸿完成
T+8h: ✅ 自动触发鉴微
T+9h: 鉴微完成
T+9h: ✅ 自动汇报主人
```

**主人操作**：1 次启动（之后全自动）

---

## 🎯 实施优先级

| 功能 | 优先级 | 预计时间 |
|------|--------|---------|
| 自动触发器 | 🔴 P0 | 1 小时 |
| 进度监控 | 🔴 P0 | 1 小时 |
| 超时催促 | 🟡 P1 | 30 分钟 |
| 卡片模板 | 🟡 P1 | 30 分钟 |
| 工作流引擎 | 🟢 P2 | 2 小时 |

---

## 🚀 立即行动

**年年请求主人确认**：

- [ ] **方案 A**：立即实施自动触发器（1 小时内完成）
- [ ] **方案 B**：先设计工作流引擎（2 小时后实施）
- [ ] **方案 C**：年年先创建原型，主人确认后再实施

**年年推荐方案 A**：立即实施自动触发器，1 小时内解决催促问题！

---

**创建者**：年年 🎀  
**创建时间**：2026-04-08 15:10  
**状态**：🔴 待主人确认实施
