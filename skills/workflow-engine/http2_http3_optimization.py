#!/usr/bin/env python3
"""
HTTP/2 & HTTP/3 服务端性能优化实战
涵盖：多路复用、Server Push、头部压缩、0-RTT、连接复用、流控

核心原则：
1. HTTP/2 多路复用 — 单连接并行请求，消除队头阻塞
2. 头部压缩 (HPACK) — 减少冗余 header 开销
3. Server Push — 主动推送关键资源（HTTP/2）
4. 0-RTT 恢复 (HTTP/3/QUIC) — 首次连接也快速
5. 连接复用 — 减少 TLS 握手和 TCP 握手开销

适用场景：OPC Platform API 网关、高并发 Web 服务、移动端 API
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ==================== HTTP 版本特性对比 ====================

@dataclass
class HTTPVersionComparison:
    """HTTP 版本特性对比"""

    # 核心差异
    features = {
        "HTTP/1.1": {
            "connection": "串行请求（队头阻塞）",
            "header": "明文传输，无压缩",
            "tls": "TLS 1.2+，每次连接完整握手",
            "rtt_to_data": "2-3 RTT（TCP + TLS + 请求）",
            "multiplexing": "否",
            "server_push": "否",
            "stream_priority": "否",
            "flow_control": "TCP 级别（粗粒度）",
            "head_of_line_blocking": "是（TCP 层）",
            "connection_migration": "否",
            "typical_perf": "基准",
        },
        "HTTP/2": {
            "connection": "多路复用（单连接并行流）",
            "header": "HPACK 二进制压缩",
            "tls": "TLS 1.2+，Session Resumption 1-RTT",
            "rtt_to_data": "1-2 RTT（连接复用后 0 RTT）",
            "multiplexing": "是（Stream 级别）",
            "server_push": "是",
            "stream_priority": "是（权重 1-256）",
            "flow_control": "Stream 级别（细粒度）",
            "head_of_line_blocking": "是（TCP 丢包时）",
            "connection_migration": "否",
            "typical_perf": "比 HTTP/1.1 快 2-4x",
        },
        "HTTP/3": {
            "connection": "QUIC 多路复用（UDP 基础）",
            "header": "QPACK 改进版头部压缩",
            "tls": "TLS 1.3 内置，0-RTT 恢复",
            "rtt_to_data": "0-1 RTT（0-RTT 恢复）",
            "multiplexing": "是（QUIC Stream 级别）",
            "server_push": "是（改进版）",
            "stream_priority": "是",
            "flow_control": "QUIC Stream 级别",
            "head_of_line_blocking": "否（UDP，丢包不影响其他流）",
            "connection_migration": "是（Connection ID 迁移）",
            "typical_perf": "比 HTTP/2 快 1.5-3x（弱网）",
        },
    }


# ==================== 性能优化配置 ====================

@dataclass
class HTTP2Config:
    """HTTP/2 服务端优化配置"""

    # 连接配置
    max_concurrent_streams: int = 100     # 最大并发流数
    initial_window_size: int = 65535      # 初始窗口大小（64KB）
    max_frame_size: int = 16384           # 最大帧大小（16KB）
    max_header_list_size: int = 8192      # 最大头部大小（8KB）

    # 连接复用
    keepalive_timeout: int = 300          # 连接空闲超时（秒）
    keepalive_max_requests: int = 1000    # 单连接最大请求数
    h2c_upgrade: bool = True              # 允许 HTTP/1.1 → HTTP/2 升级

    # 流控优化
    connection_window_size: int = 1048576  # 连接级窗口（1MB）
    stream_window_size: int = 262144       # 流级窗口（256KB）

    # Server Push
    server_push_enabled: bool = False     # 默认关闭（需要客户端支持）
    push_resources: list = field(default_factory=list)  # 推送资源列表

    @property
    def tuning_notes(self) -> str:
        return f"""
调优建议：
- max_concurrent_streams: 根据 CPU 核数调整，推荐 CPU×20
- initial_window_size: 低延迟 API 用 64KB，大文件传输用 1MB+
- connection_window_size: = max_concurrent_streams × initial_window_size
- keepalive_timeout: API 服务 300s，长连接服务 3600s
- max_requests: 防内存泄漏，定期轮换连接
        """


# ==================== 连接池监控 ====================

class ConnectionMetrics:
    """
    HTTP/2 连接性能监控

    跟踪：连接数、流数、复用率、平均延迟
    """

    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.total_streams = 0
        self.active_streams = 0
        self.total_requests = 0
        self.reused_connections = 0
        self.pushed_resources = 0
        self._request_latencies: list[float] = []

    def record_request(self, latency_ms: float, reused: bool = False):
        """记录请求"""
        self.total_requests += 1
        self._request_latencies.append(latency_ms)
        if reused:
            self.reused_connections += 1

    def record_stream(self, opened: bool = True):
        """记录流"""
        if opened:
            self.total_streams += 1
            self.active_streams += 1
        else:
            self.active_streams -= 1

    def record_connection(self, opened: bool = True):
        """记录连接"""
        if opened:
            self.total_connections += 1
            self.active_connections += 1
        else:
            self.active_connections -= 1

    @property
    def avg_latency_ms(self) -> float:
        if not self._request_latencies:
            return 0
        return sum(self._request_latencies) / len(self._request_latencies)

    @property
    def p99_latency_ms(self) -> float:
        if not self._request_latencies:
            return 0
        sorted_latencies = sorted(self._request_latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    @property
    def reuse_ratio(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.reused_connections / self.total_requests

    @property
    def multiplexing_ratio(self) -> float:
        """复用率 = 总请求数 / 总连接数"""
        if self.total_connections == 0:
            return 0
        return self.total_requests / self.total_connections

    def report(self) -> dict:
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "total_streams": self.total_streams,
            "active_streams": self.active_streams,
            "total_requests": self.total_requests,
            "reuse_ratio": round(self.reuse_ratio, 4),
            "multiplexing_ratio": round(self.multiplexing_ratio, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
        }


# ==================== 服务端 Push 管理器 ====================

class ServerPushManager:
    """
    HTTP/2 Server Push 管理器

    推送关键资源，减少客户端 RTT
    注意：HTTP/2 Server Push 在现代浏览器中被弃用（Chrome 106+ 默认关闭）
    但仍然适用于：
    - 移动端 API（预推送下一个接口数据）
    - WebSocket 降级场景
    - 内部服务间通信
    """

    def __init__(self, max_pushes_per_connection: int = 10):
        self.max_pushes = max_pushes_per_connection
        self._push_count = 0
        self._pushed_paths: set[str] = set()

    def should_push(self, path: str) -> bool:
        """判断是否应该推送"""
        if self._push_count >= self.max_pushes:
            return False
        if path in self._pushed_paths:
            return False  # 已推送过
        return True

    def record_push(self, path: str):
        """记录推送"""
        self._push_count += 1
        self._pushed_paths.add(path)

    def reset(self):
        """重置（连接关闭时）"""
        self._push_count = 0
        self._pushed_paths.clear()


# ==================== 慢启动模拟 ====================

class SlowStartSimulator:
    """
    模拟 TCP 慢启动对 HTTP 性能的影响

    HTTP/1.1: 每次新连接都要经过慢启动
    HTTP/2: 连接复用避免重复慢启动
    HTTP/3: QUIC 0-RTT 跳过慢启动
    """

    def __init__(self, base_rtt_ms: float = 50.0, init_cwnd: int = 10):
        self.base_rtt_ms = base_rtt_ms
        self.init_cwnd = init_cwnd  # 初始拥塞窗口（10 个 MSS）
        self.mss = 1460  # 最大段大小（字节）

    def estimate_transfer_time(self, data_size: int, protocol: str) -> float:
        """
        估算传输时间

        Args:
            data_size: 数据大小（字节）
            protocol: "http1" / "http2" / "http3"
        """
        rtt = self.base_rtt_ms
        cwnd = self.init_cwnd * self.mss

        if protocol == "http1":
            # TCP 慢启动 + TLS 握手
            tcp_handshake = 1 * rtt        # TCP 3-way
            tls_handshake = 2 * rtt        # TLS 1.2 完整握手
            transfer_rounds = self._calc_slow_start_rounds(data_size, cwnd)
            transfer_time = transfer_rounds * rtt
            return tcp_handshake + tls_handshake + transfer_time

        elif protocol == "http2":
            # 连接复用时 0 RTT 握手
            transfer_rounds = self._calc_slow_start_rounds(data_size, cwnd)
            transfer_time = transfer_rounds * rtt
            return transfer_time  # 假设连接已建立

        elif protocol == "http3":
            # 0-RTT 恢复
            transfer_rounds = self._calc_slow_start_rounds(data_size, cwnd)
            transfer_time = transfer_rounds * rtt
            return max(0, transfer_time - rtt)  # 0-RTT 节省 1 RTT

        return 0

    def _calc_slow_start_rounds(self, data_size: int, cwnd: int) -> int:
        """计算慢启动轮数"""
        rounds = 0
        sent = 0
        while sent < data_size:
            rounds += 1
            sent += cwnd
            cwnd *= 2  # 指数增长
        return rounds


# ==================== 测试 ====================

def test_http_comparison():
    """测试 HTTP 版本对比"""
    print("=" * 60)
    print("HTTP 版本特性对比")
    print("=" * 60)

    comp = HTTPVersionComparison()
    for version, features in comp.features.items():
        print(f"\n📌 {version}")
        for key, value in features.items():
            print(f"  {key}: {value}")


def test_http2_config():
    """测试 HTTP/2 配置"""
    print("\n" + "=" * 60)
    print("HTTP/2 优化配置")
    print("=" * 60)

    config = HTTP2Config(max_concurrent_streams=200)
    print(config.tuning_notes)


def test_connection_metrics():
    """测试连接监控"""
    print("=" * 60)
    print("测试 ConnectionMetrics")
    print("=" * 60)

    metrics = ConnectionMetrics()

    # 模拟 5 个连接
    for i in range(5):
        metrics.record_connection(opened=True)

    # 模拟 50 个请求，其中 45 个复用连接
    for i in range(50):
        latency = 10 + (i % 20)  # 10-29ms
        metrics.record_request(latency, reused=(i >= 5))
        metrics.record_stream(opened=True)
        metrics.record_stream(opened=False)  # 立即关闭

    report = metrics.report()
    print(f"  总连接数: {report['total_connections']}")
    print(f"  总请求数: {report['total_requests']}")
    print(f"  连接复用率: {report['reuse_ratio']}")
    print(f"  多路复用比: {report['multiplexing_ratio']}")
    print(f"  平均延迟: {report['avg_latency_ms']}ms")
    print(f"  P99 延迟: {report['p99_latency_ms']}ms")

    assert report["reuse_ratio"] == 0.9
    assert report["total_requests"] == 50
    assert report["total_connections"] == 5
    print("  ✅ 监控数据正确")


def test_server_push():
    """测试 Server Push 管理"""
    print("\n" + "=" * 60)
    print("测试 ServerPushManager")
    print("=" * 60)

    push_mgr = ServerPushManager(max_pushes_per_connection=3)

    assert push_mgr.should_push("/api/config") is True
    push_mgr.record_push("/api/config")

    assert push_mgr.should_push("/api/config") is False  # 已推送
    assert push_mgr.should_push("/api/users") is True
    push_mgr.record_push("/api/users")

    assert push_mgr.should_push("/api/products") is True
    push_mgr.record_push("/api/products")

    assert push_mgr.should_push("/api/orders") is False  # 超过限制
    print("  ✅ Push 管理逻辑正确")

    push_mgr.reset()
    assert push_mgr.should_push("/api/config") is True  # 重置后可推送
    print("  ✅ 重置后正常")


def test_slow_start():
    """测试慢启动模拟"""
    print("\n" + "=" * 60)
    print("测试 SlowStartSimulator")
    print("=" * 60)

    sim = SlowStartSimulator(base_rtt_ms=50.0)

    # 小数据（10KB）
    for proto in ["http1", "http2", "http3"]:
        t = sim.estimate_transfer_time(10_240, proto)
        print(f"  10KB via {proto}: {t:.0f}ms")

    # 大数据（1MB）
    print()
    for proto in ["http1", "http2", "http3"]:
        t = sim.estimate_transfer_time(1_048_576, proto)
        print(f"  1MB via {proto}: {t:.0f}ms")

    # 验证 HTTP/3 < HTTP/2 < HTTP/1.1
    t1 = sim.estimate_transfer_time(100_000, "http1")
    t2 = sim.estimate_transfer_time(100_000, "http2")
    t3 = sim.estimate_transfer_time(100_000, "http3")

    assert t1 > t2, "HTTP/2 应该比 HTTP/1.1 快"
    assert t2 > t3, "HTTP/3 应该比 HTTP/2 快（0-RTT）"
    print(f"\n  ✅ 性能排序正确: HTTP/1.1 ({t1:.0f}ms) > HTTP/2 ({t2:.0f}ms) > HTTP/3 ({t3:.0f}ms)")


async def main():
    test_http_comparison()
    test_http2_config()
    test_connection_metrics()
    test_server_push()
    test_slow_start()

    print("\n" + "=" * 60)
    print("🎉 HTTP/2 & HTTP/3 性能优化模块测试通过！")
    print("=" * 60)

    print("""
核心模式速查：

1. 连接复用 — 避免重复 TCP+TLS 握手（省 2-3 RTT）
2. 多路复用 — 单连接并行请求，消除队头阻塞
3. HPACK 头部压缩 — 减少冗余 header 开销
4. Server Push — 主动推送关键资源（现代浏览器已弃用）
5. HTTP/3 0-RTT — QUIC 内置 TLS 1.3，首次也快速
6. 流控优化 — Stream 级别窗口，细粒度控制
    """)


if __name__ == "__main__":
    asyncio.run(main())
