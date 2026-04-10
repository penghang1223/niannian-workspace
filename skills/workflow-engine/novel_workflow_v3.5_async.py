#!/usr/bin/env python3
"""
小说创作工作流 v3.5 - 异步并发模块
基于 novel_workflow_v3.py 的进度持久化，增加 asyncio 并发能力。

核心模式：
1. asyncio.gather(return_exceptions=True) — 并行处理多章节，单章失败不影响其他
2. asyncio.Semaphore — 控制并发度（模拟 pipeline max_parallel_chapters）
3. asyncio.TaskGroup — 结构化并发，所有任务成功才算成功
4. 指数退避重试 — 网络调用（飞书 API）失败自动重试
5. Fire-and-forget 安全模式 — 后台任务异常不丢失

适用场景：
- 多章节并行创作/审查
- 批量飞书文档操作
- 异步任务编排
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Coroutine, Optional, TypeVar

from novel_workflow_v3 import WorkflowProgress, IdempotentChecker, ChapterState

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ==================== 装饰器层 ====================

def async_retry(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    backoff_max: float = 30.0,
    exceptions: tuple = (Exception,)
):
    """
    异步重试装饰器 — 指数退避

    Args:
        max_retries: 最大重试次数
        backoff_base: 退避基数（秒）
        backoff_max: 最大退避时间（秒）
        exceptions: 需要重试的异常类型

    Usage:
        @async_retry(max_retries=3, backoff_base=2.0)
        async def create_feishu_doc(...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = min(backoff_base * (2 ** attempt), backoff_max)
                        logger.warning(
                            "%s 失败 (尝试 %d/%d): %s，%0.1fs 后重试",
                            func.__name__, attempt + 1, max_retries + 1, exc, delay
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "%s 失败，已重试 %d 次，放弃: %s",
                            func.__name__, max_retries, exc
                        )
            raise last_exc
        return wrapper
    return decorator


def async_safe_task(func):
    """
    Fire-and-forget 安全装饰器
    确保后台任务的异常被捕获并记录，不会静默丢失。

    Usage:
        @async_safe_task
        async def background_notify(...):
            ...

        # 调用后不 await，但异常会被记录
        asyncio.create_task(background_notify(...))
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("后台任务 %s 异常", func.__name__)
            return None
    return wrapper


# ==================== 并发控制层 ====================

class ConcurrencyLimiter:
    """
    信号量并发控制器 — 控制同时运行的任务数

    对应 v2 配置的 pipeline.max_parallel_chapters
    """

    def __init__(self, max_concurrent: int = 2):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self._active = 0
        self._completed = 0
        self._failed = 0

    async def run(self, coro: Coroutine[Any, Any, T]) -> Optional[T]:
        """在信号量控制下运行一个协程"""
        async with self.semaphore:
            self._active += 1
            try:
                result = await coro
                self._completed += 1
                return result
            except Exception as exc:
                self._failed += 1
                logger.error("任务失败: %s", exc)
                raise
            finally:
                self._active -= 1

    @property
    def stats(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "active": self._active,
            "completed": self._completed,
            "failed": self._failed,
        }


class ChapterPipeline:
    """
    章节并行流水线

    将 WorkflowProgress + ConcurrencyLimiter + IdempotentChecker 组合使用，
    实现多章节并发创作/审查。
    """

    def __init__(
        self,
        progress: WorkflowProgress,
        checker: IdempotentChecker,
        max_parallel: int = 2,
    ):
        self.progress = progress
        self.checker = checker
        self.limiter = ConcurrencyLimiter(max_concurrent=max_parallel)

    async def process_chapters(
        self,
        create_coro_factory: Callable[[int, str], Coroutine],
        status_prefix: str = "writing",
    ) -> dict:
        """
        并行处理所有待处理章节

        Args:
            create_coro_factory: 工厂函数 (chapter_num, title) -> coroutine
                返回一个异步协程，负责创建文档+更新进度
            status_prefix: 处理时的状态前缀

        Returns:
            {
                "total": int,
                "success": int,
                "failed": int,
                "skipped": int,
                "results": [...],
                "limiter_stats": {...}
            }
        """
        next_ch = self.progress.get_next_pending()
        if next_ch is None:
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0, "results": []}

        tasks = []
        # 获取所有待处理章节
        self.progress._ensure_loaded()
        pending_chapters = [
            ch for ch in self.progress.progress.chapters
            if ch["status"] in ("pending", "review_failed")
        ]

        results = []

        async def process_one(chapter: dict):
            ch_num = chapter["chapter_num"]
            title = chapter.get("title", f"第 {ch_num:02d} 章")

            # 幂等检查
            check = self.checker.before_create(ch_num, title)
            if not check["should_create"]:
                logger.info("跳过第 %d 章（已存在）", ch_num)
                return {"chapter": ch_num, "status": "skipped", "reason": check["reason"]}

            # 更新状态为处理中
            self.progress.update_chapter(ch_num, status_prefix)

            try:
                result = await create_coro_factory(ch_num, title)
                self.progress.update_chapter(
                    ch_num, "completed",
                    doc_url=result.get("doc_url", ""),
                    doc_id=result.get("doc_id", ""),
                    score=result.get("score"),
                )
                self.checker.register_created(
                    ch_num, title,
                    doc_id=result.get("doc_id", ""),
                    doc_url=result.get("doc_url", ""),
                )
                return {"chapter": ch_num, "status": "success", "result": result}
            except Exception as exc:
                self.progress.update_chapter(
                    ch_num, "review_failed",
                    last_error=str(exc)
                )
                return {"chapter": ch_num, "status": "failed", "error": str(exc)}

        # 用信号量控制并发度
        coros = [self.limiter.run(process_one(ch)) for ch in pending_chapters]
        all_results = await asyncio.gather(*coros, return_exceptions=True)

        success = sum(1 for r in all_results if isinstance(r, dict) and r.get("status") == "success")
        failed = sum(1 for r in all_results if isinstance(r, dict) and r.get("status") == "failed")
        skipped = sum(1 for r in all_results if isinstance(r, dict) and r.get("status") == "skipped")
        errors = sum(1 for r in all_results if isinstance(r, Exception))

        return {
            "total": len(pending_chapters),
            "success": success,
            "failed": failed + errors,
            "skipped": skipped,
            "results": all_results,
            "limiter_stats": self.limiter.stats,
        }


# ==================== 异步任务编排 ====================

async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float,
    fallback: T = None,
) -> T:
    """
    带超时的异步任务执行

    Usage:
        result = await run_with_timeout(
            create_feishu_doc(...),
            timeout_seconds=60.0,
            fallback={"doc_url": "", "error": "timeout"}
        )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning("任务超时 (%.1fs)", timeout_seconds)
        return fallback


async def sequential_with_rollback(
    coros: list[Coroutine[Any, Any, T]],
    rollback_fn: Callable[[int], Coroutine],
) -> list[T]:
    """
    顺序执行，失败时回滚已完成的任务

    Args:
        coros: 协程列表
        rollback_fn: 回滚函数 (index) -> coroutine

    Usage:
        # 创建 3 个飞书文档，如果第 2 个失败，回滚第 1 个
        results = await sequential_with_rollback(
            coros=[create_doc_1(), create_doc_2(), create_doc_3()],
            rollback_fn=lambda i: delete_doc(i)
        )
    """
    results = []
    for i, coro in enumerate(coros):
        try:
            result = await coro
            results.append(result)
        except Exception as exc:
            logger.error("第 %d 个任务失败，开始回滚: %s", i, exc)
            # 回滚已成功的
            for j in range(i):
                try:
                    await rollback_fn(j)
                    logger.info("已回滚第 %d 个任务", j)
                except Exception as rollback_exc:
                    logger.error("回滚第 %d 个任务失败: %s", j, rollback_exc)
            raise
    return results


# ==================== 测试 ====================

async def test_concurrency_limiter():
    """测试并发控制器"""
    print("=" * 60)
    print("测试 ConcurrencyLimiter")
    print("=" * 60)

    limiter = ConcurrencyLimiter(max_concurrent=2)

    async def slow_task(name: str, delay: float):
        async with limiter.semaphore:
            limiter._active += 1
            print(f"  ⏳ {name} 开始 (active={limiter._active})")
            await asyncio.sleep(delay)
            limiter._active -= 1
            print(f"  ✅ {name} 完成")
            return name

    # 同时启动 4 个任务，最多 2 并发
    print("\n[1] 4 任务，最多 2 并发...")
    results = await asyncio.gather(
        limiter.run(slow_task("A", 0.1)),
        limiter.run(slow_task("B", 0.15)),
        limiter.run(slow_task("C", 0.1)),
        limiter.run(slow_task("D", 0.05)),
        return_exceptions=True,
    )
    print(f"  结果: {results}")
    print(f"  统计: {limiter.stats}")
    assert limiter.stats["completed"] == 4
    assert limiter.stats["active"] == 0
    print("  ✅ 通过")


async def test_async_retry():
    """测试异步重试"""
    print("\n" + "=" * 60)
    print("测试 async_retry 装饰器")
    print("=" * 60)

    attempt_count = 0

    @async_retry(max_retries=3, backoff_base=0.01, backoff_max=0.05)
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"模拟失败 #{attempt_count}")
        return "success"

    print("\n[2] 重试 3 次后成功...")
    result = await flaky_function()
    assert result == "success"
    assert attempt_count == 3
    print(f"  ✅ 重试 {attempt_count} 次后成功")

    # 测试超过最大重试
    max_attempt = 0

    @async_retry(max_retries=2, backoff_base=0.01)
    async def always_fail():
        nonlocal max_attempt
        max_attempt += 1
        raise ValueError("永远失败")

    print("\n[3] 超过最大重试次数...")
    try:
        await always_fail()
        assert False, "应该抛出异常"
    except ValueError:
        print(f"  ✅ 重试 {max_attempt} 次后正确抛出异常")


async def test_run_with_timeout():
    """测试超时控制"""
    print("\n" + "=" * 60)
    print("测试 run_with_timeout")
    print("=" * 60)

    print("\n[4] 正常完成（不超时）...")
    async def fast_task():
        await asyncio.sleep(0.05)
        return "done"

    result = await run_with_timeout(fast_task(), timeout_seconds=1.0)
    assert result == "done"
    print("  ✅ 正常完成")

    print("\n[5] 超时返回 fallback...")
    async def slow_task():
        await asyncio.sleep(10)
        return "should not reach"

    result = await run_with_timeout(
        slow_task(),
        timeout_seconds=0.1,
        fallback={"error": "timeout"}
    )
    assert result == {"error": "timeout"}
    print("  ✅ 超时正确返回 fallback")


async def test_sequential_with_rollback():
    """测试顺序执行 + 回滚"""
    print("\n" + "=" * 60)
    print("测试 sequential_with_rollback")
    print("=" * 60)

    created = []
    rolled_back = []

    async def create(idx):
        created.append(idx)
        return f"created_{idx}"

    async def delete(idx):
        rolled_back.append(idx)

    print("\n[6] 全部成功，无回滚...")
    results = await sequential_with_rollback(
        coros=[create(0), create(1), create(2)],
        rollback_fn=delete,
    )
    assert results == ["created_0", "created_1", "created_2"]
    assert rolled_back == []
    print(f"  ✅ 全部成功: {results}")

    print("\n[7] 第 2 个失败，回滚前 2 个...")
    created.clear()
    rolled_back.clear()

    async def create_fail_2(idx):
        created.append(idx)
        if idx == 2:
            raise RuntimeError("模拟创建失败")
        return f"created_{idx}"

    try:
        await sequential_with_rollback(
            coros=[create_fail_2(0), create_fail_2(1), create_fail_2(2)],
            rollback_fn=delete,
        )
        assert False, "应该抛出异常"
    except RuntimeError:
        pass
    assert 0 in rolled_back and 1 in rolled_back
    print(f"  ✅ 已创建: {created}, 已回滚: {rolled_back}")


async def test_safe_task():
    """测试 fire-and-forget 安全模式"""
    print("\n" + "=" * 60)
    print("测试 async_safe_task")
    print("=" * 60)

    print("\n[8] 后台任务异常不会丢失...")
    error_logged = False

    class TestHandler(logging.Handler):
        def emit(self, record):
            nonlocal error_logged
            if record.levelno >= logging.ERROR:
                error_logged = True

    handler = TestHandler()
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)

    @async_safe_task
    async def bad_task():
        raise ValueError("后台任务异常")

    task = asyncio.create_task(bad_task())
    await task  # 异常已被捕获，不会抛出
    assert error_logged, "异常应该被记录到日志"
    print("  ✅ 后台任务异常被正确捕获并记录")

    logger.removeHandler(handler)


async def main():
    await test_concurrency_limiter()
    await test_async_retry()
    await test_run_with_timeout()
    await test_sequential_with_rollback()
    await test_safe_task()

    print("\n" + "=" * 60)
    print("🎉 所有异步并发测试通过！v3.5 模块可用")
    print("=" * 60)

    print("""
核心模式速查：

1. @async_retry — 网络调用自动重试（指数退避）
2. @async_safe_task — 后台任务异常不丢失
3. ConcurrencyLimiter — 信号量控制并发度
4. ChapterPipeline — 多章节并行处理
5. run_with_timeout — 超时控制 + fallback
6. sequential_with_rollback — 失败自动回滚
    """)


if __name__ == "__main__":
    asyncio.run(main())
