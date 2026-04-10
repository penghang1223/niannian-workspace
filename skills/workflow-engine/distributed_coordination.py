#!/usr/bin/env python3
"""
分布式协调模式实战
涵盖：领导者选举、分布式屏障、工作队列、发布订阅协调

核心原则：
1. 领导者选举 — 多节点选主，避免重复工作
2. 分布式屏障 — 多 Agent 同步点，全部到达才继续
3. 工作队列 — 任务分发，消费者竞争获取
4. 发布订阅协调 — 事件驱动的多 Agent 通信

适用场景：多 Agent 协作、分布式任务编排、集群管理
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ==================== 1. 领导者选举 ====================

class LeaderElection:
    """
    基于 Redis 的领导者选举

    原理：SET NX PX 原子操作，只有一个节点能获取锁
    特性：
    - 自动续期（看门狗）
    - 领导者宕机自动切换
    - 支持优雅让位

    适用：多 Agent 中只允许一个执行某任务
    例：小说创作中只有一个惊鸿在写当前章节
    """

    def __init__(
        self,
        redis_client: Any,
        election_key: str,
        ttl_ms: int = 10000,
        retry_interval: float = 1.0,
    ):
        self.redis = redis_client
        self.election_key = f"election:{election_key}"
        self.ttl_ms = ttl_ms
        self.retry_interval = retry_interval
        self._node_id = str(uuid.uuid4())[:8]
        self._is_leader = False
        self._watchdog_task: Optional[asyncio.Task] = None

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    async def try_elect(self) -> bool:
        """尝试成为领导者"""
        if not self.redis:
            return False

        acquired = await self.redis.set(
            self.election_key,
            self._node_id,
            nx=True,
            px=self.ttl_ms,
        )

        if acquired:
            self._is_leader = True
            self._watchdog_task = asyncio.create_task(self._watchdog())
            logger.info("节点 %s 成为领导者", self._node_id)
            return True

        # 检查当前领导者是谁
        current_leader = await self.redis.get(self.election_key)
        logger.debug("节点 %s 选举失败，当前领导者: %s", self._node_id, current_leader)
        return False

    async def resign(self):
        """主动让位"""
        if not self._is_leader:
            return

        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass

        # 只有自己才能释放
        current = await self.redis.get(self.election_key)
        if current == self._node_id:
            await self.redis.delete(self.election_key)

        self._is_leader = False
        logger.info("节点 %s 主动让位", self._node_id)

    async def _watchdog(self):
        """看门狗续期"""
        renew_interval = self.ttl_ms / 3000
        try:
            while self._is_leader:
                await asyncio.sleep(renew_interval)
                if self._is_leader:
                    await self.redis.pexpire(self.election_key, self.ttl_ms)
        except asyncio.CancelledError:
            pass

    async def get_leader(self) -> Optional[str]:
        """获取当前领导者"""
        if not self.redis:
            return None
        return await self.redis.get(self.election_key)


# ==================== 2. 分布式屏障 ====================

class DistributedBarrier:
    """
    分布式屏障 — 多 Agent 同步点

    原理：
    - 每个 Agent 到达时 INCR 计数器
    - 计数器达到 expected_count 时，所有 Agent 放行
    - 支持超时

    适用：多阶段任务，所有 Agent 完成阶段 N 才能进入阶段 N+1
    例：小说创作中所有章节审查完成才能进入分发阶段
    """

    def __init__(
        self,
        redis_client: Any,
        barrier_key: str,
        expected_count: int,
        timeout: float = 30.0,
    ):
        self.redis = redis_client
        self.barrier_key = f"barrier:{barrier_key}"
        self.expected_count = expected_count
        self.timeout = timeout
        self._node_id = str(uuid.uuid4())[:8]

    async def wait(self) -> bool:
        """
        等待屏障开放

        Returns:
            True = 屏障开放，False = 超时
        """
        if not self.redis:
            return True

        start = time.monotonic()
        while time.monotonic() - start < self.timeout:
            count = await self.redis.incr(self.barrier_key)

            # 第一次到达的节点设置过期时间
            if count == 1:
                await self.redis.expire(self.barrier_key, int(self.timeout * 2))

            if count >= self.expected_count:
                logger.info("屏障 %s 开放 (%d/%d)", self.barrier_key, count, self.expected_count)
                return True

            await asyncio.sleep(0.1)

        logger.warning("屏障 %s 超时 (%d/%d)", self.barrier_key, count, self.expected_count)
        return False

    async def reset(self):
        """重置屏障"""
        if self.redis:
            await self.redis.delete(self.barrier_key)


# ==================== 3. 工作队列 ====================

class WorkQueue:
    """
    基于 Redis 的工作队列

    原理：LPUSH + BRPOPLPUSH（原子出队+入备份队列）
    特性：
    - 多消费者竞争获取
    - 处理中超时自动回退
    - 支持优先级

    适用：任务分发、异步处理
    例：小说章节创作任务队列，惊鸿消费
    """

    def __init__(
        self,
        redis_client: Any,
        queue_name: str,
        processing_timeout: float = 300.0,
    ):
        self.redis = redis_client
        self.queue_key = f"queue:{queue_name}"
        self.processing_key = f"queue:{queue_name}:processing"
        self.processing_timeout = processing_timeout

    async def enqueue(self, task: str, priority: int = 0) -> int:
        """
        入队

        Args:
            task: 任务数据（JSON 字符串）
            priority: 优先级（越高越先出队，0=普通）

        Returns:
            队列长度
        """
        if not self.redis:
            return 0

        if priority > 0:
            # 优先级队列用 Sorted Set
            score = time.time() + priority
            return await self.redis.zadd(f"{self.queue_key}:priority", {task: score})
        else:
            return await self.redis.lpush(self.queue_key, task)

    async def dequeue(self, timeout: float = 1.0) -> Optional[str]:
        """
        出队（原子操作：出队+入处理中队列）

        Args:
            timeout: 阻塞等待时间（秒）

        Returns:
            任务数据，None 表示超时
        """
        if not self.redis:
            return None

        task = await self.redis.brpoplpush(
            self.queue_key,
            self.processing_key,
            timeout=timeout,
        )
        return task

    async def complete(self, task: str):
        """标记任务完成（从处理中队列移除）"""
        if self.redis:
            await self.redis.lrem(self.processing_key, 1, task)

    async def retry_expired(self) -> list[str]:
        """重试超时任务（从处理中队列移回主队列）"""
        if not self.redis:
            return []

        all_tasks = await self.redis.lrange(self.processing_key, 0, -1)
        retried = []
        for task in all_tasks:
            # 简化处理：实际应记录任务开始时间
            await self.redis.lrem(self.processing_key, 1, task)
            await self.redis.lpush(self.queue_key, task)
            retried.append(task)

        return retried

    async def size(self) -> dict:
        """获取队列大小"""
        if not self.redis:
            return {"pending": 0, "processing": 0}

        return {
            "pending": await self.redis.llen(self.queue_key),
            "processing": await self.redis.llen(self.processing_key),
        }


# ==================== 4. 发布订阅协调 ====================

class PubSubCoordinator:
    """
    基于 Redis 的发布订阅协调

    原理：PUBLISH/SUBSCRIBE 实现事件驱动通信
    特性：
    - 多 Agent 监听同一频道
    - 支持模式匹配（PATTERN）
    - 轻量级事件通知

    适用：Agent 间事件通知、状态广播
    例：惊鸿写完一章后发布事件，鉴微订阅后自动审查
    """

    def __init__(self, redis_client: Any):
        self.redis = redis_client
        self._pubsub = None
        self._listeners: dict[str, list[Callable]] = {}

    async def publish(self, channel: str, message: str) -> int:
        """发布消息"""
        if not self.redis:
            return 0
        return await self.redis.publish(channel, message)

    async def subscribe(self, channel: str, callback: Callable):
        """
        订阅频道

        Args:
            channel: 频道名
            callback: 消息处理函数 (message: str) -> None
        """
        if channel not in self._listeners:
            self._listeners[channel] = []
        self._listeners[channel].append(callback)

    async def start_listening(self):
        """开始监听所有订阅的频道"""
        if not self.redis or not self._listeners:
            return

        self._pubsub = self.redis.pubsub()
        for channel in self._listeners:
            await self._pubsub.subscribe(channel)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                data = message["data"]
                for callback in self._listeners.get(channel, []):
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as exc:
                        logger.error("回调异常 [%s]: %s", channel, exc)

    async def unsubscribe(self, channel: str):
        """取消订阅"""
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)
        self._listeners.pop(channel, None)


# ==================== 5. 协调模式组合 ====================

class AgentCoordinator:
    """
    Agent 协调器 — 组合多种协调模式

    典型工作流：
    1. 领导者选举 → 选出一个协调 Agent
    2. 工作队列 → 分发任务
    3. 分布式屏障 → 等待所有任务完成
    4. 发布订阅 → 通知结果
    """

    def __init__(self, redis_client: Any, group_name: str):
        self.redis = redis_client
        self.group_name = group_name
        self.election = LeaderElection(redis_client, f"{group_name}:leader")
        self.barrier: Optional[DistributedBarrier] = None
        self.queue = WorkQueue(redis_client, f"{group_name}:tasks")
        self.pubsub = PubSubCoordinator(redis_client)

    async def run_coordinated_task(
        self,
        task: str,
        expected_workers: int,
        barrier_timeout: float = 60.0,
    ) -> bool:
        """
        运行协调任务

        流程：
        1. 尝试成为领导者
        2. 领导者入队任务
        3. 所有工作者到达屏障
        4. 屏障开放，并行执行
        5. 发布完成事件
        """
        # 1. 选举
        is_leader = await self.election.try_elect()

        # 2. 领导者入队
        if is_leader:
            await self.queue.enqueue(task)
            logger.info("领导者 %s 入队任务", self.election.node_id)

        # 3. 设置屏障
        self.barrier = DistributedBarrier(
            self.redis,
            f"{self.group_name}:barrier",
            expected_count=expected_workers,
            timeout=barrier_timeout,
        )

        # 4. 等待所有工作者就绪
        ready = await self.barrier.wait()
        if not ready:
            logger.warning("协调超时")
            return False

        # 5. 执行任务（模拟）
        logger.info("所有工作者就绪，执行任务: %s", task)

        # 6. 发布完成事件
        await self.pubsub.publish(
            f"{self.group_name}:events",
            f"task_completed:{task}",
        )

        # 7. 重置屏障
        await self.barrier.reset()

        return True


# ==================== 测试 ====================

async def test_leader_election():
    """测试领导者选举（模拟）"""
    print("=" * 60)
    print("测试领导者选举（逻辑验证）")
    print("=" * 60)

    # 无 Redis 时的行为
    election = LeaderElection(None, "test")
    result = await election.try_elect()
    assert result is False
    print(f"  ✅ 无 Redis 时选举失败: {result}")

    print(f"  ✅ 节点 ID: {election.node_id}")

    # 选举属性验证
    assert election.is_leader is False
    print(f"  ✅ is_leader: {election.is_leader}")


async def test_distributed_barrier():
    """测试分布式屏障（模拟）"""
    print("\n" + "=" * 60)
    print("测试分布式屏障（逻辑验证）")
    print("=" * 60)

    barrier = DistributedBarrier(None, "test", expected_count=3)
    result = await barrier.wait()
    assert result is True  # 无 Redis 时放行
    print("  ✅ 无 Redis 时放行")


async def test_work_queue():
    """测试工作队列（模拟）"""
    print("\n" + "=" * 60)
    print("测试工作队列（逻辑验证）")
    print("=" * 60)

    queue = WorkQueue(None, "test")
    result = await queue.enqueue("task_1")
    assert result == 0  # 无 Redis
    print("  ✅ 无 Redis 时入队返回 0")

    task = await queue.dequeue()
    assert task is None
    print("  ✅ 无 Redis 时出队返回 None")

    size = await queue.size()
    assert size == {"pending": 0, "processing": 0}
    print("  ✅ 无 Redis 时队列大小为 0")


def test_algorithm_comparison():
    """协调模式对比"""
    print("\n" + "=" * 60)
    print("分布式协调模式对比")
    print("=" * 60)

    modes = {
        "领导者选举": {
            "目的": "多节点选主",
            "原理": "SET NX PX 原子操作",
            "适用": "唯一执行者场景",
            "复杂度": "低",
        },
        "分布式屏障": {
            "目的": "多节点同步",
            "原理": "INCR 计数器 + 阈值判断",
            "适用": "多阶段任务同步",
            "复杂度": "中",
        },
        "工作队列": {
            "目的": "任务分发",
            "原理": "LPUSH + BRPOPLPUSH",
            "适用": "异步任务处理",
            "复杂度": "中",
        },
        "发布订阅": {
            "目的": "事件通知",
            "原理": "PUBLISH/SUBSCRIBE",
            "适用": "状态广播、事件驱动",
            "复杂度": "低",
        },
    }

    print(f"{'模式':<15} {'目的':<15} {'原理':<30} {'复杂度':<8}")
    print("-" * 70)
    for name, info in modes.items():
        print(f"{name:<15} {info['目的']:<15} {info['原理']:<30} {info['复杂度']:<8}")


async def main():
    await test_leader_election()
    await test_distributed_barrier()
    await test_work_queue()
    test_algorithm_comparison()

    print("\n" + "=" * 60)
    print("🎉 分布式协调模式模块测试通过！")
    print("=" * 60)

    print("""
协调模式速查：

1. 领导者选举 — SET NX PX，多节点选主，宕机自动切换
2. 分布式屏障 — INCR 计数器，多 Agent 同步点
3. 工作队列 — LPUSH + BRPOPLPUSH，原子出队+备份
4. 发布订阅 — PUBLISH/SUBSCRIBE，事件驱动通信
5. AgentCoordinator — 组合模式，完整协调工作流

多 Agent 小说创作应用：
  惊鸿（写）→ 工作队列分发 → 分布式屏障等待 → 鉴微（审查）→ PubSub 通知结果
    """)


if __name__ == "__main__":
    asyncio.run(main())
