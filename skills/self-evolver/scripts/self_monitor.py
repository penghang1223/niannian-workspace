"""
年年自我监控脚本 - 每次心跳自动检查自身状态
Usage: python3 scripts/self_monitor.py
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys


WORKSPACE = Path("/Users/narain/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SHARED_KNOWLEDGE = WORKSPACE / "SHARED_KNOWLEDGE.md"
LEARNING_PLAN = WORKSPACE / "memory" / "LEARNING_PLAN.md"
SELF_IMPROVEMENT = WORKSPACE / "memory" / "SELF_IMPROVEMENT.md"


def check_learning_continuity():
    """检查学习连续性"""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    if not daily_file.exists():
        return {"status": "⚠️", "message": "今日无学习记录"}
    
    content = daily_file.read_text()
    
    # 检查是否有学习汇报记录
    learning_markers = ["学习汇报", "核心收获", "价值评估"]
    found = [m for m in learning_markers if m in content]
    
    if len(found) >= 2:
        return {"status": "✅", "message": f"今日有学习记录（{len(found)}/3 标记）"}
    else:
        return {"status": "🟡", "message": f"学习记录不完整（{len(found)}/3 标记）"}


def check_file_health():
    """检查文件健康度"""
    issues = []
    
    # 检查关键文件是否存在
    critical_files = [
        (MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md", "今日记忆"),
        (SHARED_KNOWLEDGE, "共享知识库"),
        (LEARNING_PLAN, "学习计划"),
        (SELF_IMPROVEMENT, "自我提升计划"),
    ]
    
    for file_path, name in critical_files:
        if not file_path.exists():
            issues.append(f"❌ {name} 不存在")
    
    # 检查记忆文件大小
    for md_file in MEMORY_DIR.glob("*.md"):
        size = md_file.stat().st_size
        if size > 100 * 1024:  # > 100KB
            issues.append(f"⚠️ {md_file.name} 过大（{size/1024:.0f}KB）")
    
    if issues:
        return {"status": "⚠️", "message": "; ".join(issues)}
    else:
        return {"status": "✅", "message": "所有关键文件健康"}


def check_error_patterns():
    """检查错误模式"""
    # 简化版：检查是否在 lessons.md 中有重复的错误
    lessons_file = MEMORY_DIR / "agents" / "main" / "lessons.md"
    
    if not lessons_file.exists():
        return {"status": "✅", "message": "无历史错误记录"}
    
    content = lessons_file.read_text()
    
    # 检查是否有重复的错误模式
    error_keywords = ["重复犯错", "再次失败", "同样的问题"]
    found = [k for k in error_keywords if k in content]
    
    if found:
        return {"status": "⚠️", "message": f"发现 {len(found)} 个错误模式"}
    else:
        return {"status": "✅", "message": "无重复错误模式"}


def check_coordination_efficiency():
    """检查协调效率"""
    # 检查今日学习汇报数量
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    if not daily_file.exists():
        return {"status": "🟡", "message": "无今日数据"}
    
    content = daily_file.read_text()
    
    # 统计学习汇报数量
    report_count = content.count("学习汇报")
    
    if report_count >= 5:
        return {"status": "✅", "message": f"今日收到 {report_count} 份学习汇报"}
    elif report_count >= 2:
        return {"status": "🟡", "message": f"今日收到 {report_count} 份学习汇报（较少）"}
    else:
        return {"status": "⚠️", "message": f"今日仅 {report_count} 份学习汇报"}


def generate_report():
    """生成监控报告"""
    print("🎀 年年自我监控报告")
    print("=" * 50)
    print(f"📅 日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    checks = [
        ("📚 学习连续性", check_learning_continuity()),
        ("📁 文件健康度", check_file_health()),
        ("🔄 错误模式", check_error_patterns()),
        ("🤝 协调效率", check_coordination_efficiency()),
    ]
    
    for name, result in checks:
        print(f"{name}: {result['status']} {result['message']}")
    
    print()
    print("=" * 50)
    
    # 返回状态
    all_good = all(r["status"] == "✅" for _, r in checks)
    if all_good:
        print("✅ 年年状态良好！")
    else:
        print("⚠️ 有项目需要关注")


if __name__ == "__main__":
    generate_report()
