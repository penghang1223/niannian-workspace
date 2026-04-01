# SKILL.md - 日志异常检测 (Log Anomaly Detection)

## 触发条件

当用户提到以下关键词时激活此 Skill：
- "日志分析"、"日志异常"、"log anomaly"
- "检测错误"、"异常检测"、"故障排查"
- "OOM"、"panic"、"崩溃"、"超时"
- "慢查询"、"限流"、"连接错误"
- "磁盘满了"、"服务挂了"、"重启了"

## 概述

日志异常检测工具，专注于从系统/应用日志中识别 **16 种关键异常模式**，并提供时间趋势分析和异常堆栈解析。

**与 python-toolkit 的分工：**
- `python-toolkit` → 日志格式化、结构化、清洗（前置处理）
- `log-anomaly` → 异常模式检测、趋势分析、报警规则（核心分析）

## 快速使用

```bash
# 基础检测：分析日志文件
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件>

# 指定时间范围
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件> --since "2024-01-01 00:00:00" --until "2024-01-01 23:59:59"

# 实时监控（tail -f 模式）
tail -f /var/log/app.log | python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py --stdin

# 指定检测模式
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件> --patterns oom,panic,timeout

# 输出 JSON 格式
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件> --json

# 趋势分析
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件> --trend --interval 300
```

## 16 种异常模式

每种模式包含：检测规则（正则）、严重等级、报警阈值、自动建议

### 1. OOM (Out of Memory)
```
严重等级: CRITICAL
关键词:  OutOfMemoryError, OOM, cannot allocate memory, oom-kill, oom_reaper
正则:    (OutOfMemoryError|OOM|out of memory|oom-kill|oom_reaper|Cannot allocate)
报警阈值: 1 次
建议:    检查内存泄漏，增加堆内存，优化数据结构
```

### 2. Panic / 致命崩溃
```
严重等级: CRITICAL
关键词:  panic, Fatal, fatal error, SIGSEGV, SIGABRT, core dumped
正则:    (panic:|fatal error:|SIGSEGV|SIGABRT|core dumped|Aborted)
报警阈值: 1 次
建议:    检查代码逻辑，查看堆栈定位根因
```

### 3. 栈溢出 (Stack Overflow)
```
严重等级: CRITICAL
关键词:  StackOverflowError, stack overflow, recursion depth exceeded
正则:    (StackOverflowError|stack overflow|recursion depth exceeded|maximum recursion|RecursionError)
报警阈值: 1 次
建议:    检查递归调用，增大栈空间限制
```

### 4. 空指针 (Null Pointer)
```
严重等级: HIGH
关键词:  NullPointerException, null pointer, undefined is not an object, TypeError: null
正则:    (NullPointerException|null pointer|Cannot read propert(y|ies) of undefined|TypeError.*null|NoneType.*attribute)
报警阈值: 5 次/分钟
建议:    添加空值检查，使用 Optional 类型
```

### 5. 超时 (Timeout)
```
严重等级: HIGH
关键词:  timeout, timed out, DeadlineExceeded, connection timed out
正则:    (timed?\s*out|TimeoutException|DeadlineExceeded|ETIMEDOUT|request timeout)
报警阈值: 10 次/5分钟
建议:    检查下游服务响应，调整超时配置
```

### 6. 连接错误 (Connection Error)
```
严重等级: HIGH
关键词:  Connection refused, connection reset, ECONNREFUSED, ECONNRESET, broken pipe
正则:    (Connection refused|ECONNREFUSED|ECONNRESET|connection reset|broken pipe|EPIPE|connection failed|connect: connection refused)
报警阈值: 5 次/分钟
建议:    检查目标服务状态，网络连通性，防火墙规则
```

### 7. 数据库错误 (Database Error)
```
严重等级: HIGH
关键词:  deadlock, SQL error, database error, connection pool exhausted, lock wait timeout
正则:    (deadlock|Deadlock found|SQL.*error|database.*error|connection pool.*exhausted|lock wait timeout|Too many connections|duplicate key)
报警阈值: 3 次/分钟
建议:    检查 SQL 性能，索引优化，连接池配置
```

### 8. 磁盘满 (Disk Full)
```
严重等级: CRITICAL
关键词:  No space left on device, disk full, ENOSPC
正则:    (No space left on device|disk full|ENOSPC|insufficient disk space)
报警阈值: 1 次
建议:    清理日志/临时文件，扩容磁盘，设置日志轮转
```

### 9. 重试 (Retry)
```
严重等级: MEDIUM
关键词:  retry, retrying, retry attempt, max retries exceeded
正则:    (retry(ing)?\s*(attempt)?|max retries exceeded|retries exhausted|RetryAfter|retry count)
报警阈值: 20 次/5分钟
建议:    检查重试原因，配置指数退避，设置熔断器
```

### 10. 慢查询 (Slow Query)
```
严重等级: MEDIUM
关键词:  slow query, Slow query, Query execution time, took longer than
正则:    ([Ss]low\s*[Qq]uery|execution time.*\d+ms|took longer than|query.*slow|latency.*\d{4,}ms)
报警阈值: 10 次/10分钟
建议:    添加索引，优化 SQL，考虑读写分离
```

### 11. 限流 (Rate Limiting)
```
严重等级: MEDIUM
关键词:  rate limit, 429, Too Many Requests, throttled, quota exceeded
正则:    (rate.?limit|429|Too Many Requests|throttl|quota exceeded|RateLimitExceeded)
报警阈值: 10 次/分钟
建议:    优化请求频率，使用缓存，申请提高配额
```

### 12. 废弃 API (Deprecated API)
```
严重等级: LOW
关键词:  deprecated, will be removed, DEPRECATED, sunset
正则:    (deprecated|DEPRECATED|will be removed|is deprecated|sunset|end.of.life)
报警阈值: 无（记录即可）
建议:    迁移到新版 API，更新依赖版本
```

### 13. 认证失败 (Auth Failure)
```
严重等级: HIGH
关键词:  authentication failed, unauthorized, 401, 403, invalid token, access denied
正则:    (authentication failed|unauthorized|401|403|invalid token|access denied|forbidden|auth.*error|credentials.*invalid)
报警阈值: 20 次/分钟
建议:    检查 token 过期，轮换密钥，检查权限配置
```

### 14. 注入攻击 (Injection Attack)
```
严重等级: CRITICAL
关键词:  SQL injection, XSS, injection detected, suspicious query, UNION SELECT
正则:    (UNION\s+SELECT|OR\s+1\s*=\s*1|<script>|javascript:|injection|sqlmap|suspicious.*(query|input))
报警阈值: 1 次
建议:    使用参数化查询，WAF 规则，输入验证
```

### 15. 堆/内存碎片 (Heap Fragmentation) [扩展模式]
```
严重等级: MEDIUM
关键词:  heap fragmentation, GC overhead, GC pause, heap dump
正则:    (heap.?fragmentation|GC overhead|GC pause.*\d+ms|Full GC|heap dump)
报警阈值: 5 次/10分钟
建议:    调整 GC 策略，检查内存分配模式
```

### 16. 证书/SSL 错误 (Certificate Error) [扩展模式]
```
严重等级: HIGH
关键词:  certificate, SSL, TLS, cert expired, verify failed
正则:    (certificate.*expired|SSL.*error|TLS.*error|CERTIFICATE_VERIFY_FAILED|cert.*invalid|x509)
报警阈值: 1 次
建议:    更新证书，检查证书链，验证系统时间
```

## 异常堆栈解析

自动提取和格式化异常堆栈信息：

```bash
# 解析堆栈追踪
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/stacktrace.py <日志文件>

# 输出示例：
# ┌─ [CRITICAL] OOM @ 2024-01-15 14:32:01
# │  File "app/service.py", line 142, in process_batch
# │    data = json.loads(response.content)
# │  File "app/models.py", line 89, in save
# │    self.session.bulk_insert_mappings(Model, records)
# │  MemoryError: Unable to allocate 2.1 GiB
# └─ 建议: 批量写入改用分块处理，每批 1000 条
```

### 堆栈解析特性
- **自动关联**：将异常类型与最近的堆栈帧关联
- **关键帧提取**：识别用户代码 vs 框架代码，优先展示用户代码
- **时间线**：按时间排序展示异常堆栈
- **相似性聚合**：相同堆栈只报告一次 + 出现次数

## 时间趋势分析

```bash
# 5 分钟粒度趋势
python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py <日志文件> --trend --interval 300

# 输出示例：
# ┌─ 异常趋势分析 (2024-01-15 全天)
# │
# │  00:00  ░░
# │  01:00  ░
# │  02:00  ░░░
# │  ...
# │  14:00  ████████████  ← OOM 集群爆发 (12次)
# │  14:30  ████████      ← 连级故障 (8次)
# │  ...
# │
# │  📈 峰值: 14:00 (OOM 集群)
# │  📊 总异常: 47 次 | CRITICAL: 3 | HIGH: 15 | MEDIUM: 29
# │  ⚠️  趋势: 上升 (后4小时比前4小时 +300%)
# └─
```

### 趋势分析特性
- **可配置粒度**：1分钟 / 5分钟 / 15分钟 / 1小时
- **异常分类趋势**：按严重等级分别统计
- **峰值检测**：自动标记异常集中爆发时段
- **趋势判断**：上升 / 下降 / 稳定
- **关联分析**：同类异常是否集中在同一时段

## 报警规则

### 默认报警规则

| 模式 | 等级 | 条件 | 动作 |
|------|------|------|------|
| OOM | CRITICAL | 任意 1 次 | 立即通知 |
| Panic | CRITICAL | 任意 1 次 | 立即通知 |
| 注入攻击 | CRITICAL | 任意 1 次 | 立即通知 + 安全审计 |
| 磁盘满 | CRITICAL | 任意 1 次 | 立即通知 |
| 超时 | HIGH | > 10次/5分钟 | 批量通知 |
| 连接错误 | HIGH | > 5次/分钟 | 批量通知 |
| 慢查询 | MEDIUM | > 10次/10分钟 | 日报汇总 |
| 重试 | MEDIUM | > 20次/5分钟 | 日报汇总 |
| 限流 | MEDIUM | > 10次/分钟 | 日报汇总 |
| 废弃API | LOW | 任意 | 周报记录 |

### 自定义报警规则

在日志文件同目录创建 `.log-anomaly.yaml`：

```yaml
rules:
  - name: "OOM紧急报警"
    pattern: "OutOfMemoryError|OOM"
    level: CRITICAL
    threshold: 1
    window: 0  # 立即
    action: notify
    channels: [feishu, email]

  - name: "数据库连接池告警"
    pattern: "connection pool.*exhausted|Too many connections"
    level: HIGH
    threshold: 3
    window: 60  # 60秒窗口
    action: notify
    channels: [feishu]

  - name: "慢查询监控"
    pattern: "[Ss]low.*[Qq]uery"
    level: MEDIUM
    threshold: 50
    window: 3600  # 1小时窗口
    action: report  # 加入日报
```

## 与 python-toolkit 协作

### 工作流

```
原始日志 → python-toolkit(格式化) → 结构化日志 → log-anomaly(检测) → 异常报告
```

### 具体协作方式

```python
# 1. 使用 python-toolkit 格式化日志
from log_toolkit import parse_log_line, setup_logging

# 2. 使用 log-anomaly 检测异常
from log_anomaly import detect_anomalies, analyze_trend

# 完整流程
structured_logs = [parse_log_line(line) for line in raw_logs]
anomalies = detect_anomalies(structured_logs)
trend = analyze_trend(anomalies, interval=300)
```

### 直接管线

```bash
# 格式化后直接检测
python3 -m log_toolkit.format < raw.log | python3 ~/.openclaw/workspace/skills/log-anomaly/scripts/detect.py --stdin
```

## 输出格式

### 人类可读格式（默认）

```
┌─ 日志异常检测报告
│  文件: /var/log/app.log
│  时间范围: 2024-01-15 00:00:00 ~ 2024-01-15 23:59:59
│  总行数: 1,247,832
│
├─ 异常摘要
│  🔴 CRITICAL: 3 (OOM: 2, Panic: 1)
│  🟠 HIGH: 15 (超时: 8, 连接错误: 5, 认证失败: 2)
│  🟡 MEDIUM: 29 (慢查询: 12, 重试: 10, 限流: 7)
│  🟢 LOW: 5 (废弃API: 5)
│
├─ 🔴 OOM (2次) — 立即处理
│  ├─ [14:32:01] app/service.py:142 → MemoryError: Unable to allocate 2.1 GiB
│  └─ [14:45:23] app/worker.py:67  → OutOfMemoryError: Java heap space
│
├─ 🟠 超时 (8次)
│  ├─ [10:15:01] GET /api/users → 30001ms (阈值: 5000ms)
│  ├─ [10:15:02] POST /api/orders → 28500ms
│  └─ ... (共 8 次)
│
├─ 📊 趋势分析
│  00-06: ░░ (2异常)
│  06-12: ░░░░ (5异常)
│  12-18: ████████████ (35异常) ← 峰值
│  18-24: ░░░░░ (7异常)
│
└─ ✅ 建议
   1. [紧急] OOM: 检查 service.py:142 批量处理逻辑，改用流式处理
   2. [高优] 超时集中: 10:15 有8次超时，检查 /api 下游服务
   3. [优化] 慢查询: 添加 users 表索引
```

### JSON 格式 (`--json`)

```json
{
  "summary": {
    "file": "/var/log/app.log",
    "total_lines": 1247832,
    "time_range": {
      "start": "2024-01-15T00:00:00+08:00",
      "end": "2024-01-15T23:59:59+08:00"
    },
    "anomalies_total": 52,
    "by_level": { "CRITICAL": 3, "HIGH": 15, "MEDIUM": 29, "LOW": 5 }
  },
  "anomalies": [
    {
      "type": "oom",
      "level": "CRITICAL",
      "count": 2,
      "instances": [
        {
          "timestamp": "2024-01-15T14:32:01+08:00",
          "line": 892451,
          "message": "MemoryError: Unable to allocate 2.1 GiB",
          "stacktrace": ["app/service.py:142", "app/models.py:89"],
          "suggestion": "批量写入改用分块处理，每批 1000 条"
        }
      ]
    }
  ],
  "trend": {
    "interval_seconds": 300,
    "buckets": [...]
  }
}
```

## 注意事项

- **大文件处理**：>1GB 文件建议用 `--since/--until` 分段分析
- **编码**：自动检测 UTF-8 / GBK / Latin-1
- **多行日志**：自动处理多行堆栈（Java/Python/Node.js）
- **性能**：检测脚本为单遍扫描，内存占用 O(异常数) 而非 O(行数)
- **去重**：同一异常堆栈自动聚合，报告时只展示首次出现 + 计数

## 文件结构

```
skills/log-anomaly/
├── SKILL.md              # 本文件
├── scripts/
│   ├── detect.py         # 主检测脚本（16种模式）
│   ├── stacktrace.py     # 堆栈解析工具
│   └── trend.py          # 趋势分析工具
├── rules/
│   └── default.yaml      # 默认报警规则
└── patterns/
    └── patterns.json     # 异常模式定义（可扩展）
```
