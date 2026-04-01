---
name: duckdb-analytics
description: DuckDB数据分析工具集 — 内存管理/ClickBench基准/结果导出。$700 MacBook也能跑大数据。
---

# DuckDB Analytics — 数据分析工具集

## 核心功能

### 1. 智能内存管理
自动使用80%可用内存，让DuckDB自己管OOM。

```python
from duckdb_setup import get_connection

conn = get_connection()  # 自动配置内存
result = conn.execute("SELECT * FROM 'data.parquet'").fetchdf()
```

### 2. ClickBench基准测试

```python
from duckdb_setup import benchmark_clickbench

results = benchmark_clickbench("hits.parquet")
# 输出每个查询的avg/min/max耗时
```

### 3. 分析结果导出

```python
from duckdb_setup import export_analytics_report

path = export_analytics_report(conn, "SELECT * FROM sales", format="parquet")
```

## 关键技巧

| 技巧 | 说明 |
|------|------|
| `SET memory_limit='80%'` | 让DuckDB自管OOM |
| `$700 MacBook能跑100M行` | 边缘计算基准验证 |
| VARIANT+GEOMETRY类型 | DuckDB 1.5新特性 |

## 使用方式

```bash
# 测试
python3 <SKILL_DIR>/scripts/duckdb_setup.py

# 在脚本中import
python3 -c "from duckdb_setup import get_connection; conn = get_connection(); print(conn.execute('SELECT version()').fetchone())"
```

## 文件

- `scripts/duckdb_setup.py` — 核心模块（连接/基准/导出）
