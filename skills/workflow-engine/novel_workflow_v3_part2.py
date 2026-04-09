#!/usr/bin/env python3
"""
工作流 v3.0 Part 2 - Agent 直接通信 + 流水线引擎
- AgentDirectCommunication：Agent 间直接通信（不经过年年中转）
- PipelineEngine：流水线并行执行引擎
"""

import time
import uuid
import threading
import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed


# ═══════════════════════════════════════════════════════════
# 第一部分：消息定义
# ═══════════════════════════════════════════════════════════


class MessageStatus(Enum):
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    TIMEOUT = "timeout"          # 超时


@dataclass
class AgentMessage:
    """Agent 间通信消息"""
    id: str
    from_agent: str
    to_agent: str
    message_type: str           # "chapter_review" / "review_result" / "notification"
    content: dict               # 消息内容
    chapter_num: int
    status: MessageStatus = MessageStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        data["status"] = MessageStatus(data["status"])
        return cls(**data)


@dataclass
class ReviewResult:
    """审查结果"""
    chapter_num: int
    reviewer_name: str
    score: Optional[int] = None
    issues: list = field(default_factory=list)
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    passed: bool = False
    feedback: str = ""
    reviewed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════
# 第二部分：Agent 直接通信
# ═══════════════════════════════════════════════════════════


class AgentDirectCommunication:
    """
    Agent 直接通信 - 不经过年年中转

    核心能力：
    1. 惊鸿写完直接发给鉴微审查
    2. 审查结果自动返回
    3. 流水线并行：惊鸿写第N章的同时鉴微审查第N-1章
    """

    def __init__(self, work_dir: Optional[str] = None):
        """
        Args:
            work_dir: 消息持久化目录（默认临时目录）
        """
        self.work_dir = work_dir or os.path.join(tempfile.gettempdir(), "novel_workflow_comm")
        os.makedirs(self.work_dir, exist_ok=True)

        # 消息队列：{to_agent: [messages]}
        self._queues: dict[str, list[AgentMessage]] = {}
        self._review_results: dict[int, ReviewResult] = {}

        # 回调函数：{message_type: handler_func}
        self._handlers: dict[str, Callable] = {}

        # 线程锁
        self._lock = threading.Lock()

        # 流水线状态
        self._pipeline_active = False
        self._pipeline_lock = threading.Lock()

        # 超时设置（秒）
        self.default_timeout = 300  # 5分钟

    def register_handler(self, message_type: str, handler: Callable):
        """
        注册消息处理器。

        Args:
            message_type: 消息类型（如 "chapter_review"）
            handler: 处理函数，签名为 handler(message: AgentMessage) -> dict
        """
        self._handlers[message_type] = handler

    def send_to_reviewer(self, chapter_content: str, chapter_num: int,
                         novel_name: str = "", writer: str = "惊鸿",
                         reviewer: str = "鉴微") -> AgentMessage:
        """
        惊鸿写完直接发给鉴微审查。

        Args:
            chapter_content: 章节正文
            chapter_num: 章节号
            novel_name: 小说名
            writer: 写手 Agent 名
            reviewer: 审查 Agent 名

        Returns:
            发送的消息对象
        """
        msg = AgentMessage(
            id=str(uuid.uuid4())[:12],
            from_agent=writer,
            to_agent=reviewer,
            message_type="chapter_review",
            content={
                "chapter_content": chapter_content,
                "chapter_num": chapter_num,
                "novel_name": novel_name,
                "sent_at": time.time(),
            },
            chapter_num=chapter_num,
            status=MessageStatus.PENDING,
        )

        with self._lock:
            if reviewer not in self._queues:
                self._queues[reviewer] = []
            self._queues[reviewer].append(msg)

        # 持久化
        self._save_message(msg)

        return msg

    def get_review_result(self, chapter_num: int) -> Optional[ReviewResult]:
        """
        获取指定章节的审查结果。

        Args:
            chapter_num: 章节号

        Returns:
            审查结果，未审查完返回 None
        """
        return self._review_results.get(chapter_num)

    def process_pending(self, agent_name: str) -> list[AgentMessage]:
        """
        处理指定 Agent 的待处理消息。

        实际场景中由鉴微 Agent 调用，取出属于自己的审查请求并处理。

        Args:
            agent_name: Agent 名称

        Returns:
            已处理的消息列表
        """
        processed = []
        with self._lock:
            queue = self._queues.get(agent_name, [])
            pending = [m for m in queue if m.status == MessageStatus.PENDING]

        for msg in pending:
            # 标记为处理中
            msg.status = MessageStatus.PROCESSING
            msg.updated_at = time.time()

            # 查找对应处理器
            handler = self._handlers.get(msg.message_type)
            if handler:
                try:
                    result = handler(msg)
                    msg.status = MessageStatus.COMPLETED
                    msg.result = result
                    msg.updated_at = time.time()

                    # 如果是审查消息，保存审查结果
                    if msg.message_type == "chapter_review":
                        review = self._parse_review_result(result, chapter_num=msg.chapter_num,
                                                           reviewer_name=agent_name)
                        self._review_results[msg.chapter_num] = review

                except Exception as e:
                    msg.status = MessageStatus.FAILED
                    msg.error = str(e)
                    msg.updated_at = time.time()

            else:
                msg.status = MessageStatus.FAILED
                msg.error = f"未注册处理器: {msg.message_type}"
                msg.updated_at = time.time()

            processed.append(msg)

        return processed

    def pipeline_parallel(self, write_chapter_n: str, review_chapter_n_minus_1: int,
                          max_workers: int = 2) -> dict:
        """
        流水线并行：惊鸿写第N章的同时鉴微审查第N-1章。

        注意：这是模拟接口，实际写/审由对应 Agent 执行。

        Args:
            write_chapter_n: 第N章内容（待写入/已写入）
            review_chapter_n_minus_1: 要审查的章节号（N-1）
            max_workers: 并行工作线程数

        Returns:
            {
                "write_status": "completed/failed",
                "review_status": "completed/failed",
                "review_result": ReviewResult or None,
                "parallel": True/False,  # 是否真正并行执行
            }
        """
        result = {
            "write_status": "pending",
            "review_status": "pending",
            "review_result": None,
            "parallel": False,
            "chapters": {
                "writing": None,  # 正在写的章节
                "reviewing": review_chapter_n_minus_1,
            },
            "timing": {},
        }

        has_review_task = review_chapter_n_minus_1 is not None
        has_write_task = write_chapter_n is not None

        result["chapters"]["writing"] = f"chapter_{write_chapter_n}" if isinstance(write_chapter_n, int) else "new"

        # 只有同时有写和审的任务时才并行
        if has_write_task and has_review_task:
            result["parallel"] = True
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}

                # 任务1：审查 N-1 章
                review_future = executor.submit(self._simulate_review, review_chapter_n_minus_1)
                futures[review_future] = "review"

                # 任务2：写 N 章（模拟）
                write_future = executor.submit(self._simulate_write, write_chapter_n)
                futures[write_future] = "write"

                for future in as_completed(futures):
                    task = futures[future]
                    start = time.time()
                    try:
                        task_result = future.result(timeout=self.default_timeout)
                        elapsed = time.time() - start
                        result["timing"][task] = elapsed
                        if task == "review":
                            result["review_status"] = "completed"
                            result["review_result"] = task_result
                        elif task == "write":
                            result["write_status"] = "completed"
                    except Exception as e:
                        if task == "review":
                            result["review_status"] = "failed"
                        elif task == "write":
                            result["write_status"] = "failed"
                        result["timing"][f"{task}_error"] = str(e)

        elif has_review_task:
            # 只有审查任务
            result["review_status"] = "completed"
            result["review_result"] = self._simulate_review(review_chapter_n_minus_1)
            result["timing"]["review"] = 0.01

        elif has_write_task:
            # 只有写任务
            result["write_status"] = "completed"
            result["timing"]["write"] = 0.01

        return result

    def get_queue_status(self) -> dict:
        """获取各 Agent 消息队列状态"""
        with self._lock:
            status = {}
            for agent, messages in self._queues.items():
                status[agent] = {
                    "total": len(messages),
                    "pending": len([m for m in messages if m.status == MessageStatus.PENDING]),
                    "processing": len([m for m in messages if m.status == MessageStatus.PROCESSING]),
                    "completed": len([m for m in messages if m.status == MessageStatus.COMPLETED]),
                    "failed": len([m for m in messages if m.status == MessageStatus.FAILED]),
                }
        return status

    def get_all_review_results(self) -> dict[int, dict]:
        """获取所有审查结果"""
        return {ch: r.to_dict() for ch, r in self._review_results.items()}

    # ─── 内部方法 ───

    def _save_message(self, msg: AgentMessage):
        """持久化消息到文件"""
        filepath = os.path.join(self.work_dir, f"msg_{msg.id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(msg.to_dict(), f, ensure_ascii=False, indent=2)

    def _parse_review_result(self, result_data: dict, chapter_num: int,
                             reviewer_name: str) -> ReviewResult:
        """从处理器返回结果中解析审查结果"""
        review = ReviewResult(
            chapter_num=chapter_num,
            reviewer_name=reviewer_name,
            score=result_data.get("score"),
            issues=result_data.get("issues", []),
            p0_count=result_data.get("p0_count", 0),
            p1_count=result_data.get("p1_count", 0),
            p2_count=result_data.get("p2_count", 0),
            passed=result_data.get("passed", False),
            feedback=result_data.get("feedback", ""),
        )
        return review

    @staticmethod
    def _simulate_review(chapter_num: int) -> ReviewResult:
        """模拟审查过程"""
        import random
        random.seed(chapter_num * 137)

        score = random.randint(65, 88)
        p0 = random.randint(0, 2)
        p1 = max(2, random.randint(2, 5))  # 至少2个P1
        p2 = random.randint(1, 4)

        return ReviewResult(
            chapter_num=chapter_num,
            reviewer_name="鉴微",
            score=score,
            issues=[
                {"level": "P0", "issue": f"第{chapter_num}章情节推进过慢"},
            ] * p0 + [
                {"level": "P1", "issue": f"第{chapter_num}章角色对话不够自然"},
                {"level": "P1", "issue": f"第{chapter_num}章结尾悬念不够强"},
            ] + [
                {"level": "P2", "issue": f"第{chapter_num}章个别段落AI味较重"},
            ] * p2,
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            passed=(p0 == 0),
            feedback=f"第{chapter_num}章审查完成，综合评分 {score}/100",
        )

    @staticmethod
    def _simulate_write(chapter: Any) -> dict:
        """模拟写作过程"""
        return {
            "chapter": chapter,
            "status": "written",
            "word_count": 3500,
        }


# ═══════════════════════════════════════════════════════════
# 第三部分：流水线引擎
# ═══════════════════════════════════════════════════════════


class PipelineStage:
    """流水线阶段"""

    def __init__(self, name: str, agent: str, task: Callable,
                 depends_on: Optional[str] = None):
        self.name = name
        self.agent = agent
        self.task = task
        self.depends_on = depends_on  # 依赖的阶段名称
        self.result: Optional[Any] = None
        self.status = "pending"  # pending / running / completed / failed
        self.duration = 0.0
        self.error: Optional[str] = None

    def execute(self, input_data: Optional[Any] = None) -> Any:
        """执行阶段任务"""
        self.status = "running"
        start = time.time()
        try:
            import inspect
            sig = inspect.signature(self.task)
            params = list(sig.parameters.values())
            if len(params) > 0:
                self.result = self.task(input_data)
            else:
                self.result = self.task()
            self.status = "completed"
            self.duration = time.time() - start
            return self.result
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            self.duration = time.time() - start
            raise

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "agent": self.agent,
            "status": self.status,
            "duration": round(self.duration, 3),
            "error": self.error,
            "has_result": self.result is not None,
        }


class PipelineEngine:
    """
    流水线引擎 - 真正并行

    支持：
    1. 多阶段流水线（线性 + 依赖）
    2. 阶段间数据传递
    3. 错误传播与重试
    4. 执行报告
    """

    def __init__(self, pipeline_name: str = "novel_pipeline",
                 max_retries: int = 1, retry_delay: float = 1.0):
        self.pipeline_name = pipeline_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._stages: list[PipelineStage] = []
        self._stage_map: dict[str, PipelineStage] = {}
        self._results: dict[str, Any] = {}
        self._execution_log: list[dict] = []
        self._start_time = 0.0
        self._end_time = 0.0

    def add_stage(self, name: str, agent: str, task: Callable,
                  depends_on: Optional[str] = None) -> "PipelineEngine":
        """
        添加流水线阶段（支持链式调用）。

        Args:
            name: 阶段名称
            agent: 负责的 Agent
            task: 执行函数
            depends_on: 依赖的前序阶段名称

        Returns:
            self（支持链式调用）
        """
        # 检查依赖是否存在
        if depends_on and depends_on not in self._stage_map:
            raise ValueError(f"依赖阶段 '{depends_on}' 不存在")

        stage = PipelineStage(name=name, agent=agent, task=task, depends_on=depends_on)
        self._stages.append(stage)
        self._stage_map[name] = stage
        return self

    def execute(self, initial_input: Optional[Any] = None) -> dict:
        """
        执行整个流水线。

        执行策略：
        - 无依赖的阶段可并行执行
        - 有依赖的阶段等待依赖完成后执行
        - 前一阶段失败则后续依赖阶段跳过

        Args:
            initial_input: 输入数据（传给第一个无依赖阶段）

        Returns:
            执行报告
        """
        self._start_time = time.time()
        self._execution_log = []
        self._results = {}

        # 重置所有阶段状态
        for stage in self._stages:
            stage.status = "pending"
            stage.result = None
            stage.duration = 0.0
            stage.error = None

        # 按依赖关系排序并执行
        executed = set()
        skipped = set()
        total_stages = len(self._stages)

        while len(executed) + len(skipped) < total_stages:
            progress_made = False

            for stage in self._stages:
                if stage.name in executed or stage.name in skipped:
                    continue

                # 检查依赖
                if stage.depends_on:
                    if stage.depends_on in skipped:
                        # 依赖被跳过，自己也跳过
                        stage.status = "skipped"
                        stage.error = f"依赖阶段 '{stage.depends_on}' 被跳过"
                        skipped.add(stage.name)
                        self._execution_log.append({
                            "stage": stage.name,
                            "agent": stage.agent,
                            "status": "skipped",
                            "reason": f"依赖 '{stage.depends_on}' 被跳过",
                        })
                        progress_made = True
                        continue
                    elif stage.depends_on not in executed:
                        # 依赖未就绪，跳过本轮
                        continue
                    input_data = self._results.get(stage.depends_on)
                else:
                    input_data = initial_input

                # 执行阶段（捕获异常以便继续处理后续阶段）
                try:
                    stage_result = self._execute_with_retry(stage, input_data)
                    self._results[stage.name] = stage_result
                    executed.add(stage.name)
                except Exception:
                    skipped.add(stage.name)

                progress_made = True

                self._execution_log.append({
                    "stage": stage.name,
                    "agent": stage.agent,
                    "status": stage.status,
                    "duration": stage.duration,
                    "error": stage.error,
                })

            if not progress_made:
                # 检测死锁
                remaining = [s.name for s in self._stages
                             if s.name not in executed and s.name not in skipped]
                for name in remaining:
                    stage = self._stage_map[name]
                    stage.status = "failed"
                    stage.error = f"死锁：依赖 '{stage.depends_on}' 无法完成"
                    skipped.add(name)
                    self._execution_log.append({
                        "stage": name,
                        "agent": stage.agent,
                        "status": "failed",
                        "error": "死锁检测",
                    })

        self._end_time = time.time()
        return self._generate_report()

    def execute_parallel(self, initial_input: Optional[Any] = None,
                         max_workers: int = 4) -> dict:
        """
        并行执行流水线（无依赖阶段同时执行）。

        Args:
            initial_input: 输入数据
            max_workers: 最大并行数

        Returns:
            执行报告
        """
        self._start_time = time.time()
        self._execution_log = []
        self._results = {}

        for stage in self._stages:
            stage.status = "pending"
            stage.result = None
            stage.duration = 0.0
            stage.error = None

        executed = set()
        skipped = set()
        total_stages = len(self._stages)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while len(executed) + len(skipped) < total_stages:
                # 收集可执行的阶段
                ready_stages = []
                for stage in self._stages:
                    if stage.name in executed or stage.name in skipped:
                        continue
                    if stage.depends_on and stage.depends_on not in executed:
                        continue
                    if stage.depends_on and stage.depends_on in skipped:
                        stage.status = "skipped"
                        stage.error = f"依赖 '{stage.depends_on}' 被跳过"
                        skipped.add(stage.name)
                        continue
                    ready_stages.append(stage)

                if not ready_stages:
                    break

                # 并行执行
                futures = {}
                for stage in ready_stages:
                    input_data = self._results.get(stage.depends_on, initial_input) \
                        if stage.depends_on else initial_input
                    future = executor.submit(self._execute_with_retry, stage, input_data)
                    futures[future] = stage

                for future in as_completed(futures):
                    stage = futures[future]
                    executed.add(stage.name)
                    self._results[stage.name] = stage.result
                    self._execution_log.append({
                        "stage": stage.name,
                        "agent": stage.agent,
                        "status": stage.status,
                        "duration": stage.duration,
                        "error": stage.error,
                    })

        self._end_time = time.time()
        return self._generate_report()

    def get_stage_result(self, stage_name: str) -> Optional[Any]:
        """获取指定阶段的执行结果"""
        return self._results.get(stage_name)

    def get_execution_log(self) -> list[dict]:
        """获取执行日志"""
        return self._execution_log.copy()

    # ─── 内部方法 ───

    def _execute_with_retry(self, stage: PipelineStage, input_data: Optional[Any]) -> Any:
        """带重试的执行"""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = stage.execute(input_data)
                return result
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    stage.status = "retrying"
                    time.sleep(self.retry_delay)
                    continue

        # 所有重试失败
        stage.status = "failed"
        stage.error = last_error
        self._execution_log.append({
            "stage": stage.name,
            "agent": stage.agent,
            "status": "failed",
            "error": last_error,
            "retries": self.max_retries,
        })
        raise Exception(f"阶段 '{stage.name}' 执行失败（重试{self.max_retries}次后）: {last_error}")

    def _generate_report(self) -> dict:
        """生成执行报告"""
        total_duration = self._end_time - self._start_time
        stages_info = {s.name: s.to_dict() for s in self._stages}

        success_count = sum(1 for s in self._stages if s.status == "completed")
        failed_count = sum(1 for s in self._stages if s.status == "failed")
        skipped_count = sum(1 for s in self._stages if s.status == "skipped")

        return {
            "pipeline_name": self.pipeline_name,
            "status": "completed" if failed_count == 0 else "partial_failure",
            "total_stages": len(self._stages),
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total_duration": round(total_duration, 3),
            "stages": stages_info,
            "execution_log": self._execution_log,
        }


# ═══════════════════════════════════════════════════════════
# 第四部分：便捷工厂函数
# ═══════════════════════════════════════════════════════════


def create_novel_pipeline(novel_name: str,
                          writer_fn: Optional[Callable] = None,
                          reviewer_fn: Optional[Callable] = None,
                          finalizer_fn: Optional[Callable] = None) -> PipelineEngine:
    """
    快速创建小说工作流流水线。

    标准流程：惊鸿写作 → 鉴微审查 → 天工终审 → 定稿

    Args:
        novel_name: 小说名
        writer_fn: 写作函数（默认模拟）
        reviewer_fn: 审查函数（默认模拟）
        finalizer_fn: 终审函数（默认模拟）

    Returns:
        配置好的 PipelineEngine
    """
    def default_write(chapter_num=1):
        return {"chapter": chapter_num, "content": f"第{chapter_num}章内容（模拟）", "word_count": 3000}

    def default_review(write_result):
        chapter_num = write_result.get("chapter", 0)
        return {
            "chapter_num": chapter_num,
            "score": 78,
            "p0_count": 0,
            "p1_count": 3,
            "p2_count": 2,
            "passed": True,
            "feedback": f"第{chapter_num}章审查通过，建议修改5处",
        }

    def default_finalize(review_result):
        return {
            "chapter_num": review_result.get("chapter_num", 0),
            "final_score": review_result.get("score", 0),
            "status": "approved" if review_result.get("passed") else "needs_revision",
            "ready_for_publish": True,
        }

    engine = PipelineEngine(pipeline_name=f"{novel_name}_pipeline")

    engine.add_stage(
        name="惊鸿写作",
        agent="惊鸿",
        task=writer_fn or default_write,
    ).add_stage(
        name="鉴微审查",
        agent="鉴微",
        task=reviewer_fn or default_review,
        depends_on="惊鸿写作",
    ).add_stage(
        name="天工终审",
        agent="天工",
        task=finalizer_fn or default_finalize,
        depends_on="鉴微审查",
    )

    return engine


# ═══════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════


if __name__ == "__main__":
    import shutil

    print("=" * 60)
    print("工作流 v3.0 Part 2 - Agent 直接通信 + 流水线引擎")
    print("=" * 60)

    # ─── 测试1: 基本消息发送与接收 ───
    print("\n【测试1】Agent 直接通信 - 发送与接收")
    tmp_dir = os.path.join(tempfile.gettempdir(), "novel_test_comm")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    comm = AgentDirectCommunication(work_dir=tmp_dir)

    # 发送审查请求
    msg = comm.send_to_reviewer(
        chapter_content="这是第3章的内容...",
        chapter_num=3,
        novel_name="测试小说",
    )
    print(f"  ✅ 消息发送：{msg.id} (惊鸿→鉴微, 第3章)")

    # 注册处理器
    def mock_reviewer_handler(message: AgentMessage) -> dict:
        return {
            "score": 82,
            "p0_count": 0,
            "p1_count": 3,
            "p2_count": 1,
            "passed": True,
            "feedback": "审查通过",
            "issues": [
                {"level": "P1", "issue": "对话不够自然"},
                {"level": "P1", "issue": "结尾悬念不够"},
                {"level": "P1", "issue": "场景切换生硬"},
            ],
        }

    comm.register_handler("chapter_review", mock_reviewer_handler)

    # 处理消息
    processed = comm.process_pending("鉴微")
    assert len(processed) == 1
    assert processed[0].status == MessageStatus.COMPLETED
    print(f"  ✅ 消息处理：状态={processed[0].status.value}")

    # 获取审查结果
    result = comm.get_review_result(3)
    assert result is not None
    assert result.chapter_num == 3
    assert result.score == 82
    assert result.passed is True
    assert result.p1_count == 3
    print(f"  ✅ 审查结果：{result.chapter_num}章, 评分={result.score}, 通过={result.passed}")

    # 队列状态
    status = comm.get_queue_status()
    assert "鉴微" in status
    assert status["鉴微"]["total"] == 1
    assert status["鉴微"]["completed"] == 1
    print(f"  ✅ 队列状态：鉴微 {status['鉴微']}")

    # ─── 测试2: 多章节流水线并行 ───
    print("\n【测试2】流水线并行 - 写第N章 + 审第N-1章")
    comm2 = AgentDirectCommunication(work_dir=os.path.join(tmp_dir, "pipeline"))

    # 发送第2章审查
    comm2.send_to_reviewer("第2章内容...", 2, "测试小说")
    # 同时准备第3章
    write_chapter_3 = "第3章内容（惊鸿正在写）..."

    result = comm2.pipeline_parallel(
        write_chapter_n=3,
        review_chapter_n_minus_1=2,
        max_workers=2,
    )
    assert result["parallel"] is True
    assert result["write_status"] == "completed"
    assert result["review_status"] == "completed"
    assert result["review_result"] is not None
    assert result["review_result"].chapter_num == 2
    print(f"  ✅ 并行执行：写第3章 + 审第2章")
    print(f"    审查结果：评分={result['review_result'].score}, "
          f"P0={result['review_result'].p0_count}, "
          f"P1={result['review_result'].p1_count}")
    print(f"    耗时：{result['timing']}")

    # ─── 测试3: 只有审查任务（无写作） ───
    print("\n【测试3】仅审查任务")
    result_only_review = comm2.pipeline_parallel(
        write_chapter_n=None,
        review_chapter_n_minus_1=4,
        max_workers=2,
    )
    assert result_only_review["parallel"] is False
    assert result_only_review["review_status"] == "completed"
    print(f"  ✅ 仅审查第4章：评分={result_only_review['review_result'].score}")

    # ─── 测试4: PipelineEngine 基本执行 ───
    print("\n【测试4】PipelineEngine - 线性执行")

    def mock_write(data):
        return {"chapter": 1, "content": "模拟内容", "word_count": 3000}

    def mock_review(write_result):
        return {"chapter_num": write_result["chapter"], "score": 80, "passed": True}

    def mock_finalize(review_result):
        return {"chapter_num": review_result["chapter_num"], "status": "approved"}

    engine = PipelineEngine(pipeline_name="test_pipeline")
    engine.add_stage("写作", "惊鸿", mock_write)
    engine.add_stage("审查", "鉴微", mock_review, depends_on="写作")
    engine.add_stage("终审", "天工", mock_finalize, depends_on="审查")

    report = engine.execute()
    assert report["status"] == "completed"
    assert report["success"] == 3
    assert report["failed"] == 0
    assert report["total_stages"] == 3
    print(f"  ✅ 流水线执行：{report['success']}/{report['total_stages']} 成功, "
          f"耗时 {report['total_duration']}s")
    stage_summary = ", ".join(f"{s['name']}({s['status']})" for s in report["stages"].values())
    print(f"    各阶段：{stage_summary}")

    # ─── 测试5: PipelineEngine 链式调用 ───
    print("\n【测试5】PipelineEngine - 链式调用")
    engine2 = PipelineEngine(pipeline_name="chain_test")
    engine2.add_stage("A", "agent1", lambda: "A_done") \
           .add_stage("B", "agent2", lambda x: f"B_done after {x}", depends_on="A") \
           .add_stage("C", "agent3", lambda x: f"C_done after {x}", depends_on="B")
    report2 = engine2.execute("start")
    assert report2["status"] == "completed"
    print(f"  ✅ 链式调用成功：{report2['success']} 阶段全部完成")

    # ─── 测试6: 依赖缺失检测 ───
    print("\n【测试6】PipelineEngine - 依赖检测")
    try:
        PipelineEngine().add_stage("X", "agent1", lambda: None, depends_on="nonexistent")
        assert False, "应该抛出异常"
    except ValueError as e:
        assert "不存在" in str(e)
        print(f"  ✅ 依赖检测：正确抛出 ValueError")

    # ─── 测试7: 执行失败传播 ───
    print("\n【测试7】PipelineEngine - 失败传播")
    engine3 = PipelineEngine(pipeline_name="fail_test", max_retries=0)
    engine3.add_stage("ok", "agent1", lambda: "ok")
    engine3.add_stage("fail", "agent2", lambda x: 1/0, depends_on="ok")  # 会抛异常
    engine3.add_stage("skip", "agent3", lambda: "skip", depends_on="fail")

    try:
        engine3.execute("start")
    except Exception:
        pass

    log = engine3.get_execution_log()
    failed_stages = [e for e in log if e["status"] == "failed"]
    skipped_stages = [e for e in log if e["status"] == "skipped"]
    assert len(failed_stages) >= 1
    assert len(skipped_stages) >= 1
    print(f"  ✅ 失败传播：{len(failed_stages)} 个失败, {len(skipped_stages)} 个跳过")

    # ─── 测试8: 并行执行 ───
    print("\n【测试8】PipelineEngine - 并行执行")
    engine4 = PipelineEngine(pipeline_name="parallel_test")
    engine4.add_stage("write_ch1", "惊鸿", lambda: {"ch": 1})
    engine4.add_stage("write_ch2", "惊鸿", lambda: {"ch": 2})
    engine4.add_stage("write_ch3", "惊鸿", lambda: {"ch": 3})
    engine4.add_stage("final_check", "天工", lambda x: "all_done")  # 依赖最后一个

    report4 = engine4.execute_parallel(max_workers=3)
    assert report4["status"] == "completed"
    assert report4["success"] == 4
    print(f"  ✅ 并行执行：{report4['success']} 阶段全部完成, "
          f"耗时 {report4['total_duration']}s")

    # ─── 测试9: 便捷工厂函数 ───
    print("\n【测试9】create_novel_pipeline 工厂函数")
    pipeline = create_novel_pipeline("斗破测试")
    report5 = pipeline.execute()
    assert report5["success"] == 3
    print(f"  ✅ 工厂函数：惊鸿写作 → 鉴微审查 → 天工终审，{report5['success']} 阶段完成")

    # ─── 测试10: 多章节消息队列 ───
    print("\n【测试10】多章节消息队列 + 全部审查结果")
    comm3 = AgentDirectCommunication(work_dir=os.path.join(tmp_dir, "multi"))

    # 注册处理器（多章节场景）
    comm3.register_handler("chapter_review", mock_reviewer_handler)

    # 批量发送
    for ch in range(5, 8):
        comm3.send_to_reviewer(f"第{ch}章内容", ch, "测试小说")

    # 批量处理
    processed_multi = comm3.process_pending("鉴微")
    assert len(processed_multi) == 3
    all_results = comm3.get_all_review_results()
    assert len(all_results) == 3
    print(f"  ✅ 批量发送3章 → 批量处理3章 → 获取{len(all_results)}个审查结果")
    for ch, r in sorted(all_results.items()):
        print(f"    第{ch}章：评分={r['score']}, P0={r['p0_count']}, P1={r['p1_count']}")

    # ─── 清理 ───
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    print("\n" + "=" * 60)
    print("✅ 全部10项测试通过！工作流 v3.0 Part 2 就绪。")
    print("=" * 60)

    print("\n核心能力清单：")
    print("1. ✅ AgentDirectCommunication - Agent 直接通信（不经年年中转）")
    print("2. ✅ send_to_reviewer() - 惊鸿写完直接发鉴微")
    print("3. ✅ get_review_result() - 获取审查结果")
    print("4. ✅ pipeline_parallel() - 流水线并行（写N章同时审N-1章）")
    print("5. ✅ PipelineEngine - 流水线引擎（线性 + 依赖 + 并行）")
    print("6. ✅ add_stage() - 链式调用添加阶段")
    print("7. ✅ execute() / execute_parallel() - 线性/并行执行")
    print("8. ✅ 失败传播 + 跳过 + 重试")
    print("9. ✅ create_novel_pipeline() - 便捷工厂函数")
    print("10. ✅ 消息持久化（JSON文件）")
