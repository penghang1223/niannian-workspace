# 工作流引擎（Workflow Engine）

> 创建时间：2026-04-08 15:45  
> 版本：v1.0  
> 用途：多 Agent 协作工作流引擎  
> 状态：🔴 实施中

---

## 🎯 核心类

### Workflow 类

```python
class Workflow:
    """工作流基类"""
    
    def __init__(self, name, steps, acceptance_criteria=None):
        self.name = name
        self.steps = steps  # List[Step]
        self.acceptance_criteria = acceptance_criteria or []
        self.current_step_index = 0
        self.status = "pending"  # pending/running/completed/failed
    
    def get_current_step(self):
        """获取当前步骤"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def next_step(self):
        """进入下一步"""
        self.current_step_index += 1
        return self.get_current_step()
    
    def is_complete(self):
        """是否完成"""
        return self.current_step_index >= len(self.steps)
```

---

### Step 类

```python
class Step:
    """工作流步骤"""
    
    def __init__(self, agent, task, timeout, next_step=None, skill=None, output=None):
        self.agent = agent  # Agent ID
        self.task = task  # 任务描述
        self.timeout = timeout  # 超时时间（秒）
        self.next = next_step  # 下一步标识
        self.skill = skill  # 调用的 Skill
        self.output = output  # 输出（完成时设置）
        self.status = "pending"  # pending/running/completed/failed
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始步骤"""
        self.status = "running"
        self.start_time = time.now()
    
    def complete(self, output):
        """完成步骤"""
        self.status = "completed"
        self.end_time = time.now()
        self.output = output
    
    def fail(self, error):
        """失败"""
        self.status = "failed"
        self.end_time = time.now()
        self.error = error
    
    def elapsed_time(self):
        """已用时间"""
        if self.start_time:
            return time.now() - self.start_time
        return 0
    
    def remaining_time(self):
        """剩余时间"""
        return self.timeout - self.elapsed_time()
```

---

### DecisionNode 类

```python
class DecisionNode:
    """决策节点"""
    
    def __init__(self, conditions, branches):
        self.conditions = conditions  # {"pass": "P0 问题=0", "fail": "P0 问题>0"}
        self.branches = branches  # {"pass": "next_agent", "fail": "revision_agent"}
        self.result = None
    
    def evaluate(self, output):
        """评估决策"""
        # 检查 P0 问题数量
        p0_count = output.get("p0_issues", 0)
        
        if p0_count == 0:
            self.result = "pass"
            return self.branches["pass"]
        else:
            self.result = "fail"
            return self.branches["fail"]
```

---

### LoopWorkflow 类

```python
class LoopWorkflow(Workflow):
    """循环工作流"""
    
    def __init__(self, name, steps, iterations, loop_condition, acceptance_criteria=None):
        super().__init__(name, steps, acceptance_criteria)
        self.iterations = iterations  # 循环次数
        self.loop_condition = loop_condition  # 循环条件
        self.current_iteration = 1
    
    def next_iteration(self):
        """进入下一次循环"""
        self.current_iteration += 1
        self.current_step_index = 0
        
        # 检查循环条件
        return eval(self.loop_condition)
    
    def is_complete(self):
        """是否完成"""
        return self.current_iteration > self.iterations
```

---

### WorkflowEngine 类

```python
class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.active_instance = None
        self.progress_tracker = ProgressTracker()
        self.workflows = {}
    
    def register_workflow(self, name, workflow):
        """注册工作流"""
        self.workflows[name] = workflow
    
    def start_workflow(self, workflow_name, project_id, context=None):
        """启动工作流"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = copy.deepcopy(self.workflows[workflow_name])
        
        self.active_instance = WorkflowInstance(
            project_id=project_id,
            workflow=workflow,
            context=context or {}
        )
        
        # 执行第 1 步
        return self.execute_current_step()
    
    def execute_current_step(self):
        """执行当前步骤"""
        instance = self.active_instance
        step = instance.workflow.get_current_step()
        
        if not step:
            return self.on_workflow_complete()
        
        # 检查是否是决策节点
        if isinstance(step, DecisionNode):
            return self.handle_decision_node(step)
        
        # 通知 Agent 开始
        message = f"[工作流] {instance.workflow.name} - 开始执行：{step.task}"
        sessions_send(
            sessionKey=f"agent:{step.agent}:main",
            message=message
        )
        
        # 注册进度追踪
        self.progress_tracker.register_start(
            project_id=instance.project_id,
            agent=step.agent,
            task=step.task,
            timeout=step.timeout
        )
        
        # 更新状态
        step.start()
        instance.workflow.status = "running"
        
        return {"status": "started", "agent": step.agent, "task": step.task}
    
    def on_step_complete(self, agent, output):
        """步骤完成回调"""
        instance = self.active_instance
        step = instance.workflow.get_current_step()
        
        # 验证步骤
        if step.agent != agent:
            return {"error": f"Unexpected agent: {agent}"}
        
        # 完成步骤
        step.complete(output)
        
        # 验证验收标准
        if not self.verify_acceptance_criteria(step, output):
            return self.handle_failure(step, output)
        
        # 获取下一步
        next_step_key = step.next
        
        if next_step_key == "decision_node":
            # 决策节点
            instance.workflow.next_step()
            return self.handle_decision_node(instance.workflow.get_current_step(), output)
        
        elif next_step_key == "next_iteration":
            # 循环到下一次
            if instance.workflow.next_iteration():
                instance.workflow.next_step()
                return self.execute_current_step()
            else:
                return self.on_workflow_complete()
        
        elif next_step_key is None:
            # 等待主人确认
            return self.report_to_owner()
        
        else:
            # 执行下一步
            instance.workflow.next_step()
            return self.execute_current_step()
    
    def handle_decision_node(self, decision_node, output=None):
        """处理决策节点"""
        branch = decision_node.evaluate(output or {})
        
        # 找到分支对应的步骤索引
        next_index = self.find_step_by_key(branch)
        
        if next_index is not None:
            self.active_instance.workflow.current_step_index = next_index
            return self.execute_current_step()
        else:
            return {"error": f"Decision branch '{branch}' not found"}
    
    def find_step_by_key(self, key):
        """根据 key 查找步骤索引"""
        for i, step in enumerate(self.active_instance.workflow.steps):
            if hasattr(step, 'key') and step.key == key:
                return i
        return None
    
    def verify_acceptance_criteria(self, step, output):
        """验证验收标准"""
        if not self.active_instance.workflow.acceptance_criteria:
            return True
        
        # TODO: 实现验收标准验证
        return True
    
    def handle_failure(self, step, output):
        """处理失败"""
        step.fail("Acceptance criteria not met")
        
        # TODO: 实现失败处理（重试/回滚/升级）
        return {"status": "failed", "step": step.task, "reason": "验收标准未通过"}
    
    def report_to_owner(self):
        """汇报主人"""
        instance = self.active_instance
        
        send_card(
            template="workflow_checkpoint",
            workflow_name=instance.workflow.name,
            progress=f"{instance.workflow.current_step_index}/{len(instance.workflow.steps)}",
            status="waiting_confirmation"
        )
        
        return {"status": "waiting_confirmation"}
    
    def on_workflow_complete(self):
        """工作流完成"""
        instance = self.active_instance
        instance.workflow.status = "completed"
        
        send_card(
            template="workflow_completion",
            workflow_name=instance.workflow.name,
            project_id=instance.project_id
        )
        
        return {"status": "completed"}
```

---

### WorkflowInstance 类

```python
class WorkflowInstance:
    """工作流实例"""
    
    def __init__(self, project_id, workflow, context=None):
        self.project_id = project_id
        self.workflow = workflow
        self.context = context or {}
        self.start_time = time.now()
        self.end_time = None
        self.step_history = []
    
    def record_step(self, step, output):
        """记录步骤历史"""
        self.step_history.append({
            "step": step.task,
            "agent": step.agent,
            "output": output,
            "start_time": step.start_time,
            "end_time": step.end_time
        })
```

---

### ProgressTracker 类

```python
class ProgressTracker:
    """进度追踪器（集成自动触发 + 超时监控）"""
    
    def __init__(self):
        self.projects = {}
    
    def register_start(self, project_id, agent, task, timeout):
        """注册任务开始"""
        if project_id not in self.projects:
            self.projects[project_id] = {"agent_status": {}}
        
        self.projects[project_id]["agent_status"][agent] = {
            "task": task,
            "status": "running",
            "start_time": time.now(),
            "timeout": timeout
        }
        
        # 启动超时监控
        asyncio.create_task(self.monitor_timeout(project_id, agent))
    
    def register_complete(self, project_id, agent, output):
        """注册任务完成"""
        if project_id in self.projects:
            self.projects[project_id]["agent_status"][agent] = {
                "status": "completed",
                "output": output,
                "end_time": time.now()
            }
            
            # 自动触发下一环节
            self.trigger_next(project_id, agent)
    
    async def monitor_timeout(self, project_id, agent):
        """超时监控"""
        status = self.projects[project_id]["agent_status"][agent]
        
        while status["status"] == "running":
            await asyncio.sleep(60)
            
            elapsed = time.now() - status["start_time"]
            timeout = status["timeout"]
            
            if elapsed >= timeout * 0.5 and elapsed < timeout * 0.8:
                self.send_reminder(agent, elapsed, timeout)
            elif elapsed >= timeout * 0.8 and elapsed < timeout:
                self.send_urge(agent, elapsed, timeout)
            elif elapsed >= timeout:
                self.escalate(project_id, agent, elapsed, timeout)
                break
    
    def send_reminder(self, agent, elapsed, timeout):
        """发送提醒"""
        sessions_send(
            sessionKey=f"agent:{agent}:main",
            message=f"[进度提醒] 任务已进行 {elapsed:.0f}/{timeout:.0f} 秒（50%），请加油～"
        )
    
    def send_urge(self, agent, elapsed, timeout):
        """发送催促"""
        sessions_send(
            sessionKey=f"agent:{agent}:main",
            message=f"[催促] 任务即将超时！{elapsed:.0f}/{timeout:.0f} 秒（80%），请加快进度！"
        )
    
    def escalate(self, project_id, agent, elapsed, timeout):
        """超时升级汇报"""
        send_card(
            template="timeout_escalation",
            agent=agent,
            elapsed_time=f"{elapsed:.0f}秒",
            threshold=f"{timeout:.0f}秒"
        )
    
    def trigger_next(self, project_id, agent):
        """自动触发下一环节"""
        # TODO: 根据工作流定义获取下一环节 Agent
        pass
```

---

## 📋 工作流定义

### Wave-1：选题定方向

```python
def create_wave_1():
    return Workflow(
        name="选题定方向",
        steps=[
            Step("望舒", "分析题材数据", timeout=1800, next="灵犀"),
            Step("灵犀", "提供创意脑洞", timeout=1800, next="灵犀_vote"),
            Step("灵犀", "虚拟读者投票", timeout=1800, next="年年"),
            Step("年年", "汇总汇报", timeout=600, next=None)
        ],
        acceptance_criteria=[
            "PRD 包含题材数据 + 竞品分析",
            "创意框架包含 3 个创意方案",
            "虚拟读者投票≥30 个样本"
        ]
    )
```

### Wave-2：大纲 + 人设

```python
def create_wave_2():
    return Workflow(
        name="大纲 + 人设",
        steps=[
            Step("惊鸿", "生成大纲 + 角色卡", timeout=3600, next="鉴微"),
            Step("鉴微", "审查", timeout=1800, next="decision_node"),
            DecisionNode(
                conditions={"pass": "P0 问题=0", "fail": "P0 问题>0"},
                branches={"pass": "年年", "fail": "惊鸿_revision"}
            ),
            Step("惊鸿_revision", "按意见修改", timeout=1800, next="鉴微_re_review"),
            Step("鉴微_re_review", "重新审查", timeout=1800, next="decision_node"),
            Step("年年", "汇报主人", timeout=600, next=None)
        ],
        acceptance_criteria=[
            "大纲包含三幕式结构（12 章）",
            "角色卡包含主角 + 配角（≥5 人）",
            "虚拟读者评分≥85 分",
            "鉴微审查通过（P0 问题=0）"
        ]
    )
```

### Wave-3：章节创作（循环 12 次）

```python
def create_wave_3():
    return LoopWorkflow(
        name="章节创作",
        steps=[
            Step("惊鸿", "创作第{iteration}章", timeout=7200, next="鉴微"),
            Step("鉴微", "审查", timeout=3600, next="decision_node"),
            DecisionNode(
                conditions={"pass": "P0 问题=0", "fail": "P0 问题>0"},
                branches={"pass": "年年", "fail": "惊鸿_revision"}
            ),
            Step("惊鸿_revision", "按 P0 意见修改", timeout=3600, next="鉴微_re_review"),
            Step("鉴微_re_review", "重新审查", timeout=1800, next="decision_node"),
            Step("年年", "第{iteration}章完成汇报", timeout=600, next="next_iteration")
        ],
        iterations=12,
        loop_condition="current_iteration <= iterations",
        acceptance_criteria=[
            "章节字数 3000-4000 字",
            "虚拟读者评分≥85 分",
            "鉴微审查通过（P0 问题=0）",
            "付费意愿≥80%"
        ]
    )
```

---

## 🚀 使用方法

### 启动工作流

```python
# 创建工作流引擎
engine = WorkflowEngine()

# 注册工作流
engine.register_workflow("wave_1", create_wave_1())
engine.register_workflow("wave_2", create_wave_2())
engine.register_workflow("wave_3", create_wave_3())

# 启动工作流
result = engine.start_workflow(
    workflow_name="wave_1",
    project_id="novel_001",
    context={"novel_name": "我在修仙界开网约车"}
)

# 输出：
# {
#   "status": "started",
#   "agent": "望舒",
#   "task": "分析题材数据"
# }
```

### 步骤完成回调

```python
# 当 Agent 完成任务时调用
result = engine.on_step_complete(
    agent="望舒",
    output={
        "prd": "PRD-我在修仙界开网约车-v1.0",
        "competitor_analysis": {...}
    }
)

# 输出：
# {
#   "status": "started",
#   "agent": "灵犀",
#   "task": "提供创意脑洞"
# }
# 自动触发下一环节！
```

---

## 📊 预期效果

### 当前状态（需要催促）

```
T+0h: 主人："启动小说创作"
T+0h: 年年私信望舒
T+2h: 望舒完成
T+2h: ❌ 等待主人催促灵犀
T+3h: 主人："灵犀，提供创意"
...
主人操作：10+ 次催促
```

---

### 工作流实施后（自动执行）

```
T+0h: 主人："启动小说创作工作流"
T+0h: ✅ 自动执行 Wave-1 Step-1（望舒）
T+2h: 望舒完成
T+2h: ✅ 自动触发 Step-2（灵犀）
T+4h: 灵犀完成
T+4h: ✅ 自动触发 Step-3（年年汇报）
T+4h: 主人确认
T+4h: ✅ 自动执行 Wave-2
...
主人操作：1 次启动 + 3 次确认
```

---

**创建者**：年年 🎀  
**创建时间**：2026-04-08 15:45  
**版本**：v1.0  
**状态**：🔴 实施中
