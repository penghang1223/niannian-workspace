# 🛡️ 本尔 - 测试工程师学习笔记

## 📚 学习路线图
- **第一轮（P0）**：pytest 基础 → pytest 进阶 → API 测试 → UI 测试
- **第二轮（P0）**：测试用例设计 → 缺陷管理 → 代码审查 → 持续集成
- **第三轮**：压力测试 → 监控告警

---

## 1. pytest 基础 - 测试框架/断言/夹具

### 🎯 核心概念
pytest 是 Python 最流行的测试框架，以简洁的语法和强大的 fixture 系统著称。

### 📝 基础语法
```python
# test_sample.py
def func(x):
    return x + 1

def test_answer():
    assert func(3) == 5  # 断言失败会显示中间值
```

### 🔧 断言系统
- **基本断言**：`assert condition`，失败时显示变量值
- **异常断言**：`with pytest.raises(SystemExit):`
- **浮点近似**：`pytest.approx(0.3)` 处理精度问题
- **无需 `self.assertEqual`**：直接用 Python 原生 assert

### 📦 测试组织
```python
# 分组到类中（类名必须以 Test 开头）
class TestClass:
    def test_one(self):
        x = "this"
        assert "h" in x
    
    def test_two(self):
        x = "hello"
        assert hasattr(x, "check")  # 失败
```

**重要**：每个测试方法有独立的类实例，不会共享状态

### 🎭 Fixture 系统（核心重点）
```python
import pytest

@pytest.fixture
def fruit_bowl():
    return [Fruit("apple"), Fruit("banana")]

def test_fruit_salad(fruit_bowl):  # 自动注入
    fruit_salad = FruitSalad(*fruit_bowl)
    assert all(fruit.cubed for fruit in fruit_salad.fruit)
```

#### Fixture 关键特性
| 特性 | 说明 |
|------|------|
| **请求机制** | 测试函数参数名匹配 fixture 函数名 |
| **可嵌套** | fixture 可以请求其他 fixture |
| **自动缓存** | 同一测试中重复请求同一 fixture 只执行一次 |
| **可复用** | 不同测试获得各自独立的 fixture 实例 |

#### Fixture 作用域（Scope）
```python
@pytest.fixture(scope="module")  # 整个模块共享
def smtp_connection():
    return smtplib.SMTP("smtp.gmail.com", 587)

@pytest.fixture(scope="session")  # 整个测试会话共享
def database():
    return create_database()
```

作用域选项：`function`(默认) → `class` → `module` → `package` → `session`

#### Autouse Fixture（自动使用）
```python
@pytest.fixture(autouse=True)
def setup_logging():
    # 所有测试自动使用，无需显式请求
    logging.basicConfig(level=logging.DEBUG)
```

### 🏃 运行命令
```bash
pytest                    # 运行所有测试
pytest -q                 # 简洁输出
pytest -k "test_name"     # 按名称过滤
pytest --fixtures         # 查看所有 fixture
```

### 💡 关键记忆点
1. **测试发现**：自动识别 `test_*.py` 或 `*_test.py` 文件
2. **断言即 Python**：用原生 assert，无需特殊方法
3. **Fixture 是核心**：setup/teardown 全靠它
4. **作用域选择**：按需选择，平衡性能和隔离性

---

## 2. pytest 进阶 - 参数化/标记/插件

### 🎯 参数化（Parametrize）
```python
@pytest.mark.parametrize("test_input,expected", [
    ("3+5", 8), 
    ("2+4", 6), 
    ("6*9", 42)
])
def test_eval(test_input, expected):
    assert eval(test_input) == expected
```

#### 参数化高级用法
```python
# 组合参数化（笛卡尔积）
@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("y", [2, 3])
def test_foo(x, y):  # 运行4次: (0,2),(1,2),(0,3),(1,3)
    pass

# 标记特定参数组合为 xfail
@pytest.mark.parametrize("test_input,expected", [
    ("3+5", 8),
    pytest.param("6*9", 42, marks=pytest.mark.xfail)  # 期望失败
])
```

#### Fixture 参数化
```python
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param  # 每个测试运行3次

def test_number(number):
    assert number > 0
```

### 🏷️ 标记系统（Markers）
```python
# 内置标记
@pytest.mark.skip(reason="功能未实现")
@pytest.mark.skipif(sys.platform == "win32", reason="不支持Windows")
@pytest.mark.xfail(reason="已知bug")
@pytest.mark.usefixtures("fixture_name")

# 自定义标记
@pytest.mark.slow
def test_slow_operation():
    time.sleep(5)
```

#### 运行标记测试
```bash
pytest -m slow              # 只运行 slow 标记的测试
pytest -m "not slow"        # 排除 slow 测试
pytest -m "slow and smoke"  # 组合条件
```

#### 注册标记（防止警告）
```toml
# pytest.toml
[pytest]
markers = [
    "slow: marks tests as slow",
    "smoke: marks smoke tests"
]
```

### 🔌 插件生态
常用插件：
- **pytest-cov**：测试覆盖率
- **pytest-xdist**：并行执行
- **pytest-mock**：Mock 支持
- **pytest-html**：生成 HTML 报告
- **pytest-timeout**：测试超时控制

### 📊 conftest.py
- 存放共享 fixture 的文件
- 可在多个目录级别存在
- 自动被同级及子目录测试发现

### 💡 关键记忆点
1. **参数化**：减少重复代码，一个测试函数覆盖多组数据
2. **标记系统**：灵活的测试分类和选择机制
3. **xfail vs skip**：xfail=已知会失败，skip=跳过不执行
4. **组合参数化**：笛卡尔积产生大量测试用例

---

## 3. API 测试 - Requests/接口自动化

### 🎯 核心库：Requests
```python
import requests

# 基本请求
r = requests.get('https://api.github.com/events')
r = requests.post('https://httpbin.org/post', data={'key': 'value'})
r = requests.put('https://httpbin.org/put', json={'key': 'value'})
r = requests.delete('https://httpbin.org/delete')
```

### 📊 Response 对象属性
```python
r.status_code  # 状态码 200/404/500
r.text         # 响应文本（自动解码）
r.json()       # JSON 响应解析
r.content      # 二进制内容
r.headers      # 响应头
r.url          # 最终URL（含参数）
r.encoding     # 编码格式
```

### 🔧 请求参数详解
```python
# URL 参数
params = {'key1': 'value1', 'key2': 'value2'}
requests.get('https://api.example.com', params=params)

# JSON 请求体
requests.post(url, json={'name': 'test'})

# 表单数据
requests.post(url, data={'username': 'admin'})

# 文件上传
files = {'file': open('report.xlsx', 'rb')}
requests.post(url, files=files)

# 请求头
headers = {'Authorization': 'Bearer token123'}
requests.get(url, headers=headers)
```

### 🧪 pytest + API 测试
```python
import pytest
import requests

@pytest.fixture
def api_client():
    """API 客户端 fixture"""
    session = requests.Session()
    session.headers.update({'Authorization': 'Bearer test-token'})
    return session

@pytest.fixture
def base_url():
    return "https://api.example.com"

def test_get_users(api_client, base_url):
    response = api_client.get(f"{base_url}/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_user(api_client, base_url):
    user_data = {"name": "Test User", "email": "test@example.com"}
    response = api_client.post(f"{base_url}/users", json=user_data)
    assert response.status_code == 201
    assert response.json()['name'] == "Test User"

@pytest.mark.parametrize("user_id,expected_status", [
    (1, 200),
    (999, 404),
    (-1, 400)
])
def test_get_user_by_id(api_client, base_url, user_id, expected_status):
    response = api_client.get(f"{base_url}/users/{user_id}")
    assert response.status_code == expected_status
```

### 📋 API 测试检查清单
| 检查项 | 方法 |
|--------|------|
| 状态码 | `assert r.status_code == 200` |
| 响应时间 | `assert r.elapsed.total_seconds() < 2` |
| JSON 结构 | `assert 'id' in r.json()` |
| 数据类型 | `assert isinstance(r.json()['count'], int)` |
| 业务逻辑 | `assert r.json()['status'] == 'success'` |

### 🏗️ 测试框架架构
```python
# conftest.py - 全局配置
@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv("API_URL", "http://localhost:8000")

@pytest.fixture(scope="session")
def auth_token(api_base_url):
    """获取认证 token（整个测试会话共享）"""
    response = requests.post(f"{api_base_url}/auth/login", 
                           json={"user": "test", "pass": "test123"})
    return response.json()['token']
```

### 💡 关键记忆点
1. **Session 对象**：复用连接，性能更好
2. **状态码优先**：先验证状态码，再验证内容
3. **参数化**：一个测试覆盖正常/异常场景
4. **fixture 复用**：认证、URL 等配置提取为 fixture
5. **超时控制**：`requests.get(url, timeout=5)`

---

## 4. UI 测试 - Selenium/Playwright 基础

### 🎯 两种主流框架对比
| 特性 | Selenium | Playwright |
|------|----------|------------|
| 速度 | 较慢（WebDriver 协议） | 快（CDP 协议） |
| 自动等待 | 需手动处理 | 内置自动等待 |
| 浏览器支持 | Chrome/Firefox/Safari/Edge | Chromium/Firefox/WebKit |
| 定位器 | CSS/XPath 为主 | 多种现代定位器 |
| 异步支持 | 同步为主 | 同步+异步 |
| 推荐度 | 成熟稳定（适合遗留项目） | **首选**（现代项目） |

### 🚀 Playwright 快速开始
```python
# 安装
pip install pytest-playwright playwright
playwright install

# test_example.py
import re
from playwright.sync_api import Page, expect

def test_has_title(page: Page):
    page.goto("https://playwright.dev/")
    expect(page).to_have_title(re.compile("Playwright"))

def test_get_started_link(page: Page):
    page.goto("https://playwright.dev/")
    page.get_by_role("link", name="Get started").click()
    expect(page.get_by_role("heading", name="Installation")).to_be_visible()
```

### 🔍 Playwright 定位器（核心重点）
```python
# 按角色定位（推荐首选）
page.get_by_role("button", name="Sign in").click()
page.get_by_role("checkbox", name="Subscribe").check()
page.get_by_role("heading", name="Welcome").to_be_visible()

# 按文本定位
page.get_by_text("Welcome, John").to_be_visible()
page.get_by_text(re.compile("submit", re.IGNORECASE)).click()

# 按标签定位（表单控件）
page.get_by_label("Password").fill("secret")

# 按 placeholder 定位
page.get_by_placeholder("name@example.com").fill("test@test.com")

# 按 test-id 定位（最稳定）
page.get_by_test_id("submit-btn").click()

# CSS/XPath（不推荐，但支持）
page.locator("css=button.primary").click()
page.locator("xpath=//button[@type='submit']").click()
```

#### 定位器优先级（最佳实践）
1. **Role** - `get_by_role()`（最接近用户感知）
2. **Label** - `get_by_label()`（表单控件）
3. **Text** - `get_by_text()`（非交互元素）
4. **Test ID** - `get_by_test_id()`（最稳定）
5. **CSS/XPath** - 最后选择

### 📝 Playwright 操作
```python
# 页面导航
page.goto("https://example.com")
page.go_back()
page.reload()

# 元素操作
page.get_by_role("textbox").fill("hello")
page.get_by_role("button").click()
page.get_by_role("checkbox").check()
page.get_by_role("link").hover()

# 断言（Web-first assertions）
expect(page).to_have_title("Title")
expect(page.get_by_text("Hello")).to_be_visible()
expect(page.get_by_role("button")).to_be_enabled()
expect(page.locator("#count")).to_have_text("5")
```

### 🧪 pytest 集成
```python
# conftest.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()
```

### 💡 关键记忆点
1. **Playwright > Selenium**：现代项目的首选
2. **定位器选择**：Role > Label > Text > Test-ID > CSS
3. **自动等待**：Playwright 内置，Selenium 需手动处理
4. **headless 模式**：CI/CD 环境使用 headless=True
5. **截图/视频**：支持自动截图和录屏调试

---

## 5. 测试用例设计 - 等价类/边界值/场景法

### 🎯 核心目标
用最少的测试用例覆盖最多的场景，提高测试效率和覆盖率。

### 📊 1. 等价类划分（Equivalence Partitioning）
**原理**：将输入数据划分为若干等价类，从每个类中选取一个代表值测试。

#### 示例：披萨订购数量（1-10个有效）
```
有效等价类：1-10（选一个值如 5 测试）
无效等价类：≤0（选 0 测试）、≥11（选 11 测试）
```

| 测试用例 | 输入值 | 等价类 | 预期结果 |
|----------|--------|--------|----------|
| TC1 | 5 | 有效 | 成功 |
| TC2 | 0 | 无效（<1） | 错误 |
| TC3 | 11 | 无效（>10） | 错误 |

#### 等价类类型
- **有效等价类**：合理、有意义的输入
- **无效等价类**：不合理、无意义的输入

### 📏 2. 边界值分析（Boundary Value Analysis）
**原理**：测试等价类边界上的值，因为边界是 Bug 高发区。

#### 示例：密码字段（6-10字符）
```
边界值：6（最小有效）、10（最大有效）
边界外：5（刚好无效）、11（刚好无效）
```

| 测试用例 | 输入长度 | 位置 | 预期结果 |
|----------|----------|------|----------|
| TC1 | 5 | 边界外（无效） | 不接受 |
| TC2 | 6 | 边界（有效最小） | 接受 |
| TC3 | 10 | 边界（有效最大） | 接受 |
| TC4 | 11 | 边界外（无效） | 不接受 |

#### BVA 测试点选择
```
有效区间 [min, max]
测试点：min-1, min, min+1, max-1, max, max+1
```

### 🎬 3. 场景法（Scenario-based Testing）
**原理**：基于业务流程/用户操作路径设计测试。

#### 示例：电商购物流程
```
场景1（正常流程）：
  浏览商品 → 加入购物车 → 填写地址 → 选择支付 → 确认订单
  
场景2（异常流程）：
  浏览商品 → 加入购物车 → 库存不足 → 提示用户
  
场景3（边界流程）：
  浏览商品 → 加入购物车 → 超出限购 → 提示用户
```

### 🛠️ 组合使用策略
```python
# 测试用例设计模板
def test_calculate_discount():
    # 等价类：正常折扣率
    assert calculate_discount(100, 0.1) == 90
    
    # 边界值：折扣率边界
    assert calculate_discount(100, 0) == 100    # 最小折扣
    assert calculate_discount(100, 1.0) == 0    # 最大折扣
    
    # 无效等价类
    with pytest.raises(ValueError):
        calculate_discount(100, -0.1)  # 负数折扣
        
    with pytest.raises(ValueError):
        calculate_discount(100, 1.5)   # 超过100%
```

### 📋 测试用例设计检查清单
- [ ] 正常流程（Happy Path）
- [ ] 边界值（最小/最大）
- [ ] 无效输入（等价类）
- [ ] 异常场景（错误处理）
- [ ] 组合场景（多字段交互）

### 💡 关键记忆点
1. **等价类**：减少测试用例数量，保持覆盖率
2. **边界值**：Bug 高发区，必须覆盖
3. **场景法**：从业务角度设计，模拟真实用户
4. **组合使用**：三种方法结合效果最佳
5. **自动化集成**：设计用例时考虑可自动化性

---

## 6. 缺陷管理 - Bug 生命周期/优先级

### 🎯 缺陷管理目标
系统化管理 Bug，确保每个缺陷都被跟踪、修复、验证，避免遗漏。

### 🔄 Bug 生命周期
```
新建(New) → 确认(Accepted) → 分配(Assigned) → 修复(Fixed) → 验证(Verified) → 关闭(Closed)
                ↓                    ↓
            拒绝(Rejected)      延期(Deferred)
```

#### 详细流程
1. **发现（Discovery）**：测试人员发现并提交缺陷
2. **确认（Accepted）**：开发确认是真实缺陷
3. **分类（Categorization）**：按优先级/严重程度分类
4. **分配（Assignment）**：指派给开发人员
5. **修复（Resolution）**：开发修复代码
6. **验证（Verification）**：测试验证修复
7. **关闭（Closure）**：确认修复后关闭

### 📊 缺陷优先级（Priority）vs 严重程度（Severity）
| 级别 | 优先级（业务影响） | 严重程度（技术影响） |
|------|-------------------|---------------------|
| P0/Critical | 阻断性问题，必须立即修复 | 系统崩溃/数据丢失 |
| P1/High | 主要功能受损 | 核心功能不可用 |
| P2/Medium | 功能异常但有替代方案 | 功能缺陷 |
| P3/Low | 不影响使用体验 | 界面/建议性问题 |

#### 示例分类
```python
# 优先级分类示例
缺陷列表 = [
    {"问题": "登录功能完全无法使用", "优先级": "Critical"},  # 阻断业务
    {"问题": "网站响应速度慢", "优先级": "High"},          # 影响体验
    {"问题": "手机端显示错位", "优先级": "Medium"},        # 部分用户
    {"问题": "某个链接失效", "优先级": "Low"},             # 轻微影响
]
```

### 📝 缺陷报告模板
```markdown
## 缺陷报告

**标题**：[模块] 简洁描述问题
**优先级**：P0/P1/P2/P3
**严重程度**：Critical/High/Medium/Low
**环境**：Chrome 120 / iOS 17 / Android 14
**复现步骤**：
1. 打开页面 X
2. 点击按钮 Y
3. 输入数据 Z

**预期结果**：应该显示 A
**实际结果**：显示 B 或报错
**附件**：截图/录屏/日志
**关联用例**：TC-001
```

### 📈 缺陷关键指标
| 指标 | 公式 | 含义 |
|------|------|------|
| 缺陷密度 | 缺陷数/代码行数 | 代码质量 |
| 缺陷拒绝率(DRR) | 拒绝缺陷/总缺陷 | 测试准确性 |
| 缺陷修复率 | 已修复/总缺陷 | 开发效率 |
| 缺陷重开率 | 重开缺陷/已关闭 | 修复质量 |

### 🔧 常用缺陷管理工具
- **Jira**：最流行，灵活配置
- **飞书项目/多维表格**：国内常用
- **Bugzilla**：开源经典
- **GitHub Issues**：轻量级
- **禅道**：国内开源

### 💡 关键记忆点
1. **生命周期必须完整**：不能只提交不跟踪
2. **优先级影响修复顺序**：P0 > P1 > P2 > P3
3. **缺陷报告要详细**：复现步骤是核心
4. **指标驱动改进**：用数据说话
5. **沟通很重要**：缺陷是团队共同问题

---

## 7. 代码审查 - 代码质量/安全审查

### 🎯 代码审查目标
在代码合并前发现问题，提高代码质量，促进知识共享。

### 🔍 审查维度（Google 工程实践）

#### 1. 设计（Design）
- 整体架构是否合理？
- 是否符合现有代码库的设计？
- 是否过度设计？

#### 2. 功能性（Functionality）
- 代码是否实现了预期功能？
- 边界情况是否处理？
- 并发/竞态条件是否存在？

#### 3. 复杂度（Complexity）
- 代码是否过于复杂？
- 能否被其他开发者快速理解？
- 是否存在过度工程化？

#### 4. 测试（Tests）
- 单元测试是否充分？
- 测试是否能捕获回归？
- 测试代码本身质量如何？

#### 5. 命名（Naming）
- 变量/函数/类名是否清晰？
- 是否遵循命名规范？

#### 6. 注释（Comments）
- 注释是否解释了"为什么"而非"是什么"？
- 是否有不必要的注释？

#### 7. 风格（Style）
- 是否遵循团队编码规范？
- 代码格式是否一致？

### 🔒 安全审查重点
```python
# ❌ 安全漏洞示例
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL注入
    return db.execute(query)

# ✅ 安全写法
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    return db.execute(query, (user_id,))
```

#### 常见安全问题清单
- [ ] SQL 注入
- [ ] XSS（跨站脚本）
- [ ] CSRF（跨站请求伪造）
- [ ] 敏感信息硬编码
- [ ] 不安全的反序列化
- [ ] 路径遍历
- [ ] 权限检查缺失

### 📋 审查检查清单
```markdown
## 代码审查清单

### 设计
- [ ] 逻辑清晰，无明显 bug
- [ ] 错误处理完善
- [ ] 无重复代码

### 性能
- [ ] 无 N+1 查询
- [ ] 无内存泄漏
- [ ] 避免不必要的计算

### 安全
- [ ] 输入验证
- [ ] 权限检查
- [ ] 敏感数据加密

### 可维护性
- [ ] 命名清晰
- [ ] 函数职责单一
- [ ] 有必要的注释
- [ ] 测试覆盖
```

### 💬 审查评论技巧
- **明确**：指出具体问题，不模糊
- **建设性**：给出改进建议
- **分级**：Blocking（必须改）vs Nit（可选）
- **尊重**：对事不对人

### 🛠️ 审查工具
- **GitHub PR Review**：最流行
- **飞书代码审查**：国内团队常用
- **Gerrit**：专业代码审查
- **SonarQube**：自动化质量检查

### 💡 关键记忆点
1. **审查是协作**：不是挑刺，是共同提高
2. **安全优先**：安全隐患必须阻断
3. **自动化辅助**：lint/格式化工具减少人工审查负担
4. **及时响应**：审查不应拖延（Google 建议 <1 天）
5. **学习机会**：审查是团队知识共享的渠道

---

## 8. 持续集成 - Jenkins/GitHub Actions

### 🎯 持续集成（CI）核心理念
- **频繁集成**：开发者每天多次提交代码
- **自动构建**：每次提交触发自动构建和测试
- **快速反馈**：几分钟内知道构建是否成功

### 🔄 CI/CD 流程
```
代码提交 → 自动构建 → 自动测试 → 自动部署 → 监控
    ↓           ↓          ↓          ↓
  Git Push   Compile   Unit Test   Deploy
```

### 🚀 GitHub Actions 快速开始

#### 基础配置文件
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]  # 触发条件

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

#### 常用触发条件
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点
  workflow_dispatch:  # 手动触发
```

#### 矩阵测试（多版本）
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pytest
```

### 🏗️ Jenkins 核心概念

#### Pipeline 脚本（Jenkinsfile）
```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                sh 'pytest --junitxml=results.xml'
            }
            post {
                always {
                    junit 'results.xml'
                }
            }
        }
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

### 📊 CI/CD 最佳实践
| 实践 | 说明 |
|------|------|
| 快速反馈 | 测试 < 10 分钟完成 |
| 自动化 | 无人工干预 |
| 版本控制 | 一切配置在 Git 中 |
| 环境一致 | Docker 容器化 |
| 并行执行 | 提高效率 |
| 失败即停 | 测试失败中断流水线 |

### 🔧 常用 CI/CD 工具
| 工具 | 特点 | 适用场景 |
|------|------|----------|
| **GitHub Actions** | 集成 GitHub，免费额度 | 开源/小团队 |
| **Jenkins** | 灵活插件，自托管 | 大型企业 |
| **GitLab CI** | 一体化平台 | GitLab 用户 |
| **CircleCI** | 云原生，快速 | 中小团队 |
| **Travis CI** | 简单易用 | 开源项目 |

### 🧪 测试集成示例
```yaml
# 完整测试流水线
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: pip install flake8 mypy
      - run: flake8 src/
      - run: mypy src/

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: pip install pytest pytest-cov
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: docker build -t app .
      - run: docker push $IMAGE
```

### 💡 关键记忆点
1. **自动化是核心**：减少人工干预
2. **快速反馈**：尽早发现问题
3. **配置即代码**：所有配置版本化
4. **环境一致性**：用 Docker 避免环境问题
5. **安全第一**：密钥/凭证用 Secrets 管理

---

## 9. 压力测试 - JMeter/Locust/k6

### 🎯 压力测试目标
验证系统在高负载下的性能、稳定性和容量极限。

### 📊 性能测试类型
| 类型 | 目标 | 持续时间 | 并发用户 |
|------|------|----------|----------|
| **负载测试** | 正常负载下性能 | 较长 | 预期值 |
| **压力测试** | 找到系统极限 | 中等 | 逐步增加 |
| **稳定性测试** | 长时间运行稳定性 | 很长 | 70-80%负载 |
| **峰值测试** | 突发流量处理 | 短 | 瞬时高峰 |

### 🐍 Locust（Python，推荐）
```python
# locustfile.py
from locust import HttpUser, between, task

class WebsiteUser(HttpUser):
    wait_time = between(5, 15)  # 用户等待时间

    def on_start(self):
        """用户启动时执行"""
        self.client.post("/login", {
            "username": "test_user",
            "password": "test123"
        })

    @task(3)  # 权重为3，执行频率更高
    def index(self):
        self.client.get("/")
        self.client.get("/static/assets.js")

    @task(1)  # 权重为1
    def about(self):
        self.client.get("/about/")
```

#### Locust 运行命令
```bash
# 基础运行
locust -f locustfile.py --host=https://example.com

# 无界面模式（CI/CD）
locust -f locustfile.py --host=https://example.com \
       --headless -u 100 -r 10 --run-time 1m

# 分布式运行
locust -f locustfile.py --master
locust -f locustfile.py --worker --master-host=192.168.1.1
```

### 📈 关键性能指标
| 指标 | 说明 | 参考值 |
|------|------|--------|
| **响应时间（RT）** | 请求到响应的时间 | < 200ms（API） |
| **吞吐量（TPS/QPS）** | 每秒处理请求数 | 越高越好 |
| **并发用户数** | 同时在线用户 | 根据业务定 |
| **错误率** | 失败请求占比 | < 0.1% |
| **CPU/内存使用** | 服务器资源占用 | < 80% |

### 🔧 JMeter（Java，企业级）
```xml
<!-- 基础测试计划结构 -->
<TestPlan>
  <ThreadGroup>
    <num_threads>100</num_threads>  <!-- 并发用户 -->
    <ramp_time>60</ramp_time>       <!-- 加压时间(秒) -->
    <loop_count>10</loop_count>     <!-- 循环次数 -->
  </ThreadGroup>
  <HTTPSampler>
    <domain>api.example.com</domain>
    <port>443</port>
    <path>/users</path>
    <method>GET</method>
  </HTTPSampler>
</TestPlan>
```

### ⚡ k6（Go，现代化）
```javascript
// script.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // 30秒加到20用户
    { duration: '1m', target: 100 },    // 1分钟加到100用户
    { duration: '30s', target: 0 },     // 30秒降到0
  ],
};

export default function () {
  const res = http.get('https://api.example.com/users');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### 📋 测试执行检查清单
```markdown
### 测试前
- [ ] 确定测试目标（RT/TPS/并发）
- [ ] 准备测试环境（独立环境）
- [ ] 准备测试数据
- [ ] 通知相关团队

### 测试中
- [ ] 监控服务器资源
- [ ] 记录异常和错误
- [ ] 逐步加压观察

### 测试后
- [ ] 分析测试结果
- [ ] 生成性能报告
- [ ] 提出优化建议
- [ ] 回归验证修复
```

### 💡 关键记忆点
1. **Locust 首选**：Python 生态，易于集成
2. **逐步加压**：不要一次性打满，观察拐点
3. **监控同步**：压力测试必须配合服务器监控
4. **独立环境**：不要在生产环境做压力测试
5. **数据驱动**：用真实数据比例模拟

---

## 10. 监控告警 - Prometheus/Grafana

### 🎯 监控目标
实时了解系统状态，快速发现和响应问题，保障系统稳定性。

### 🏗️ Prometheus 架构
```
┌─────────────────────────────────────────────────────────┐
│                      Prometheus Server                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Scrape   │  │ Storage  │  │ Alert    │             │
│  │ (拉取)   │  │ (存储)   │  │ (告警)   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
       ↑                              ↓
┌──────────────┐              ┌──────────────┐
│ Exporters    │              │ Alertmanager │
│ (指标导出)   │              │ (告警管理)   │
└──────────────┘              └──────────────┘
       ↑                              ↓
┌──────────────┐              ┌──────────────┐
│ App/Metrics  │              │ Email/Slack  │
│ (应用指标)   │              │ (通知渠道)   │
└──────────────┘              └──────────────┘
```

### 📊 Prometheus 指标类型
```python
# Counter（计数器）- 只增不减
http_requests_total = Counter('http_requests_total', 'Total HTTP requests')

# Gauge（仪表盘）- 可增可减
current_connections = Gauge('current_connections', 'Current connections')

# Histogram（直方图）- 统计分布
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Summary（摘要）- 分位数统计
request_size = Summary('request_size_bytes', 'Request size')
```

### 🔍 PromQL 查询语言
```promql
# 基础查询
http_requests_total

# 过滤标签
http_requests_total{method="GET", status="200"}

# 聚合函数
sum(rate(http_requests_total[5m])) by (method)

# 计算 QPS
rate(http_requests_total[1m])

# 响应时间 P99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# 错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

### 📈 Grafana 仪表盘
```json
{
  "panels": [
    {
      "title": "请求 QPS",
      "type": "graph",
      "targets": [
        { "expr": "sum(rate(http_requests_total[5m]))" }
      ]
    },
    {
      "title": "响应时间 P99",
      "type": "graph",
      "targets": [
        { "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))" }
      ]
    }
  ]
}
```

### 🚨 告警规则配置
```yaml
# alert-rules.yml
groups:
  - name: service-alerts
    rules:
      # 高错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率告警"
          description: "错误率超过 5%，当前值 {{ $value }}"

      # 高延迟告警
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "高延迟告警"
          description: "P95 响应时间超过 1 秒"

      # 服务不可用
      - alert: ServiceDown
        expr: up{job="api-server"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务宕机"
```

### 📋 告警通知渠道
```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'
  - name: 'critical-alerts'
    webhook_configs:
      - url: 'https://hooks.slack.com/services/xxx'
```

### 🔧 常用 Exporter
| Exporter | 用途 |
|----------|------|
| **node_exporter** | 服务器硬件指标 |
| **blackbox_exporter** | 黑盒探测（HTTP/TCP/DNS） |
| **mysqld_exporter** | MySQL 数据库 |
| **redis_exporter** | Redis 缓存 |
| **cadvisor** | Docker 容器指标 |

### 💡 关键记忆点
1. **Prometheus 拉模型**：主动拉取指标，而非推送
2. **PromQL 灵活**：强大的查询和聚合能力
3. **Grafana 可视化**：美观的仪表盘展示
4. **告警分层**：Warning → Critical 逐步升级
5. **四黄金信号**：延迟、流量、错误、饱和度

---

## 📝 学习总结

### ✅ 已完成学习主题（10/10）

| 轮次 | 主题 | 状态 |
|------|------|------|
| **第一轮** | pytest 基础 | ✅ |
| | pytest 进阶 | ✅ |
| | API 测试 | ✅ |
| | UI 测试 | ✅ |
| **第二轮** | 测试用例设计 | ✅ |
| | 缺陷管理 | ✅ |
| | 代码审查 | ✅ |
| | 持续集成 | ✅ |
| **第三轮** | 压力测试 | ✅ |
| | 监控告警 | ✅ |

### 🎯 核心能力覆盖
- **自动化测试**：pytest + Playwright + Requests
- **质量保障**：用例设计 + 缺陷管理 + 代码审查 + CI/CD
- **性能测试**：Locust/k6 + Prometheus 监控

### 📚 推荐下一步
1. 实战练习：用 pytest + Playwright 写自动化测试
2. 搭建 CI：GitHub Actions 集成测试流水线
3. 性能调优：Locust 压测 + Grafana 仪表盘
4. 安全测试：OWASP Top 10 + 安全扫描工具

---

*学习笔记由本尔 🛡️ 整理，持续更新中...*
