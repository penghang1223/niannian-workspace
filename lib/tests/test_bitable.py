"""
Test cases for Feishu Bitable (多维表格) operations.

Covers: create app, create table, CRUD records, fields, views, filters, sorting.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Setup mock MongoDB
from tests.mock_mongo import MockMongoClient

mock_client = MockMongoClient()
mock_db = mock_client["feishu_bitable"]

# Insert test data
mock_db.apps.insert_one({
    "_id": "app_001",
    "app_token": "bascn9Mn3qO4vXYZ",
    "name": "测试多维表格",
    "folder_token": "fldcnXXXXXX",
    "url": "https://xxx.feishu.cn/base/bascn9Mn3qO4vXYZ",
    "created_by": "ou_abc123",
    "created_at": datetime.now(timezone.utc),
    "tables": ["tbl_001"]
})

mock_db.tables.insert_one({
    "_id": "tbl_001",
    "app_token": "bascn9Mn3qO4vXYZ",
    "table_id": "tbl001",
    "name": "数据表1",
    "default_view_name": "默认视图",
    "fields": [
        {"field_id": "fld001", "field_name": "任务名称", "type": 1},
        {"field_id": "fld002", "field_name": "状态", "type": 3, "property": {"options": [{"name": "进行中"}, {"name": "已完成"}]}},
        {"field_id": "fld003", "field_name": "优先级", "type": 2},
        {"field_id": "fld004", "field_name": "标签", "type": 4},
        {"field_id": "fld005", "field_name": "截止日期", "type": 5},
    ],
    "created_at": datetime.now(timezone.utc)
})

mock_db.records.insert_many([
    {
        "_id": "rec_001",
        "app_token": "bascn9Mn3qO4vXYZ",
        "table_id": "tbl001",
        "record_id": "rec001",
        "fields": {
            "任务名称": "完成PRD文档",
            "状态": "进行中",
            "优先级": 1,
            "标签": ["产品", "紧急"],
            "截止日期": 1740441600000
        },
        "created_time": datetime.now(timezone.utc) - timedelta(days=2),
        "last_modified_time": datetime.now(timezone.utc) - timedelta(hours=1)
    },
    {
        "_id": "rec_002",
        "app_token": "bascn9Mn3qO4vXYZ",
        "table_id": "tbl001",
        "record_id": "rec002",
        "fields": {
            "任务名称": "设计评审",
            "状态": "已完成",
            "优先级": 2,
            "标签": ["设计"],
            "截止日期": 1740355200000
        },
        "created_time": datetime.now(timezone.utc) - timedelta(days=3),
        "last_modified_time": datetime.now(timezone.utc) - timedelta(days=1)
    },
    {
        "_id": "rec_003",
        "app_token": "bascn9Mn3qO4vXYZ",
        "table_id": "tbl001",
        "record_id": "rec003",
        "fields": {
            "任务名称": "用户调研",
            "状态": "进行中",
            "优先级": 3,
            "标签": ["产品", "研究"],
            "截止_date": 1740528000000
        },
        "created_time": datetime.now(timezone.utc) - timedelta(days=1),
        "last_modified_time": datetime.now(timezone.utc)
    }
])

# ─── CRUD Record Tests ───────────────────────────────────────────────────────

def test_list_records():
    """Test listing records from a table."""
    records = list(mock_db.records.find({"table_id": "tbl001"}))
    assert len(records) == 3
    assert records[0]["fields"]["任务名称"] == "完成PRD文档"


def test_filter_records_by_status():
    """Test filtering records by single-select field."""
    records = list(mock_db.records.find({
        "table_id": "tbl001",
        "fields.状态": "进行中"
    }))
    assert len(records) == 2
    for r in records:
        assert r["fields"]["状态"] == "进行中"


def test_filter_records_by_tags():
    """Test filtering records by multi-select field using $all."""
    records = list(mock_db.records.find({
        "table_id": "tbl001",
        "fields.标签": {"$all": ["产品"]}
    }))
    assert len(records) == 2


def test_filter_records_by_priority_range():
    """Test filtering by numeric field with range."""
    records = list(mock_db.records.find({
        "table_id": "tbl001",
        "fields.优先级": {"$lte": 2}
    }))
    assert len(records) == 2
    for r in records:
        assert r["fields"]["优先级"] <= 2


def test_sort_records_by_priority():
    """Test sorting records by priority."""
    cursor = mock_db.records.find({"table_id": "tbl001"})
    records = list(cursor.sort("fields.优先级", 1))
    assert records[0]["fields"]["优先级"] == 1
    assert records[-1]["fields"]["优先级"] == 3


def test_pagination():
    """Test pagination with skip and limit."""
    cursor = mock_db.records.find({"table_id": "tbl001"})
    page1 = list(cursor.sort("record_id", 1).skip(0).limit(2))
    assert len(page1) == 2

    cursor2 = mock_db.records.find({"table_id": "tbl001"})
    page2 = list(cursor2.sort("record_id", 1).skip(2).limit(2))
    assert len(page2) == 1


def test_insert_record():
    """Test inserting a new record."""
    new_record = {
        "app_token": "bascn9Mn3qO4vXYZ",
        "table_id": "tbl001",
        "record_id": "rec004",
        "fields": {
            "任务名称": "新任务",
            "状态": "进行中",
            "优先级": 1,
            "标签": ["开发"],
        }
    }
    result = mock_db.records.insert_one(new_record)
    assert result.acknowledged

    found = mock_db.records.find_one({"record_id": "rec004"})
    assert found is not None
    assert found["fields"]["任务名称"] == "新任务"


def test_update_record():
    """Test updating a record's fields."""
    result = mock_db.records.update_one(
        {"record_id": "rec001"},
        {"$set": {"fields.状态": "已完成"}}
    )
    assert result.modified_count == 1

    found = mock_db.records.find_one({"record_id": "rec001"})
    assert found["fields"]["状态"] == "已完成"


def test_delete_record():
    """Test deleting a record."""
    result = mock_db.records.delete_one({"record_id": "rec003"})
    assert result.deleted_count == 1

    found = mock_db.records.find_one({"record_id": "rec003"})
    assert found is None


def test_count_records():
    """Test counting records."""
    count = mock_db.records.count_documents({"table_id": "tbl001"})
    assert count >= 2  # after delete test


# ─── App & Table Tests ───────────────────────────────────────────────────────

def test_create_app():
    """Test creating a bitable app."""
    new_app = {
        "_id": "app_002",
        "app_token": "bascnNEWtoken",
        "name": "新多维表格",
        "folder_token": "fldcnYYYYYY",
        "url": "https://xxx.feishu.cn/base/bascnNEWtoken",
        "created_by": "ou_def456",
        "created_at": datetime.now(timezone.utc),
        "tables": []
    }
    result = mock_db.apps.insert_one(new_app)
    assert result.acknowledged

    found = mock_db.apps.find_one({"app_token": "bascnNEWtoken"})
    assert found is not None
    assert found["name"] == "新多维表格"


def test_create_table_with_fields():
    """Test creating a table with predefined fields."""
    new_table = {
        "_id": "tbl_002",
        "app_token": "bascn9Mn3qO4vXYZ",
        "table_id": "tbl002",
        "name": "数据表2",
        "default_view_name": "默认视图",
        "fields": [
            {"field_id": "fld101", "field_name": "客户名称", "type": 1},
            {"field_id": "fld102", "field_name": "订单金额", "type": 2},
            {"field_id": "fld103", "field_name": "下单日期", "type": 5},
        ],
        "created_at": datetime.now(timezone.utc)
    }
    result = mock_db.tables.insert_one(new_table)
    assert result.acknowledged

    found = mock_db.tables.find_one({"table_id": "tbl002"})
    assert found is not None
    assert len(found["fields"]) == 3


# ─── Aggregation Tests ───────────────────────────────────────────────────────

def test_aggregate_records_by_status():
    """Test grouping records by status."""
    pipeline = [
        {"$match": {"table_id": "tbl001"}},
        {"$group": {"_id": "$fields.状态", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(mock_db.records.aggregate(pipeline))
    assert len(results) >= 2
    statuses = {r["_id"] for r in results}
    assert "进行中" in statuses
    assert "已完成" in statuses


def test_aggregate_tag_distribution():
    """Test analyzing tag distribution with $unwind."""
    pipeline = [
        {"$match": {"table_id": "tbl001"}},
        {"$unwind": "$fields.标签"},
        {"$group": {"_id": "$fields.标签", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(mock_db.records.aggregate(pipeline))
    assert len(results) >= 3  # 产品, 紧急, 设计, 研究
    tags = {r["_id"] for r in results}
    assert "产品" in tags
    assert "设计" in tags


def test_aggregate_avg_priority_by_status():
    """Test computing average priority by status."""
    pipeline = [
        {"$match": {"table_id": "tbl001"}},
        {"$group": {"_id": "$fields.状态", "avg_priority": {"$avg": "$fields.优先级"}}}
    ]
    results = list(mock_db.records.aggregate(pipeline))
    assert len(results) >= 2
    for r in results:
        assert "avg_priority" in r
        assert isinstance(r["avg_priority"], (int, float))


# ─── Field Type Tests ────────────────────────────────────────────────────────

def test_distinct_field_values():
    """Test getting distinct values for a field."""
    statuses = mock_db.records.distinct("fields.状态")
    assert "进行中" in statuses
    assert "已完成" in statuses


def test_nested_field_query():
    """Test querying nested document fields."""
    record = mock_db.records.find_one({"record_id": "rec001"})
    assert record["fields"]["任务名称"] == "完成PRD文档"
    assert record["fields"]["优先级"] == 1
    assert "产品" in record["fields"]["标签"]


# ─── Edge Cases ──────────────────────────────────────────────────────────────

def test_find_nonexistent_record():
    """Test finding a record that doesn't exist."""
    result = mock_db.records.find_one({"record_id": "nonexistent"})
    assert result is None


def test_delete_nonexistent_record():
    """Test deleting a record that doesn't exist."""
    result = mock_db.records.delete_one({"record_id": "nonexistent"})
    assert result.deleted_count == 0


def test_update_nonexistent_record():
    """Test updating a record that doesn't exist."""
    result = mock_db.records.update_one(
        {"record_id": "nonexistent"},
        {"$set": {"fields.状态": "已完成"}}
    )
    assert result.modified_count == 0


def test_upsert_record():
    """Test upserting a record."""
    result = mock_db.records.update_one(
        {"record_id": "rec_upsert"},
        {"$set": {"fields.任务名称": "Upsert任务", "table_id": "tbl001"}},
        upsert=True
    )
    assert result.upserted_id is not None

    found = mock_db.records.find_one({"record_id": "rec_upsert"})
    assert found is not None
    assert found["fields"]["任务名称"] == "Upsert任务"
