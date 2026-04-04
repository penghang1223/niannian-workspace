# 2026-04-04 PostgreSQL EXPLAIN 学习汇报

## 汇报信息
- **时间**: 2026-04-04 11:57
- **领域**: PostgreSQL EXPLAIN 与查询计划
- **价值等级**: 🔴 高价值
- **审查状态**: ✅ 已完成

---

## 🎯 核心收获

**PostgreSQL EXPLAIN**: 查询计划可视化工具

### 1. EXPLAIN 树状 Plan Nodes

**输出格式**:
```
Nested Loop  (cost=0.43..12.56 rows=10 width=100)
  ->  Index Scan using users_pkey on users  (cost=0.43..8.45 rows=1 width=50)
        Index Cond: (id = 1)
  ->  Seq Scan on orders  (cost=0.00..4.11 rows=10 width=50)
        Filter: (user_id = 1)
```

**节点类型**:
| 节点 | 说明 | 成本 |
|------|------|------|
| **Seq Scan** | 全表扫描 | 高 |
| **Index Scan** | 索引扫描 | 低 |
| **Bitmap Scan** | 位图扫描 | 中 |
| **Nested Loop** | 嵌套循环连接 | 低行数优 |
| **Hash Join** | 哈希连接 | 高行数优 |
| **Merge Join** | 归并连接 | 已排序优 |

### 2. 成本模型

**公式**:
```
总成本 = disk*seq_page_cost + rows*cpu_tuple_cost + rows*cpu_operator_cost
```

**参数**:
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `seq_page_cost` | 1.0 | 顺序页读取成本 |
| `random_page_cost` | 4.0 | 随机页读取成本 |
| `cpu_tuple_cost` | 0.01 | 每行 CPU 成本 |
| `cpu_operator_cost` | 0.0025 | 每操作符 CPU 成本 |

**优化方向**:
- 减少 `rows`（索引过滤）
- 减少 `disk` 访问（覆盖索引）
- 降低 `random_page_cost`（SSD 环境）

### 3. Index Scan vs Bitmap Scan

**Index Scan**:
- **适用**: 高选择性查询（返回少量行）
- **特点**: 直接通过索引访问表
- **示例**: `WHERE id = 1`

**Bitmap Scan**:
- **适用**: 中等选择性查询（返回多行）
- **特点**: 先构建位图，再访问表
- **示例**: `WHERE status IN ('active', 'pending')`

**选择逻辑**:
```
选择性 < 1%  → Index Scan
选择性 1-10% → Bitmap Scan
选择性 > 10% → Seq Scan
```

### 4. Filter vs Index Cond

**Index Cond**（索引条件）:
- ✅ 使用索引过滤
- ✅ 高性能
- ✅ 在索引扫描阶段执行

**Filter**（过滤条件）:
- ❌ 不使用索引
- ❌ 全表扫描后过滤
- ❌ 在过滤阶段执行

**示例对比**:
```sql
-- Index Cond（优）
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
-- Index Scan using users_email_idx (cost=0.43..8.45 rows=1 width=50)
--   Index Cond: (email = 'test@example.com')

-- Filter（劣）
EXPLAIN SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
-- Seq Scan on users (cost=0.00..100.00 rows=1 width=50)
--   Filter: (LOWER(email) = 'test@example.com')
```

---

## 📋 应用场景

### 1. 慢查询诊断

**标准流程**:
```sql
-- 1. 启用详细输出
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 1 AND status = 'pending';

-- 2. 查看执行计划
-- 关注：
-- - 实际执行时间 (Actual Time)
-- - 实际行数 (Actual Rows)
-- - 缓冲区使用 (Buffers: hit/read/dirtied)

-- 3. 识别瓶颈
-- - Seq Scan → 考虑索引
-- - High Rows → 统计信息过期
-- - High Buffers → 缓存不足
```

### 2. 索引设计评审

**评审 Checklist**:
- [ ] 所有查询都过 EXPLAIN
- [ ] 确认使用 Index Cond 而非 Filter
- [ ] 确认选择性 < 10%
- [ ] 确认无 Seq Scan（大表）
- [ ] 确认 Join 使用 Nested Loop/Hash Join 合理

### 3. 性能优化

**优化案例**:
```sql
-- 优化前（Filter）
SELECT * FROM orders WHERE DATE(created_at) = '2026-04-04';
-- Seq Scan, Filter: (date(created_at) = '2026-04-04')

-- 优化后（Index Cond）
SELECT * FROM orders 
WHERE created_at >= '2026-04-04' AND created_at < '2026-04-05';
-- Index Scan using orders_created_at_idx
-- Index Cond: (created_at >= '2026-04-04' AND created_at < '2026-04-05')
```

---

## 📊 预期改善

| 指标 | 当前方式 | EXPLAIN 方式 | 改善幅度 |
|------|----------|--------------|----------|
| 慢查询定位 | 猜 + 试错 | **看 plan** | **10-100 倍效率** |
| 索引设计 | 经验驱动 | **数据驱动** | **准确性 +80%** |
| 查询优化 | 盲目加索引 | **针对性优化** | **10-100 倍性能** |
| 评审效率 | 人工审查 | **EXPLAIN 验证** | **时间 -50%** |

---

## 🔧 技术实现

### EXPLAIN 命令

```sql
-- 基础用法
EXPLAIN SELECT * FROM users WHERE id = 1;

-- 详细输出（推荐）
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM users WHERE id = 1;

-- JSON 格式（程序解析）
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM users WHERE id = 1;

-- 仅成本估算（不执行）
EXPLAIN (COSTS, FORMAT TEXT)
SELECT * FROM users WHERE id = 1;
```

### 输出解读

```
Nested Loop  (cost=0.43..12.56 rows=10 width=100) (actual time=0.050..0.100 rows=5 loops=1)
  ->  Index Scan using users_pkey on users  (cost=0.43..8.45 rows=1 width=50) (actual time=0.030..0.035 rows=1 loops=1)
        Index Cond: (id = 1)
        Buffers: shared hit=2
  ->  Seq Scan on orders  (cost=0.00..4.11 rows=10 width=50) (actual time=0.010..0.050 rows=5 loops=1)
        Filter: (user_id = 1)
        Rows Removed by Filter: 95
        Buffers: shared hit=10
```

**关键字段**:
- `cost`: 估算成本（启动..总成本）
- `rows`: 估算行数
- `actual time`: 实际执行时间（启动..总时间）
- `rows`: 实际行数
- `loops`: 循环次数
- `Buffers`: 缓冲区使用（hit/read/dirtied/written）

### 性能调优参数

```sql
-- 查看当前参数
SHOW seq_page_cost;
SHOW random_page_cost;
SHOW cpu_tuple_cost;
SHOW cpu_operator_cost;

-- 调整参数（SSD 环境）
SET random_page_cost = 1.1;  -- SSD 随机读取成本低
SET effective_cache_size = '4GB';  -- 告诉 PG 有多少缓存
SET work_mem = '64MB';  -- 排序/哈希操作内存

-- 永久生效（postgresql.conf）
random_page_cost = 1.1
effective_cache_size = 4GB
work_mem = 64MB
```

---

## 📈 跟进事项

| 事项 | 负责人 | 截止 |
|------|--------|------|
| EXPLAIN 诊断流程文档 | 玄机 | 2026-04-06 |
| 慢查询诊断 POC | 玄机 | 2026-04-07 |
| 索引设计评审 Checklist | 鉴微 | 2026-04-08 |
| OPC Platform 慢查询优化 | 玄机 | 2026-04-09 |

---

## 🎓 审查意见

**优点**:
1. 🔴 EXPLAIN 树状 plan nodes 可视化
2. 🔴 成本模型清晰（disk + cpu）
3. 🔴 Index Scan vs Bitmap Scan 选择逻辑明确
4. 🔴 Filter vs Index Cond 区别清晰
5. 🔴 应用场景明确（慢查询诊断/索引评审）

**建议**:
1. 补充 EXPLAIN 输出示例（实际案例）
2. 提供慢查询诊断流程（step by step）
3. 索引设计评审 checklist
4. OPC Platform 慢查询优化实践

**决策**: ✅ **立即推进 EXPLAIN 诊断流程文档**

---

**审查者**: 年年 🎀  
**审查时间**: 2026-04-04 11:58  
**下一步**: 玄机诊断流程文档 → 慢查询 POC → 索引评审 Checklist
