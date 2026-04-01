# data-quality

数据质量检测技能 — 数据清洗与校验工具集。

## 与 duckdb-analytics 的区别

| 技能 | 职责 |
|------|------|
| `duckdb-analytics` | 数据分析引擎：聚合、统计、可视化 |
| `data-quality` | 数据清洗与校验：发现脏数据、评估质量 |

## 触发条件

用户说："检查数据质量"、"数据校验"、"数据清洗"、"找脏数据"、"数据一致性"、"重复检测"、"非空检查"。

## 快速开始

```bash
# 安装依赖
pip install duckdb pandas tabulate

# 运行检测
python skills/data-quality/scripts/dq_check.py --input data.csv --config skills/data-quality/config.yaml
```

## 检测维度（五维模型）

| 维度 | 说明 |
|------|------|
| 完整性 | 非空率、必填字段缺失 |
| 唯一性 | 主键重复、业务键重复 |
| 一致性 | 跨表/跨字段逻辑一致性 |
| 时效性 | 数据新鲜度、时间顺序 |
| 格式验证 | 枚举值、正则、数值范围 |

## 检测项目清单

### 1. 非空率检查（完整性）

```python
import pandas as pd

def check_null_rate(df: pd.DataFrame, required_cols: list[str] = None) -> dict:
    """检查各列非空率，返回低质量列"""
    result = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        total = len(df)
        null_rate = null_count / total if total > 0 else 0
        result[col] = {
            "null_count": null_count,
            "total": total,
            "null_rate": round(null_rate, 4),
            "status": "PASS" if null_rate < 0.05 else ("WARN" if null_rate < 0.20 else "FAIL"),
        }
    # 必填字段额外标红
    if required_cols:
        for col in required_cols:
            if col in result and result[col]["null_count"] > 0:
                result[col]["status"] = "FAIL"
    return result
```

**阈值**：< 5% PASS / 5-20% WARN / ≥ 20% FAIL

### 2. 主键重复检测（唯一性）

```python
def check_duplicates(df: pd.DataFrame, pk_cols: list[str]) -> dict:
    """检查主键/业务键重复"""
    dup_mask = df.duplicated(subset=pk_cols, keep=False)
    dup_rows = df[dup_mask]
    dup_groups = dup_rows.groupby(pk_cols).size().reset_index(name="count")
    dup_groups = dup_groups[dup_groups["count"] > 1]

    return {
        "pk_cols": pk_cols,
        "total_rows": len(df),
        "duplicate_rows": int(dup_mask.sum()),
        "duplicate_groups": len(dup_groups),
        "dup_rate": round(dup_mask.sum() / len(df), 4) if len(df) > 0 else 0,
        "status": "PASS" if len(dup_groups) == 0 else "FAIL",
        "sample_duplicates": dup_groups.head(10).to_dict("records"),
    }
```

### 3. 时间顺序验证（一致性）

```python
def check_time_order(df: pd.DataFrame, start_col: str, end_col: str) -> dict:
    """验证 start <= end 的时间逻辑"""
    if start_col not in df.columns or end_col not in df.columns:
        return {"status": "SKIP", "reason": "columns not found"}

    # 统一转 datetime
    starts = pd.to_datetime(df[start_col], errors="coerce")
    ends = pd.to_datetime(df[end_col], errors="coerce")

    valid_mask = starts.notna() & ends.notna()
    violations = valid_mask & (starts > ends)
    violation_count = int(violations.sum())
    valid_count = int(valid_mask.sum())

    return {
        "rule": f"{start_col} <= {end_col}",
        "valid_pairs": valid_count,
        "violations": violation_count,
        "violation_rate": round(violation_count / valid_count, 4) if valid_count > 0 else 0,
        "status": "PASS" if violation_count == 0 else "FAIL",
        "sample_violations": df[violations].head(5).to_dict("records"),
    }
```

### 4. 数值范围检查（格式验证）

```python
import numpy as np

def check_numeric_range(df: pd.DataFrame, col: str, min_val=None, max_val=None) -> dict:
    """检查数值列是否在合理范围内"""
    if col not in df.columns:
        return {"status": "SKIP", "reason": "column not found"}

    series = pd.to_numeric(df[col], errors="coerce")
    valid = series.dropna()
    total = len(df)

    violations = pd.Series(False, index=df.index)
    if min_val is not None:
        violations |= (series < min_val)
    if max_val is not None:
        violations |= (series > max_val)

    # 排除 NaN 的违规
    violations = violations & series.notna()

    return {
        "column": col,
        "min": float(valid.min()) if len(valid) > 0 else None,
        "max": float(valid.max()) if len(valid) > 0 else None,
        "mean": round(float(valid.mean()), 2) if len(valid) > 0 else None,
        "expected_range": [min_val, max_val],
        "outliers": int(violations.sum()),
        "outlier_rate": round(int(violations.sum()) / total, 4) if total > 0 else 0,
        "status": "PASS" if violations.sum() == 0 else ("WARN" if violations.sum() / total < 0.01 else "FAIL"),
    }
```

### 5. 枚举值校验（格式验证）

```python
def check_enum_values(df: pd.DataFrame, col: str, allowed: list[str]) -> dict:
    """检查列值是否在允许的枚举列表内"""
    if col not in df.columns:
        return {"status": "SKIP", "reason": "column not found"}

    actual = set(df[col].dropna().unique())
    allowed_set = set(allowed)
    invalid = actual - allowed_set
    total = len(df)
    invalid_count = int((~df[col].isin(allowed_set) & df[col].notna()).sum())

    return {
        "column": col,
        "allowed_values": allowed,
        "actual_values": sorted(actual),
        "invalid_values": sorted(invalid),
        "invalid_count": invalid_count,
        "invalid_rate": round(invalid_count / total, 4) if total > 0 else 0,
        "status": "PASS" if len(invalid) == 0 else "FAIL",
    }
```

### 6. 数据新鲜度评估（时效性）

```python
from datetime import datetime, timezone

def check_freshness(df: pd.DataFrame, time_col: str, max_age_hours: float = 24) -> dict:
    """评估数据新鲜度 — 最近一条记录距今多久"""
    if time_col not in df.columns:
        return {"status": "SKIP", "reason": "column not found"}

    timestamps = pd.to_datetime(df[time_col], errors="coerce").dropna()
    if len(timestamps) == 0:
        return {"status": "FAIL", "reason": "no valid timestamps"}

    latest = timestamps.max()
    now = pd.Timestamp.now(tz=latest.tz if latest.tz else None)
    age_hours = (now - latest).total_seconds() / 3600
    earliest = timestamps.min()

    return {
        "column": time_col,
        "earliest": str(earliest),
        "latest": str(latest),
        "age_hours": round(age_hours, 2),
        "max_allowed_hours": max_age_hours,
        "row_count": len(timestamps),
        "status": "PASS" if age_hours <= max_age_hours else "FAIL",
    }
```

### 7. 跨字段一致性验证

```python
def check_cross_field(df: pd.DataFrame, rules: list[dict]) -> dict:
    """自定义跨字段规则校验

    rules 示例:
    [
        {"name": "amount_positive", "expr": "amount > 0", "description": "金额必须为正"},
        {"name": "status_logic", "expr": "status != 'completed' or end_time.notna()", "description": "完成状态必须有结束时间"},
    ]
    """
    results = []
    for rule in rules:
        try:
            mask = df.query(rule["expr"])
            violations = len(df) - len(mask)
        except Exception as e:
            violations = -1  # 表达式错误

        results.append({
            "rule_name": rule["name"],
            "description": rule.get("description", ""),
            "expression": rule["expr"],
            "violations": violations,
            "status": "PASS" if violations == 0 else ("ERROR" if violations == -1 else "FAIL"),
        })

    return {"rules_checked": len(rules), "results": results}
```

## 完整检测脚本

`scripts/dq_check.py` — 一键运行所有检测：

```python
#!/usr/bin/env python3
"""data-quality: 数据质量检测脚本"""
import argparse
import json
import sys
import pandas as pd
from pathlib import Path

# 检测函数内联（避免 import 依赖）
# 实际使用时可拆分为独立模块

def run_all_checks(df: pd.DataFrame, config: dict) -> dict:
    report = {"total_rows": len(df), "total_cols": len(df.columns), "checks": {}}

    # 1. 非空率
    report["checks"]["null_rate"] = check_null_rate(
        df, config.get("required_columns", [])
    )

    # 2. 主键重复
    if "primary_keys" in config:
        report["checks"]["duplicates"] = check_duplicates(df, config["primary_keys"])

    # 3. 时间顺序
    for rule in config.get("time_order_rules", []):
        key = f"time_order_{rule['start']}_{rule['end']}"
        report["checks"][key] = check_time_order(df, rule["start"], rule["end"])

    # 4. 数值范围
    for col_cfg in config.get("numeric_ranges", []):
        key = f"range_{col_cfg['column']}"
        report["checks"][key] = check_numeric_range(
            df, col_cfg["column"], col_cfg.get("min"), col_cfg.get("max")
        )

    # 5. 枚举值
    for col_cfg in config.get("enum_columns", []):
        key = f"enum_{col_cfg['column']}"
        report["checks"][key] = check_enum_values(df, col_cfg["column"], col_cfg["values"])

    # 6. 数据新鲜度
    if "freshness" in config:
        fc = config["freshness"]
        report["checks"]["freshness"] = check_freshness(
            df, fc["time_column"], fc.get("max_age_hours", 24)
        )

    # 7. 跨字段规则
    if "cross_field_rules" in config:
        report["checks"]["cross_field"] = check_cross_field(df, config["cross_field_rules"])

    # 汇总
    all_checks = []
    for category in report["checks"].values():
        if isinstance(category, dict):
            if "status" in category:
                all_checks.append(category["status"])
            elif "results" in category:
                all_checks.extend(r["status"] for r in category["results"])
            else:
                for item in category.values():
                    if isinstance(item, dict) and "status" in item:
                        all_checks.append(item["status"])

    report["summary"] = {
        "total": len(all_checks),
        "passed": all_checks.count("PASS"),
        "warnings": all_checks.count("WARN"),
        "failed": all_checks.count("FAIL"),
        "overall": "PASS" if "FAIL" not in all_checks else "FAIL",
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Data Quality Checker")
    parser.add_argument("--input", required=True, help="CSV/Parquet/JSON file path")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--output", help="Output report path (JSON)")
    parser.add_argument("--format", choices=["json", "table"], default="table")
    args = parser.parse_args()

    import yaml
    config = yaml.safe_load(Path(args.config).read_text())

    # 读取数据
    path = Path(args.input)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    elif path.suffix == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix in (".json", ".jsonl"):
        df = pd.read_json(path, lines=path.suffix == ".jsonl")
    else:
        print(f"Unsupported format: {path.suffix}", file=sys.stderr)
        sys.exit(1)

    report = run_all_checks(df, config)

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        print(f"Report saved to {args.output}")

    if args.format == "table":
        print(format_table_report(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    # 退出码：有 FAIL 则返回 1
    sys.exit(0 if report["summary"]["overall"] == "PASS" else 1)


def format_table_report(report: dict) -> str:
    lines = []
    s = report["summary"]
    lines.append(f"{'='*60}")
    lines.append(f"  数据质量报告  |  总行数: {report['total_rows']}  |  总列数: {report['total_cols']}")
    lines.append(f"  ✅ PASS: {s['passed']}  ⚠️ WARN: {s['warnings']}  ❌ FAIL: {s['failed']}")
    lines.append(f"  综合评级: {'✅ PASS' if s['overall'] == 'PASS' else '❌ FAIL'}")
    lines.append(f"{'='*60}")

    for category, data in report["checks"].items():
        lines.append(f"\n📋 {category}")
        if isinstance(data, dict):
            if "status" in data:
                icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "💥"}.get(data["status"], "?")
                lines.append(f"  {icon} {data['status']}")
                for k, v in data.items():
                    if k != "status":
                        lines.append(f"    {k}: {v}")
            elif "results" in data:
                for r in data["results"]:
                    icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}.get(r["status"], "?")
                    lines.append(f"  {icon} {r['rule_name']}: {r['description']} (violations: {r['violations']})")
            else:
                for col, info in data.items():
                    if isinstance(info, dict) and "status" in info:
                        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(info["status"], "?")
                        rate = info.get("null_rate", info.get("dup_rate", ""))
                        lines.append(f"  {icon} {col}: {info['status']} (rate: {rate})")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
```

## 配置文件模板

`config.yaml` 示例：

```yaml
# 数据质量检测配置
required_columns:
  - id
  - name
  - created_at

primary_keys:
  - id

time_order_rules:
  - start: created_at
    end: updated_at
  - start: order_date
    end: ship_date

numeric_ranges:
  - column: age
    min: 0
    max: 150
  - column: amount
    min: 0
    max: 1000000

enum_columns:
  - column: status
    values: [pending, active, completed, cancelled]
  - column: currency
    values: [CNY, USD, EUR, GBP, JPY]

freshness:
  time_column: updated_at
  max_age_hours: 48

cross_field_rules:
  - name: amount_positive
    expr: "amount > 0"
    description: "金额必须为正数"
  - name: completed_has_end
    expr: "status != 'completed' or end_time.notna()"
    description: "完成状态必须有结束时间"
```

## 报告格式

### 控制台输出（默认）

```
============================================================
  数据质量报告  |  总行数: 10000  |  总列数: 8
  ✅ PASS: 12  ⚠️ WARN: 2  ❌ FAIL: 1
  综合评级: ❌ FAIL
============================================================

📋 null_rate
  ✅ id: PASS (rate: 0.0)
  ✅ name: PASS (rate: 0.002)
  ⚠️ email: WARN (rate: 0.12)
  ❌ phone: FAIL (rate: 0.35)

📋 duplicates
  ❌ FAIL (duplicate_groups: 3, dup_rate: 0.001)

📋 time_order_created_at_updated_at
  ✅ PASS (violations: 0)

📋 enum_status
  ❌ FAIL (invalid_values: ['delivered', 'returned'], invalid_count: 47)
```

### JSON 报告（`--output report.json`）

```json
{
  "total_rows": 10000,
  "total_cols": 8,
  "checks": { "..." : "..." },
  "summary": {
    "total": 15,
    "passed": 12,
    "warnings": 2,
    "failed": 1,
    "overall": "FAIL"
  }
}
```

## 使用流程

1. **准备数据** — CSV / Parquet / JSON 文件
2. **编写配置** — 参照 `config.yaml` 模板
3. **运行检测** — `python scripts/dq_check.py --input data.csv --config config.yaml`
4. **查看报告** — 控制台表格或 JSON 输出
5. **修复数据** — 根据 FAIL 项目逐项清洗
6. **复检** — 重新运行确认 PASS

## 在飞书/对话中使用

当用户说"检查这个文件的数据质量"：

1. 下载/读取用户提供的文件
2. 快速扫描列名和数据类型
3. 自动生成合理配置（必填=所有列，主键=id列，枚举=低基数字符串列）
4. 运行检测并返回报告摘要
5. 详细报告写入文件供下载
