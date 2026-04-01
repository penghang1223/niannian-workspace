"""
StreamingToolExecutor 使用示例

演示如何使用流式并行工具执行器:
1. 基础用法 — 并行执行多个工具
2. 流式检测 — 模拟从 LLM 流式响应中检测工具调用
3. 错误隔离 — 一个工具失败不影响其他
4. 并发控制 — 非并发工具独占执行
"""

import asyncio
import json
import logging
import time
from typing import Any

from streaming_executor import (
    StreamingToolDetector,
    StreamingToolExecutor,
    ToolBlock,
    ToolDefinition,
    ToolResult,
    create_tool_block,
    create_tool_definition,
    load_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── 示例工具执行函数 ─────────────────────────────────────────────────────

async def execute_read_file(block: ToolBlock) -> ToolResult:
    """模拟文件读取工具"""
    file_path = block.input.get("file_path", "unknown")
    logger.info(f"📖 读取文件: {file_path}")
    await asyncio.sleep(0.3)  # 模拟 I/O 延迟
    return ToolResult(
        tool_use_id=block.id,
        tool_name="read_file",
        content=f"文件内容: {file_path} 的内容...",
    )


async def execute_web_search(block: ToolBlock) -> ToolResult:
    """模拟网络搜索工具"""
    query = block.input.get("query", "")
    logger.info(f"🔍 搜索: {query}")
    await asyncio.sleep(0.5)  # 模拟网络延迟
    return ToolResult(
        tool_use_id=block.id,
        tool_name="web_search",
        content=f"搜索结果: 关于 '{query}' 的 3 条结果...",
    )


async def execute_bash(block: ToolBlock) -> ToolResult:
    """模拟 Bash 命令执行（非并发安全）"""
    command = block.input.get("command", "")
    logger.info(f"⚡ 执行命令: {command}")
    await asyncio.sleep(0.2)

    # 模拟某些命令失败
    if "fail" in command:
        return ToolResult(
            tool_use_id=block.id,
            tool_name="bash",
            content=f"命令执行失败: {command}",
            is_error=True,
            error_message="命令返回非零退出码",
        )

    return ToolResult(
        tool_use_id=block.id,
        tool_name="bash",
        content=f"命令输出: {command} -> OK",
    )


async def execute_write_file(block: ToolBlock) -> ToolResult:
    """模拟文件写入（非并发安全 — 避免写同一文件冲突）"""
    file_path = block.input.get("file_path", "")
    content = block.input.get("content", "")
    logger.info(f"✏️ 写入文件: {file_path}")
    await asyncio.sleep(0.4)
    return ToolResult(
        tool_use_id=block.id,
        tool_name="write_file",
        content=f"已写入 {len(content)} 字节到 {file_path}",
    )


async def execute_slow_tool(block: ToolBlock) -> ToolResult:
    """模拟慢工具（用于测试超时）"""
    delay = block.input.get("delay", 2)
    logger.info(f"🐢 慢工具执行中 (延迟 {delay}s)...")
    await asyncio.sleep(delay)
    return ToolResult(
        tool_use_id=block.id,
        tool_name="slow_tool",
        content=f"慢工具完成 (耗时 {delay}s)",
    )


# ─── 工具注册表 ───────────────────────────────────────────────────────────

def create_tool_registry() -> dict:
    """创建工具注册表"""
    return {
        "read_file": create_tool_definition(
            name="read_file",
            executor=execute_read_file,
            description="读取文件内容",
            is_concurrency_safe=True,  # 读操作可并行
        ),
        "web_search": create_tool_definition(
            name="web_search",
            executor=execute_web_search,
            description="网络搜索",
            is_concurrency_safe=True,  # 搜索可并行
        ),
        "bash": create_tool_definition(
            name="bash",
            executor=execute_bash,
            description="执行 Bash 命令",
            is_concurrency_safe=False,  # Bash 命令不可并行（可能有依赖关系）
        ),
        "write_file": create_tool_definition(
            name="write_file",
            executor=execute_write_file,
            description="写入文件",
            is_concurrency_safe=False,  # 写操作不可并行（避免冲突）
        ),
        "slow_tool": create_tool_definition(
            name="slow_tool",
            executor=execute_slow_tool,
            description="慢工具（测试用）",
            is_concurrency_safe=True,
            timeout=5.0,  # 5 秒超时
        ),
    }


# ─── 示例 1: 基础并行执行 ────────────────────────────────────────────────

async def example_basic_parallel():
    """示例 1: 多个并发安全的工具并行执行"""
    print("\n" + "=" * 60)
    print("📌 示例 1: 基础并行执行")
    print("=" * 60)

    tools = create_tool_registry()
    executor = StreamingToolExecutor(tools)

    # 同时添加 3 个并发安全的工具
    executor.add_tool(create_tool_block("read_file", {"file_path": "/src/main.py"}))
    executor.add_tool(create_tool_block("read_file", {"file_path": "/src/utils.py"}))
    executor.add_tool(create_tool_block("web_search", {"query": "Python async best practices"}))

    print(f"\n已添加 {executor.tool_count} 个工具，等待执行...\n")

    # 收集结果
    start = time.monotonic()
    results = []
    async for update in executor.get_results():
        if update.result:
            results.append(update.result)
            status = "❌" if update.result.is_error else "✅"
            print(f"  {status} [{update.result.tool_name}] {update.result.content[:60]}")
        elif update.progress:
            print(f"  ⏳ 进度: {update.progress.message}")

    elapsed = (time.monotonic() - start) * 1000
    print(f"\n📊 完成: {len(results)} 个结果, 总耗时 {elapsed:.0f}ms")
    print(f"   统计: {executor.get_stats()}")


# ─── 示例 2: 流式检测模拟 ────────────────────────────────────────────────

async def example_streaming_detection():
    """示例 2: 模拟从 LLM 流式响应中检测工具调用"""
    print("\n" + "=" * 60)
    print("📌 示例 2: 流式检测模拟")
    print("=" * 60)

    tools = create_tool_registry()
    executor = StreamingToolExecutor(tools)
    detector = StreamingToolDetector(executor)

    # 模拟 LLM 流式输出的 chunks（实际使用中从 API 流读取）
    chunks = [
        '好的，我来帮你查看这些文件。首先',
        '让我读取项目结构...\n',
        '{"type": "tool_use", "id": "toolu_001", "name": "read_file", "input": {"file_path": "/project/README.md"}}',
        '\n然后搜索相关文档...\n',
        '{"type": "tool_use", "id": "toolu_002", "name": "web_search", "input": {"query": "Python project structure best practices"}}',
        '\n最后检查依赖文件...\n',
        '{"type": "tool_use", "id": "toolu_003", "name": "read_file", "input": {"file_path": "/project/requirements.txt"}}',
    ]

    print("\n模拟流式输入:")
    detected_tools = []
    for i, chunk in enumerate(chunks):
        print(f"  chunk[{i}]: {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
        detected = detector.feed(chunk)
        detected_tools.extend(detected)
        if detected:
            for t in detected:
                print(f"    🎯 检测到工具: {t.name} (id={t.id})")
        await asyncio.sleep(0.05)  # 模拟流式延迟

    print(f"\n共检测到 {len(detected_tools)} 个工具调用")

    # 收集结果
    results = []
    async for update in executor.get_results():
        if update.result:
            results.append(update.result)
            status = "❌" if update.result.is_error else "✅"
            print(f"  {status} [{update.result.tool_name}] {update.result.content[:60]}")

    print(f"\n📊 完成: {len(results)} 个结果")


# ─── 示例 3: 错误隔离 ────────────────────────────────────────────────────

async def example_error_isolation():
    """示例 3: 错误隔离 — Bash 错误取消其他 Bash 并发，但不影响读取"""
    print("\n" + "=" * 60)
    print("📌 示例 3: 错误隔离")
    print("=" * 60)

    tools = create_tool_registry()
    config = load_config()  # 使用默认配置（bash_error_cascades=true）
    executor = StreamingToolExecutor(tools, config=config)

    # 添加多个工具，其中一个会失败
    executor.add_tool(create_tool_block("bash", {"command": "mkdir /tmp/test"}))
    executor.add_tool(create_tool_block("bash", {"command": "fail-command"}))  # 会失败
    executor.add_tool(create_tool_block("bash", {"command": "echo done"}))  # 会被取消
    # 注意: read_file 是并发安全的，不受 bash 级联影响

    print("\n执行中（其中一个 bash 会失败）...\n")

    results = []
    async for update in executor.get_results():
        if update.result:
            results.append(update.result)
            status = "❌" if update.result.is_error else "✅"
            error_info = f" (错误: {update.result.error_message})" if update.result.is_error else ""
            print(f"  {status} [{update.result.tool_name}] {update.result.content[:50]}{error_info}")

    print(f"\n📊 结果: {len(results)} 个, "
          f"成功 {sum(1 for r in results if not r.is_error)}, "
          f"失败 {sum(1 for r in results if r.is_error)}")


# ─── 示例 4: 并发控制（非并发工具独占） ─────────────────────────────────

async def example_concurrency_control():
    """示例 4: 非并发工具独占执行，并发工具在其前后并行"""
    print("\n" + "=" * 60)
    print("📌 示例 4: 并发控制")
    print("=" * 60)

    tools = create_tool_registry()
    executor = StreamingToolExecutor(tools, config={"max_concurrent_tools": 3})

    # 添加顺序: 2个并发安全 → 1个非并发安全 → 1个并发安全
    executor.add_tool(create_tool_block("read_file", {"file_path": "/a.py"}))
    executor.add_tool(create_tool_block("read_file", {"file_path": "/b.py"}))
    executor.add_tool(create_tool_block("write_file", {"file_path": "/out.txt", "content": "data"}))  # 非并发
    executor.add_tool(create_tool_block("web_search", {"query": "async"}))

    print("\n工具执行顺序（write_file 会独占执行）:\n")

    results = []
    start = time.monotonic()
    async for update in executor.get_results():
        if update.result:
            results.append(update.result)
            t = time.monotonic() - start
            safe = "🟢并发" if update.result.tool_name in ("read_file", "web_search") else "🔴独占"
            print(f"  [{t:.2f}s] {safe} {update.result.tool_name}: {update.result.content[:40]}")

    print(f"\n📊 完成: {len(results)} 个结果")


# ─── 示例 5: 超时和重试 ─────────────────────────────────────────────────

async def example_timeout_retry():
    """示例 5: 超时控制和自动重试"""
    print("\n" + "=" * 60)
    print("📌 示例 5: 超时和重试")
    print("=" * 60)

    tools = create_tool_registry()
    # 配置短超时来触发超时
    config = {"tool_timeout_seconds": 1, "retry_max_attempts": 1, "retry_delay_seconds": 0.5}
    executor = StreamingToolExecutor(tools, config=config)

    # 添加一个会超时的工具
    executor.add_tool(create_tool_block("slow_tool", {"delay": 3}))  # 3秒延迟，超时1秒
    executor.add_tool(create_tool_block("read_file", {"file_path": "/quick.py"}))  # 快速完成

    print("\n执行中（slow_tool 会超时并重试）...\n")

    results = []
    async for update in executor.get_results():
        if update.progress:
            print(f"  ⏳ {update.progress.message}")
        if update.result:
            results.append(update.result)
            status = "❌" if update.result.is_error else "✅"
            print(f"  {status} [{update.result.tool_name}] {update.result.content[:60]}")

    print(f"\n📊 结果: {len(results)} 个")


# ─── 主入口 ───────────────────────────────────────────────────────────────

async def main():
    print("🚀 StreamingToolExecutor 流式并行工具执行器演示")
    print("   参考 Claude Code 的 StreamingToolExecutor 实现\n")

    await example_basic_parallel()
    await example_streaming_detection()
    await example_error_isolation()
    await example_concurrency_control()
    await example_timeout_retry()

    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
