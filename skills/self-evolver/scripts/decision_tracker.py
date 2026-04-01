"""
决策追踪器 — 记录决策依据，支持复盘
Usage: 
  python3 decision_tracker.py record "选择React而非Vue" "团队熟悉度+生态"
  python3 decision_tracker.py review
  python3 decision_tracker.py stats
"""

import sys
import json
from pathlib import Path
from datetime import datetime

DECISIONS_FILE = Path("/Users/narain/.openclaw/workspace/memory/decisions.jsonl")


def record_decision(decision: str, reason: str, category: str = "general"):
    """记录决策"""
    DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "reason": reason,
        "category": category,
        "outcome": None,  # 后续复盘时填写
    }
    
    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"✅ 决策已记录：{decision}")


def review_decisions(n: int = 10):
    """查看最近的决策"""
    if not DECISIONS_FILE.exists():
        print("📭 暂无决策记录")
        return
    
    lines = DECISIONS_FILE.read_text().strip().split("\n")
    recent = lines[-n:]
    
    print(f"\n📊 最近 {len(recent)} 条决策")
    print("=" * 50)
    
    for i, line in enumerate(recent, 1):
        entry = json.loads(line)
        time = entry["timestamp"][:16].replace("T", " ")
        outcome = "✅" if entry.get("outcome") == "good" else "❌" if entry.get("outcome") == "bad" else "⏳"
        print(f"{i}. [{time}] {outcome} {entry['decision']}")
        print(f"   理由：{entry['reason']}")
    
    print("=" * 50)


def mark_outcome(decision_keyword: str, outcome: str):
    """标记决策结果"""
    if not DECISIONS_FILE.exists():
        print("📭 暂无决策记录")
        return
    
    lines = DECISIONS_FILE.read_text().strip().split("\n")
    updated = False
    
    for i, line in enumerate(lines):
        entry = json.loads(line)
        if decision_keyword in entry["decision"] and entry.get("outcome") is None:
            entry["outcome"] = outcome
            lines[i] = json.dumps(entry, ensure_ascii=False)
            updated = True
            print(f"✅ 已标记：{entry['decision']} → {outcome}")
            break
    
    if updated:
        DECISIONS_FILE.write_text("\n".join(lines) + "\n")
    else:
        print(f"⚠️ 未找到匹配的决策：{decision_keyword}")


def stats():
    """决策统计"""
    if not DECISIONS_FILE.exists():
        print("📭 暂无决策记录")
        return
    
    lines = DECISIONS_FILE.read_text().strip().split("\n")
    total = len(lines)
    good = sum(1 for l in lines if json.loads(l).get("outcome") == "good")
    bad = sum(1 for l in lines if json.loads(l).get("outcome") == "bad")
    pending = total - good - bad
    
    print(f"\n📊 决策统计")
    print("=" * 50)
    print(f"总计：{total} 条")
    print(f"✅ 好决策：{good} ({good/total*100:.0f}%)" if total else "")
    print(f"❌ 坏决策：{bad} ({bad/total*100:.0f}%)" if total else "")
    print(f"⏳ 待复盘：{pending}")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  record <decision> <reason> [category]")
        print("  review [n]")
        print("  mark <keyword> <good|bad>")
        print("  stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "record":
        decision = sys.argv[2] if len(sys.argv) > 2 else ""
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        category = sys.argv[4] if len(sys.argv) > 4 else "general"
        record_decision(decision, reason, category)
    
    elif cmd == "review":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        review_decisions(n)
    
    elif cmd == "mark":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        outcome = sys.argv[3] if len(sys.argv) > 3 else "good"
        mark_outcome(keyword, outcome)
    
    elif cmd == "stats":
        stats()
    
    else:
        print(f"Unknown command: {cmd}")
