---
name: python-toolkit
description: Python生产级工具集 — logging/异常处理/性能分析。告别print调试，所有新脚本import即用。
---

# Python Toolkit — 生产级工具集

## 模块

### 1. log_setup — 生产级日志

替代print，支持彩色终端+文件轮转+JSON格式+exc_info。

```python
from log_setup import get_logger, log_calls

log = get_logger(__name__, log_file="/tmp/my_script.log")
log.info("Server started")
log.error("Connection failed", exc_info=True)

@log_calls()
def fetch_data(url):
    # 自动记录函数调用和返回
    ...
```

**特性**：
- 彩色终端输出（DEBUG/INFO/WARNING/ERROR）
- 文件轮转（10MB，保留5个备份）
- JSON格式（便于日志聚合）
- @log_calls装饰器（自动记录函数调用）
- exc_info（自动记录traceback）

### 使用方式

```bash
# 在脚本中直接import
python3 -c "from log_setup import get_logger; log = get_logger('test'); log.info('Hello')"
```

## 文件

- `scripts/log_setup.py` — 生产级日志模块
