# Python 爬虫工具链 (Python Crawler Toolkit)

> 生产级 Python 爬虫开发全栈指南：反检测、高并发、压缩存储

## 与 web-content-fetcher 的区别

| 维度 | web-content-fetcher | python-crawler |
|------|-------------------|----------------|
| 定位 | 通用 URL 内容提取（黑盒） | 完整爬虫工具链（白盒） |
| 使用方式 | 一行调用，自动降级 | 编写 Python 脚本，完全控制 |
| 适用场景 | 快速读取单个页面 | 大规模采集、反爬对抗、定制化抓取 |
| 输出 | Markdown 文本 | 自定义（JSON/CSV/数据库等） |

**选择指南**：只需读取一篇文章 → web-content-fetcher；需要爬取多页、处理反爬、自定义流程 → python-crawler。

---

## 1. 反检测策略决策树

选择正确的工具是反检测的第一步。根据目标站点特征做决策：

```
目标站点分析
├── 纯静态页面（无 JS 渲染）
│   ├── 有 TLS 指纹检测（Cloudflare / Akamai）
│   │   └── ✅ curl_cffi（JA3/JA4 模拟）
│   └── 无 TLS 指纹检测
│       └── ✅ httpx AsyncClient（HTTP/2 高并发）
├── 需要 JS 渲染（SPA / 动态加载）
│   ├── 有 Bot 检测（指纹 / WebDriver 检测）
│   │   └── ✅ Playwright + 反检测补丁
│   └── 无 Bot 检测
│       └── ✅ Playwright（默认配置即可）
└── 需要登录态 / 复杂交互
    └── ✅ Playwright（持久化 Context）
```

### 常见反爬提供商识别

| 提供商 | 特征 | 应对方案 |
|--------|------|----------|
| **Cloudflare** | 403/503 + `cf-ray` header、JS Challenge、Turnstile CAPTCHA | curl_cffi（JA3 模拟）或 Playwright |
| **Akamai** | `akamai-*` headers、Bot Manager 响应 | curl_cffi + 浏览器 User-Agent |
| **PerimeterX/HUMAN** | `_px` cookies、`humansecurity` 域名 | Playwright + 持久化 session |
| **DataDome** | `datadome` cookie、`dd` 前缀 | curl_cffi + 代理轮换 |
| **Imperva/Incapsula** | `incap_ses`/`visid_incap` cookies | Playwright + JS 执行 |
| **GeeTest** | 滑块/点选验证码 | 第三方打码 或 Playwright 自动化 |
| **reCAPTCHA/hCaptcha** | iframe 嵌入验证码 | 第三方打码服务 |

**快速识别命令**：
```bash
# 检查响应头中的反爬标识
curl -sI https://target.com | grep -iE 'cf-ray|akamai|incap|px|datadome|server'
```

---

## 2. curl_cffi — 反 TLS 指纹（JA3/JA4 模拟）

`curl_cffi` 底层使用修改版 curl，能模拟真实浏览器的 TLS Client Hello 指纹，绕过 Cloudflare/Akamai 等的 JA3/JA4 检测。

### 安装

```bash
pip install curl_cffi
```

### 基础用法

```python
from curl_cffi import requests

# 模拟 Chrome 浏览器 TLS 指纹
resp = requests.get(
    "https://target.com",
    impersonate="chrome",  # 自动匹配 Chrome 110-131
)
print(resp.status_code)
print(resp.text[:500])
```

### 支持的 impersonate 选项

```python
# Chrome 系列（最常用）
impersonate="chrome"           # 最新版 Chrome
impersonate="chrome120"        # Chrome 120
impersonate="chrome110"        # Chrome 110

# Safari 系列
impersonate="safari"           # 最新版 Safari
impersonate="safari15_5"       # Safari 15.5
impersonate="safari17_0"       # Safari 17.0

# Firefox 系列
impersonate="firefox"          # 最新版 Firefox
impersonate="firefox109"       # Firefox 109

# Edge
impersonate="edge99"           # Edge 99
```

### 高级配置（完整反检测）

```python
from curl_cffi import requests

session = requests.Session()

# 设置请求头（与 impersonate 的浏览器版本一致）
session.headers.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="120", "Google Chrome";v="120", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
})

resp = session.get(
    "https://target.com",
    impersonate="chrome120",
    timeout=30,
    verify=True,
)

# 处理重定向和 cookies
print(resp.cookies)
print(resp.history)  # 重定向链
```

### 代理支持

```python
resp = session.get(
    "https://target.com",
    impersonate="chrome",
    proxy="http://user:pass@proxy:8080",
    # 或 socks5
    # proxy="socks5://user:pass@proxy:1080",
)
```

### curl_cffi 的适用边界

- ✅ 绕过 Cloudflare / Akamai 的 TLS 指纹检测
- ✅ 高性能（C 底层，比 requests 快）
- ✅ 支持 HTTP/2
- ❌ 不执行 JavaScript
- ❌ 不处理需要 JS 渲染的 SPA 页面

---

## 3. Playwright — 反检测配置

当目标站点需要 JS 渲染或有 Bot 指纹检测时，使用 Playwright。

### 安装

```bash
pip install playwright
playwright install chromium
```

### 基础反检测配置

```python
import asyncio
from playwright.async_api import async_playwright

async def create_stealth_browser():
    """创建反检测浏览器实例"""
    p = await async_playwright().start()
    
    browser = await p.chromium.launch(
        headless=True,  # 生产环境用 True，调试用 False
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--start-maximized",
            "--disable-extensions",
        ],
    )
    
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        color_scheme="light",
        permissions=["geolocation"],
        java_script_enabled=True,
    )
    
    # 注入反检测脚本（每次页面加载前执行）
    await context.add_init_script("""
        // 隐藏 webdriver 属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // 伪造 plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' },
                ];
            },
        });
        
        // 伪造 languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en'],
        });
        
        // 伪造 platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel',
        });
        
        // 伪造 hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        // 伪装 chrome 对象（Chrome 浏览器特有）
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() { return {}; },
            app: { isInstalled: false, InstallState: 'disabled', RunningState: 'cannot_run' },
        };
        
        // 阻止 permissions 查询泄露自动化状态
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 伪造 WebGL 指标
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        };
    """)
    
    return p, browser, context
```

### 持久化登录态

```python
async def use_persistent_context(p, user_data_dir="/tmp/playwright-profile"):
    """使用持久化 Context 保存 cookies 和 localStorage"""
    context = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=True,
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 ...",
        args=["--disable-blink-features=AutomationControlled"],
    )
    return context
    # cookies / localStorage 自动持久化到 user_data_dir
```

### 模拟人类行为

```python
import random

async def human_like_navigation(page, url):
    """模拟人类导航行为"""
    # 随机延迟
    await asyncio.sleep(random.uniform(1, 3))
    
    # 移动鼠标（随机轨迹）
    await page.mouse.move(
        random.randint(100, 800),
        random.randint(100, 600),
        steps=random.randint(5, 20),
    )
    
    # 正常导航
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    
    # 模拟阅读时间
    await asyncio.sleep(random.uniform(2, 5))
    
    # 随机滚动
    for _ in range(random.randint(1, 3)):
        await page.mouse.wheel(0, random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))
```

### Playwright 的适用边界

- ✅ 完整 JS 渲染引擎
- ✅ 可模拟真实用户交互
- ✅ 持久化 Context 保持登录态
- ❌ 资源消耗大（每个页面 ≈ 100-300MB）
- ❌ 速度慢于 HTTP 客户端
- ❌ 部分高端指纹检测（PerimeterX）仍可识别

---

## 4. httpx AsyncClient — HTTP/2 高并发

适合无 TLS 指纹检测的站点大规模并发采集。

### 安装

```bash
pip install httpx[http2]
```

### 基础用法

```python
import httpx
import asyncio

async def fetch_page(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.text

async def main():
    async with httpx.AsyncClient(
        http2=True,              # 启用 HTTP/2
        follow_redirects=True,   # 自动跟随重定向
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    ) as client:
        urls = [f"https://example.com/page/{i}" for i in range(100)]
        tasks = [fetch_page(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print(f"获取了 {len(results)} 个页面")

asyncio.run(main())
```

### HTTP/2 多路复用优势

```python
# HTTP/1.1: 每个请求需要独立 TCP 连接（受浏览器 6 连接限制）
# HTTP/2:   单连接多路复用，并行请求无需排队

async with httpx.AsyncClient(
    http2=True,
    # 连接池配置
    limits=httpx.Limits(
        max_connections=100,        # 最大连接数
        max_keepalive_connections=20,  # 保持活跃连接数
    ),
) as client:
    # 这些请求在 HTTP/2 下共享同一 TCP 连接
    ...
```

### 错误处理与重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url)
    if resp.status_code == 429:  # Rate Limited
        retry_after = int(resp.headers.get("Retry-After", 5))
        await asyncio.sleep(retry_after)
        raise httpx.HTTPStatusError("429", request=resp.request, response=resp)
    resp.raise_for_status()
    return resp.text
```

---

## 5. 并发控制 — asyncio TaskGroup + Semaphore

### Semaphore 限流（经典方案）

```python
import asyncio
import httpx

async def crawl_with_semaphore(urls: list[str], max_concurrent: int = 10):
    """使用 Semaphore 控制并发数"""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []
    
    async def limited_fetch(client: httpx.AsyncClient, url: str):
        async with semaphore:  # 同时最多 max_concurrent 个请求
            try:
                resp = await client.get(url, timeout=15)
                return {"url": url, "status": resp.status_code, "content": resp.text[:500]}
            except Exception as e:
                return {"url": url, "error": str(e)}
    
    async with httpx.AsyncClient(http2=True) as client:
        tasks = [limited_fetch(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    return results
```

### Python 3.11+ TaskGroup（结构化并发）

```python
import asyncio
import httpx

async def crawl_with_taskgroup(urls: list[str], max_concurrent: int = 10):
    """使用 TaskGroup + Semaphore 实现结构化并发
    
    优势：
    - 任何子任务异常 → 自动取消所有兄弟任务
    - 作用域结束 → 所有任务已完成（不会泄漏）
    - 异常传播更清晰（ExceptionGroup）
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []
    
    async def fetch(client: httpx.AsyncClient, url: str, idx: int):
        async with semaphore:
            resp = await client.get(url, timeout=15)
            results.append({"idx": idx, "url": url, "status": resp.status_code})
    
    async with httpx.AsyncClient(http2=True) as client:
        async with asyncio.TaskGroup() as tg:
            for i, url in enumerate(urls):
                tg.create_task(fetch(client, url, i))
    
    # TaskGroup 结束时，所有任务已完成
    return sorted(results, key=lambda x: x["idx"])
```

### 带速率限制的高级并发控制

```python
import asyncio
import time

class RateLimiter:
    """令牌桶速率限制器"""
    
    def __init__(self, rate: float, burst: int = 1):
        """
        rate: 每秒允许的请求数
        burst: 突发容量
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

# 使用示例
async def crawl_with_rate_limit(urls: list[str]):
    limiter = RateLimiter(rate=5, burst=10)  # 每秒 5 个请求，突发 10 个
    semaphore = asyncio.Semaphore(20)
    
    async def fetch(client, url):
        async with semaphore:
            await limiter.acquire()  # 速率限制
            return await client.get(url)
    
    async with httpx.AsyncClient(http2=True) as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch(client, url)) for url in urls]
```

---

## 6. Python 3.14 zstd 压缩存储

Python 3.14 原生支持 zstd（Zstandard）压缩，比 gzip 压缩率高 30-50%，速度更快。

### 安装要求

- Python 3.14+ （原生 `compression.zstd` 模块）
- Python 3.13 及以下：`pip install zstandard`（第三方库）

### 原生 zstd（Python 3.14+）

```python
import compression.zstd as zstd
import json

def save_compressed(data: list[dict], filepath: str, level: int = 3):
    """使用 zstd 压缩存储爬取数据
    
    level: 压缩级别 1-22（默认 3，推荐 3-6 平衡速度和压缩率）
    """
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    compressed = zstd.compress(raw, level=level)
    
    with open(filepath, "wb") as f:
        f.write(compressed)
    
    ratio = len(compressed) / len(raw) * 100
    print(f"原始: {len(raw):,} bytes → 压缩: {len(compressed):,} bytes ({ratio:.1f}%)")

def load_compressed(filepath: str) -> list[dict]:
    """读取 zstd 压缩文件"""
    with open(filepath, "rb") as f:
        compressed = f.read()
    raw = zstd.decompress(compressed)
    return json.loads(raw)

# 流式压缩（适合大文件）
def save_streaming(data_iter, filepath: str):
    """流式写入 zstd 压缩文件（避免内存爆炸）"""
    import io
    with open(filepath, "wb") as f:
        with zstd.open(f, "wb", level=3) as compressor:
            for item in data_iter:
                compressor.write(json.dumps(item, ensure_ascii=False) + "\n")
```

### 兼容方案（Python 3.13 及以下）

```python
import zstandard as zstd  # pip install zstandard
import json

def save_compressed_compat(data: list[dict], filepath: str, level: int = 3):
    """兼容 Python < 3.14 的 zstd 压缩"""
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    cctx = zstd.ZstdCompressor(level=level)
    compressed = cctx.compress(raw)
    
    with open(filepath, "wb") as f:
        f.write(compressed)

def load_compressed_compat(filepath: str) -> list[dict]:
    with open(filepath, "rb") as f:
        compressed = f.read()
    dctx = zstd.ZstdDecompressor()
    raw = dctx.decompress(compressed)
    return json.loads(raw)
```

### 压缩格式对比

| 格式 | 压缩率 | 压缩速度 | 解压速度 | Python 支持 |
|------|--------|----------|----------|-------------|
| zstd 3 | ★★★★★ | ★★★★★ | ★★★★★ | 3.14 原生 / pip |
| gzip 6 | ★★★☆☆ | ★★★★☆ | ★★★★☆ | 原生 |
| lz4 | ★★☆☆☆ | ★★★★★+ | ★★★★★+ | pip |
| bz2 | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | 原生 |
| xz | ★★★★★+ | ★☆☆☆☆ | ★★★☆☆ | 原生 |

**推荐**：爬虫数据存储首选 zstd（压缩率高 + 速度快），分发给第三方选 gzip（兼容性好）。

---

## 7. 完整爬虫项目模板

```python
"""
生产级爬虫模板 — 整合所有工具链
"""
import asyncio
import json
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

import httpx
from curl_cffi import requests as curl_requests

# Python 3.14+
try:
    import compression.zstd as zstd
except ImportError:
    import zstandard as zstd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    url: str
    status: int
    content: str
    headers: dict
    crawled_at: str = field(default_factory=lambda: datetime.now().isoformat())
    fingerprint: str = ""  # curl_cffi impersonate name
    
    def __post_init__(self):
        self.fingerprint = hashlib.md5(self.url.encode()).hexdigest()[:8]


class Spider:
    """统一爬虫接口，自动选择最佳抓取策略"""
    
    def __init__(
        self,
        max_concurrent: int = 10,
        rate_limit: float = 5.0,  # 每秒请求数
        output_dir: str = "output",
        compress_level: int = 3,
    ):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.compress_level = compress_level
        self.results: list[CrawlResult] = []
    
    async def fetch_httpx(self, url: str) -> CrawlResult:
        """HTTP/2 高并发方案（无 TLS 指纹检测时使用）"""
        async with self.semaphore:
            async with httpx.AsyncClient(http2=True, timeout=15) as client:
                resp = await client.get(url)
                return CrawlResult(
                    url=url,
                    status=resp.status_code,
                    content=resp.text,
                    headers=dict(resp.headers),
                )
    
    def fetch_curl_cffi(self, url: str, impersonate: str = "chrome") -> CrawlResult:
        """curl_cffi 方案（有 TLS 指纹检测时使用）"""
        resp = curl_requests.get(url, impersonate=impersonate, timeout=15)
        return CrawlResult(
            url=url,
            status=resp.status_code,
            content=resp.text,
            headers=dict(resp.headers),
            fingerprint=impersonate,
        )
    
    async def crawl_batch(self, urls: list[str], strategy: str = "httpx"):
        """批量爬取
        
        strategy: "httpx" | "curl_cffi"
        """
        if strategy == "httpx":
            async with asyncio.TaskGroup() as tg:
                for url in urls:
                    tg.create_task(self._fetch_and_store(url))
        elif strategy == "curl_cffi":
            for url in urls:
                result = self.fetch_curl_cffi(url)
                self.results.append(result)
                logger.info(f"[curl_cffi] {result.status} {url}")
    
    async def _fetch_and_store(self, url: str):
        result = await self.fetch_httpx(url)
        self.results.append(result)
        logger.info(f"[httpx] {result.status} {url}")
    
    def save(self, filename: str = "results"):
        """zstd 压缩存储"""
        data = [asdict(r) for r in self.results]
        filepath = self.output_dir / f"{filename}.json.zst"
        
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        
        try:
            compressed = zstd.compress(raw, level=self.compress_level)
        except AttributeError:
            cctx = zstd.ZstdCompressor(level=self.compress_level)
            compressed = cctx.compress(raw)
        
        with open(filepath, "wb") as f:
            f.write(compressed)
        
        ratio = len(compressed) / len(raw) * 100
        logger.info(
            f"已保存 {len(data)} 条记录 → {filepath} "
            f"({len(raw):,} → {len(compressed):,} bytes, {ratio:.1f}%)"
        )


# === 使用示例 ===
async def main():
    spider = Spider(max_concurrent=20, output_dir="output")
    
    urls = [f"https://example.com/page/{i}" for i in range(1, 101)]
    
    # 场景 1：无反爬，用 httpx 高并发
    await spider.crawl_batch(urls[:50], strategy="httpx")
    
    # 场景 2：有 Cloudflare，用 curl_cffi
    spider.results.clear()
    for url in urls[50:]:
        result = spider.fetch_curl_cffi(url, impersonate="chrome120")
        spider.results.append(result)
    
    spider.save("crawl_2024")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. 常见问题与排错

### curl_cffi 报 SSL 错误
```python
# 尝试更新 impersonate 版本
resp = requests.get(url, impersonate="chrome120")  # 换版本

# 或降级验证
resp = requests.get(url, impersonate="chrome", verify=False)  # 不推荐生产用
```

### Playwright 被检测到
```python
# 1. 确认注入脚本在 add_init_script 中（页面加载前执行）
# 2. 使用 launch_persistent_context 替代 launch + new_context
# 3. 检查 navigator.webdriver 是否为 undefined
page.evaluate("navigator.webdriver")  # 应返回 undefined
```

### httpx HTTP/2 连接失败
```bash
# 确认安装了 h2 支持
pip install "httpx[http2]"
python -c "import h2; print(h2.__version__)"
```

### zstd 压缩报错
```python
# Python 3.14+ 用 compression.zstd
# Python < 3.14 用 pip install zstandard
import sys
print(sys.version)  # 确认 Python 版本
```

---

## 9. 依赖清单

```txt
# requirements.txt
curl_cffi>=0.7.0
httpx[http2]>=0.27.0
playwright>=1.40.0
tenacity>=8.2.0
zstandard>=0.22.0; python_version < "3.14"
```

```bash
pip install -r requirements.txt
playwright install chromium
```
