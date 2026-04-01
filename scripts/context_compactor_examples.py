#!/usr/bin/env python3
"""
ContextCompactor 使用示例

演示 microcompact 上下文压缩的三种使用方式：
1. Python API 调用
2. CLI 命令行使用
3. 集成到 Agent 系统
"""

import json
import sys
import time

sys.path.insert(0, "scripts")
from context_compactor import (
    ContextCompactor,
    MicrocompactConfig,
    CompactionStats,
    microcompact,
    microcompact_from_file,
    Message,
    ContentBlock,
)


# ═══════════════════════════════════════════════
# 示例 1: Python API 基础用法
# ═══════════════════════════════════════════════

def example_basic_api():
    """最简单的 API 调用方式。"""
    print("=" * 60)
    print("示例 1: Python API 基础用法")
    print("=" * 60)

    # 构造对话消息（模拟真实 Agent 对话）
    messages = [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "帮我读取 config.json 文件"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "name": "read", "id": "t1",
             "input": {"file_path": "config.json"}}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1",
             "content": json.dumps([{"app": "myapp", "version": "1.0"}] * 100)}
        ]},
        {"role": "assistant", "content": "配置文件内容已读取，版本为 1.0"},
        # 重复消息（会被合并）
        {"role": "user", "content": "帮我读取 config.json 文件"},
        {"role": "user", "content": "帮我读取 config.json 文件"},
        {"role": "assistant", "content": "好的，再次读取"},
    ]

    # 一行搞定
    compacted, stats = microcompact(messages)

    print(stats.summary())
    print(f"\n原始消息: {len(messages)} 条")
    print(f"压缩后:   {len(compacted)} 条")


# ═══════════════════════════════════════════════
# 示例 2: 自定义配置
# ═══════════════════════════════════════════════

def example_custom_config():
    """使用自定义配置进行压缩。"""
    print("\n" + "=" * 60)
    print("示例 2: 自定义配置")
    print("=" * 60)

    config = MicrocompactConfig(
        # 相似度阈值：80% 相同即视为重复
        similarity_threshold=0.80,
        # 超过 2000 tokens 的工具结果会被压缩
        max_tool_result_tokens=2000,
        # 保留压缩后头部 800 tokens
        tool_result_head_tokens=800,
        # 保留尾部 200 tokens
        tool_result_tail_tokens=200,
        # 时间触发：最后助手消息 30 分钟后触发清理
        time_based_enabled=True,
        gap_threshold_minutes=30.0,
        # 保留最近 3 个工具结果
        keep_recent_tool_results=3,
    )

    # 模拟大文本工具结果
    large_output = "\n".join(
        f"[LOG] Entry {i}: processing request with data payload"
        for i in range(500)
    )

    messages = [
        {"role": "user", "content": "查看日志文件"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "name": "bash", "id": "t1",
             "input": {"command": "cat app.log"}}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": large_output}
        ]},
        {"role": "assistant", "content": "日志显示正常运行。"},
    ]

    compacted, stats = microcompact(messages, config)
    print(stats.summary())

    # 查看压缩效果
    original_size = len(json.dumps(messages))
    compacted_size = len(json.dumps(compacted))
    print(f"\nJSON 大小: {original_size:,} → {compacted_size:,} bytes")
    print(f"压缩比: {compacted_size/original_size:.1%}")


# ═══════════════════════════════════════════════
# 示例 3: 文件操作模式
# ═══════════════════════════════════════════════

def example_file_operations():
    """从文件读取 → 压缩 → 写入文件。"""
    print("\n" + "=" * 60)
    print("示例 3: 文件操作")
    print("=" * 60)

    # 准备测试数据
    test_messages = [
        {"role": "user", "content": "Search for TODO comments"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "name": "grep", "id": "g1",
             "input": {"pattern": "TODO"}}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "g1",
             "content": "file.py:42: TODO: refactor this\n" * 30}
        ]},
        {"role": "assistant", "content": "Found 30 TODO comments."},
    ]

    # 写入临时文件
    input_file = "/tmp/test_messages.json"
    with open(input_file, "w") as f:
        json.dump(test_messages, f)

    # 压缩并输出
    stats = microcompact_from_file(
        input_path=input_file,
        output_path="/tmp/compacted_messages.json",
        config_path="scripts/context_compact_config.json",
    )

    print(stats.summary())


# ═══════════════════════════════════════════════
# 示例 4: 集成到 Agent 系统
# ═══════════════════════════════════════════════

class AgentContext:
    """模拟 Agent 上下文管理器，集成 microcompact。"""

    def __init__(self, config: MicrocompactConfig | None = None):
        self.messages: list[dict] = []
        self.compactor = ContextCompactor(config)
        self.total_tokens = 0
        self.compact_count = 0

    def add_message(self, role: str, content: str | list):
        """添加消息到上下文。"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })

    def check_and_compact(self, token_threshold: int = 10000) -> bool:
        """检查 token 使用量，超过阈值则压缩。

        Returns:
            True if compaction was performed.
        """
        # 估算当前 token 数
        compacted, stats = microcompact(self.messages, self.compactor.config)
        self.total_tokens = stats.tokens_before

        if self.total_tokens >= token_threshold:
            self.messages = compacted
            self.compact_count += 1
            print(f"[ContextCompactor] 第 {self.compact_count} 次压缩")
            print(stats.summary())
            return True
        return False

    def get_messages(self) -> list[dict]:
        """获取当前上下文消息。"""
        return self.messages


def example_agent_integration():
    """在 Agent 系统中集成 microcompact。"""
    print("\n" + "=" * 60)
    print("示例 4: Agent 系统集成")
    print("=" * 60)

    config = MicrocompactConfig(
        max_tool_result_tokens=3000,
        similarity_threshold=0.85,
    )
    ctx = AgentContext(config)

    # 模拟对话流
    ctx.add_message("system", "You are a helpful assistant.")

    for turn in range(5):
        ctx.add_message("user", f"帮我执行第 {turn+1} 个任务")

        # 模拟工具调用
        tool_output = f"任务 {turn+1} 执行结果：\n" + "详细输出...\n" * 200
        ctx.add_message("assistant", [
            {"type": "tool_use", "name": "bash", "id": f"t{turn}",
             "input": {"command": f"task_{turn}"}}
        ])
        ctx.add_message("user", [
            {"type": "tool_result", "tool_use_id": f"t{turn}",
             "content": tool_output}
        ])
        ctx.add_message("assistant", f"任务 {turn+1} 完成。")

        # 检查是否需要压缩
        ctx.check_and_compact(token_threshold=500)

    print(f"\n最终上下文: {len(ctx.get_messages())} 条消息")
    print(f"压缩次数: {ctx.compact_count}")


# ═══════════════════════════════════════════════
# 示例 5: Claude Code 风格的紧凑使用
# ═══════════════════════════════════════════════

def example_claude_code_style():
    """模拟 Claude Code 的 microcompact 调用方式。

    Claude Code 在 API 调用前自动运行 microcompact：
    1. 检查时间间隔（>1h → 清理旧结果）
    2. 检查 token 阈值（>180K → 触发压缩）
    3. 将压缩后的消息发送给 API
    """
    print("\n" + "=" * 60)
    print("示例 5: Claude Code 风格")
    print("=" * 60)

    def call_model(messages: list[dict]) -> dict:
        """模拟 API 调用，自动运行 microcompact。"""
        # Step 1: microcompact（Claude Code 的 microcompactMessages）
        compacted, stats = microcompact(messages)

        if stats.tokens_saved > 0:
            print(f"  [microcompact] 节省 {stats.tokens_saved:,} tokens")

        # Step 2: 检查是否需要 full compact
        if stats.tokens_after > 180_000:
            print("  [warning] 上下文仍过大，建议 full compact")

        # Step 3: 发送到 API
        return {"role": "assistant", "content": "Response from model"}

    # 模拟多次对话
    messages = [{"role": "system", "content": "You are a coding assistant."}]

    for i in range(3):
        messages.append({"role": "user", "content": f"Task {i+1}: do something"})
        messages.append({"role": "assistant", "content": [
            {"type": "tool_use", "name": "read", "id": f"r{i}",
             "input": {"file": f"file{i}.py"}}
        ]})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"r{i}",
             "content": f"def func{i}(): pass\n" * 100}
        ]})

        response = call_model(messages)
        messages.append(response)

    final_stats = microcompact(messages)[1]
    print(f"\n最终: {final_stats.original_message_count} → "
          f"{final_stats.compacted_message_count} messages")


# ═══════════════════════════════════════════════
# 运行所有示例
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    example_basic_api()
    example_custom_config()
    example_file_operations()
    example_agent_integration()
    example_claude_code_style()

    print("\n" + "=" * 60)
    print("所有示例运行完毕！")
    print("=" * 60)
