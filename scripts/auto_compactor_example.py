#!/usr/bin/env python3
"""
Auto Compactor 使用示例
演示如何在对话系统中集成自动压缩功能
"""

import sys
import json
sys.path.insert(0, ".")

from scripts.auto_compactor import AutoCompactor, compact_conversation, estimate_messages_tokens


# =====================================================================
# 示例 1: 基础用法 — 每轮对话后检查并自动压缩
# =====================================================================

def example_basic():
    """最基本的用法：创建压缩器，每次对话轮次后检查"""
    compactor = AutoCompactor(config_path="auto_compact_config.json")

    # 模拟对话
    messages = [
        {"role": "user", "content": "帮我写一个 Python 的快速排序"},
        {"role": "assistant", "content": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    ..."},
        {"role": "user", "content": "能加个归并排序对比吗"},
        {"role": "assistant", "content": "def mergesort(arr):\n    ..."},
    ]

    # 每轮对话后检查
    messages, result = compactor.check_and_compact(messages)
    if result:
        print(f"✅ 压缩完成: {result.pre_compact_tokens} → {result.post_compact_tokens} tokens")
    else:
        print(f"ℹ️ 未压缩，当前 token: {estimate_messages_tokens(messages)}")


# =====================================================================
# 示例 2: 带自定义摘要指令
# =====================================================================

def example_custom_instructions():
    """针对特定场景定制摘要指令"""
    compactor = AutoCompactor(config_path="auto_compact_config.json")

    messages = _make_long_conversation()

    # 自定义指令：关注代码变更和错误
    custom = (
        "When summarizing, focus on code changes and errors encountered. "
        "Include full code snippets for all modified files."
    )

    messages, result = compactor.check_and_compact(
        messages, custom_instructions=custom
    )
    if result:
        print(f"摘要:\n{result.summary[:300]}...")


# =====================================================================
# 示例 3: 强制压缩（不检查阈值）
# =====================================================================

def example_force_compact():
    """强制压缩 — 用于手动触发或调试"""
    messages = _make_long_conversation()

    messages, result = compact_conversation(
        messages,
        config_path="auto_compact_config.json",
        force=True,
    )
    if result:
        print(f"强制压缩: {result.pre_compact_tokens} → {result.post_compact_tokens}")
        print(f"摘要长度: {len(result.summary)} 字符")


# =====================================================================
# 示例 4: 上下文分析（不压缩，只看统计）
# =====================================================================

def example_analyze():
    """分析上下文 token 分布，帮助调优压缩策略"""
    compactor = AutoCompactor()
    messages = _make_long_conversation()

    # Token 使用情况
    usage = compactor.get_token_usage(messages)
    print("=== Token 使用 ===")
    print(f"  总计: {usage['total_tokens']:,} / {usage['max_tokens']:,}")
    print(f"  使用率: {usage['usage_ratio']:.1%}")
    print(f"  压缩阈值: {usage['compact_threshold']:,}")
    print(f"  需要压缩: {usage['needs_compaction']}")

    # 上下文分析
    stats = compactor.analyze_context(messages)
    print("\n=== 上下文分析 ===")
    print(f"  用户消息: {stats['user_messages_tokens']:,} tokens")
    print(f"  助手消息: {stats['assistant_messages_tokens']:,} tokens")
    print(f"  工具请求: {stats['tool_requests_tokens']:,} tokens ({stats['tool_request_count']} 次)")
    print(f"  工具结果: {stats['tool_results_tokens']:,} tokens ({stats['tool_result_count']} 次)")


# =====================================================================
# 示例 5: 集成到对话循环中
# =====================================================================

def example_conversation_loop():
    """模拟真实的对话循环，自动压缩"""
    compactor = AutoCompactor(config_path="auto_compact_config.json")
    messages = []
    system_prompt = "You are a helpful coding assistant."

    # 模拟 100 轮对话
    for turn in range(100):
        # 用户消息
        user_msg = {"role": "user", "content": f"Turn {turn}: 帮我修改这个函数" + " x" * 50}
        messages.append(user_msg)

        # 助手回复（模拟）
        assistant_msg = {"role": "assistant", "content": f"好的，第 {turn} 轮修改如下:" + " y" * 80}
        messages.append(assistant_msg)

        # ✅ 关键：每轮检查是否需要压缩
        messages, result = compactor.check_and_compact(messages, system_prompt)
        if result:
            print(f"  🔄 Turn {turn}: 压缩! {result.pre_compact_tokens:,} → {result.post_compact_tokens:,} tokens")

    print(f"\n最终消息数: {len(messages)}")
    print(f"压缩统计: {compactor.stats}")


# =====================================================================
# 示例 6: 在现有 Agent 系统中集成
# =====================================================================

def example_agent_integration():
    """在 Agent 对话系统中集成 AutoCompactor"""

    class SimpleAgent:
        def __init__(self):
            self.compactor = AutoCompactor(config_path="auto_compact_config.json")
            self.messages = []
            self.system = "You are a helpful assistant."

        def chat(self, user_input: str) -> str:
            # 添加用户消息
            self.messages.append({"role": "user", "content": user_input})

            # 🔍 检查是否需要压缩（在调用 LLM 之前）
            self.messages, compact_result = self.compactor.check_and_compact(
                self.messages, self.system
            )

            if compact_result:
                print(f"  [压缩] {compact_result.pre_compact_tokens} → {compact_result.post_compact_tokens}")

            # 调用 LLM（这里简化）
            response = f"Response to: {user_input[:50]}"
            self.messages.append({"role": "assistant", "content": response})
            return response

    agent = SimpleAgent()
    for i in range(200):
        reply = agent.chat(f"Question {i}: " + "context " * 30)
        if i % 50 == 0:
            print(f"Turn {i}: {len(agent.messages)} messages, stats: {agent.compactor.stats}")


# =====================================================================
# Helpers
# =====================================================================

def _make_long_conversation(n: int = 60) -> list[dict]:
    """生成模拟长对话"""
    messages = []
    for i in range(n):
        messages.append({
            "role": "user",
            "content": f"问题 {i+1}：请帮我分析这段代码的性能问题。" + "上下文内容。" * 25,
        })
        messages.append({
            "role": "assistant",
            "content": f"分析结果 {i+1}：这段代码存在以下性能瓶颈。" + "详细分析。" * 35,
        })
    return messages


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto Compactor 使用示例")
    parser.add_argument("example", nargs="?", default="basic",
                        choices=["basic", "custom", "force", "analyze", "loop", "agent"],
                        help="运行哪个示例")
    args = parser.parse_args()

    examples = {
        "basic": ("基础用法", example_basic),
        "custom": ("自定义指令", example_custom_instructions),
        "force": ("强制压缩", example_force_compact),
        "analyze": ("上下文分析", example_analyze),
        "loop": ("对话循环", example_conversation_loop),
        "agent": ("Agent 集成", example_agent_integration),
    }

    title, func = examples[args.example]
    print(f"{'='*60}")
    print(f"  示例: {title}")
    print(f"{'='*60}\n")
    func()
