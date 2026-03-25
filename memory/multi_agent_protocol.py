#!/usr/bin/env python3
"""
多 Agent 通信协议实现

基于 hello-agents Ch10 + 囡囡扩展设计
支持：项目经理、开发工程师、测试工程师、囡囡 四个 Agent 协同

创建：2026-03-02 22:45
作者：囡囡 🎀
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

# 导入知识库（如果可用）
try:
    from knowledge_base import KnowledgeBase
except ImportError:
    KnowledgeBase = None  # 降级处理


# ==================== 枚举定义 ====================

class MessageType(str, Enum):
    """消息类型枚举"""
    
    # 任务相关
    TASK_ASSIGN = "task_assign"       # 分配任务
    TASK_SUBMIT = "task_submit"       # 提交任务
    TASK_UPDATE = "task_update"       # 更新进度
    TASK_CANCEL = "task_cancel"       # 取消任务
    
    # 协同相关
    REQUEST_HELP = "request_help"     # 请求帮助
    OFFER_HELP = "offer_help"         # 提供帮助
    SHARE_INFO = "share_info"         # 共享信息
    
    # 质量相关
    QUALITY_CHECK = "quality_check"   # 质量检查
    QUALITY_REPORT = "quality_report" # 质量报告
    
    # 囡囡专属
    INTENT_PREDICTION = "intent_prediction"  # 意图预测
    MEMORY_UPDATE = "memory_update"          # 记忆更新
    
    # 管理相关
    STATUS_REPORT = "status_report"   # 状态汇报
    HEARTBEAT = "heartbeat"           # 心跳


class MessageStatus(str, Enum):
    """消息状态枚举"""
    PENDING = "pending"       # 待发送
    SENT = "sent"            # 已发送
    DELIVERED = "delivered"  # 已送达
    READ = "read"            # 已读
    REPLIED = "replied"      # 已回复
    FAILED = "failed"        # 失败


class AgentRole(str, Enum):
    """Agent 角色枚举"""
    PROJECT_MANAGER = "project_manager"  # 项目经理
    DEVELOPER = "developer"              # 开发工程师
    TESTER = "tester"                    # 测试工程师
    NANNAN = "nannan"                    # 囡囡


# ==================== 数据类定义 ====================

@dataclass
class AgentMessage:
    """Agent 通信消息格式"""
    
    # 消息元数据
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""           # 会话 ID (追踪完整流程)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 发送者和接收者
    sender: str = ""                    # 发送者
    receiver: str = ""                  # 接收者
    receiver_type: str = "agent"        # 接收者类型 (agent/human)
    
    # 消息类型
    message_type: str = ""              # 消息类型
    priority: int = 3                   # 优先级 (1-5, 5 最高)
    
    # 消息内容
    content: Dict[str, Any] = field(default_factory=dict)
    
    # 状态追踪
    status: str = "pending"             # 状态
    parent_message_id: Optional[str] = None  # 父消息 ID (如果是回复)
    
    # 扩展字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentMessage':
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """从 JSON 字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class TaskContent:
    """任务内容格式"""
    
    task_id: str = ""
    task_name: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    deadline: str = ""
    estimated_hours: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TaskSubmitContent:
    """任务提交内容格式"""
    
    task_id: str = ""
    status: str = ""  # completed/failed/partial
    deliverables: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class QualityReportContent:
    """质量报告内容格式"""
    
    task_id: str = ""
    evaluator: str = ""
    dimensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_score: float = 0.0
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IntentPredictionContent:
    """意图预测内容格式"""
    
    original_request: str = ""
    predicted_intents: List[Dict[str, Any]] = field(default_factory=list)
    suggested_workflow: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ==================== 消息队列 ====================

class MessageQueue:
    """Agent 消息队列（内存版）"""
    
    def __init__(self):
        self.queues: Dict[str, List[AgentMessage]] = {
            AgentRole.PROJECT_MANAGER.value: [],
            AgentRole.DEVELOPER.value: [],
            AgentRole.TESTER.value: [],
            AgentRole.NANNAN.value: []
        }
        self.message_history: List[AgentMessage] = []  # 历史记录
    
    def send(self, message: AgentMessage) -> bool:
        """发送消息到接收者队列"""
        try:
            receiver = message.receiver
            if receiver not in self.queues:
                print(f"⚠️  未知接收者：{receiver}")
                return False
            
            message.status = MessageStatus.SENT.value
            self.queues[receiver].append(message)
            self.message_history.append(message)
            print(f"✅ 消息已发送：{message.message_id[:8]}... → {receiver}")
            return True
        except Exception as e:
            print(f"❌ 发送失败：{e}")
            return False
    
    def receive(self, agent_id: str, mark_as_read: bool = True) -> List[AgentMessage]:
        """接收者获取消息"""
        try:
            if agent_id not in self.queues:
                return []
            
            messages = self.queues[agent_id]
            if mark_as_read:
                for msg in messages:
                    msg.status = MessageStatus.READ.value
                self.queues[agent_id] = []  # 清空队列
            
            print(f"📥 {agent_id} 收到 {len(messages)} 条消息")
            return messages
        except Exception as e:
            print(f"❌ 接收失败：{e}")
            return []
    
    def status(self, agent_id: str) -> Dict:
        """获取队列状态"""
        return {
            "pending_messages": len(self.queues.get(agent_id, [])),
            "agent_id": agent_id,
            "total_history": len(self.message_history)
        }
    
    def get_conversation(self, conversation_id: str) -> List[AgentMessage]:
        """获取完整会话历史"""
        return [
            msg for msg in self.message_history
            if msg.conversation_id == conversation_id
        ]


# ==================== 项目经理 Agent ====================

class ProjectManagerAgent:
    """项目经理 Agent (协调器)"""
    
    def __init__(self, message_queue: MessageQueue, knowledge_base: KnowledgeBase = None):
        self.message_queue = message_queue
        self.active_conversations: Dict[str, Dict] = {}
        self.role = AgentRole.PROJECT_MANAGER.value
        self.knowledge_base = knowledge_base  # 知识库引用
    
    def receive_human_request(self, request: str, human_id: str = "owner") -> str:
        """接收主人请求"""
        print(f"\n👤 主人请求：{request}")
        
        # 先在知识库中搜索相关知识
        if self.knowledge_base:
            print(f"  🔍 从知识库检索相关知识...")
            results = self.knowledge_base.search(request, limit=3)
            if results:
                print(f"  ✅ 找到 {len(results)} 条相关知识")
                for r in results:
                    print(f"     - {r.topic} ({r.category})")
        
        # 创建会话
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_conversations[conversation_id] = {
            "request": request,
            "human_id": human_id,
            "start_time": datetime.now().isoformat(),
            "tasks": [],
            "status": "analyzing",
            "related_knowledge": [r.id for r in results] if self.knowledge_base else []
        }
        
        # 发送意图预测请求给囡囡
        prediction_msg = AgentMessage(
            conversation_id=conversation_id,
            sender=self.role,
            receiver=AgentRole.NANNAN.value,
            message_type=MessageType.INTENT_PREDICTION.value,
            priority=5,
            content={"original_request": request},
            metadata={"human_id": human_id}
        )
        self.message_queue.send(prediction_msg)
        
        return conversation_id
    
    def assign_tasks(self, conversation_id: str, tasks: List[Dict]) -> None:
        """分配任务"""
        if conversation_id not in self.active_conversations:
            print(f"❌ 会话不存在：{conversation_id}")
            return
        
        print(f"\n📋 分配 {len(tasks)} 个任务...")
        
        for task in tasks:
            # 创建任务分配消息
            task_msg = AgentMessage(
                conversation_id=conversation_id,
                sender=self.role,
                receiver=task["receiver"],
                message_type=MessageType.TASK_ASSIGN.value,
                priority=task.get("priority", 3),
                content={
                    "task_id": task["task_id"],
                    "task_name": task["task_name"],
                    "description": task["description"],
                    "requirements": task.get("requirements", []),
                    "acceptance_criteria": task.get("acceptance_criteria", []),
                    "deadline": task.get("deadline", ""),
                    "estimated_hours": task.get("estimated_hours", 0)
                },
                metadata={
                    "project": task.get("project", "店小秘 ERP"),
                    "module": task.get("module", ""),
                    "tags": task.get("tags", [])
                }
            )
            
            self.message_queue.send(task_msg)
            self.active_conversations[conversation_id]["tasks"].append(task["task_id"])
        
        self.active_conversations[conversation_id]["status"] = "in_progress"
        print(f"✅ 任务分配完成，会话状态：in_progress")
    
    def collect_results(self, conversation_id: str) -> Dict:
        """收集结果"""
        print(f"\n📥 收集会话 {conversation_id} 的结果...")
        
        # 获取会话所有消息
        messages = self.message_queue.get_conversation(conversation_id)
        
        results = {
            "conversation_id": conversation_id,
            "task_submissions": [],
            "quality_reports": [],
            "status": "collecting"
        }
        
        for msg in messages:
            if msg.message_type == MessageType.TASK_SUBMIT.value:
                results["task_submissions"].append(msg.to_dict())
            elif msg.message_type == MessageType.QUALITY_REPORT.value:
                results["quality_reports"].append(msg.to_dict())
        
        results["status"] = "completed"
        results["total_tasks"] = len(results["task_submissions"])
        results["total_quality_checks"] = len(results["quality_reports"])
        
        print(f"✅ 收集完成：{results['total_tasks']} 个任务，{results['total_quality_checks']} 个质量报告")
        return results
    
    def integrate_results(self, results: Dict) -> str:
        """整合结果并生成回复"""
        print(f"\n🔧 整合结果...")
        
        # 简单整合（实际应该更复杂）
        summary = []
        summary.append(f"📊 任务完成总结")
        summary.append(f"=" * 40)
        summary.append(f"总任务数：{results.get('total_tasks', 0)}")
        summary.append(f"质量检查：{results.get('total_quality_checks', 0)}")
        
        for submission in results.get("task_submissions", []):
            content = submission.get("content", {})
            summary.append(f"\n✅ 任务：{content.get('task_name', 'Unknown')}")
            summary.append(f"   状态：{content.get('status', 'Unknown')}")
            summary.append(f"   说明：{content.get('notes', 'No notes')}")
        
        # 添加质量评分
        for report in results.get("quality_reports", []):
            content = report.get("content", {})
            summary.append(f"\n📈 质量评分：{content.get('overall_score', 0):.2f}")
            summary.append(f"   建议：{content.get('recommendation', 'No recommendation')}")
        
        summary_text = "\n".join(summary)
        print(f"✅ 结果整合完成")
        return summary_text


# ==================== 开发工程师 Agent ====================

class DeveloperAgent:
    """开发工程师 Agent"""
    
    def __init__(self, message_queue: MessageQueue, knowledge_base: KnowledgeBase = None):
        self.message_queue = message_queue
        self.role = AgentRole.DEVELOPER.value
        self.active_tasks: Dict[str, Dict] = {}
        self.knowledge_base = knowledge_base  # 知识库引用
    
    def process_tasks(self) -> None:
        """处理任务"""
        print(f"\n👨‍💻 {self.role} 开始处理任务...")
        
        # 获取消息
        messages = self.message_queue.receive(self.role)
        
        for msg in messages:
            if msg.message_type == MessageType.TASK_ASSIGN.value:
                self._handle_task_assign(msg)
    
    def _handle_task_assign(self, message: AgentMessage) -> None:
        """处理任务分配"""
        content = message.content
        task_id = content.get("task_id", "")
        
        print(f"  📝 接收任务：{content.get('task_name', 'Unknown')}")
        
        # 记录任务
        self.active_tasks[task_id] = {
            "message": message.to_dict(),
            "status": "in_progress",
            "start_time": datetime.now().isoformat()
        }
        
        # 模拟任务完成（实际应该执行真实工作）
        self._simulate_task_completion(task_id, message.conversation_id)
    
    def _simulate_task_completion(self, task_id: str, conversation_id: str) -> None:
        """模拟任务完成"""
        print(f"  💻 执行任务：{task_id}...")
        
        # 模拟工作
        import time
        time.sleep(0.5)  # 模拟 0.5 秒工作
        
        # 创建提交消息
        submit_msg = AgentMessage(
            conversation_id=conversation_id,
            sender=self.role,
            receiver=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.TASK_SUBMIT.value,
            priority=4,
            content={
                "task_id": task_id,
                "status": "completed",
                "deliverables": {
                    "code": {
                        "repository": "https://github.com/example/repo",
                        "branch": f"feature/{task_id}",
                        "files": ["src/main.py", "tests/test_main.py"]
                    },
                    "documentation": {
                        "api_docs": "docs/api.md",
                        "design_doc": "docs/design.md"
                    }
                },
                "test_results": {
                    "unit_tests": "85% coverage",
                    "integration_tests": "passed"
                },
                "notes": "任务已完成，代码已提交"
            },
            parent_message_id=self.active_tasks[task_id]["message"]["message_id"],
            metadata={
                "actual_hours": 0.5,
                "code_quality_score": 0.90,
                "complexity_score": 0.60
            }
        )
        
        self.message_queue.send(submit_msg)
        self.active_tasks[task_id]["status"] = "completed"
        print(f"  ✅ 任务完成：{task_id}")


# ==================== 测试工程师 Agent ====================

class TesterAgent:
    """测试工程师 Agent"""
    
    def __init__(self, message_queue: MessageQueue, knowledge_base: KnowledgeBase = None):
        self.message_queue = message_queue
        self.role = AgentRole.TESTER.value
        self.active_tasks: Dict[str, Dict] = {}
        self.knowledge_base = knowledge_base  # 知识库引用
    
    def process_tasks(self) -> None:
        """处理任务"""
        print(f"\n🧪 {self.role} 开始处理任务...")
        
        # 获取消息
        messages = self.message_queue.receive(self.role)
        
        for msg in messages:
            if msg.message_type == MessageType.TASK_ASSIGN.value:
                self._handle_task_assign(msg)
    
    def _handle_task_assign(self, message: AgentMessage) -> None:
        """处理任务分配"""
        content = message.content
        task_id = content.get("task_id", "")
        
        print(f"  📝 接收任务：{content.get('task_name', 'Unknown')}")
        
        # 记录任务
        self.active_tasks[task_id] = {
            "message": message.to_dict(),
            "status": "in_progress",
            "start_time": datetime.now().isoformat()
        }
        
        # 模拟任务完成
        self._simulate_task_completion(task_id, message.conversation_id)
    
    def _simulate_task_completion(self, task_id: str, conversation_id: str) -> None:
        """模拟任务完成"""
        print(f"  🔍 执行测试：{task_id}...")
        
        # 模拟工作
        import time
        time.sleep(0.5)  # 模拟 0.5 秒工作
        
        # 创建提交消息
        submit_msg = AgentMessage(
            conversation_id=conversation_id,
            sender=self.role,
            receiver=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.TASK_SUBMIT.value,
            priority=4,
            content={
                "task_id": task_id,
                "status": "completed",
                "deliverables": {
                    "test_report": {
                        "test_cases": 25,
                        "passed": 24,
                        "failed": 1,
                        "skipped": 0
                    },
                    "coverage_report": {
                        "line_coverage": "85%",
                        "branch_coverage": "78%"
                    }
                },
                "test_results": {
                    "functional_tests": "passed",
                    "security_scan": "passed",
                    "performance_tests": "passed"
                },
                "notes": "测试完成，发现 1 个非关键问题"
            },
            parent_message_id=self.active_tasks[task_id]["message"]["message_id"],
            metadata={
                "actual_hours": 0.5,
                "test_quality_score": 0.92,
                "bugs_found": 1
            }
        )
        
        self.message_queue.send(submit_msg)
        self.active_tasks[task_id]["status"] = "completed"
        print(f"  ✅ 测试完成：{task_id}")


# ==================== 囡囡 Agent ====================

class NannanAgent:
    """囡囡 Agent (智能助手) - 兼任知识管理员"""
    
    def __init__(self, message_queue: MessageQueue, knowledge_base: KnowledgeBase = None):
        self.message_queue = message_queue
        self.role = AgentRole.NANNAN.value
        self.memories: List[Dict] = []
        self.knowledge_base = knowledge_base  # 知识库
        
        # 自动分享新知识
        self.auto_share_enabled = True
    
    def process_requests(self) -> None:
        """处理请求"""
        print(f"\n🎀 {self.role} 开始处理请求...")
        
        # 获取消息
        messages = self.message_queue.receive(self.role)
        
        for msg in messages:
            if msg.message_type == MessageType.INTENT_PREDICTION.value:
                self._handle_intent_prediction(msg)
            elif msg.message_type == MessageType.QUALITY_CHECK.value:
                self._handle_quality_check(msg)
            elif msg.message_type == "knowledge_share":
                self._handle_knowledge_share(msg)
            elif msg.message_type == "knowledge_query":
                self._handle_knowledge_query(msg)
    
    def _handle_intent_prediction(self, message: AgentMessage) -> None:
        """处理意图预测请求"""
        content = message.content
        request = content.get("original_request", "")
        
        print(f"  💡 预测意图：{request[:50]}...")
        
        # 模拟意图预测（实际应该用 LLM）
        predicted_intents = [
            {
                "intent": "实现功能",
                "confidence": 0.95,
                "tasks": ["developer: 实现代码"]
            },
            {
                "intent": "需要测试",
                "confidence": 0.90,
                "tasks": ["tester: 生成测试用例"]
            },
            {
                "intent": "需要文档",
                "confidence": 0.88,
                "tasks": ["developer: 编写文档"]
            }
        ]
        
        suggested_workflow = [
            "1. 分配开发任务给 developer",
            "2. 同时分配测试任务给 tester",
            "3. 完成后进行质量评估",
            "4. 整合结果交付主人"
        ]
        
        # 创建预测消息
        prediction_msg = AgentMessage(
            conversation_id=message.conversation_id,
            sender=self.role,
            receiver=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.INTENT_PREDICTION.value,
            priority=3,
            content={
                "original_request": request,
                "predicted_intents": predicted_intents,
                "suggested_workflow": suggested_workflow
            },
            metadata={
                "prediction_model": "nannan_predictor_v2.1",
                "prediction_tokens": 850
            }
        )
        
        self.message_queue.send(prediction_msg)
        print(f"  ✅ 意图预测完成")
        
        # 生成任务分配建议
        self._suggest_task_assignment(message.conversation_id, request)
    
    def _suggest_task_assignment(self, conversation_id: str, request: str) -> None:
        """生成任务分配建议"""
        print(f"  📋 生成任务分配建议...")
        
        tasks = [
            {
                "task_id": "task_dev_001",
                "task_name": "实现功能代码",
                "receiver": AgentRole.DEVELOPER.value,
                "description": f"实现：{request}",
                "requirements": ["代码规范", "单元测试", "文档完整"],
                "priority": 4,
                "estimated_hours": 4
            },
            {
                "task_id": "task_test_001",
                "task_name": "生成测试用例",
                "receiver": AgentRole.TESTER.value,
                "description": f"为功能生成测试用例：{request}",
                "requirements": ["覆盖率>80%", "包含边界测试", "性能测试"],
                "priority": 4,
                "estimated_hours": 2
            }
        ]
        
        # 发送建议给项目经理
        suggestion_msg = AgentMessage(
            conversation_id=conversation_id,
            sender=self.role,
            receiver=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.SHARE_INFO.value,
            priority=3,
            content={
                "type": "task_assignment_suggestion",
                "tasks": tasks
            },
            metadata={
                "suggestion_source": "nannan_intent_prediction"
            }
        )
        
        self.message_queue.send(suggestion_msg)
        print(f"  ✅ 任务分配建议已发送")
    
    def _handle_quality_check(self, message: AgentMessage) -> None:
        """处理质量检查请求"""
        content = message.content
        task_id = content.get("task_id", "")
        
        print(f"  📊 质量检查：{task_id}...")
        
        # 模拟质量评估（实际应该用 evaluator）
        dimensions = {
            "task_completion": {
                "score": 0.95,
                "details": "所有需求已实现"
            },
            "response_time": {
                "score": 1.0,
                "details": "提前完成"
            },
            "code_quality": {
                "score": 0.90,
                "details": "代码规范，注释完整"
            },
            "test_coverage": {
                "score": 0.85,
                "details": "覆盖率 85%"
            },
            "cost_efficiency": {
                "score": 0.92,
                "details": "成本低于预期"
            }
        }
        
        overall_score = sum(d["score"] for d in dimensions.values()) / len(dimensions)
        
        # 创建质量报告
        report_msg = AgentMessage(
            conversation_id=message.conversation_id,
            sender=self.role,
            receiver=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.QUALITY_REPORT.value,
            priority=3,
            content={
                "task_id": task_id,
                "evaluator": "nannan_evaluator_v2.1",
                "dimensions": dimensions,
                "overall_score": overall_score,
                "recommendation": "可以交付" if overall_score > 0.85 else "需要改进"
            },
            metadata={
                "evaluation_model": "nannan_evaluator_v2.1",
                "evaluation_tokens": 1250
            }
        )
        
        self.message_queue.send(report_msg)
        print(f"  ✅ 质量报告完成，评分：{overall_score:.2f}")
    
    def _handle_knowledge_share(self, message: AgentMessage) -> None:
        """处理知识分享"""
        content = message.content
        topic = content.get("topic", "")
        summary = content.get("summary", "")
        file_path = content.get("file_path", "")
        
        print(f"  📚 分享知识：{topic}")
        
        # 添加到知识库
        if self.knowledge_base:
            knowledge_id = self.knowledge_base.add(
                topic=topic,
                content=summary,
                author=message.sender,
                category="通用",
                file_path=file_path,
                tags=content.get("tags", [])
            )
            
            # 自动分享给其他 Agent
            if self.auto_share_enabled:
                self.knowledge_base.share_to_all_agents(knowledge_id)
            
            print(f"  ✅ 知识已添加并分享：{knowledge_id}")
    
    def _handle_knowledge_query(self, message: AgentMessage) -> None:
        """处理知识查询"""
        content = message.content
        query = content.get("query", "")
        category = content.get("category", "")
        
        print(f"  🔍 查询知识：{query}")
        
        if self.knowledge_base:
            # 搜索知识
            results = self.knowledge_base.search(query, category=category, limit=5)
            
            if results:
                # 返回搜索结果
                response_content = {
                    "query": query,
                    "results": [
                        {
                            "id": item.id,
                            "topic": item.topic,
                            "category": item.category,
                            "summary": item.content[:200],
                            "file_path": item.file_path
                        }
                        for item in results
                    ],
                    "count": len(results)
                }
            else:
                response_content = {
                    "query": query,
                    "results": [],
                    "count": 0,
                    "message": "未找到相关知识"
                }
            
            # 发送回复
            response_msg = AgentMessage(
                conversation_id=message.conversation_id,
                sender=self.role,
                receiver=message.sender,
                message_type="knowledge_query_result",
                content=response_content,
                parent_message_id=message.message_id
            )
            self.message_queue.send(response_msg)
            print(f"  ✅ 查询完成，找到 {len(results)} 条结果")
        else:
            print(f"  ⚠️  知识库未初始化")
    
    def share_learning(self, topic: str, content: str, file_path: str = None, 
                       category: str = "通用", tags: List[str] = None):
        """囡囡主动分享学习成果"""
        if not self.knowledge_base:
            return
        
        print(f"\n🎀 囡囡主动分享知识：{topic}")
        
        # 添加到知识库
        knowledge_id = self.knowledge_base.add(
            topic=topic,
            content=content,
            author=self.role,
            category=category,
            file_path=file_path,
            tags=tags or []
        )
        
        # 分享给所有 Agent
        self.knowledge_base.share_to_all_agents(knowledge_id)
        
        # 发送通知消息
        for agent in [AgentRole.PROJECT_MANAGER.value, AgentRole.DEVELOPER.value, 
                      AgentRole.TESTER.value]:
            notify_msg = AgentMessage(
                sender=self.role,
                receiver=agent,
                message_type="knowledge_notification",
                content={
                    "type": "new_knowledge",
                    "knowledge_id": knowledge_id,
                    "topic": topic,
                    "category": category,
                    "summary": content[:100] + "..." if len(content) > 100 else content
                }
            )
            self.message_queue.send(notify_msg)
        
        print(f"  ✅ 知识已分享：{knowledge_id}")


# ==================== 主流程 ====================

async def run_multi_agent_demo():
    """运行多 Agent 协同演示"""
    
    print("=" * 60)
    print("🎯 多 Agent 协同演示")
    print("=" * 60)
    
    # 创建消息队列
    queue = MessageQueue()
    
    # 创建 Agent
    pm = ProjectManagerAgent(queue)
    dev = DeveloperAgent(queue)
    tester = TesterAgent(queue)
    nannan = NannanAgent(queue)
    
    print(f"\n✅ Agent 团队已就绪：")
    print(f"   - 项目经理 (协调器)")
    print(f"   - 开发工程师 (执行者)")
    print(f"   - 测试工程师 (执行者)")
    print(f"   - 囡囡 (智能助手)")
    
    # 模拟主人请求
    print("\n" + "=" * 60)
    conversation_id = pm.receive_human_request("帮我实现一个用户登录功能")
    print(f"📝 会话 ID: {conversation_id}")
    
    # 囡囡处理意图预测
    nannan.process_requests()
    
    # 项目经理根据囡囡的建议分配任务
    tasks = [
        {
            "task_id": "task_dev_001",
            "task_name": "实现用户登录 API",
            "receiver": AgentRole.DEVELOPER.value,
            "description": "实现支持邮箱/密码和 OAuth2.0 的登录功能",
            "requirements": [
                "支持邮箱/密码登录",
                "支持 OAuth2.0 (Google/GitHub)",
                "返回 JWT token",
                "实现速率限制"
            ],
            "acceptance_criteria": [
                "单元测试覆盖率 > 80%",
                "API 响应时间 < 200ms",
                "通过安全扫描"
            ],
            "deadline": "2026-03-03T12:00:00Z",
            "estimated_hours": 4,
            "priority": 4,
            "project": "店小秘 ERP",
            "module": "用户认证",
            "tags": ["backend", "api", "security"]
        },
        {
            "task_id": "task_test_001",
            "task_name": "生成登录功能测试用例",
            "receiver": AgentRole.TESTER.value,
            "description": "为登录功能生成完整的测试用例",
            "requirements": [
                "覆盖率 > 80%",
                "包含边界测试",
                "包含安全测试",
                "包含性能测试"
            ],
            "acceptance_criteria": [
                "测试用例数量 > 20",
                "包含正向和反向测试",
                "自动化测试脚本"
            ],
            "deadline": "2026-03-03T12:00:00Z",
            "estimated_hours": 2,
            "priority": 4,
            "project": "店小秘 ERP",
            "module": "用户认证",
            "tags": ["testing", "qa", "automation"]
        }
    ]
    
    pm.assign_tasks(conversation_id, tasks)
    
    # 开发和测试 Agent 处理任务
    dev.process_tasks()
    tester.process_tasks()
    
    # 囡囡进行质量检查
    quality_check_msg = AgentMessage(
        conversation_id=conversation_id,
        sender=AgentRole.PROJECT_MANAGER.value,
        receiver=AgentRole.NANNAN.value,
        message_type=MessageType.QUALITY_CHECK.value,
        content={"task_id": "task_dev_001"}
    )
    queue.send(quality_check_msg)
    nannan.process_requests()
    
    # 项目经理收集结果
    results = pm.collect_results(conversation_id)
    
    # 整合结果
    summary = pm.integrate_results(results)
    
    print("\n" + "=" * 60)
    print("🎉 多 Agent 协同完成！")
    print("=" * 60)
    print(summary)
    
    # 显示队列状态
    print("\n📊 队列状态:")
    for agent_id in [AgentRole.PROJECT_MANAGER.value, AgentRole.DEVELOPER.value, 
                     AgentRole.TESTER.value, AgentRole.NANNAN.value]:
        status = queue.status(agent_id)
        print(f"   {agent_id}: {status['pending_messages']} 条待处理")
    
    return conversation_id, results


# ==================== 运行 ====================

if __name__ == "__main__":
    # 运行演示
    asyncio.run(run_multi_agent_demo())
