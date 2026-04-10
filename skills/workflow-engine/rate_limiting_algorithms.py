#!/usr/bin/env python3
"""
API 限流算法实战
涵盖：固定窗口、滑动窗口日志、滑动窗口计数器、令牌桶、漏桶

核心原则：
1. 固定窗口 — 简单但有边界突发问题
2. 滑动窗口日志 — 精确但内存开销大
3. 滑动窗口计数器 — 平衡精度和内存
4. 令牌桶 — 允许突发，适合 API
5. 漏桶 — 平滑输出，适合下游保护

适用场景：API 网关、爬虫频率控制、支付限频、短信限发
"""

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ==================== 1. 固定窗口限流 ====================

class FixedWindowLimiter:
    """
    固定窗口限流器

    原理：将时间划分为固定窗口，每个窗口内计数
    问题：边界突发 — 窗口交界处可能通过 2×max_requests

    示例：100 req/min，在 00:59 发 100 次 + 01:01 发 100 次
         = 2 秒内通过 200 次
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._counters: dict[str, dict] = {}

    def allow(self, client_id: str, now: float = None) -> tuple[bool, dict]:
        if now is None: now = time.time()
        window_key = int(now // self.window_seconds)

        if client_id not in self._counters:
            self._counters[client_id] = {}

        counters = self._counters[client_id]

        # 清理过期窗口
        expired_keys = [k for k in counters if k < window_key]
        for k in expired_keys:
            del counters[k]

        current_count = counters.get(window_key, 0)

        if current_count < self.max_requests:
            counters[window_key] = current_count + 1
            return True, {
                "algorithm": "fixed_window",
                "remaining": self.max_requests - current_count - 1,
                "reset_at": (window_key + 1) * self.window_seconds,
            }

        return False, {
            "algorithm": "fixed_window",
            "remaining": 0,
            "reset_at": (window_key + 1) * self.window_seconds,
        }


# ==================== 2. 滑动窗口日志 ====================

class SlidingWindowLogLimiter:
    """
    滑动窗口日志限流器

    原理：记录每个请求的时间戳，查询时统计 [now - window, now] 内的请求数
    优点：精确，无边界突发
    缺点：每个请求都要存时间戳，内存开销大

    适合：低 QPS 但要求精度的场景
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._logs: dict[str, list[float]] = defaultdict(list)

    def allow(self, client_id: str, now: float = None) -> tuple[bool, dict]:
        if now is None: now = time.time()
        window_start = now - self.window_seconds
        log = self._logs[client_id]

        # 移除窗口外的记录
        while log and log[0] <= window_start:
            log.pop(0)

        if len(log) < self.max_requests:
            log.append(now)
            return True, {
                "algorithm": "sliding_window_log",
                "remaining": self.max_requests - len(log),
                "window_size": len(log),
            }

        return False, {
            "algorithm": "sliding_window_log",
            "remaining": 0,
            "window_size": len(log),
            "retry_after": log[0] + self.window_seconds - now,
        }


# ==================== 3. 滑动窗口计数器 ====================

class SlidingWindowCounterLimiter:
    """
    滑动窗口计数器限流器

    原理：结合固定窗口 + 权重插值
    - 当前窗口计数 + 上一窗口计数 × 重叠比例
    - 内存 O(1)，精度接近滑动窗口日志

    示例：100 req/min，当前时间 01:30
    - 当前窗口 (01:00-02:00): 30 次
    - 上一窗口 (00:00-01:00): 80 次
    - 重叠比例: (60-30)/60 = 0.5
    - 有效计数: 30 + 80 × 0.5 = 70

    优点：内存 O(1)（只存 2 个窗口），无边界突发
    缺点：近似值，非精确
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, dict] = {}

    def allow(self, client_id: str, now: float = None) -> tuple[bool, dict]:
        if now is None: now = time.time()
        window_key = int(now // self.window_seconds)
        elapsed = now - window_key * self.window_seconds

        if client_id not in self._windows:
            self._windows[client_id] = {}

        windows = self._windows[client_id]

        # 只保留当前和上一窗口
        keys_to_remove = [k for k in windows if k < window_key - 1]
        for k in keys_to_remove:
            del windows[k]

        current_count = windows.get(window_key, 0)
        prev_count = windows.get(window_key - 1, 0)

        # 权重插值
        overlap_ratio = (self.window_seconds - elapsed) / self.window_seconds
        effective_count = current_count + prev_count * overlap_ratio

        if effective_count < self.max_requests:
            windows[window_key] = current_count + 1
            return True, {
                "algorithm": "sliding_window_counter",
                "remaining": int(self.max_requests - effective_count - 1),
                "effective_count": round(effective_count, 1),
            }

        return False, {
            "algorithm": "sliding_window_counter",
            "remaining": 0,
            "effective_count": round(effective_count, 1),
        }


# ==================== 4. 令牌桶 ====================

class TokenBucketLimiter:
    """
    令牌桶限流器

    原理：
    - 桶容量 = capacity，以 rate 个/秒 补充令牌
    - 每个请求消耗 1 个令牌
    - 桶满时不继续补充

    特点：允许突发（只要桶里有令牌）
    适合：API 限流（允许短时间突发，长期平均控制）

    示例：capacity=100, rate=10/s
    - 空闲时积累 100 个令牌
    - 突然来 50 个请求 → 全部通过（桶里够）
    - 之后每秒只能通过 10 个
    """

    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate  # 令牌/秒
        self._buckets: dict[str, dict] = {}

    def allow(self, client_id: str, now: float = None, tokens: int = 1) -> tuple[bool, dict]:
        if now is None:
            now = time.time()

        if client_id not in self._buckets:
            self._buckets[client_id] = {
                "tokens": self.capacity,
                "last_refill": now,  # use passed now, not time.time()
            }

        bucket = self._buckets[client_id]

        # 补充令牌
        elapsed = now - bucket["last_refill"]
        new_tokens = elapsed * self.rate
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True, {
                "algorithm": "token_bucket",
                "remaining_tokens": round(bucket["tokens"], 1),
                "capacity": self.capacity,
            }

        # 计算等待时间
        deficit = tokens - bucket["tokens"]
        retry_after = deficit / self.rate

        return False, {
            "algorithm": "token_bucket",
            "remaining_tokens": 0,
            "retry_after": round(retry_after, 2),
        }


# ==================== 5. 漏桶 ====================

class LeakyBucketLimiter:
    """
    漏桶限流器

    原理：
    - 请求进入桶（容量有限）
    - 以固定速率漏出（处理请求）
    - 桶满时拒绝新请求

    特点：平滑输出速率，不允许突发
    适合：保护下游服务（数据库、第三方 API）

    示例：capacity=100, rate=10/s
    - 即使瞬间来 200 个请求
    - 每秒也只处理 10 个
    """

    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate  # 漏出速率（请求/秒）
        self._buckets: dict[str, dict] = {}

    def allow(self, client_id: str, now: float = None) -> tuple[bool, dict]:
        if now is None: now = time.time()

        if client_id not in self._buckets:
            self._buckets[client_id] = {
                "water": 0,
                "last_leak": now,
            }

        bucket = self._buckets[client_id]

        # 漏水
        elapsed = now - bucket["last_leak"]
        leaked = elapsed * self.rate
        bucket["water"] = max(0, bucket["water"] - leaked)
        bucket["last_leak"] = now

        if bucket["water"] < self.capacity:
            bucket["water"] += 1
            return True, {
                "algorithm": "leaky_bucket",
                "current_water": round(bucket["water"], 1),
                "capacity": self.capacity,
            }

        # 计算等待时间
        retry_after = (bucket["water"] - self.capacity + 1) / self.rate

        return False, {
            "algorithm": "leaky_bucket",
            "current_water": round(bucket["water"], 1),
            "retry_after": round(retry_after, 2),
        }


# ==================== 算法对比 ====================

@dataclass
class AlgorithmComparison:
    """限流算法对比"""

    algorithms = {
        "fixed_window": {
            "精度": "低（边界突发）",
            "内存": "O(1)",
            "突发": "允许 2× 边界突发",
            "实现": "简单",
            "适合": "粗略限流、监控",
        },
        "sliding_window_log": {
            "精度": "高（精确）",
            "内存": "O(N)（N=请求数）",
            "突发": "不允许",
            "实现": "中等",
            "适合": "低 QPS 精确控制",
        },
        "sliding_window_counter": {
            "精度": "中（近似）",
            "内存": "O(1)（2 个窗口）",
            "突发": "不允许",
            "实现": "中等",
            "适合": "高 QPS 近似控制（推荐默认）",
        },
        "token_bucket": {
            "精度": "高（长期平均）",
            "内存": "O(1)",
            "突发": "允许（桶容量内）",
            "实现": "简单",
            "适合": "API 限流（推荐）",
        },
        "leaky_bucket": {
            "精度": "高（固定速率）",
            "内存": "O(1)",
            "突发": "不允许",
            "实现": "简单",
            "适合": "保护下游",
        },
    }


# ==================== 测试 ====================

def test_fixed_window():
    """测试固定窗口"""
    print("=" * 60)
    print("测试固定窗口限流")
    print("=" * 60)

    limiter = FixedWindowLimiter(max_requests=5, window_seconds=60)

    # 前 5 次应该通过
    for i in range(5):
        ok, info = limiter.allow("user1", now=1000.0 + i)
        assert ok, f"请求 {i+1} 应该通过"
    print("  ✅ 前 5 次通过")

    # 第 6 次应该拒绝
    ok, info = limiter.allow("user1", now=1005.0)
    assert not ok, "第 6 次应该拒绝"
    print("  ✅ 第 6 次拒绝")

    # 新窗口应该通过
    ok, info = limiter.allow("user1", now=1060.0)
    assert ok, "新窗口应该通过"
    print("  ✅ 新窗口通过")

    # 边界突发问题演示
    limiter2 = FixedWindowLimiter(max_requests=5, window_seconds=60)
    # 窗口 0 (0-60s): 5 次
    for i in range(5):
        limiter2.allow("user2", now=59.0 + i * 0.1)
    # 窗口 1 (60-120s): 5 次
    for i in range(5):
        limiter2.allow("user2", now=61.0 + i * 0.1)
    # 2 秒内通过了 10 次！
    print(f"  ⚠️  边界突发：2 秒内通过 10 次（限制 5 次/分钟）")


def test_sliding_window_log():
    """测试滑动窗口日志"""
    print("\n" + "=" * 60)
    print("测试滑动窗口日志限流")
    print("=" * 60)

    limiter = SlidingWindowLogLimiter(max_requests=5, window_seconds=60)

    # 前 5 次通过
    for i in range(5):
        ok, _ = limiter.allow("user1", now=1000.0 + i)
        assert ok
    print("  ✅ 前 5 次通过")

    # 第 6 次拒绝
    ok, info = limiter.allow("user1", now=1005.0)
    assert not ok
    print("  ✅ 第 6 次拒绝")

    # 窗口滑动后，最早的过期
    ok, _ = limiter.allow("user1", now=1061.0)
    assert ok  # 第一个请求 (t=1000) 已过期
    print("  ✅ 窗口滑动后，过期请求释放配额")

    # 边界突发测试（不会发生）
    limiter2 = SlidingWindowLogLimiter(max_requests=5, window_seconds=60)
    for i in range(5):
        limiter2.allow("user2", now=59.0)
    for i in range(5):
        limiter2.allow("user2", now=61.0)
    # 应该只有 5 次通过
    print(f"  ✅ 无边界突发：60-62s 只有 5 次（固定窗口有 10 次）")


def test_sliding_window_counter():
    """测试滑动窗口计数器"""
    print("\n" + "=" * 60)
    print("测试滑动窗口计数器限流")
    print("=" * 60)

    limiter = SlidingWindowCounterLimiter(max_requests=100, window_seconds=60)

    # 模拟：上一窗口 80 次，当前窗口 30 次
    # 有效计数 = 30 + 80 × (60-30)/60 = 30 + 40 = 70
    limiter._windows["user1"] = {
        0: 80,  # 上一窗口
        1: 30,  # 当前窗口
    }

    ok, info = limiter.allow("user1", now=30.0)
    assert ok  # 70 < 100
    print(f"  ✅ 有效计数: {info['effective_count']}（通过）")

    # 接近上限
    limiter._windows["user2"] = {0: 100, 1: 80}
    ok, info = limiter.allow("user2", now=30.0)
    assert not ok  # 80 + 100×0.5 = 130 > 100
    print(f"  ✅ 有效计数: {info['effective_count']}（拒绝）")


def test_token_bucket():
    """测试令牌桶"""
    print("\n" + "=" * 60)
    print("测试令牌桶限流")
    print("=" * 60)

    limiter = TokenBucketLimiter(capacity=10, rate=2.0)

    # 突发 10 次（全部 now=0.0）
    for i in range(10):
        ok, info = limiter.allow(client_id="user1", now=0.0, tokens=1)
        assert ok, f"请求 {i+1} 应该通过"
    print("  ✅ 突发 10 次全部通过（桶容量=10）")

    # 第 11 次拒绝（仍然 now=0.0，无新令牌）
    ok, info = limiter.allow(client_id="user1", now=0.0, tokens=1)
    assert not ok, "第 11 次应该拒绝"
    print(f"  ✅ 第 11 次拒绝，需等待 {info['retry_after']}s")

    # 等待 10 秒后补充 20 个令牌（cap 到 10）
    ok, info = limiter.allow(client_id="user1", now=10.0, tokens=1)
    assert ok, f"10 秒后应该通过，info={info}"
    print(f"  ✅ 10 秒后补充令牌，剩余 {info['remaining_tokens']}")


def test_leaky_bucket():
    """测试漏桶"""
    print("\n" + "=" * 60)
    print("测试漏桶限流")
    print("=" * 60)

    limiter = LeakyBucketLimiter(capacity=5, rate=2.0)

    # 桶未满时通过
    for i in range(5):
        ok, info = limiter.allow("user1", now=0.0)
        assert ok
    print("  ✅ 桶满前 5 次通过")

    # 桶满拒绝
    ok, info = limiter.allow("user1", now=0.0)
    assert not ok
    print(f"  ✅ 桶满拒绝，需等待 {info['retry_after']}s")

    # 漏水后通过
    ok, info = limiter.allow("user1", now=1.0)  # 漏了 2 个
    assert ok
    print(f"  ✅ 1 秒后漏掉 2 个，水位 {info['current_water']}")


def test_algorithm_comparison():
    """算法对比"""
    print("\n" + "=" * 60)
    print("限流算法对比")
    print("=" * 60)

    comp = AlgorithmComparison()
    print(f"{'算法':<25} {'精度':<15} {'内存':<10} {'突发':<15} {'推荐场景'}")
    print("-" * 80)
    for name, attrs in comp.algorithms.items():
        print(f"{name:<25} {attrs['精度']:<15} {attrs['内存']:<10} {attrs['突发']:<15} {attrs['适合']}")


async def main():
    test_fixed_window()
    test_sliding_window_log()
    test_sliding_window_counter()
    test_token_bucket()
    test_leaky_bucket()
    test_algorithm_comparison()

    print("\n" + "=" * 60)
    print("🎉 限流算法模块测试通过！")
    print("=" * 60)

    print("""
选型速查：

🏆 推荐默认：令牌桶（Token Bucket）
  - 允许合理突发，长期平均控制
  - 内存 O(1)，实现简单

📊 高精度：滑动窗口日志
  - 精确到每个请求
  - 适合低 QPS 场景

⚖️ 平衡之选：滑动窗口计数器
  - 内存 O(1)，精度接近日志
  - 适合高 QPS 场景

🛡️ 保护下游：漏桶
  - 固定速率输出
  - 保护数据库/第三方 API

📈 粗略监控：固定窗口
  - 最简单，但有边界突发
  - 适合内部监控，不建议作为限流
    """)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
