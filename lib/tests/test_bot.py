"""
Test cases for Bot conversation & message handling.

Covers: message routing, command parsing, session management, context tracking.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from tests.mock_mongo import MockMongoClient

mock_client = MockMongoClient()
mock_db = mock_client["bot_conversations"]

# Seed test data
mock_db.sessions.insert_many([
    {
        "_id": "sess_001",
        "user_id": "ou_user001",
        "chat_id": "oc_group001",
        "session_type": "group",
        "context": {"last_intent": "greeting", "turn_count": 5},
        "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "last_active": datetime.now(timezone.utc) - timedelta(minutes=5),
        "is_active": True
    },
    {
        "_id": "sess_002",
        "user_id": "ou_user002",
        "chat_id": "oc_group001",
        "session_type": "group",
        "context": {"last_intent": "help", "turn_count": 3},
        "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "last_active": datetime.now(timezone.utc) - timedelta(minutes=30),
        "is_active": True
    },
    {
        "_id": "sess_003",
        "user_id": "ou_user001",
        "chat_id": None,
        "session_type": "p2p",
        "context": {"last_intent": "settings", "turn_count": 12},
        "created_at": datetime.now(timezone.utc) - timedelta(days=1),
        "last_active": datetime.now(timezone.utc) - timedelta(hours=3),
        "is_active": False
    }
])

mock_db.messages.insert_many([
    {
        "_id": "msg_001",
        "session_id": "sess_001",
        "message_id": "om_msg001",
        "sender_id": "ou_user001",
        "msg_type": "text",
        "content": "你好",
        "intent": "greeting",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=10)
    },
    {
        "_id": "msg_002",
        "session_id": "sess_001",
        "message_id": "om_msg002",
        "sender_id": "bot",
        "msg_type": "text",
        "content": "你好！有什么可以帮你的吗？",
        "intent": "greeting_response",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=9)
    },
    {
        "_id": "msg_003",
        "session_id": "sess_001",
        "message_id": "om_msg003",
        "sender_id": "ou_user001",
        "msg_type": "text",
        "content": "帮我查看今天的数据",
        "intent": "query",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=5)
    },
    {
        "_id": "msg_004",
        "session_id": "sess_002",
        "message_id": "om_msg004",
        "sender_id": "ou_user002",
        "msg_type": "text",
        "content": "help",
        "intent": "help",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=30)
    }
])


# ─── Session Tests ───────────────────────────────────────────────────────────

def test_list_active_sessions():
    """Test listing active sessions."""
    sessions = list(mock_db.sessions.find({"is_active": True}))
    assert len(sessions) == 2


def test_find_session_by_user():
    """Test finding a session by user_id."""
    session = mock_db.sessions.find_one({"user_id": "ou_user001", "session_type": "p2p"})
    assert session is not None
    assert session["_id"] == "sess_003"
    assert session["session_type"] == "p2p"


def test_find_session_by_chat():
    """Test finding sessions in a group chat."""
    sessions = list(mock_db.sessions.find({"chat_id": "oc_group001"}))
    assert len(sessions) == 2


def test_session_turn_count():
    """Test session context tracking."""
    session = mock_db.sessions.find_one({"_id": "sess_001"})
    assert session["context"]["turn_count"] == 5


def test_update_session_activity():
    """Test updating session last_active timestamp."""
    result = mock_db.sessions.update_one(
        {"_id": "sess_001"},
        {"$set": {"last_active": datetime.now(timezone.utc)}}
    )
    assert result.modified_count == 1

    session = mock_db.sessions.find_one({"_id": "sess_001"})
    assert session["last_active"] is not None


def test_deactivate_session():
    """Test deactivating a session."""
    result = mock_db.sessions.update_one(
        {"_id": "sess_002"},
        {"$set": {"is_active": False}}
    )
    assert result.modified_count == 1

    session = mock_db.sessions.find_one({"_id": "sess_002"})
    assert session["is_active"] is False


# ─── Message Tests ───────────────────────────────────────────────────────────

def test_list_messages_in_session():
    """Test listing messages in a session."""
    messages = list(mock_db.messages.find({"session_id": "sess_001"}))
    assert len(messages) == 3


def test_messages_chronological():
    """Test messages are returned in chronological order."""
    cursor = mock_db.messages.find({"session_id": "sess_001"})
    messages = list(cursor.sort("created_at", 1))
    assert messages[0]["message_id"] == "om_msg001"
    assert messages[1]["message_id"] == "om_msg002"
    assert messages[2]["message_id"] == "om_msg003"


def test_filter_by_sender():
    """Test filtering messages by sender type."""
    bot_msgs = list(mock_db.messages.find({"sender_id": "bot"}))
    assert len(bot_msgs) == 1
    assert bot_msgs[0]["msg_type"] == "text"


def test_filter_by_intent():
    """Test filtering messages by intent."""
    greeting_msgs = list(mock_db.messages.find({"intent": "greeting"}))
    assert len(greeting_msgs) == 1
    assert greeting_msgs[0]["content"] == "你好"


def test_insert_new_message():
    """Test inserting a new message."""
    new_msg = {
        "_id": "msg_005",
        "session_id": "sess_001",
        "message_id": "om_msg005",
        "sender_id": "bot",
        "msg_type": "text",
        "content": "好的，正在为您查询今天的销售数据...",
        "intent": "query_response",
        "created_at": datetime.now(timezone.utc)
    }
    result = mock_db.messages.insert_one(new_msg)
    assert result.acknowledged

    msg = mock_db.messages.find_one({"message_id": "om_msg005"})
    assert msg is not None
    assert "销售数据" in msg["content"]


# ─── Aggregation Tests ───────────────────────────────────────────────────────

def test_aggregate_messages_by_intent():
    """Test message count by intent."""
    pipeline = [
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(mock_db.messages.aggregate(pipeline))
    assert len(results) >= 4
    total = sum(r["count"] for r in results)
    assert total >= 4


def test_aggregate_session_message_counts():
    """Test counting messages per session."""
    pipeline = [
        {"$group": {"_id": "$session_id", "msg_count": {"$sum": 1}}},
        {"$sort": {"msg_count": -1}}
    ]
    results = list(mock_db.messages.aggregate(pipeline))
    assert len(results) >= 2
    assert results[0]["msg_count"] >= 3  # sess_001 has most messages


def test_aggregate_user_message_frequency():
    """Test counting messages per user (excluding bot)."""
    pipeline = [
        {"$match": {"sender_id": {"$ne": "bot"}}},
        {"$group": {"_id": "$sender_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(mock_db.messages.aggregate(pipeline))
    users = {r["_id"] for r in results}
    assert "ou_user001" in users
    assert "ou_user002" in users


# ─── Cross-Collection Query Tests ────────────────────────────────────────────

def test_get_session_with_messages():
    """Test retrieving a session and its messages together."""
    session = mock_db.sessions.find_one({"_id": "sess_001"})
    assert session is not None

    messages = list(mock_db.messages.find({"session_id": "sess_001"}))
    assert len(messages) > 0
    assert session["context"]["turn_count"] == len(messages)


def test_find_user_sessions_with_latest_message():
    """Test finding all sessions for a user with their latest messages."""
    user_sessions = list(mock_db.sessions.find({"user_id": "ou_user001"}))
    assert len(user_sessions) == 2

    for session in user_sessions:
        messages = list(
            mock_db.messages.find({"session_id": session["_id"]})
            .sort("created_at", -1)
            .limit(1)
        )
        # At least one session (sess_001) should have messages
        if session["_id"] == "sess_001":
            assert len(messages) == 1


# ─── Edge Cases ──────────────────────────────────────────────────────────────

def test_empty_session_messages():
    """Test querying messages for an empty session."""
    messages = list(mock_db.messages.find({"session_id": "sess_empty"}))
    assert len(messages) == 0


def test_distinct_intents():
    """Test getting distinct intents."""
    intents = mock_db.messages.distinct("intent")
    assert len(intents) >= 4
    assert "greeting" in intents
    assert "query" in intents


def test_time_range_filter():
    """Test filtering messages by time range."""
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = list(mock_db.messages.find({
        "created_at": {"$gte": one_hour_ago}
    }))
    assert len(recent) >= 3  # most messages are recent
