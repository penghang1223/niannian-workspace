#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流引擎（Workflow Engine）
版本：v1.0
创建时间：2026-04-08
用途：多 Agent 协作工作流引擎
"""

import time
import asyncio
import copy
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_CONFIRMATION = "waiting_confirmation"


@dataclass
class Step:
    """工作流步骤"""
    agent: str
    task: str
    timeout: int  # 秒
    next: Optional[str] = None
    skill: Optional[str] = None
    key: Optional[str] = None  # 步骤标识（用于决策节点分支）
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    output: Any = None
    error: Optional[str] = None
    
    def start(self):
        """开始步骤"""
        self.status = StepStatus.RUNNING
        self.start_time = time.time()
    
    def complete(self, output):
        """完成步骤"""
        self.status = StepStatus.COMPLETED
        self.end_time = time.time()
        self.output = output
    
    def fail(self, error):
        """失败"""
        self.status = StepStatus.FAILED
        self.end_time = time.time()
        self.error = error
    
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        if self.start_time:
            return time.time() - self.start_time
        return 0
    
    def remaining_time(self) -> float:
        """剩余时间（秒）"""
        return self.timeout - self.elapsed_time()


@dataclass
class DecisionNode:
    """决策节点"""
    conditions: Dict[str, str]
    branches: Dict[str, str]
    result: Optional[str] = None
    
    def evaluate(self, output: Dict) -> str:
        """评估决策"""
        # 检查 P0 问题数量
        p0_count = output.get("p0_issues", 0)
        
        if p0_count == 0:
            self.result = "pass"
            return self.branches.get("pass", "next")
        else:
            self.result = "fail"
            return self.branches.get("fail", "revision")


@dataclass
class Workflow:
    """工作流基类"""
    name: str
    steps: List[Any]  # List[Step | DecisionNode]
    acceptance_criteria: List[str] = field(default_factory=list)
    current_step_index: int = 0
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    def get_current_step(self) -> Optional[Any]:
        """获取当前步骤"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def next_step(self) -> Optional[Any]:
        """进入下一步"""
        self.current_step_index += 1
        return self.get_current_step()
    
    def is_complete(self) -> bool:
        """是否完成"""
        return self.current_step_index >= len(self.steps)


@dataclass
class LoopWorkflow(Workflow):
    """循环工作流"""
    iterations: int = 1
    loop_condition: str = "current_iteration <= iterations"
    current_iteration: int = 1
    
    def next_iteration(self) -> bool:
        """进入下一次循环"""
        self.current_iteration += 1
        self.current_step_index = 0
        
        # 检查循环条件
        return self.current_iteration <= self.iterations
    
    def is_complete(self) -> bool:
        """是否完成"""
        return self.current_iteration > self.iterations


@dataclass
class WorkflowInstance:
    """工作流实例"""
    project_id: str
    workflow: Workflow
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    step_history: List[Dict] = field(default_factory=list)
    
    def record_step(self, step: Step, output: Any):
        """记录步骤历史"""
        self.step_history.append({
            "step": step.task,
            "agent": step.agent,
            "output": output,
            "start_time": step.start_time,
            "end_time": step.end_time
        })


class ProgressTracker:
    """进度追踪器（集成自动触发 + 超时监控）"""
    
    def __init__(self):
        self.projects: Dict[str, Dict] = {}
    
    def register_start(self, project_id: str, agent: str, task: str, timeout: int):
        """注册任务开始"""
        if project_id not in self.projects:
            self.projects[project_id] = {"agent_status": {}}
        
        self.projects[project_id]["agent_status"][agent] = {
            "task": task,
            "status": "running",
            "start_time": time.time(),
            "timeout": timeout
        }
        
        # 启动超时监控（如果有事件循环）
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.monitor_timeout(project_id, agent))
        except RuntimeError:
            # 没有运行的事件循环，跳过异步监控
            pass
    
    def register_complete(self, project_id: str, agent: str, output: Any):
        """注册任务完成"""
        if project_id in self.projects:
            self.projects[project_id]["agent_status"][agent] = {
                "status": "completed",
                "output": output,
                "end_time": time.time()
            }
    
    async def monitor_timeout(self, project_id: str, agent: str):
        """超时监控"""
        status = self.projects[project_id]["agent_status"][agent]
        
        while status["status"] == "running":
            await asyncio.sleep(60)
            
            elapsed = time.time() - status["start_time"]
            timeout = status["timeout"]
            
            if elapsed >= timeout * 0.5 and elapsed < timeout * 0.8:
                self.send_reminder(agent, elapsed, timeout)
            elif elapsed >= timeout * 0.8 and elapsed < timeout:
                self.send_urge(agent, elapsed, timeout)
            elif elapsed >= timeout:
                self.escalate(project_id, agent, elapsed, timeout)
                break
    
    def __init__(self, send_message_callback=None, send_card_callback=None):
        self.projects: Dict[str, Dict] = {}
        self.send_message_callback = send_message_callback
        self.send_card_callback = send_card_callback
    
    def send_reminder(self, agent: str, elapsed: float, timeout: float):
        """发送提醒"""
        percent = int(elapsed / timeout * 100)
        message = f"[进度提醒] 任务已进行 {elapsed:.0f}/{timeout:.0f} 秒（{percent}%），请加油～"
        
        if self.send_message_callback:
            self.send_message_callback(f"agent:{agent}:main", message)
        else:
            print(f"⏰ 提醒 {agent}: {message}")
    
    def send_urge(self, agent: str, elapsed: float, timeout: float):
        """发送催促"""
        percent = int(elapsed / timeout * 100)
        message = f"[催促] 任务即将超时！{elapsed:.0f}/{timeout:.0f} 秒（{percent}%），请加快进度！"
        
        if self.send_message_callback:
            self.send_message_callback(f"agent:{agent}:main", message)
        else:
            print(f"⚠️ 催促 {agent}: {message}")
    
    def escalate(self, project_id: str, agent: str, elapsed: float, timeout: float):
        """超时升级汇报"""
        message = f"🔴 **超时升级汇报**\n\nAgent：{agent}\n超时：{elapsed:.0f}/{timeout:.0f} 秒\n请主人指示下一步行动！"
        
        if self.send_card_callback:
            self.send_card_callback(message)
        else:
            print(f"🔴 升级汇报：{message}")


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.active_instance: Optional[WorkflowInstance] = None
        self.progress_tracker = ProgressTracker()
        self.workflows: Dict[str, Workflow] = {}
    
    def register_workflow(self, name: str, workflow: Workflow):
        """注册工作流"""
        self.workflows[name] = workflow
    
    def start_workflow(self, workflow_name: str, project_id: str, context: Dict = None) -> Dict:
        """启动工作流"""
        if workflow_name not in self.workflows:
            return {"error": f"Workflow '{workflow_name}' not found"}
        
        workflow = copy.deepcopy(self.workflows[workflow_name])
        
        self.active_instance = WorkflowInstance(
            project_id=project_id,
            workflow=workflow,
            context=context or {}
        )
        
        # 执行第 1 步
        return self.execute_current_step()
    
    def execute_current_step(self) -> Dict:
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
        
        # 使用回调函数发送消息（避免硬编码依赖）
        if hasattr(self, 'send_message_callback'):
            self.send_message_callback(f"agent:{step.agent}:main", message)
        else:
            # 如果没有回调，打印消息（测试模式）
            print(f"📤 发送消息给 {step.agent}: {message}")
        
        # 注册进度追踪
        self.progress_tracker.register_start(
            project_id=instance.project_id,
            agent=step.agent,
            task=step.task,
            timeout=step.timeout
        )
        
        # 更新状态
        step.start()
        instance.workflow.status = WorkflowStatus.RUNNING
        
        return {"status": "started", "agent": step.agent, "task": step.task}
    
    def on_step_complete(self, agent: str, output: Dict) -> Dict:
        """步骤完成回调"""
        instance = self.active_instance
        step = instance.workflow.get_current_step()
        
        # 检查是否是决策节点（决策节点没有 agent 属性）
        if isinstance(step, DecisionNode):
            return self.handle_decision_node(step, output)
        
        # 验证步骤
        if step.agent != agent:
            return {"error": f"Unexpected agent: {agent}"}
        
        # 完成步骤
        step.complete(output)
        instance.record_step(step, output)
        
        # 验证验收标准
        if not self.verify_acceptance_criteria(step, output):
            return self.handle_failure(step, output)
        
        # 获取下一步
        next_step_key = step.next
        
        # 进入下一步
        instance.workflow.next_step()
        next_step = instance.workflow.get_current_step()
        
        # 检查下一步是否是决策节点
        if isinstance(next_step, DecisionNode):
            return self.handle_decision_node(next_step, output)
        
        elif next_step_key == "next_iteration":
            # 循环到下一次
            if isinstance(instance.workflow, LoopWorkflow):
                if instance.workflow.next_iteration():
                    return self.execute_current_step()
                else:
                    return self.on_workflow_complete()
            else:
                return {"error": "Not a LoopWorkflow"}
        
        elif next_step_key is None:
            # 等待主人确认
            return self.report_to_owner()
        
        else:
            # 执行下一步
            return self.execute_current_step()
    
    def handle_decision_node(self, decision_node: DecisionNode, output: Dict = None) -> Dict:
        """处理决策节点"""
        branch = decision_node.evaluate(output or {})
        
        # 找到分支对应的步骤索引
        next_index = self.find_step_by_key(branch)
        
        if next_index is not None:
            self.active_instance.workflow.current_step_index = next_index
            return self.execute_current_step()
        else:
            return {"error": f"Decision branch '{branch}' not found"}
    
    def find_step_by_key(self, key: str) -> Optional[int]:
        """根据 key 查找步骤索引"""
        for i, step in enumerate(self.active_instance.workflow.steps):
            if hasattr(step, 'key') and step.key == key:
                return i
        return None
    
    def verify_acceptance_criteria(self, step: Step, output: Dict) -> bool:
        """验证验收标准"""
        if not self.active_instance.workflow.acceptance_criteria:
            return True
        
        # TODO: 实现验收标准验证
        return True
    
    def handle_failure(self, step: Step, output: Dict) -> Dict:
        """处理失败"""
        step.fail("Acceptance criteria not met")
        
        # TODO: 实现失败处理（重试/回滚/升级）
        return {"status": "failed", "step": step.task, "reason": "验收标准未通过"}
    
    def report_to_owner(self) -> Dict:
        """汇报主人"""
        instance = self.active_instance
        
        message = f"📋 **工作流节点确认**\n\n工作流：{instance.workflow.name}\n进度：{instance.workflow.current_step_index}/{len(instance.workflow.steps)}\n状态：等待主人确认"
        
        if hasattr(self, 'send_card_callback') and self.send_card_callback:
            self.send_card_callback(message)
        else:
            print(f"📋 汇报主人：{message}")
        
        instance.workflow.status = WorkflowStatus.WAITING_CONFIRMATION
        
        return {"status": "waiting_confirmation"}
    
    def on_workflow_complete(self) -> Dict:
        """工作流完成"""
        instance = self.active_instance
        instance.workflow.status = WorkflowStatus.COMPLETED
        instance.end_time = time.time()
        
        elapsed = instance.end_time - instance.start_time
        message = f"✅ **工作流完成**\n\n工作流：{instance.workflow.name}\n项目：{instance.project_id}\n耗时：{elapsed:.0f}秒"
        
        if hasattr(self, 'send_card_callback') and self.send_card_callback:
            self.send_card_callback(message)
        else:
            print(f"✅ {message}")
        
        return {"status": "completed"}


# ==================== 预定义工作流 ====================

def create_wave_1() -> Workflow:
    """第 1 阶段：选题定方向"""
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


def create_wave_2() -> Workflow:
    """第 2 阶段：大纲 + 人设"""
    return Workflow(
        name="大纲 + 人设",
        steps=[
            Step("惊鸿", "生成大纲 + 角色卡", timeout=3600, next="decision_node", key="惊鸿_outline"),
            Step("鉴微", "审查", timeout=1800, next="decision_node", key="鉴微_review"),
            DecisionNode(
                conditions={"pass": "P0 问题=0", "fail": "P0 问题>0"},
                branches={"pass": "年年_report", "fail": "惊鸿_revision"}
            ),
            Step("惊鸿_revision", "按意见修改", timeout=1800, next="鉴微_re_review", key="惊鸿_revision"),
            Step("鉴微_re_review", "重新审查", timeout=1800, next="decision_node", key="鉴微_re_review"),
            Step("年年", "汇报主人", timeout=600, next=None, key="年年_report")
        ],
        acceptance_criteria=[
            "大纲包含三幕式结构（12 章）",
            "角色卡包含主角 + 配角（≥5 人）",
            "虚拟读者评分≥85 分",
            "鉴微审查通过（P0 问题=0）"
        ]
    )


def create_wave_3() -> LoopWorkflow:
    """第 3 阶段：章节创作（循环 12 次）"""
    return LoopWorkflow(
        name="章节创作",
        steps=[
            Step("惊鸿", "创作第{iteration}章", timeout=7200, next="decision_node", key="惊鸿_chapter"),
            Step("鉴微", "审查", timeout=3600, next="decision_node", key="鉴微_review"),
            DecisionNode(
                conditions={"pass": "P0 问题=0", "fail": "P0 问题>0"},
                branches={"pass": "年年_report", "fail": "惊鸿_revision"}
            ),
            Step("惊鸿_revision", "按 P0 意见修改", timeout=3600, next="鉴微_re_review", key="惊鸿_revision"),
            Step("鉴微_re_review", "重新审查", timeout=1800, next="decision_node", key="鉴微_re_review"),
            Step("年年", "第{iteration}章完成汇报", timeout=600, next="next_iteration", key="年年_report")
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


# ==================== 使用示例 ====================

if __name__ == "__main__":
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
    
    print(f"启动结果：{result}")
