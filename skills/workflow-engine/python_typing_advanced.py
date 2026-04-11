#!/usr/bin/env python3
"""
Python 类型系统高级用法实战
涵盖：TypeGuard、Protocol、TypedDict、泛型、重载、运行时类型检查

核心原则：
1. TypeGuard — 运行时类型收窄，替代 assert isinstance
2. Protocol — 结构子类型（鸭子类型），替代继承
3. TypedDict — 字典类型安全，替代 dict[str, Any]
4. 泛型 — 参数化类型，替代 Any
5. 重载 — 多签名支持，替代 Union 分支

适用场景：所有 Python 项目，尤其工作流引擎模块
"""

import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    TypeVar,
    Union,
    overload,
)

# Python 3.8-3.9 兼容
if sys.version_info >= (3, 10):
    from typing import TypeAlias, TypeGuard
else:
    TypeAlias = Any
    # TypeGuard 兼容：Python 3.9 不支持 TypeGuard[T] 语法
    class _TypeGuardMeta(type):
        def __getitem__(cls, item):
            return bool
    class TypeGuard(metaclass=_TypeGuardMeta):
        pass

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, runtime_checkable
else:
    from typing_extensions import Literal, Protocol, runtime_checkable

if sys.version_info >= (3, 11):
    from typing import Self, TypedDict, assert_never
else:
    from typing import TypedDict


# ==================== 1. TypeGuard — 类型收窄 ====================

def is_db_error(error: Exception) -> TypeGuard[ConnectionError]:
    """
    类型守卫 — 判断是否为数据库连接错误

    使用场景：异常处理中收窄类型
    """
    return isinstance(error, ConnectionError)


def is_retryable_status(status: int) -> TypeGuard[Literal[408, 429, 500, 502, 503]]:
    """判断 HTTP 状态码是否可重试"""
    return status in (408, 429, 500, 502, 503)


def test_typeguard():
    """测试类型守卫"""
    print("=" * 60)
    print("测试 TypeGuard（类型守卫）")
    print("=" * 60)

    # 可重试状态码
    for status in [200, 408, 429, 500, 503]:
        if is_retryable_status(status):
            print(f"  ✅ {status} 可重试")
        else:
            print(f"  ❌ {status} 不可重试")

    # 异常分类
    err1 = ConnectionError("timeout")
    assert is_db_error(err1)
    print(f"  ✅ ConnectionError 被正确识别")

    err2 = ValueError("bad value")
    assert not is_db_error(err2)
    print(f"  ✅ ValueError 不被误判")


# ==================== 2. Protocol — 结构子类型 ====================

@runtime_checkable
class RetryableError(Protocol):
    """可重试错误协议 — 任何有 should_retry() 方法的对象"""

    def should_retry(self, attempt: int) -> bool: ...


@runtime_checkable
class CacheBackend(Protocol):
    """缓存后端协议 — 不依赖具体实现"""

    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...
    async def delete(self, key: str) -> bool: ...


class RedisCache:
    """Redis 缓存实现 — 自动满足 CacheBackend 协议"""

    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        pass

    async def delete(self, key: str) -> bool:
        return True


class MemoryCache:
    """内存缓存实现 — 也满足 CacheBackend 协议"""

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}

    async def get(self, key: str) -> Optional[str]:
        if key in self._store:
            value, expiry = self._store[key]
            if time.time() < expiry:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._store[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> bool:
        return bool(self._store.pop(key, None))


def get_cache(backend: str = "memory") -> CacheBackend:
    """工厂函数 — 返回满足协议的对象"""
    if backend == "redis":
        return RedisCache()
    return MemoryCache()


async def test_protocol():
    """测试 Protocol（结构子类型）"""
    print("\n" + "=" * 60)
    print("测试 Protocol（结构子类型）")
    print("=" * 60)

    cache = get_cache("memory")
    assert isinstance(cache, CacheBackend)
    print("  ✅ MemoryCache 满足 CacheBackend 协议")

    await cache.set("user:1", "Alice", ttl=60)
    value = await cache.get("user:1")
    assert value == "Alice"
    print(f"  ✅ 读写: user:1 = {value}")

    deleted = await cache.delete("user:1")
    assert deleted is True
    print(f"  ✅ 删除: {deleted}")

    # 过期测试
    await cache.set("temp", "data", ttl=0)
    import asyncio
    await asyncio.sleep(0.01)
    value = await cache.get("temp")
    assert value is None
    print("  ✅ TTL 过期正确")


# ==================== 3. TypedDict — 字典类型安全 ====================

class TaskInfo(TypedDict, total=False):
    """任务信息 — total=False 表示所有字段可选"""
    id: str
    name: str
    status: Literal["pending", "running", "completed", "failed"]
    priority: int
    created_at: str
    error: str


class ConnectionConfig(TypedDict):
    """连接配置 — total=True（默认）所有字段必填"""
    host: str
    port: int
    database: str
    timeout: float


def validate_task(info: dict) -> TaskInfo:
    """验证并收窄为 TaskInfo"""
    assert "id" in info or "name" in info, "至少需要一个字段"
    if "status" in info:
        assert info["status"] in ("pending", "running", "completed", "failed")
    return info  # type: ignore


def test_typeddict():
    """测试 TypedDict"""
    print("\n" + "=" * 60)
    print("测试 TypedDict")
    print("=" * 60)

    # 必填字段
    config: ConnectionConfig = {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "timeout": 30.0,
    }
    print(f"  ✅ 连接配置: {config}")

    # 可选字段
    task: TaskInfo = {
        "id": "task_001",
        "name": "生成章节",
        "status": "pending",
    }
    print(f"  ✅ 任务信息: {task}")

    # 验证
    validated = validate_task({"id": "t1", "status": "pending"})
    print(f"  ✅ 验证通过: {validated}")


# ==================== 4. 泛型 ====================

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Result(Generic[T]):
    """
    泛型结果类型 — 成功或失败

    替代：返回 (value, error) 元组
    """

    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self._value = value
        self._error = error

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(value=value)

    @classmethod
    def failure(cls, error: str) -> "Result[T]":
        return cls(error=error)

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def is_failure(self) -> bool:
        return self._error is not None

    def unwrap(self) -> T:
        if self._error:
            raise ValueError(f"Result is error: {self._error}")
        return self._value  # type: ignore

    def unwrap_or(self, default: T) -> T:
        return self._value if self._value is not None else default

    def map(self, fn: Callable[[T], T]) -> "Result[T]":
        if self.is_success:
            return Result.success(fn(self.unwrap()))
        return self

    def __repr__(self) -> str:
        if self.is_success:
            return f"Success({self._value!r})"
        return f"Failure({self._error!r})"


class TypedDict(Generic[K, V]):
    """类型安全字典"""

    def __init__(self):
        self._data: dict[K, V] = {}

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        return self._data.get(key, default)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def remove(self, key: K) -> Optional[V]:
        return self._data.pop(key, None)

    def __len__(self) -> int:
        return len(self._data)

    def keys(self) -> list[K]:
        return list(self._data.keys())


def test_generics():
    """测试泛型"""
    print("\n" + "=" * 60)
    print("测试泛型")
    print("=" * 60)

    # Result 类型
    ok: Result[int] = Result.success(42)
    assert ok.is_success
    assert ok.unwrap() == 42
    print(f"  ✅ Success: {ok}")

    err: Result[int] = Result.failure("DB connection failed")
    assert err.is_failure
    assert err.unwrap_or(0) == 0
    print(f"  ✅ Failure: {err}, unwrap_or(0) = {err.unwrap_or(0)}")

    # map 操作
    result = Result.success(10)
    mapped = result.map(lambda x: x * 2)
    assert mapped.unwrap() == 20
    print(f"  ✅ map(×2): {mapped}")

    # TypedDict
    td: TypedDict[str, int] = TypedDict()
    td.set("a", 1)
    td.set("b", 2)
    assert len(td) == 2
    assert td.get("a") == 1
    print(f"  ✅ TypedDict: len={len(td)}, keys={td.keys()}")


# ==================== 5. 重载 ====================

@overload
def parse_duration(value: int) -> str: ...


@overload
def parse_duration(value: str) -> int: ...


def parse_duration(value: Union[int, str]) -> Union[str, int]:
    """
    重载函数：
    - int → 格式化为字符串
    - str → 解析为秒数
    """
    if isinstance(value, int):
        if value < 60:
            return f"{value}s"
        elif value < 3600:
            return f"{value // 60}m{value % 60}s"
        else:
            return f"{value // 3600}h{(value % 3600) // 60}m"
    else:
        # 简单解析
        if value.endswith("h"):
            return int(value[:-1]) * 3600
        elif value.endswith("m"):
            return int(value[:-1]) * 60
        elif value.endswith("s"):
            return int(value[:-1])
        return int(value)


def test_overload():
    """测试重载"""
    print("\n" + "=" * 60)
    print("测试重载")
    print("=" * 60)

    # int → str
    assert parse_duration(30) == "30s"
    assert parse_duration(90) == "1m30s"
    assert parse_duration(3661) == "1h1m"
    print("  ✅ int → str: 30→30s, 90→1m30s, 3661→1h1m")

    # str → int
    assert parse_duration("30s") == 30
    assert parse_duration("5m") == 300
    assert parse_duration("2h") == 7200
    print("  ✅ str → int: 30s→30, 5m→300, 2h→7200")


# ==================== 6. 实战：类型安全的工作流配置 ====================

WorkflowStatus = Literal["pending", "running", "completed", "failed"]


class WorkflowConfig(TypedDict, total=False):
    """工作流配置"""
    name: str
    max_retries: int
    timeout: float
    parallel: bool
    status: WorkflowStatus


class WorkflowEngine(Generic[T]):
    """类型安全的工作流引擎"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self._results: dict[str, Result[T]] = {}

    def execute(self, task_id: str, fn: Callable[[], T]) -> Result[T]:
        """执行任务"""
        try:
            result = fn()
            self._results[task_id] = Result.success(result)
            return self._results[task_id]
        except Exception as exc:
            self._results[task_id] = Result.failure(str(exc))
            return self._results[task_id]

    def get_result(self, task_id: str) -> Optional[Result[T]]:
        return self._results.get(task_id)

    @property
    def stats(self) -> dict:
        success = sum(1 for r in self._results.values() if r.is_success)
        return {
            "total": len(self._results),
            "success": success,
            "failed": len(self._results) - success,
        }


def test_workflow_engine():
    """测试类型安全工作流引擎"""
    print("\n" + "=" * 60)
    print("测试类型安全工作流引擎")
    print("=" * 60)

    config: WorkflowConfig = {
        "name": "小说创作",
        "max_retries": 3,
        "timeout": 300.0,
        "parallel": True,
    }

    engine: WorkflowEngine[str] = WorkflowEngine(config)

    # 成功任务
    r1 = engine.execute("chapter_1", lambda: "穿越")
    assert r1.is_success
    assert r1.unwrap() == "穿越"
    print(f"  ✅ chapter_1: {r1}")

    # 失败任务
    def failing_task():
        raise RuntimeError("模拟失败")

    r2 = engine.execute("chapter_2", failing_task)
    assert r2.is_failure
    print(f"  ✅ chapter_2: {r2}")

    # 统计
    stats = engine.stats
    assert stats["total"] == 2
    assert stats["success"] == 1
    assert stats["failed"] == 1
    print(f"  ✅ 统计: {stats}")


# ==================== 测试入口 ====================

async def main():
    test_typeguard()
    await test_protocol()
    test_typeddict()
    test_generics()
    test_overload()
    test_workflow_engine()

    print("\n" + "=" * 60)
    print("🎉 Python 类型系统高级用法测试通过！")
    print("=" * 60)

    print("""
核心模式速查：

1. TypeGuard — 运行时类型收窄，替代 assert isinstance
2. Protocol — 结构子类型（鸭子类型），解耦依赖
3. TypedDict — 字典类型安全，替代 dict[str, Any]
4. 泛型 Result<T> — 成功/失败类型安全，替代 (value, error)
5. 重载 — 多签名支持，类型推断自动选择
6. 泛型容器 — TypedDict<K, V> 替代 dict
    """)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
