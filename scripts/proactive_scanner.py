#!/usr/bin/env python3
"""
主动消息扫描脚本
用于心跳时扫描飞书消息，发现问题并管理催促状态
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 工作空间路径
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/Users/narain/.openclaw/workspace"))
ESCALATION_STATE_FILE = WORKSPACE / "memory" / "escalation-state.json"

# 关键词列表
KEYWORDS = [
    "待办", "跟进", "TODO", "Action", "截止", "urgent", "紧急",
    "明天", "下周", "逾期", "deadline", "reminder", "提醒"
]

# 催促延迟配置（小时）
DEFAULT_CONFIG = {
    "reminder_delay_hours": 24,
    "urge_delay_hours": 48,
    "escalate_delay_hours": 72,
    "max_reminders": 3
}


def load_escalation_state():
    """加载催促状态"""
    if ESCALATION_STATE_FILE.exists():
        with open(ESCALATION_STATE_FILE, "r") as f:
            return json.load(f)
    return {"items": [], "config": DEFAULT_CONFIG, "last_scan": None, "version": "1.0"}


def save_escalation_state(state):
    """保存催促状态"""
    ESCALATION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ESCALATION_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def check_escalation_items(state):
    """检查催促状态，返回需要行动的项目"""
    now = datetime.now()
    actions = []
    
    config = state.get("config", DEFAULT_CONFIG)
    reminder_delay = timedelta(hours=config.get("reminder_delay_hours", 24))
    urge_delay = timedelta(hours=config.get("urge_delay_hours", 48))
    escalate_delay = timedelta(hours=config.get("escalate_delay_hours", 72))
    
    for item in state.get("items", []):
        if item.get("state") == "completed":
            continue
            
        created = datetime.fromisoformat(item["created"])
        elapsed = now - created
        
        current_state = item.get("state", "pending")
        
        if current_state == "pending" and elapsed > reminder_delay:
            actions.append({
                "item_id": item["id"],
                "action": "remind",
                "description": item["description"],
                "elapsed_hours": elapsed.total_seconds() / 3600
            })
        elif current_state == "reminded" and elapsed > urge_delay:
            actions.append({
                "item_id": item["id"],
                "action": "urge",
                "description": item["description"],
                "elapsed_hours": elapsed.total_seconds() / 3600
            })
        elif current_state == "urged" and elapsed > escalate_delay:
            actions.append({
                "item_id": item["id"],
                "action": "escalate",
                "description": item["description"],
                "elapsed_hours": elapsed.total_seconds() / 3600
            })
    
    return actions


def add_escalation_item(state, item_id, description, assignee="主人"):
    """添加新的催促项"""
    now = datetime.now().isoformat()
    
    # 检查是否已存在
    for item in state.get("items", []):
        if item["id"] == item_id:
            return False  # 已存在
    
    state["items"].append({
        "id": item_id,
        "description": description,
        "created": now,
        "state": "pending",
        "remind_count": 0,
        "last_reminded": None,
        "assignee": assignee
    })
    
    return True


def update_item_state(state, item_id, new_state):
    """更新催促项状态"""
    for item in state.get("items", []):
        if item["id"] == item_id:
            item["state"] = new_state
            if new_state == "reminded":
                item["remind_count"] = item.get("remind_count", 0) + 1
                item["last_reminded"] = datetime.now().isoformat()
            return True
    return False


def remove_completed_item(state, item_id):
    """移除已完成的催促项"""
    state["items"] = [item for item in state.get("items", []) if item["id"] != item_id]
    return True


def generate_scan_report(state, scan_results):
    """生成扫描报告"""
    actions = check_escalation_items(state)
    
    report = {
        "scan_time": datetime.now().isoformat(),
        "messages_scanned": scan_results.get("total_messages", 0),
        "issues_found": len(scan_results.get("issues", [])),
        "issues": scan_results.get("issues", []),
        "escalation_actions": actions,
        "pending_items": len([i for i in state.get("items", []) if i.get("state") == "pending"]),
        "reminded_items": len([i for i in state.get("items", []) if i.get("state") == "reminded"]),
        "urged_items": len([i for i in state.get("items", []) if i.get("state") == "urged"]),
        "escalated_items": len([i for i in state.get("items", []) if i.get("state") == "escalated"])
    }
    
    return report


if __name__ == "__main__":
    # 测试代码
    state = load_escalation_state()
    print(f"当前催促状态: {len(state.get('items', []))} 个项目")
    
    # 添加测试项
    add_escalation_item(state, "test-001", "测试催促功能")
    save_escalation_state(state)
    
    # 检查催促
    actions = check_escalation_items(state)
    print(f"需要行动: {len(actions)} 项")
    
    for action in actions:
        print(f"  - {action['action']}: {action['description']}")
