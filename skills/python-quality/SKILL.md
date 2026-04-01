# Python Code Quality Toolkit

> 代码质量、测试、性能分析、包管理 — 全方位 Python 工程化工具集

## 定位

专注 Python **代码质量维度**：lint、格式化、测试、性能、包管理。

与 `python-toolkit`（logging / 异常处理 / 运行时）互补，不重复。

---

## 🔧 Ruff — 一站式 Linter + Formatter

Ruff 用 Rust 编写，**比 flake8 + isort + pyupgrade + black 快 100x**，一个工具替代四个。

### 安装

```bash
uv add --dev ruff
# 或
pip install ruff
```

### 常用命令

```bash
# Lint（检查）
ruff check .

# 自动修复可修复的问题
ruff check . --fix

# 格式化（替代 black）
ruff format .

# 检查 + 格式化一步到位
ruff check . --fix && ruff format .
```

### pyproject.toml 配置（推荐）

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "SIM",   # flake8-simplify
    "C4",    # flake8-comprehensions
    "RUF",   # ruff-specific rules
]
ignore = ["E501"]  # 行长由 formatter 管

[tool.ruff.lint.isort]
known-first-party = ["myproject"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 实用规则速查

| 规则 | 说明 | 示例 |
|------|------|------|
| `UP032` | f-string 替代 .format() | `"{}".format(x)` → `f"{x}"` |
| `UP035` | deprecated import | `typing.Dict` → `dict` |
| `SIM108` | 三元表达式 | `if/else` → `x if cond else y` |
| `C400` | list() → 列表推导 | `list(x for x in items)` → `[x for x in items]` |
| `B905` | zip() 需 strict=True | Python 3.10+ 防长度不一致 |

### pre-commit 集成

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

---

## 🧪 pytest Fixtures 最佳实践

### conftest.py 层级结构

```
project/
├── conftest.py          # 全局 fixtures
├── tests/
│   ├── conftest.py      # tests 级 fixtures
│   ├── api/
│   │   ├── conftest.py  # api 测试专用 fixtures
│   │   └── test_users.py
│   └── unit/
│       └── test_calc.py
```

**规则**：fixtures 放在最近的 conftest.py，避免全局污染。

### Scope 选择

```python
import pytest

@pytest.fixture(scope="session")   # 整个测试会话一次
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")    # 每个测试模块一次
def db_session(db_engine):
    session = sessionmaker(bind=db_engine)()
    yield session
    session.close()

@pytest.fixture(scope="function")  # 每个测试函数一次（默认）
def user(db_session):
    user = User(name="test")
    db_session.add(user)
    db_session.commit()
    yield user
    db_session.delete(user)
    db_session.commit()
```

### 参数化 Fixtures

```python
@pytest.fixture(params=["sqlite", "postgres"], ids=["sqlite", "pg"])
def db_backend(request):
    return request.param

def test_query(db_backend):  # 自动跑两遍
    ...
```

### Factory Fixture 模式

```python
@pytest.fixture
def make_user(db_session):
    """返回工厂函数，测试中按需创建用户"""
    def _make(**overrides):
        defaults = {"name": "Test", "email": "test@example.com"}
        defaults.update(overrides)
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        return user
    return _make

def test_admin(make_user):
    admin = make_user(role="admin")
    assert admin.role == "admin"
```

### tmp_path vs tmp_path_factory

```python
# 函数级临时目录（自动清理）
def test_write_file(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"ok": true}')
    assert f.exists()

# 会话级临时目录
@pytest.fixture(scope="session")
def shared_data(tmp_path_factory):
    d = tmp_path_factory.mktemp("shared")
    (d / "config.yaml").write_text("key: val")
    return d
```

### 标记与跳过

```python
@pytest.mark.slow           # 慢测试
@pytest.mark.integration    # 集成测试
@pytest.skipif(sys.platform == "win32", reason="Unix only")
@pytest.skipif(not HAS_GPU, reason="No GPU")
```

```bash
# 运行时过滤
pytest -m "not slow"        # 跳过慢测试
pytest -m integration       # 只跑集成测试
```

---

## 📦 uv — 下一代包管理

uv 同样用 Rust 编写，比 pip 快 **10-100x**。

### 核心工作流

```bash
# 初始化项目
uv init myproject
cd myproject

# 添加依赖
uv add requests
uv add --dev pytest ruff mypy

# 移除依赖
uv remove requests

# 安装全部依赖
uv sync

# 运行命令（自动使用项目虚拟环境）
uv run python main.py
uv run pytest
uv run ruff check .

# 锁定依赖
uv lock
```

### pyproject.toml 结构

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.9",
    "mypy>=1.14",
]
```

### 多 Python 版本

```bash
# 安装指定 Python 版本
uv python install 3.12 3.13

# 用特定版本创建虚拟环境
uv venv --python 3.13

# 查看已安装的 Python
uv python list
```

### 与 pip 的对比

| 操作 | pip | uv |
|------|-----|-----|
| 安装依赖 | `pip install -r requirements.txt` | `uv sync` |
| 添加包 | `pip install X` + 手动更新 requirements.txt | `uv add X` |
| 运行脚本 | `pip install -e . && python script.py` | `uv run script.py` |
| 锁文件 | 需 pip-tools / poetry | 内置 `uv.lock` |

---

## 📊 cProfile + snakeviz 性能分析

### cProfile 基础

```bash
# 分析脚本
python -m cProfile -o profile.stats myscript.py

# 只看最慢的 20 个函数
python -m cProfile -s cumulative myscript.py
```

### 代码内 profiling

```python
import cProfile
import pstats

def profile_section():
    profiler = cProfile.Profile()
    profiler.enable()

    # 要分析的代码
    result = expensive_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20
    stats.dump_stats("profile.stats")
    return result
```

### snakeviz 可视化

```bash
# 安装
uv add --dev snakeviz

# 生成 profile 文件后可视化
snakeviz profile.stats
# 自动打开浏览器，展示火焰图和调用树
```

### 性能分析决策流程

```
代码慢？
  ├─ CPU 密集 → cProfile → 找热点函数 → 优化算法 / 用 C 扩展
  ├─ IO 密集 → 建议用 asyncio / threading
  ├─ 内存问题 → tracemalloc / memray
  └─ 不确定 → 先 cProfile 看 cumtime vs tottime
      ├─ cumtime 高 = 函数及其子函数总耗时 → 往下追
      └─ tottime 高 = 函数自身耗时 → 这就是热点
```

### 用装饰器快速 profiling

```python
import cProfile
import functools
import pstats
from io import StringIO

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(15)
        print(f"\n--- Profile: {func.__name__} ---")
        print(stream.getvalue())
        return result
    return wrapper

@profile
def process_data(data):
    ...
```

---

## 🗜️ Python 3.14 zstd 压缩

Python 3.14 标准库新增 `compression.zstd` 模块（PEP 784），无需第三方库。

### 基础用法

```python
import compression.zstd as zstd

# 压缩
data = b"Hello " * 10000
compressed = zstd.compress(data)
print(f"压缩率: {len(compressed) / len(data):.1%}")

# 解压
decompressed = zstd.decompress(compressed)
assert decompressed == data
```

### 流式压缩（大文件）

```python
import compression.zstd as zstd

# 压缩
with open("large.bin", "rb") as src:
    with open("large.bin.zst", "wb") as dst:
        with zstd.open(dst, "wb") as compressor:
            while chunk := src.read(65536):
                compressor.write(chunk)

# 解压
with zstd.open("large.bin.zst", "rb") as src:
    with open("large_restored.bin", "wb") as dst:
        while chunk := src.read(65536):
            dst.write(chunk)
```

### 压缩级别

```python
# 级别 1-22，默认 3。级别越高压缩率越好但越慢
light = zstd.compress(data, level=1)    # 快
heavy = zstd.compress(data, level=19)   # 慢但更小
```

### 与 gzip/zlib 对比

```python
import gzip
import compression.zstd as zstd
import time

data = b"repetitive data " * 100000

# 压缩对比
t0 = time.perf_counter()
gz = gzip.compress(data)
t_gzip = time.perf_counter() - t0

t0 = time.perf_counter()
zs = zstd.compress(data)
t_zstd = time.perf_counter() - t0

print(f"gzip: {len(gz)} bytes, {t_gzip:.3f}s")
print(f"zstd: {len(zs)} bytes, {t_zstd:.3f}s")
# zstd 通常快 3-5x，压缩率更好
```

---

## 🔄 itertools 实用模式

### 常用组合模式

```python
from itertools import chain, islice, groupby, pairwise, batched, takewhile, dropwhile
from operator import itemgetter
```

### batched — 分批处理（3.12+）

```python
from itertools import batched

# 将列表分批处理（如批量 API 调用）
urls = [f"https://api.example.com/{i}" for i in range(100)]

for batch in batched(urls, 10):
    responses = asyncio.gather(*[fetch(u) for u in batch])
    process(responses)
```

### pairwise — 相邻配对（3.10+）

```python
from itertools import pairwise

prices = [100, 105, 103, 110, 108]
changes = [b - a for a, b in pairwise(prices)]
# [5, -2, 7, -2]
```

### groupby — 分组（需预排序）

```python
from itertools import groupby
from operator import itemgetter

data = [
    {"dept": "eng", "name": "Alice"},
    {"dept": "eng", "name": "Bob"},
    {"dept": "hr", "name": "Carol"},
]
data.sort(key=itemgetter("dept"))

for dept, members in groupby(data, key=itemgetter("dept")):
    print(f"{dept}: {[m['name'] for m in members]}")
# eng: ['Alice', 'Bob']
# hr: ['Carol']
```

### chain.from_iterable — 展平嵌套

```python
from itertools import chain

nested = [[1, 2], [3, 4], [5]]
flat = list(chain.from_iterable(nested))
# [1, 2, 3, 4, 5]

# 比 sum(nested, []) 快得多（O(n) vs O(n²)）
```

### takewhile / dropwhile — 条件截取

```python
from itertools import takewhile, dropwhile

# 取满足条件的前缀
sorted_scores = [95, 88, 82, 76, 70, 65]
passing = list(takewhile(lambda s: s >= 70, sorted_scores))
# [95, 88, 82, 76, 70]

# 跳过满足条件的前缀
raw = ["", "", "  ", "hello", "world"]
content = list(dropwhile(lambda s: not s.strip(), raw))
# ['hello', 'world']
```

### islice — 惰性切片

```python
from itertools import islice

def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# 取前 10 个斐波那契数（不会生成无限序列）
first_10 = list(islice(fibonacci(), 10))
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### 组合技：数据管道

```python
from itertools import chain, batched, filterfalse, starmap
from operator import lt

# 管道：获取 → 过滤 → 分批 → 处理
def process_pipeline(records):
    valid = filter(lambda r: r.get("status") == "active", records)
    for batch in batched(valid, 50):
        results = starmap(transform, [(b,) for b in batch])
        yield from results
```

---

## 📋 项目配置模板

完整 `pyproject.toml` 参考：

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=6.0",
    "ruff>=0.9",
    "mypy>=1.14",
    "snakeviz>=2.2",
]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM", "C4", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["myproject"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q --strict-markers"
markers = [
    "slow: 慢测试",
    "integration: 集成测试",
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
```

---

## ⚡ Quick Reference

```bash
# 代码质量一站式
uv run ruff check . --fix && uv run ruff format .

# 测试 + 覆盖率
uv run pytest --cov=src --cov-report=term-missing

# 性能分析
uv run python -m cProfile -o prof.stats script.py && snakeviz prof.stats

# 类型检查
uv run mypy src/
```
