"""Mock MongoDB client and collections for testing without a real database."""
import copy
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId


class InsertOneResult:
    def __init__(self, inserted_id, acknowledged=True):
        self.inserted_id = inserted_id
        self.acknowledged = acknowledged


def get_nested_value(doc: dict, field_path: str):
    """Get a nested value from a document using dot notation."""
    parts = field_path.split(".")
    current = doc
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def set_nested_value(doc: dict, field_path: str, value):
    """Set a nested value in a document using dot notation."""
    parts = field_path.split(".")
    current = doc
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def matches_filter(doc: dict, filter_spec: dict) -> bool:
    """Check if a document matches a MongoDB-style filter."""
    if not filter_spec:
        return True

    for key, condition in filter_spec.items():
        if key == "$or":
            if not any(matches_filter(doc, sub) for sub in condition):
                return False
            continue

        if key == "$and":
            if not all(matches_filter(doc, sub) for sub in condition):
                return False
            continue

        doc_value = get_nested_value(doc, key)

        if isinstance(condition, dict):
            for op, op_value in condition.items():
                if op == "$eq":
                    if doc_value != op_value:
                        return False
                elif op == "$ne":
                    if doc_value == op_value:
                        return False
                elif op == "$gt":
                    if not (doc_value is not None and doc_value > op_value):
                        return False
                elif op == "$gte":
                    if not (doc_value is not None and doc_value >= op_value):
                        return False
                elif op == "$lt":
                    if not (doc_value is not None and doc_value < op_value):
                        return False
                elif op == "$lte":
                    if not (doc_value is not None and doc_value <= op_value):
                        return False
                elif op == "$in":
                    if doc_value not in op_value:
                        return False
                elif op == "$nin":
                    if doc_value in op_value:
                        return False
                elif op == "$exists":
                    exists = doc_value is not None
                    if op_value != exists:
                        return False
                elif op == "$regex":
                    if doc_value is None or not re.search(op_value, str(doc_value)):
                        return False
                elif op == "$all":
                    if not isinstance(doc_value, list):
                        return False
                    if not all(item in doc_value for item in op_value):
                        return False
                elif op == "$elemMatch":
                    if not isinstance(doc_value, list):
                        return False
                    if not any(matches_filter(item, op_value) if isinstance(item, dict) else item == op_value for item in doc_value):
                        return False
        else:
            # Direct equality check
            if doc_value != condition:
                return False

    return True


def execute_aggregation(documents: List[Dict], pipeline: List[Dict]) -> List[Dict]:
    """Execute a MongoDB aggregation pipeline on a list of documents."""
    result = copy.deepcopy(documents)

    for stage in pipeline:
        if "$match" in stage:
            result = [doc for doc in result if matches_filter(doc, stage["$match"])]

        elif "$group" in stage:
            groups = {}
            group_spec = stage["$group"]
            group_id = group_spec["_id"]

            for doc in result:
                if group_id is None:
                    key = "__null__"
                elif isinstance(group_id, str) and group_id.startswith("$"):
                    key = get_nested_value(doc, group_id[1:])
                elif isinstance(group_id, dict):
                    key = {}
                    for k, v in group_id.items():
                        if isinstance(v, str) and v.startswith("$"):
                            key[k] = get_nested_value(doc, v[1:])
                        else:
                            key[k] = v
                    key = str(sorted(key.items()))
                else:
                    key = str(group_id)

                if key not in groups:
                    groups[key] = {"_id": key if group_id is None else get_nested_value(doc, group_id[1:]) if isinstance(group_id, str) and group_id.startswith("$") else group_id}

                for field_name, accumulator in group_spec.items():
                    if field_name == "_id":
                        continue

                    if "$sum" in accumulator:
                        val = accumulator["$sum"]
                        if isinstance(val, (int, float)):
                            groups[key].setdefault(field_name, 0)
                            groups[key][field_name] += val
                        elif isinstance(val, str) and val.startswith("$"):
                            groups[key].setdefault(field_name, 0)
                            groups[key][field_name] += get_nested_value(doc, val[1:]) or 0

                    elif "$avg" in accumulator:
                        val = accumulator["$avg"]
                        if isinstance(val, str) and val.startswith("$"):
                            groups[key].setdefault(field_name, [])
                            groups[key][field_name].append(get_nested_value(doc, val[1:]) or 0)

                    elif "$min" in accumulator:
                        val = accumulator["$min"]
                        if isinstance(val, str) and val.startswith("$"):
                            v = get_nested_value(doc, val[1:])
                            if v is not None:
                                if field_name not in groups[key]:
                                    groups[key][field_name] = v
                                else:
                                    groups[key][field_name] = min(groups[key][field_name], v)

                    elif "$max" in accumulator:
                        val = accumulator["$max"]
                        if isinstance(val, str) and val.startswith("$"):
                            v = get_nested_value(doc, val[1:])
                            if v is not None:
                                if field_name not in groups[key]:
                                    groups[key][field_name] = v
                                else:
                                    groups[key][field_name] = max(groups[key][field_name], v)

                    elif "$addToSet" in accumulator:
                        val = accumulator["$addToSet"]
                        if isinstance(val, str) and val.startswith("$"):
                            v = get_nested_value(doc, val[1:])
                            if v is not None:
                                groups[key].setdefault(field_name, [])
                                if isinstance(v, list):
                                    for item in v:
                                        if item not in groups[key][field_name]:
                                            groups[key][field_name].append(item)
                                else:
                                    if v not in groups[key][field_name]:
                                        groups[key][field_name].append(v)

                    elif "$push" in accumulator:
                        val = accumulator["$push"]
                        if isinstance(val, str) and val.startswith("$"):
                            v = get_nested_value(doc, val[1:])
                            if v is not None:
                                groups[key].setdefault(field_name, [])
                                groups[key][field_name].append(v)

            result = list(groups.values())

            # Convert $avg lists to averages
            for group in result:
                for field_name, accumulator in group_spec.items():
                    if field_name == "_id":
                        continue
                    if "$avg" in accumulator:
                        val = group.get(field_name)
                        if isinstance(val, list):
                            group[field_name] = sum(val) / len(val) if val else 0

        elif "$sort" in stage:
            sort_spec = stage["$sort"]
            for key, direction in reversed(list(sort_spec.items())):
                result.sort(key=lambda x: (x.get(key) is None, x.get(key, 0)), reverse=(direction == -1))

        elif "$skip" in stage:
            result = result[stage["$skip"]:]

        elif "$limit" in stage:
            result = result[:stage["$limit"]]

        elif "$unwind" in stage:
            unwind_field = stage["$unwind"]
            if isinstance(unwind_field, str) and unwind_field.startswith("$"):
                field_name = unwind_field[1:]
            else:
                field_name = unwind_field

            new_result = []
            for doc in result:
                val = get_nested_value(doc, field_name)
                if isinstance(val, list):
                    for item in val:
                        new_doc = copy.deepcopy(doc)
                        set_nested_value(new_doc, field_name, item)
                        new_result.append(new_doc)
                else:
                    new_result.append(doc)
            result = new_result

        elif "$project" in stage:
            project_spec = stage["$project"]
            new_result = []
            for doc in result:
                new_doc = {}
                for field, spec in project_spec.items():
                    if isinstance(spec, int) and spec == 1:
                        val = get_nested_value(doc, field)
                        if val is not None:
                            set_nested_value(new_doc, field, val)
                    elif isinstance(spec, str) and spec.startswith("$"):
                        val = get_nested_value(doc, spec[1:])
                        if val is not None:
                            set_nested_value(new_doc, field, val)
                    elif isinstance(spec, dict):
                        # Handle expressions like {$size: "$array"}
                        if "$size" in spec:
                            arr = get_nested_value(doc, spec["$size"][1:] if isinstance(spec["$size"], str) else spec["$size"])
                            new_doc[field] = len(arr) if isinstance(arr, list) else 0
                new_result.append(new_doc)
            result = new_result

    return result


class MockCursor:
    """Mock MongoDB cursor."""

    def __init__(self, documents: list, filter_spec: dict = None):
        self._documents = copy.deepcopy(documents)
        self._filter = filter_spec or {}
        self._sort_key = None
        self._sort_direction = 1
        self._skip_count = 0
        self._limit_count = None

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            self._sort_key = key_or_list
        else:
            self._sort_key = key_or_list
            self._sort_direction = direction
        return self

    def skip(self, count):
        self._skip_count = count
        return self

    def limit(self, count):
        self._limit_count = count
        return self

    def __iter__(self):
        filtered = [copy.deepcopy(doc) for doc in self._documents if matches_filter(doc, self._filter)]

        if self._sort_key:
            if isinstance(self._sort_key, list):
                for key, direction in reversed(self._sort_key):
                    filtered.sort(key=lambda x: (x.get(key) is None, x.get(key, 0)), reverse=(direction == -1))
            else:
                filtered.sort(
                    key=lambda x: (x.get(self._sort_key) is None, x.get(self._sort_key, 0)),
                    reverse=(self._sort_direction == -1),
                )

        if self._skip_count:
            filtered = filtered[self._skip_count:]

        if self._limit_count is not None:
            filtered = filtered[: self._limit_count]

        return iter(filtered)

    def __len__(self):
        return sum(1 for doc in self._documents if matches_filter(doc, self._filter))


class MockCollection:
    """Mock MongoDB collection."""

    def __init__(self, name, database):
        self._name = name
        self._database = database
        self._documents = []
        self._indexes = {}

    def insert_one(self, document, **kwargs):
        document = copy.deepcopy(document)
        if "_id" not in document:
            document["_id"] = ObjectId()
        self._documents.append(document)
        return InsertOneResult(document["_id"], acknowledged=True)

    def insert_many(self, documents, **kwargs):
        ids = []
        for doc in documents:
            result = self.insert_one(doc)
            ids.append(result.inserted_id)
        return type("InsertManyResult", (), {"inserted_ids": ids, "acknowledged": True})()

    def find(self, filter=None, *args, **kwargs):
        return MockCursor(self._documents, filter or {})

    def find_one(self, filter=None, *args, **kwargs):
        for doc in self._documents:
            if matches_filter(doc, filter or {}):
                return copy.deepcopy(doc)
        return None

    def aggregate(self, pipeline, **kwargs):
        return execute_aggregation(self._documents, pipeline)

    def count_documents(self, filter, **kwargs):
        return sum(1 for doc in self._documents if matches_filter(doc, filter))

    def distinct(self, key, filter=None, **kwargs):
        values = set()
        for doc in self._documents:
            if matches_filter(doc, filter or {}):
                val = get_nested_value(doc, key)
                if val is not None:
                    if isinstance(val, list):
                        values.update(val)
                    else:
                        values.add(val)
        return list(values)

    def update_one(self, filter, update, upsert=False, **kwargs):
        for doc in self._documents:
            if matches_filter(doc, filter):
                if "$set" in update:
                    for key, value in update["$set"].items():
                        set_nested_value(doc, key, value)
                return type("UpdateResult", (), {"modified_count": 1, "matched_count": 1})()
        if upsert:
            new_doc = {}
            if "$set" in update:
                for key, value in update["$set"].items():
                    set_nested_value(new_doc, key, value)
            if "_id" not in new_doc:
                new_doc["_id"] = ObjectId()
            self._documents.append(new_doc)
            return type("UpdateResult", (), {"modified_count": 0, "matched_count": 0, "upserted_id": new_doc["_id"]})()
        return type("UpdateResult", (), {"modified_count": 0, "matched_count": 0})()

    def delete_one(self, filter, **kwargs):
        for i, doc in enumerate(self._documents):
            if matches_filter(doc, filter):
                self._documents.pop(i)
                return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    def create_index(self, keys, **kwargs):
        index_name = str(keys)
        self._indexes[index_name] = keys
        return index_name


class MockDatabase:
    """Mock MongoDB database."""

    def __init__(self, name="test_db"):
        self._name = name
        self._collections = {}

    def __getitem__(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollection(name, self)
        return self._collections[name]

    def __getattr__(self, name):
        return self[name]

    def list_collection_names(self):
        return list(self._collections.keys())

    def drop_collection(self, name):
        if name in self._collections:
            del self._collections[name]


class MockMongoClient:
    """Mock MongoDB client."""

    def __init__(self):
        self._databases = {}

    def __getitem__(self, name):
        if name not in self._databases:
            self._databases[name] = MockDatabase(name)
        return self._databases[name]

    def __getattr__(self, name):
        return self[name]

    def list_database_names(self):
        return list(self._databases.keys())

    def close(self):
        pass
