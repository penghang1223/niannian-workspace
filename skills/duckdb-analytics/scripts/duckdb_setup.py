"""
DuckDB production setup with memory management.
Usage: from duckdb_setup import get_connection; conn = get_connection()
"""

import duckdb
import os
import sys
from pathlib import Path


def get_connection(
    db_path: str = ":memory:",
    memory_limit: str = None,
    threads: int = None,
    temp_dir: str = None,
) -> duckdb.DuckDBPyConnection:
    """
    获取配置好的 DuckDB 连接
    
    Args:
        db_path: 数据库路径，默认内存数据库
        memory_limit: 内存限制（如 '80%', '4GB'），默认自动计算
        threads: 线程数，默认 CPU 核心数
        temp_dir: 临时文件目录
    
    Returns:
        配置好的 DuckDB 连接
    
    Example:
        from duckdb_setup import get_connection
        conn = get_connection()
        result = conn.execute("SELECT * FROM 'data.parquet'").fetchdf()
    """
    conn = duckdb.connect(db_path)
    
    # 内存管理：默认 80% 可用内存
    if memory_limit is None:
        memory_limit = "80%"
    
    if memory_limit.endswith("%"):
        # 需要 psutil 来获取实际内存
        try:
            import psutil
            total_gb = psutil.virtual_memory().total / (1024**3)
            percent = int(memory_limit.rstrip('%'))
            limit_gb = total_gb * percent / 100
            memory_limit = f"{limit_gb:.1f}GB"
        except ImportError:
            # 没有 psutil，使用保守值
            memory_limit = "4GB"
    
    conn.execute(f"SET memory_limit='{memory_limit}'")
    
    # 线程数
    if threads:
        conn.execute(f"SET threads={threads}")
    
    # 临时目录
    if temp_dir:
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        conn.execute(f"SET temp_directory='{temp_dir}'")
    
    return conn


def benchmark_clickbench(
    data_path: str,
    queries: list = None,
    iterations: int = 3,
) -> dict:
    """
    运行 ClickBench 基准测试
    
    Args:
        data_path: 数据文件路径（Parquet/CSV）
        queries: 查询列表，默认使用标准 ClickBench
        iterations: 每个查询运行次数
    
    Returns:
        包含每个查询耗时的字典
    
    Example:
        from duckdb_setup import benchmark_clickbench
        results = benchmark_clickbench("hits.parquet")
    """
    conn = get_connection()
    
    # 加载数据
    if data_path.endswith('.parquet'):
        conn.execute(f"CREATE VIEW hits AS SELECT * FROM '{data_path}'")
    else:
        conn.execute(f"CREATE TABLE hits AS SELECT * FROM read_csv_auto('{data_path}')")
    
    # 默认查询
    if queries is None:
        queries = [
            ("Q1: COUNT", "SELECT COUNT(*) FROM hits"),
            ("Q2: WHERE", "SELECT COUNT(*) FROM hits WHERE AdvEngineID <> 0"),
            ("Q3: GROUP BY", "SELECT RegionID, COUNT(*) AS c FROM hits GROUP BY RegionID ORDER BY c DESC LIMIT 10"),
            ("Q4: JOIN", "SELECT hits.UserID, COUNT(*) FROM hits GROUP BY hits.UserID ORDER BY COUNT(*) DESC LIMIT 10"),
        ]
    
    results = {}
    for name, query in queries:
        times = []
        for _ in range(iterations):
            import time
            start = time.time()
            conn.execute(query).fetchall()
            elapsed = time.time() - start
            times.append(elapsed)
        
        results[name] = {
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
        }
    
    return results


def export_analytics_report(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    output_path: str = None,
    format: str = "parquet",
) -> str:
    """
    导出分析结果
    
    Args:
        conn: DuckDB 连接
        query: SQL 查询
        output_path: 输出路径，默认自动生成
        format: 输出格式（parquet/csv/json）
    
    Returns:
        输出文件路径
    """
    if output_path is None:
        import time
        timestamp = int(time.time())
        output_path = f"analytics_{timestamp}.{format}"
    
    if format == "parquet":
        conn.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET)")
    elif format == "csv":
        conn.execute(f"COPY ({query}) TO '{output_path}' (HEADER, DELIMITER ',')")
    elif format == "json":
        conn.execute(f"COPY ({query}) TO '{output_path}' (FORMAT JSON)")
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return output_path


# Quick test
if __name__ == "__main__":
    print("🦆 DuckDB Setup Test")
    
    # 测试连接
    conn = get_connection()
    print(f"✅ 连接成功")
    
    # 测试查询
    result = conn.execute("SELECT version()").fetchone()
    print(f"✅ DuckDB 版本: {result[0]}")
    
    # 测试内存配置
    result = conn.execute("SELECT current_setting('memory_limit')").fetchone()
    print(f"✅ 内存限制: {result[0]}")
    
    # 测试大数据集（模拟）
    conn.execute("CREATE TABLE test AS SELECT range as id, random() as value FROM range(1000000)")
    result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
    print(f"✅ 测试表: {result[0]} 行")
    
    # 测试分析查询
    result = conn.execute("SELECT AVG(value), MIN(value), MAX(value) FROM test").fetchone()
    print(f"✅ 分析结果: avg={result[0]:.4f}, min={result[1]:.4f}, max={result[2]:.4f}")
    
    print("\n✅ duckdb_setup.py works!")
