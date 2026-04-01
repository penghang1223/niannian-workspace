#!/usr/bin/env python3
"""
context_tracker.py - 上下文追踪 + Token预算管理（OpenClaw适配版）

融合 claude-howto 的 context-tracker hook 和 token_budget.py 的预算管理功能。

功能：
1. Hook模式：兼容Claude Code UserPromptSubmit/Stop事件，追踪每次请求token消耗
2. CLI模式：预算管理（status/record/check/reset/continue/report）
3. 估算模式：对文本/文件进行token估算并记录
4. 自动预算检查：每次记录后自动检查阈值，输出警告/建议
5. 状态持久化：跨会话保持预算状态

用法：
    # Hook模式（Claude Code hooks）
    echo '{"hook_event_name":"UserPromptSubmit","session_id":"xxx","transcript_path":"..."}' | python3 scripts/context_tracker.py --hook
    echo '{"hook_event_name":"Stop","session_id":"xxx","transcript_path":"..."}' | python3 scripts/context_tracker.py --hook

    # CLI模式
    python3 scripts/context_tracker.py status          # 查看预算状态
    python3 scripts/context_tracker.py record 1500     # 记录token消耗
    python3 scripts/context_tracker.py check           # 检查预算告警
    python3 scripts/context_tracker.py reset           # 重置预算
    python3 scripts/context_tracker.py continue        # 续期预算
    python3 scripts/context_tracker.py report          # 详细报告

    # 估算模式
    python3 scripts/context_tracker.py estimate "some text here"
    python3 scripts/context_tracker.py estimate --file /path/to/file.txt

    # 测试模式
    python3 scripts/context_tracker.py --test
"""

import json
import sys
import os
import argparse
import tempfile
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum


# ══════════════════════════════════════════════════════════════
# 预算管理（源自 token_budget.py）
# ══════════════════════════════════════════════════════════════

class BudgetStatus(Enum):
    """预算状态枚举"""
    NORMAL = "normal"
    WARNING = "warning"
    DANGER = "danger"
    EXHAUSTED = "exhausted"
    CONTINUED = "continued"


@dataclass
class BudgetConfig:
    """预算配置"""
    total_budget: int = 500_000
    warning_threshold: float = 0.75
    danger_threshold: float = 0.90
    auto_compact_threshold: float = 0.85
    continuation_budget: int = 200_000
    max_continuations: int = 5

    @classmethod
    def from_file(cls, config_path: str) -> "BudgetConfig":
        """从配置文件加载"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            budget_data = data.get("budget", {})
            return cls(
                total_budget=budget_data.get("total_budget", 500_000),
                warning_threshold=budget_data.get("warning_threshold", 0.75),
                danger_threshold=budget_data.get("danger_threshold", 0.90),
                auto_compact_threshold=budget_data.get("auto_compact_threshold", 0.85),
                continuation_budget=budget_data.get("continuation_budget", 200_000),
                max_continuations=budget_data.get("max_continuations", 5),
            )
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


@dataclass
class TokenRecord:
    """单次Token使用记录"""
    tokens: int
    timestamp: str
    description: str = ""
    session_id: str = ""
    event_type: str = ""


@dataclass
class BudgetState:
    """预算状态"""
    total_budget: int = 500_000
    used_tokens: int = 0
    remaining_tokens: int = 500_000
    current_session_tokens: int = 0
    continuation_count: int = 0
    status: str = "normal"
    period_start: str = ""
    period_end: Optional[str] = None
    last_compact_suggestion: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetState":
        return cls(
            total_budget=data.get("total_budget", 500_000),
            used_tokens=data.get("used_tokens", 0),
            remaining_tokens=data.get("remaining_tokens", 500_000),
            current_session_tokens=data.get("current_session_tokens", 0),
            continuation_count=data.get("continuation_count", 0),
            status=data.get("status", "normal"),
            period_start=data.get("period_start", ""),
            period_end=data.get("period_end"),
            last_compact_suggestion=data.get("last_compact_suggestion"),
            history=data.get("history", []),
        )


class TokenBudget:
    """Token预算管理器"""

    CONFIG_FILE = "token_budget_config.json"
    DEFAULT_STATE_FILE = "logs/token_budget_state.json"
    HISTORY_SIZE = 100

    def __init__(self, config_path: Optional[str] = None, state_file: Optional[str] = None):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_path = config_path or str(self.root_dir / self.CONFIG_FILE)
        self.config = BudgetConfig.from_file(self.config_path)

        self.state_file = state_file or str(self.root_dir / self.DEFAULT_STATE_FILE)
        self.state = self._load_state()

    def _load_state(self) -> BudgetState:
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return BudgetState.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            now = datetime.now().isoformat()
            return BudgetState(
                total_budget=self.config.total_budget,
                remaining_tokens=self.config.total_budget,
                period_start=now,
            )

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)

    def _update_status(self):
        usage_ratio = (
            self.state.used_tokens / self.state.total_budget
            if self.state.total_budget > 0
            else 1.0
        )
        if usage_ratio >= 1.0:
            self.state.status = BudgetStatus.EXHAUSTED.value
        elif usage_ratio >= self.config.danger_threshold:
            self.state.status = BudgetStatus.DANGER.value
        elif usage_ratio >= self.config.warning_threshold:
            self.state.status = BudgetStatus.WARNING.value
        else:
            self.state.status = BudgetStatus.NORMAL.value

        self.state.remaining_tokens = max(
            0, self.state.total_budget - self.state.used_tokens
        )

    # ── 核心 API ──────────────────────────────────────────────

    def record(self, tokens: int, description: str = "",
               session_id: str = "", event_type: str = "") -> Dict[str, Any]:
        """记录token使用"""
        self.state.used_tokens += tokens
        self.state.current_session_tokens += tokens

        record = TokenRecord(
            tokens=tokens,
            timestamp=datetime.now().isoformat(),
            description=description,
            session_id=session_id,
            event_type=event_type,
        )
        self.state.history.append(asdict(record))
        if len(self.state.history) > self.HISTORY_SIZE:
            self.state.history = self.state.history[-self.HISTORY_SIZE:]

        self._update_status()
        self._save_state()

        return self._build_result(f"已记录 {tokens} tokens")

    def status(self) -> Dict[str, Any]:
        self._update_status()
        usage_ratio = (
            self.state.used_tokens / self.state.total_budget
            if self.state.total_budget > 0
            else 0
        )
        return {
            "status": self.state.status,
            "total_budget": self.state.total_budget,
            "used_tokens": self.state.used_tokens,
            "remaining_tokens": self.state.remaining_tokens,
            "current_session_tokens": self.state.current_session_tokens,
            "usage_ratio": round(usage_ratio, 4),
            "usage_percent": f"{usage_ratio * 100:.1f}%",
            "continuation_count": self.state.continuation_count,
            "max_continuations": self.config.max_continuations,
            "period_start": self.state.period_start,
        }

    def check(self) -> Dict[str, Any]:
        self._update_status()
        usage_ratio = (
            self.state.used_tokens / self.state.total_budget
            if self.state.total_budget > 0
            else 1.0
        )

        result: Dict[str, Any] = {
            "status": self.state.status,
            "usage_ratio": round(usage_ratio, 4),
            "actions": [],
        }

        if usage_ratio >= self.config.auto_compact_threshold:
            now = datetime.now().isoformat()
            result["actions"].append(
                {
                    "type": "auto_compact",
                    "message": (
                        f"⚡ Token使用率 {usage_ratio*100:.1f}% 已超过自动压缩阈值 "
                        f"{self.config.auto_compact_threshold*100:.0f}%，建议立即压缩上下文"
                    ),
                    "priority": "high",
                }
            )
            self.state.last_compact_suggestion = now

        if usage_ratio >= self.config.danger_threshold:
            result["actions"].append(
                {
                    "type": "danger",
                    "message": (
                        f"🚨 Token使用率 {usage_ratio*100:.1f}% 已超过危险阈值 "
                        f"{self.config.danger_threshold*100:.0f}%，剩余 {self.state.remaining_tokens} tokens"
                    ),
                    "priority": "critical",
                }
            )
        elif usage_ratio >= self.config.warning_threshold:
            result["actions"].append(
                {
                    "type": "warning",
                    "message": (
                        f"⚠️ Token使用率 {usage_ratio*100:.1f}% 已超过警告阈值 "
                        f"{self.config.warning_threshold*100:.0f}%，剩余 {self.state.remaining_tokens} tokens"
                    ),
                    "priority": "medium",
                }
            )

        if self.state.remaining_tokens <= 0:
            if self.state.continuation_count < self.config.max_continuations:
                result["actions"].append(
                    {
                        "type": "budget_exhausted",
                        "message": (
                            f"🔴 Token预算已耗尽！已续期 "
                            f"{self.state.continuation_count}/{self.config.max_continuations} 次，可继续续期"
                        ),
                        "priority": "critical",
                        "can_continue": True,
                    }
                )
            else:
                result["actions"].append(
                    {
                        "type": "budget_exhausted",
                        "message": f"🔴 Token预算已耗尽！已达最大续期次数 {self.config.max_continuations}",
                        "priority": "critical",
                        "can_continue": False,
                    }
                )

        self._save_state()
        return result

    def reset(self) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        self.state = BudgetState(
            total_budget=self.config.total_budget,
            remaining_tokens=self.config.total_budget,
            period_start=now,
        )
        self._save_state()
        return self._build_result("预算已重置")

    def continue_budget(self) -> Dict[str, Any]:
        if self.state.continuation_count >= self.config.max_continuations:
            return {
                "success": False,
                "message": f"已达最大续期次数 {self.config.max_continuations}",
                "continuation_count": self.state.continuation_count,
            }

        self.state.continuation_count += 1
        self.state.total_budget += self.config.continuation_budget
        self.state.remaining_tokens += self.config.continuation_budget
        self.state.status = BudgetStatus.CONTINUED.value
        self._save_state()

        return self._build_result(
            f"已续期 #{self.state.continuation_count}，增加 {self.config.continuation_budget} tokens"
        )

    def report(self) -> Dict[str, Any]:
        status = self.status()
        check = self.check()

        recent_history = self.state.history[-20:] if self.state.history else []
        total_recent = sum(r["tokens"] for r in recent_history)
        avg_per_record = total_recent / len(recent_history) if recent_history else 0

        return {
            **status,
            "check": check,
            "trend": {
                "recent_records": len(recent_history),
                "recent_total_tokens": total_recent,
                "avg_tokens_per_record": round(avg_per_record, 1),
                "estimated_records_remaining": (
                    int(self.state.remaining_tokens / avg_per_record)
                    if avg_per_record > 0
                    else "N/A"
                ),
            },
            "config": {
                "warning_threshold": f"{self.config.warning_threshold*100:.0f}%",
                "danger_threshold": f"{self.config.danger_threshold*100:.0f}%",
                "auto_compact_threshold": f"{self.config.auto_compact_threshold*100:.0f}%",
                "continuation_budget": self.config.continuation_budget,
                "max_continuations": self.config.max_continuations,
            },
            "recommendations": self._get_recommendations(check, status),
        }

    def _get_recommendations(self, check: Dict, status: Dict) -> List[str]:
        recs = []
        ratio = status["usage_ratio"]

        if ratio >= 0.95:
            recs.append("🚨 立即执行上下文压缩（microcompact/autocompact）")
            recs.append("💡 考虑使用 budget continue 续期")
        elif ratio >= 0.85:
            recs.append("⚡ 建议执行上下文压缩")
            recs.append("📝 减少不必要的工具调用")
        elif ratio >= 0.75:
            recs.append("⚠️ 关注token消耗，准备压缩")
        else:
            recs.append("✅ 预算充足，正常使用")

        if self.state.continuation_count > 0:
            recs.append(f"📊 已续期 {self.state.continuation_count} 次")

        return recs

    def _build_result(self, message: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": message,
            "status": self.state.status,
            "used_tokens": self.state.used_tokens,
            "remaining_tokens": self.state.remaining_tokens,
            "total_budget": self.state.total_budget,
            "usage_percent": f"{(self.state.used_tokens/self.state.total_budget)*100:.1f}%",
        }

    # ── CLI 格式化输出 ─────────────────────────────────────────

    @staticmethod
    def format_status(data: Dict[str, Any]) -> str:
        status_emoji = {
            "normal": "🟢",
            "warning": "⚠️",
            "danger": "🚨",
            "exhausted": "🔴",
            "continued": "🔄",
        }
        emoji = status_emoji.get(data.get("status", ""), "❓")

        lines = [
            f"\n{'='*50}",
            f"  {emoji} Token 预算状态",
            f"{'='*50}",
            f"  状态:       {data.get('status', 'N/A').upper()}",
            f"  总预算:     {data.get('total_budget', 0):,} tokens",
            f"  已使用:     {data.get('used_tokens', 0):,} tokens",
            f"  剩余:       {data.get('remaining_tokens', 0):,} tokens",
            f"  使用率:     {data.get('usage_percent', '0%')}",
            f"  本次会话:   {data.get('current_session_tokens', 0):,} tokens",
            f"  续期次数:   {data.get('continuation_count', 0)}/{data.get('max_continuations', 5)}",
            f"  周期开始:   {data.get('period_start', 'N/A')[:19]}",
            f"{'='*50}",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_check(data: Dict[str, Any]) -> str:
        lines = [f"\n{'='*50}", f"  🔍 Token 预算检查", f"{'='*50}"]
        actions = data.get("actions", [])
        if not actions:
            lines.append("  ✅ 一切正常，无需操作")
        else:
            for action in actions:
                lines.append(f"  {action['message']}")
        lines.append(f"{'='*50}")
        return "\n".join(lines)

    @staticmethod
    def format_report(data: Dict[str, Any]) -> str:
        status_emoji = {
            "normal": "🟢",
            "warning": "⚠️",
            "danger": "🚨",
            "exhausted": "🔴",
            "continued": "🔄",
        }
        emoji = status_emoji.get(data.get("status", ""), "❓")
        trend = data.get("trend", {})
        config = data.get("config", {})
        recs = data.get("recommendations", [])

        lines = [
            f"\n{'='*55}",
            f"  {emoji} Token 预算详细报告",
            f"{'='*55}",
            f"\n📊 预算概况",
            f"  总预算:         {data.get('total_budget', 0):,} tokens",
            f"  已使用:         {data.get('used_tokens', 0):,} tokens",
            f"  剩余:           {data.get('remaining_tokens', 0):,} tokens",
            f"  使用率:         {data.get('usage_percent', '0%')}",
            f"  本次会话使用:   {data.get('current_session_tokens', 0):,} tokens",
            f"  续期次数:       {data.get('continuation_count', 0)}/{data.get('max_continuations', 5)}",
            f"\n📈 使用趋势",
            f"  近期记录数:     {trend.get('recent_records', 0)}",
            f"  近期总消耗:     {trend.get('recent_total_tokens', 0):,} tokens",
            f"  平均每次消耗:   {trend.get('avg_tokens_per_record', 0)} tokens",
            f"  预计剩余次数:   {trend.get('estimated_records_remaining', 'N/A')}",
            f"\n⚙️ 配置参数",
            f"  警告阈值:       {config.get('warning_threshold', '75%')}",
            f"  危险阈值:       {config.get('danger_threshold', '90%')}",
            f"  自动压缩阈值:   {config.get('auto_compact_threshold', '85%')}",
            f"  续期预算:       {config.get('continuation_budget', 200000):,} tokens",
            f"  最大续期次数:   {config.get('max_continuations', 5)}",
            f"\n💡 建议",
        ]
        for rec in recs:
            lines.append(f"  {rec}")
        lines.append(f"{'='*55}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# 上下文追踪（源自 claude-howto context-tracker.py）
# ══════════════════════════════════════════════════════════════

def get_state_file(session_id: str) -> str:
    """获取session级别的临时状态文件路径"""
    return os.path.join(tempfile.gettempdir(), f"openclaw-context-{session_id}.json")


def count_tokens_estimate(text: str) -> int:
    """
    估算token数量（字符数/4，约80-90%准确率）
    适用于英文和大部分代码场景
    """
    return len(text) // 4


def read_transcript(transcript_path: str) -> str:
    """读取并拼接transcript文件中的所有文本内容"""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    content = []
    with open(transcript_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if "message" in entry:
                    msg = entry["message"]
                    if isinstance(msg.get("content"), str):
                        content.append(msg["content"])
                    elif isinstance(msg.get("content"), list):
                        for block in msg["content"]:
                            if isinstance(block, dict) and block.get("type") == "text":
                                content.append(block.get("text", ""))
            except json.JSONDecodeError:
                continue

    return "\n".join(content)


def handle_user_prompt_submit(data: dict, budget: TokenBudget) -> None:
    """
    UserPromptSubmit hook：保存当前token计数
    同时记录到预算管理器
    """
    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")

    transcript_content = read_transcript(transcript_path)
    current_tokens = count_tokens_estimate(transcript_content)

    # 保存到临时文件（用于Stop事件计算delta）
    state_file = get_state_file(session_id)
    with open(state_file, "w") as f:
        json.dump({"pre_tokens": current_tokens, "session_id": session_id}, f)

    # 输出到stderr供hook系统读取
    print(
        f"[Context Tracker] Pre-request baseline: ~{current_tokens:,} tokens",
        file=sys.stderr,
    )


def handle_stop(data: dict, budget: TokenBudget) -> None:
    """
    Stop hook：计算本次请求的token增量，记录到预算管理器并检查状态
    """
    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")

    transcript_content = read_transcript(transcript_path)
    current_tokens = count_tokens_estimate(transcript_content)

    # 读取pre-message计数
    state_file = get_state_file(session_id)
    pre_tokens = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
                pre_tokens = state.get("pre_tokens", 0)
        except (json.JSONDecodeError, IOError):
            pass

    # 计算增量
    delta_tokens = max(0, current_tokens - pre_tokens)

    # 记录到预算管理器
    if delta_tokens > 0:
        budget.record(
            delta_tokens,
            description=f"session {session_id[:8]}... request",
            session_id=session_id,
            event_type="stop",
        )

    # 输出本次请求消耗
    budget_status = budget.status()
    remaining = budget_status["remaining_tokens"]
    percentage = budget_status["usage_ratio"] * 100

    print(
        f"Context: ~{current_tokens:,} tokens ({percentage:.1f}% budget used, ~{remaining:,} remaining)",
        file=sys.stderr,
    )
    if delta_tokens > 0:
        print(f"This request: ~{delta_tokens:,} tokens", file=sys.stderr)

    # 自动检查预算状态并输出告警
    check_result = budget.check()
    for action in check_result.get("actions", []):
        print(f"  {action['message']}", file=sys.stderr)

    # 清理临时文件
    try:
        os.remove(state_file)
    except OSError:
        pass


def run_hook_mode(budget: TokenBudget) -> None:
    """Hook模式：从stdin读取事件数据并处理"""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Error: Invalid JSON from stdin", file=sys.stderr)
        sys.exit(1)

    event = data.get("hook_event_name", "")

    if event == "UserPromptSubmit":
        handle_user_prompt_submit(data, budget)
    elif event == "Stop":
        handle_stop(data, budget)
    else:
        print(f"[Context Tracker] Unknown event: {event}", file=sys.stderr)

    sys.exit(0)


# ══════════════════════════════════════════════════════════════
# 估算模式
# ══════════════════════════════════════════════════════════════

def estimate_text(text: str) -> int:
    """估算文本的token数量"""
    return count_tokens_estimate(text)


def estimate_file(file_path: str) -> int:
    """估算文件的token数量"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}", file=sys.stderr)
        return 0
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return count_tokens_estimate(text)


# ══════════════════════════════════════════════════════════════
# 测试套件
# ══════════════════════════════════════════════════════════════

def run_tests() -> bool:
    """运行完整测试套件"""
    import shutil

    passed = 0
    failed = 0
    tests: List[tuple] = []

    def test(name: str):
        def decorator(fn):
            tests.append((name, fn))
        return decorator

    tmp_dir = tempfile.mkdtemp()

    try:
        test_config = {
            "budget": {
                "total_budget": 10000,
                "warning_threshold": 0.5,
                "danger_threshold": 0.8,
                "auto_compact_threshold": 0.7,
                "continuation_budget": 5000,
                "max_continuations": 3,
            }
        }
        config_path = os.path.join(tmp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        # ── 预算管理测试 ──

        @test("初始状态正确")
        def test_initial_status():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state.json"),
            )
            s = tb.status()
            assert s["total_budget"] == 10000
            assert s["used_tokens"] == 0
            assert s["remaining_tokens"] == 10000
            assert s["status"] == "normal"

        @test("记录token使用")
        def test_record():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state2.json"),
            )
            result = tb.record(3000, "test record")
            assert result["success"]
            assert result["used_tokens"] == 3000
            assert result["remaining_tokens"] == 7000

        @test("带session_id的记录")
        def test_record_with_session():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state2b.json"),
            )
            result = tb.record(1000, "hook request", session_id="sess-abc", event_type="stop")
            assert result["success"]
            assert len(tb.state.history) == 1
            assert tb.state.history[0]["session_id"] == "sess-abc"
            assert tb.state.history[0]["event_type"] == "stop"

        @test("警告阈值触发")
        def test_warning_threshold():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state3.json"),
            )
            tb.record(6000, "test")
            check = tb.check()
            assert check["status"] == "warning"
            assert any(a["type"] == "warning" for a in check["actions"])

        @test("危险阈值触发")
        def test_danger_threshold():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state4.json"),
            )
            tb.record(8500, "test")
            check = tb.check()
            assert check["status"] == "danger"

        @test("自动压缩建议触发")
        def test_auto_compact():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state5.json"),
            )
            tb.record(7500, "test")
            check = tb.check()
            assert any(a["type"] == "auto_compact" for a in check["actions"])

        @test("预算耗尽")
        def test_exhausted():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state6.json"),
            )
            tb.record(10000, "test")
            check = tb.check()
            assert check["status"] == "exhausted"
            assert any(a["type"] == "budget_exhausted" for a in check["actions"])

        @test("预算续期")
        def test_continue():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state7.json"),
            )
            tb.record(10000, "test")
            result = tb.continue_budget()
            assert result["success"]
            assert result["remaining_tokens"] == 5000
            assert result["total_budget"] == 15000

        @test("续期上限")
        def test_max_continuations():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state8.json"),
            )
            tb.record(10000, "test")
            for _ in range(3):
                tb.continue_budget()
            result = tb.continue_budget()
            assert not result["success"]
            assert "最大续期" in result["message"]

        @test("预算重置")
        def test_reset():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state9.json"),
            )
            tb.record(8000, "test")
            result = tb.reset()
            assert result["success"]
            assert result["used_tokens"] == 0
            assert result["remaining_tokens"] == 10000

        @test("详细报告")
        def test_report():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state10.json"),
            )
            tb.record(3000, "test1")
            tb.record(2000, "test2")
            report = tb.report()
            assert "trend" in report
            assert "config" in report
            assert "recommendations" in report
            assert report["trend"]["recent_total_tokens"] == 5000

        @test("历史记录限制")
        def test_history_limit():
            tb = TokenBudget(
                config_path=config_path,
                state_file=os.path.join(tmp_dir, "state11.json"),
            )
            for i in range(150):
                tb.record(10, f"record {i}")
            assert len(tb.state.history) == tb.HISTORY_SIZE

        @test("状态持久化")
        def test_persistence():
            state_path = os.path.join(tmp_dir, "state12.json")
            tb1 = TokenBudget(config_path=config_path, state_file=state_path)
            tb1.record(4000, "save test")
            tb2 = TokenBudget(config_path=config_path, state_file=state_path)
            assert tb2.state.used_tokens == 4000
            assert tb2.state.remaining_tokens == 6000

        # ── Token估算测试 ──

        @test("Token估算 - 空文本")
        def test_estimate_empty():
            assert estimate_text("") == 0

        @test("Token估算 - 英文文本")
        def test_estimate_english():
            tokens = estimate_text("Hello world, this is a test.")
            assert tokens > 0
            assert tokens == len("Hello world, this is a test.") // 4

        @test("Token估算 - 中文文本")
        def test_estimate_chinese():
            tokens = estimate_text("你好世界，这是一段测试文本。")
            assert tokens > 0

        @test("Token估算 - 文件")
        def test_estimate_file():
            test_file = os.path.join(tmp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("A" * 400)  # 100 tokens
            assert estimate_file(test_file) == 100

        @test("Token估算 - 不存在的文件")
        def test_estimate_missing_file():
            tokens = estimate_file("/nonexistent/path/file.txt")
            assert tokens == 0

        # ── Hook流程集成测试 ──

        @test("Hook流程 - UserPromptSubmit → Stop 完整流程")
        def test_hook_flow():
            state_path = os.path.join(tmp_dir, "state_hook.json")
            tb = TokenBudget(config_path=config_path, state_file=state_path)

            # 模拟transcript文件
            transcript = os.path.join(tmp_dir, "transcript.jsonl")
            with open(transcript, "w") as f:
                f.write(json.dumps({"message": {"content": "Hello " * 100}}) + "\n")

            # UserPromptSubmit
            session_id = "test-session-001"
            data_submit = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": session_id,
                "transcript_path": transcript,
            }
            handle_user_prompt_submit(data_submit, tb)

            # 验证临时状态文件
            state_file = get_state_file(session_id)
            assert os.path.exists(state_file)

            # 追加更多内容模拟响应
            with open(transcript, "a") as f:
                f.write(json.dumps({"message": {"content": "Response " * 200}}) + "\n")

            # Stop
            data_stop = {
                "hook_event_name": "Stop",
                "session_id": session_id,
                "transcript_path": transcript,
            }
            handle_stop(data_stop, tb)

            # 验证预算记录
            s = tb.status()
            assert s["used_tokens"] > 0, "Should have recorded tokens"

        # 执行所有测试
        print(f"\n🧪 运行 {len(tests)} 个测试...\n")
        for name, fn in tests:
            try:
                fn()
                print(f"  ✅ {name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                failed += 1

        print(f"\n{'='*50}")
        print(f"  通过: {passed}  失败: {failed}  总计: {len(tests)}")
        print(f"{'='*50}\n")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return failed == 0


# ══════════════════════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Context Tracker + Token Budget - OpenClaw 上下文追踪与预算管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Hook模式
  echo '{"hook_event_name":"Stop","session_id":"xxx"}' | python3 scripts/context_tracker.py --hook

  # 预算管理
  python3 scripts/context_tracker.py status          # 查看预算状态
  python3 scripts/context_tracker.py record 1500     # 记录token消耗
  python3 scripts/context_tracker.py check           # 检查告警
  python3 scripts/context_tracker.py reset           # 重置预算
  python3 scripts/context_tracker.py continue        # 续期预算
  python3 scripts/context_tracker.py report          # 详细报告

  # Token估算
  python3 scripts/context_tracker.py estimate "some text"
  python3 scripts/context_tracker.py estimate --file script.py

  # 测试
  python3 scripts/context_tracker.py --test
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["status", "record", "check", "reset", "continue", "report", "estimate"],
        default="status",
        help="操作命令",
    )
    parser.add_argument(
        "tokens_or_text",
        nargs="?",
        help="token数量（record命令）或文本内容（estimate命令）",
    )
    parser.add_argument(
        "-d", "--description",
        default="",
        help="使用描述（record命令可选）",
    )
    parser.add_argument(
        "--config",
        help="指定配置文件路径",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以JSON格式输出",
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help="Hook模式：从stdin读取Claude Code事件",
    )
    parser.add_argument(
        "--file",
        help="估算模式：指定文件路径",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="运行测试模式",
    )

    args = parser.parse_args()

    # 测试模式
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    # 初始化预算管理器
    budget = TokenBudget(config_path=args.config)

    # Hook模式
    if args.hook:
        run_hook_mode(budget)
        return  # run_hook_mode 内部会 sys.exit

    # CLI命令模式
    if args.command == "status":
        result = budget.status()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(TokenBudget.format_status(result))

    elif args.command == "record":
        if args.tokens_or_text is None:
            print("❌ 错误: record 命令需要指定 token 数量")
            print("用法: python3 scripts/context_tracker.py record <tokens> [-d 描述]")
            sys.exit(1)
        try:
            tokens = int(args.tokens_or_text)
        except ValueError:
            print(f"❌ 错误: 无效的token数量 '{args.tokens_or_text}'")
            sys.exit(1)
        result = budget.record(tokens, args.description)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"✅ {result['message']}")
            print(
                f"   已用: {result['used_tokens']:,} | "
                f"剩余: {result['remaining_tokens']:,} | "
                f"使用率: {result['usage_percent']}"
            )

    elif args.command == "check":
        result = budget.check()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(TokenBudget.format_check(result))

    elif args.command == "reset":
        result = budget.reset()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"✅ {result['message']}")
            print(f"   预算: {result['total_budget']:,} tokens | 已用: {result['used_tokens']:,}")

    elif args.command == "continue":
        result = budget.continue_budget()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["success"]:
                print(f"✅ {result['message']}")
                print(f"   总预算: {result['total_budget']:,} | 剩余: {result['remaining_tokens']:,}")
            else:
                print(f"❌ {result['message']}")

    elif args.command == "report":
        result = budget.report()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(TokenBudget.format_report(result))

    elif args.command == "estimate":
        if args.file:
            tokens = estimate_file(args.file)
            if tokens > 0:
                print(f"📄 文件估算: ~{tokens:,} tokens")
        elif args.tokens_or_text:
            tokens = estimate_text(args.tokens_or_text)
            print(f"📝 文本估算: ~{tokens:,} tokens")
        else:
            print("❌ 请提供文本或 --file 参数")
            print("用法: python3 scripts/context_tracker.py estimate 'text here'")
            print("      python3 scripts/context_tracker.py estimate --file /path/to/file")
            sys.exit(1)


if __name__ == "__main__":
    main()
