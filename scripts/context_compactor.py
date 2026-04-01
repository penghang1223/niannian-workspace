#!/usr/bin/env python3
"""
Context Compactor — Microcompact 上下文压缩机制

参考 Claude Code (tengu) 的 microcompact 实现：
- 检测重复消息（相同 role + 相似内容）→ 合并
- 合并连续的工具调用结果
- 压缩长文本（保留关键信息）
- 基于时间的旧工具结果清理
- 基于 token 阈值的自动压缩触发

Architecture:
  ┌──────────────────────────────────────────────┐
  │              microcompactMessages             │
  │  ┌────────────────────────────────────────┐  │
  │  │  1. Time-based MC (timeBasedMC)        │  │
  │  │     gap > 60min → clear old results    │  │
  │  ├────────────────────────────────────────┤  │
  │  │  2. Duplicate Detection                │  │
  │  │     same role + similar content → merge│  │
  │  ├────────────────────────────────────────┤  │
  │  │  3. Tool Result Grouping               │  │
  │  │     consecutive tool_results → merge   │  │
  │  ├────────────────────────────────────────┤  │
  │  │  4. Long Text Compression              │  │
  │  │     truncate + keep head/tail          │  │
  │  └────────────────────────────────────────┘  │
  └──────────────────────────────────────────────┘
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Data Models (mirrors Claude Code's Message types)
# ──────────────────────────────────────────────

Role = Literal["system", "user", "assistant"]


@dataclass
class ContentBlock:
    """Single content block within a message."""

    type: str  # "text", "tool_use", "tool_result", "image", "thinking"
    text: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    content: Any = None  # tool_result content
    input: dict | None = None  # tool_use input
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"type": self.type}
        if self.text is not None:
            d["text"] = self.text
        if self.tool_use_id is not None:
            d["tool_use_id"] = self.tool_use_id
        if self.tool_name is not None:
            d["name"] = self.tool_name
        if self.content is not None:
            d["content"] = self.content
        if self.input is not None:
            d["input"] = self.input
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ContentBlock":
        return cls(
            type=d.get("type", "text"),
            text=d.get("text"),
            tool_use_id=d.get("tool_use_id"),
            tool_name=d.get("name"),
            content=d.get("content"),
            input=d.get("input"),
        )


@dataclass
class Message:
    """A single message in the conversation."""

    role: Role
    content: str | list[ContentBlock]
    timestamp: float = 0.0
    message_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.message_id is None:
            self.message_id = self._generate_id()

    def _generate_id(self) -> str:
        raw = f"{self.role}:{self.content!r}:{self.timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @property
    def content_blocks(self) -> list[ContentBlock]:
        if isinstance(self.content, str):
            return [ContentBlock(type="text", text=self.content)]
        return self.content

    @property
    def text_content(self) -> str:
        blocks = self.content_blocks
        return "\n".join(
            b.text for b in blocks if b.type == "text" and b.text
        )

    def token_estimate(self) -> int:
        """Rough token count estimation (~4 chars per token, padded 4/3)."""
        total = 0
        for block in self.content_blocks:
            if block.type == "text" and block.text:
                total += len(block.text) // 4
            elif block.type == "tool_result":
                total += self._estimate_tool_result_tokens(block)
            elif block.type == "tool_use":
                total += len(str(block.input or "")) // 4
            elif block.type in ("image", "document"):
                total += 2000  # fixed estimate for images
            else:
                total += len(str(block)) // 4
        return int(total * 4 / 3)

    @staticmethod
    def _estimate_tool_result_tokens(block: ContentBlock) -> int:
        if block.content is None:
            return 0
        if isinstance(block.content, str):
            return len(block.content) // 4
        total = 0
        if isinstance(block.content, list):
            for item in block.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        total += len(item.get("text", "")) // 4
                    elif item.get("type") in ("image", "document"):
                        total += 2000
                elif isinstance(item, str):
                    total += len(item) // 4
        return total

    def to_dict(self) -> dict:
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {
            "role": self.role,
            "content": [b.to_dict() for b in self.content],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        raw_content = d.get("content", "")
        if isinstance(raw_content, str):
            return cls(
                role=d["role"],
                content=raw_content,
                timestamp=d.get("timestamp", time.time()),
                message_id=d.get("message_id"),
            )
        blocks = [ContentBlock.from_dict(b) for b in raw_content]
        return cls(
            role=d["role"],
            content=blocks,
            timestamp=d.get("timestamp", time.time()),
            message_id=d.get("message_id"),
        )


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

@dataclass
class MicrocompactConfig:
    """Configuration for microcompact behavior."""

    # ── Duplicate detection ──
    similarity_threshold: float = 0.85
    """Content similarity ratio to consider two messages duplicates (0-1)."""

    # ── Long text compression ──
    max_tool_result_tokens: int = 5000
    """Max tokens for a single tool result before compression."""
    tool_result_head_tokens: int = 2000
    """Tokens to keep from the head of a compressed tool result."""
    tool_result_tail_tokens: int = 500
    """Tokens to keep from the tail of a compressed tool result."""

    # ── Time-based clearing ──
    time_based_enabled: bool = True
    gap_threshold_minutes: float = 60.0
    """Clear old results if gap since last assistant message > this."""
    keep_recent_tool_results: int = 5
    """Keep this many most-recent tool results during time-based clearing."""

    # ── Compactable tools (results can be cleared) ──
    compactable_tools: set[str] = field(default_factory=lambda: {
        "read", "bash", "exec", "shell", "grep", "glob",
        "web_search", "web_fetch", "file_read", "file_write",
        "file_edit", "cat", "ls", "find", "head", "tail",
    })

    # ── Token budget ──
    max_input_tokens: int = 180_000
    """Token threshold that triggers compaction."""
    target_input_tokens: int = 40_000
    """Target token count after compaction."""

    @classmethod
    def from_file(cls, path: str | Path) -> "MicrocompactConfig":
        """Load config from a JSON file."""
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        # Map JSON keys to dataclass fields
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in field_names}
        if "compactable_tools" in filtered:
            filtered["compactable_tools"] = set(filtered["compactable_tools"])
        return cls(**filtered)

    def to_file(self, path: str | Path) -> None:
        """Save config to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "similarity_threshold": self.similarity_threshold,
            "max_tool_result_tokens": self.max_tool_result_tokens,
            "tool_result_head_tokens": self.tool_result_head_tokens,
            "tool_result_tail_tokens": self.tool_result_tail_tokens,
            "time_based_enabled": self.time_based_enabled,
            "gap_threshold_minutes": self.gap_threshold_minutes,
            "keep_recent_tool_results": self.keep_recent_tool_results,
            "compactable_tools": sorted(self.compactable_tools),
            "max_input_tokens": self.max_input_tokens,
            "target_input_tokens": self.target_input_tokens,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────
# Compaction Statistics
# ──────────────────────────────────────────────

@dataclass
class CompactionStats:
    """Statistics from a microcompact run."""

    original_message_count: int = 0
    compacted_message_count: int = 0
    duplicates_merged: int = 0
    tool_results_grouped: int = 0
    tool_results_cleared: int = 0
    long_texts_compressed: int = 0
    tokens_before: int = 0
    tokens_after: int = 0
    time_based_cleared: int = 0

    @property
    def tokens_saved(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)

    @property
    def compression_ratio(self) -> float:
        if self.tokens_before == 0:
            return 1.0
        return self.tokens_after / self.tokens_before

    def summary(self) -> str:
        lines = [
            "═══ Microcompact Summary ═══",
            f"  Messages: {self.original_message_count} → {self.compacted_message_count}",
            f"  Tokens:   {self.tokens_before:,} → {self.tokens_after:,} "
            f"(saved {self.tokens_saved:,}, {self.compression_ratio:.1%} retained)",
            f"  Actions:",
            f"    • Duplicates merged:       {self.duplicates_merged}",
            f"    • Tool results grouped:    {self.tool_results_grouped}",
            f"    • Tool results compressed:  {self.long_texts_compressed}",
            f"    • Tool results cleared:     {self.tool_results_cleared}",
            f"    • Time-based cleared:      {self.time_based_cleared}",
            "══════════════════════════════",
        ]
        return "\n".join(lines)


# ──────────────────────────────────────────────
# Core Algorithms
# ──────────────────────────────────────────────

class ContextCompactor:
    """Microcompact context compactor.

    Implements the 4-stage pipeline:
    1. Time-based clearing (gap > threshold → clear old tool results)
    2. Duplicate message detection and merging
    3. Consecutive tool result grouping
    4. Long text compression
    """

    def __init__(self, config: MicrocompactConfig | None = None):
        self.config = config or MicrocompactConfig()
        self.stats = CompactionStats()

    def compact(self, messages: list[Message]) -> list[Message]:
        """Run full microcompact pipeline on messages."""
        self.stats = CompactionStats(
            original_message_count=len(messages),
            tokens_before=sum(m.token_estimate() for m in messages),
        )

        result = messages

        # Stage 1: Time-based clearing
        result = self._time_based_clearing(result)

        # Stage 2: Duplicate detection & merging
        result = self._merge_duplicates(result)

        # Stage 3: Group consecutive tool results
        result = self._group_tool_results(result)

        # Stage 4: Compress long texts
        result = self._compress_long_texts(result)

        self.stats.compacted_message_count = len(result)
        self.stats.tokens_after = sum(m.token_estimate() for m in result)

        return result

    def compact_json(self, messages_json: list[dict]) -> list[dict]:
        """Compact messages from JSON dicts (API-friendly interface)."""
        messages = [Message.from_dict(d) for d in messages_json]
        compacted = self.compact(messages)
        return [m.to_dict() for m in compacted]

    # ── Stage 1: Time-based clearing ──

    def _time_based_clearing(
        self, messages: list[Message]
    ) -> list[Message]:
        """Clear old tool results when cache has expired (gap > threshold)."""
        if not self.config.time_based_enabled:
            return messages

        # Find last assistant message timestamp
        last_assistant_ts = None
        for msg in reversed(messages):
            if msg.role == "assistant":
                last_assistant_ts = msg.timestamp
                break

        if last_assistant_ts is None:
            return messages

        gap_minutes = (time.time() - last_assistant_ts) / 60.0
        if gap_minutes < self.config.gap_threshold_minutes:
            return messages

        logger.info(
            f"[Time-based MC] gap {gap_minutes:.1f}min > "
            f"{self.config.gap_threshold_minutes}min threshold"
        )

        # Collect compactable tool_use IDs in encounter order
        compactable_ids = self._collect_compactable_tool_ids(messages)
        keep_set = set(
            compactable_ids[-self.config.keep_recent_tool_results:]
        )
        clear_set = set(compactable_ids) - keep_set

        if not clear_set:
            return messages

        CLEARED_MARKER = "[Old tool result content cleared]"
        result = []
        for msg in messages:
            if msg.role != "user" or not isinstance(msg.content, list):
                result.append(msg)
                continue

            touched = False
            new_blocks = []
            for block in msg.content:
                if (
                    block.type == "tool_result"
                    and block.tool_use_id in clear_set
                    and block.content != CLEARED_MARKER
                ):
                    self.stats.time_based_cleared += 1
                    touched = True
                    new_blocks.append(
                        ContentBlock(
                            type="tool_result",
                            tool_use_id=block.tool_use_id,
                            content=CLEARED_MARKER,
                        )
                    )
                else:
                    new_blocks.append(block)

            if touched:
                result.append(
                    Message(
                        role=msg.role,
                        content=new_blocks,
                        timestamp=msg.timestamp,
                        message_id=msg.message_id,
                        metadata=msg.metadata,
                    )
                )
            else:
                result.append(msg)

        logger.info(
            f"[Time-based MC] cleared {len(clear_set)} tool results, "
            f"kept last {len(keep_set)}"
        )
        return result

    def _collect_compactable_tool_ids(self, messages: list[Message]) -> list[str]:
        """Collect tool_use IDs for compactable tools, in encounter order."""
        ids = []
        for msg in messages:
            if msg.role != "assistant" or not isinstance(msg.content, list):
                continue
            for block in msg.content:
                if (
                    block.type == "tool_use"
                    and block.tool_name in self.config.compactable_tools
                    and block.tool_use_id
                ):
                    ids.append(block.tool_use_id)
        return ids

    # ── Stage 2: Duplicate detection & merging ──

    def _merge_duplicates(self, messages: list[Message]) -> list[Message]:
        """Merge messages with same role and similar content.

        Claude Code's approach: detect messages where the role matches
        and content similarity exceeds the threshold, then keep the
        newer message (more information-dense).
        """
        if len(messages) <= 1:
            return messages

        result: list[Message] = [messages[0]]

        for msg in messages[1:]:
            merged = False
            # Check against recent messages in result (last 10 for efficiency)
            for prev_msg in reversed(result[-10:]):
                if prev_msg.role != msg.role:
                    continue

                similarity = self._content_similarity(prev_msg, msg)
                if similarity >= self.config.similarity_threshold:
                    # Keep the newer (longer) message
                    if self._content_length(msg) >= self._content_length(prev_msg):
                        result[-1] = msg  # Replace previous
                    # else: keep previous, skip current
                    self.stats.duplicates_merged += 1
                    merged = True
                    break

            if not merged:
                result.append(msg)

        return result

    def _content_similarity(self, a: Message, b: Message) -> float:
        """Calculate content similarity between two messages.

        Uses SequenceMatcher for text similarity, plus structural
        comparison for content block messages.
        """
        a_text = a.text_content
        b_text = b.text_content

        if not a_text and not b_text:
            # Both have no text — check structural similarity
            return self._structural_similarity(a, b)
        if not a_text or not b_text:
            return 0.0

        # Normalize whitespace for comparison
        a_norm = " ".join(a_text.split())
        b_norm = " ".join(b_text.split())

        if a_norm == b_norm:
            return 1.0

        return SequenceMatcher(None, a_norm, b_norm).ratio()

    def _structural_similarity(self, a: Message, b: Message) -> float:
        """Compare structural similarity of block-based messages."""
        a_blocks = a.content_blocks
        b_blocks = b.content_blocks

        if len(a_blocks) != len(b_blocks):
            return 0.0

        matches = 0
        for ab, bb in zip(a_blocks, b_blocks):
            if ab.type != bb.type:
                continue
            if ab.type == "tool_use" and ab.tool_name == bb.tool_name:
                matches += 1
            elif ab.type == "tool_result" and ab.tool_use_id == bb.tool_use_id:
                matches += 1

        return matches / max(len(a_blocks), 1)

    @staticmethod
    def _content_length(msg: Message) -> int:
        if isinstance(msg.content, str):
            return len(msg.content)
        return sum(len(str(b)) for b in msg.content_blocks)

    # ── Stage 3: Group consecutive tool results ──

    def _group_tool_results(
        self, messages: list[Message]
    ) -> list[Message]:
        """Group consecutive tool result messages from the same role.

        When multiple tool results arrive in sequence (user role), they
        can be combined into a single message to reduce message count
        and improve prompt cache locality.
        """
        if len(messages) <= 1:
            return messages

        result: list[Message] = []
        i = 0

        while i < len(messages):
            msg = messages[i]

            # Look for consecutive user messages with only tool_result blocks
            if msg.role == "user" and self._is_tool_result_message(msg):
                group = [msg]
                j = i + 1
                while j < len(messages) and messages[j].role == "user":
                    if self._is_tool_result_message(messages[j]):
                        group.append(messages[j])
                        j += 1
                    else:
                        break

                if len(group) > 1:
                    # Merge into single message
                    merged_blocks = []
                    for g in group:
                        merged_blocks.extend(g.content_blocks)
                    merged = Message(
                        role="user",
                        content=merged_blocks,
                        timestamp=group[-1].timestamp,
                        message_id=group[-1].message_id,
                    )
                    result.append(merged)
                    self.stats.tool_results_grouped += len(group) - 1
                    i = j
                    continue

            result.append(msg)
            i += 1

        return result

    @staticmethod
    def _is_tool_result_message(msg: Message) -> bool:
        """Check if a message contains only tool_result blocks."""
        if isinstance(msg.content, str):
            return False
        return all(b.type == "tool_result" for b in msg.content)

    # ── Stage 4: Long text compression ──

    def _compress_long_texts(
        self, messages: list[Message]
    ) -> list[Message]:
        """Compress long text blocks while preserving key information.

        Strategy (from Claude Code's approach):
        - Keep head (most important context) + tail (recent state)
        - Replace middle with truncation marker
        - Preserve tool call structure
        """
        result = []

        for msg in messages:
            if isinstance(msg.content, str):
                compressed = self._compress_text(
                    msg.content, self.config.max_tool_result_tokens * 4
                )
                if compressed != msg.content:
                    self.stats.long_texts_compressed += 1
                    result.append(
                        Message(
                            role=msg.role,
                            content=compressed,
                            timestamp=msg.timestamp,
                            message_id=msg.message_id,
                            metadata=msg.metadata,
                        )
                    )
                else:
                    result.append(msg)
                continue

            # Block-based messages
            new_blocks = []
            touched = False
            for block in msg.content_blocks:
                if block.type == "tool_result":
                    compressed_block = self._compress_tool_result(block)
                    if compressed_block is not block:
                        self.stats.long_texts_compressed += 1
                        touched = True
                    new_blocks.append(compressed_block)
                elif block.type == "text" and block.text:
                    compressed_text = self._compress_text(
                        block.text,
                        self.config.max_tool_result_tokens * 4,
                    )
                    if compressed_text != block.text:
                        self.stats.long_texts_compressed += 1
                        touched = True
                        new_blocks.append(
                            ContentBlock(type="text", text=compressed_text)
                        )
                    else:
                        new_blocks.append(block)
                else:
                    new_blocks.append(block)

            if touched:
                result.append(
                    Message(
                        role=msg.role,
                        content=new_blocks,
                        timestamp=msg.timestamp,
                        message_id=msg.message_id,
                        metadata=msg.metadata,
                    )
                )
            else:
                result.append(msg)

        return result

    def _compress_tool_result(self, block: ContentBlock) -> ContentBlock:
        """Compress a single tool_result block if it exceeds token limits."""
        if block.content is None:
            return block

        text = block.content if isinstance(block.content, str) else ""
        if not text:
            # Array content — estimate from serialized form
            text = json.dumps(block.content, ensure_ascii=False)

        char_limit = self.config.max_tool_result_tokens * 4
        if len(text) <= char_limit:
            return block

        compressed = self._compress_text(text, char_limit)
        return ContentBlock(
            type="tool_result",
            tool_use_id=block.tool_use_id,
            content=compressed,
        )

    def _compress_text(self, text: str, char_limit: int) -> str:
        """Compress text by keeping head + tail with truncation marker."""
        if len(text) <= char_limit:
            return text

        head_chars = self.config.tool_result_head_tokens * 4
        tail_chars = self.config.tool_result_tail_tokens * 4
        omitted = len(text) - head_chars - tail_chars

        marker = (
            f"\n\n[... {omitted:,} chars omitted — "
            f"original was {len(text):,} chars total ...]\n\n"
        )

        return text[:head_chars] + marker + text[-tail_chars:]


# ──────────────────────────────────────────────
# Convenience Functions
# ──────────────────────────────────────────────

def microcompact(
    messages: list[dict],
    config: MicrocompactConfig | None = None,
) -> tuple[list[dict], CompactionStats]:
    """One-shot microcompact. Returns (compacted_messages, stats).

    Args:
        messages: List of message dicts with 'role' and 'content'.
        config: Optional configuration overrides.

    Returns:
        Tuple of (compacted message dicts, compaction statistics).
    """
    compactor = ContextCompactor(config)
    compacted = compactor.compact_json(messages)
    return compacted, compactor.stats


def microcompact_from_file(
    input_path: str | Path,
    output_path: str | Path | None = None,
    config_path: str | Path | None = None,
) -> CompactionStats:
    """Compact messages from a JSON file.

    Args:
        input_path: Path to input JSON file (list of message dicts).
        output_path: Path to write compacted messages. Default: <input>_compacted.json
        config_path: Path to config JSON file.

    Returns:
        Compaction statistics.
    """
    input_path = Path(input_path)
    config = MicrocompactConfig.from_file(config_path) if config_path else MicrocompactConfig()

    with open(input_path) as f:
        messages = json.load(f)

    compacted, stats = microcompact(messages, config)

    if output_path is None:
        output_path = input_path.with_suffix(".compacted.json")
    output_path = Path(output_path)

    with open(output_path, "w") as f:
        json.dump(compacted, f, indent=2, ensure_ascii=False)

    return stats


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    """CLI interface for context compactor."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Microcompact — 上下文压缩工具 (参考 Claude Code)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compact messages from stdin
  cat messages.json | python context_compactor.py

  # Compact a file
  python context_compactor.py messages.json

  # With custom config
  python context_compactor.py messages.json --config context_compact_config.json

  # Output to specific file
  python context_compactor.py messages.json -o compacted.json

  # Just show stats (dry run)
  python context_compactor.py messages.json --dry-run

  # Verbose logging
  python context_compactor.py messages.json -v
        """,
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input JSON file (reads stdin if omitted)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <input>_compacted.json or stdout)",
    )
    parser.add_argument(
        "--config",
        help="Config JSON file path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show stats without writing output",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    # Load messages
    if args.input:
        with open(args.input) as f:
            messages = json.load(f)
    else:
        messages = json.load(sys.stdin)

    # Load config
    config = MicrocompactConfig.from_file(args.config) if args.config else MicrocompactConfig()

    # Compact
    compacted, stats = microcompact(messages, config)

    # Output
    if args.dry_run:
        print(stats.summary())
    else:
        if args.output:
            with open(args.output, "w") as f:
                json.dump(compacted, f, indent=2, ensure_ascii=False)
            print(stats.summary(), file=sys.stderr)
        else:
            json.dump(compacted, sys.stdout, indent=2, ensure_ascii=False)
            print(file=sys.stderr)
            print(stats.summary(), file=sys.stderr)


if __name__ == "__main__":
    main()
