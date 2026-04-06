# 安全检查清单

> **版本**: 1.0  
> **作者**: 年年 🎀  
> **创建时间**: 2026-04-05  
> **适用 Agent**: 执明（安全审查官）/鉴微（测试工程师）  
> **触发条件**: 自动触发（检测到代码提交）/手动触发（@security-check）

---

## 🎯 审查目标

通过安全检查，确保：
1. **无 SQL 注入风险** - 所有数据库查询使用参数化
2. **无 XSS 风险** - 所有用户输入过滤/输出转义
3. **无 CSRF 风险** - 所有表单使用 Token
4. **敏感信息安全** - 密码/密钥加密存储
5. **权限校验完整** - 所有接口权限校验

---

## 📋 安全检查清单

### 1. SQL 注入（权重 25%）

#### 检查项
- [ ] 所有 SQL 查询使用参数化/ORM
- [ ] 无字符串拼接 SQL
- [ ] 输入验证和过滤
- [ ] 最小权限原则（数据库用户权限）

#### 安全检查

```python
# ✅ 正确：参数化查询
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
cursor.execute("SELECT * FROM users WHERE name = %s", (user_name,))

# ✅ 正确：ORM 查询
User.objects.filter(id=user_id)
User.objects.filter(name=user_name)

# ❌ 错误：SQL 拼接
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL 注入
cursor.execute("SELECT * FROM users WHERE id = " + user_id)  # SQL 注入
cursor.execute("SELECT * FROM users WHERE name = '" + user_name + "'")  # SQL 注入
```

#### 修复建议

```python
# 修复前（SQL 拼接）
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()

# 修复后（参数化查询）
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()
```

---

### 2. XSS 攻击（权重 20%）

#### 检查项
- [ ] 所有用户输入过滤
- [ ] 所有输出转义
- [ ] 使用安全的模板引擎
- [ ] Content-Security-Policy 头

#### 安全检查

```python
# ✅ 正确：输出转义
from html import escape

def render_user_name(user_name):
    safe_name = escape(user_name)
    return f"<div>{safe_name}</div>"

# ✅ 正确：使用安全模板
from jinja2 import Template

template = Template("Hello {{ name }}")  # Jinja2 自动转义
return template.render(name=user_name)

# ❌ 错误：直接输出
def render_user_name(user_name):
    return f"<div>{user_name}</div>"  # XSS 风险

# ❌ 错误：使用 mark_safe（Django）
from django.utils.safestring import mark_safe
return mark_safe(user_input)  # XSS 风险
```

#### 修复建议

```python
# 修复前（直接输出）
def render_comment(comment):
    return f"<div class='comment'>{comment}</div>"

# 修复后（转义输出）
from html import escape

def render_comment(comment):
    safe_comment = escape(comment)
    return f"<div class='comment'>{safe_comment}</div>"
```

---

### 3. CSRF 攻击（权重 15%）

#### 检查项
- [ ] 所有表单使用 CSRF Token
- [ ] AJAX 请求包含 Token
- [ ] 验证 Token 有效性
- [ ] SameSite Cookie 属性

#### 安全检查

```python
# ✅ 正确：CSRF Token
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">提交</button>
</form>

# ✅ 正确：AJAX 请求包含 Token
fetch('/api/update', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrf_token
    },
    body: JSON.stringify(data)
})

# ❌ 错误：无 CSRF Token
<form method="post">
    <button type="submit">提交</button>
</form>
```

#### 修复建议

```python
# 修复前（无 CSRF Token）
@app.route('/update', methods=['POST'])
def update():
    data = request.form['data']
    # 处理数据
    return 'OK'

# 修复后（添加 CSRF Token）
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/update', methods=['POST'])
def update():
    # CSRF Token 自动验证
    data = request.form['data']
    # 处理数据
    return 'OK'
```

---

### 4. 敏感信息（权重 20%）

#### 检查项
- [ ] 密码加密存储（bcrypt/argon2）
- [ ] 密钥使用环境变量
- [ ] 无硬编码密钥
- [ ] 敏感数据加密传输（HTTPS）
- [ ] 日志中无敏感信息

#### 安全检查

```python
# ✅ 正确：密码加密
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# ✅ 正确：使用环境变量
import os
api_key = os.getenv("API_KEY")
database_url = os.getenv("DATABASE_URL")

# ✅ 正确：HTTPS 传输
requests.post("https://api.example.com/data", json=data)

# ❌ 错误：明文密码
def store_password(password):
    # 直接存储明文密码
    cursor.execute("INSERT INTO users (password) VALUES (%s)", (password,))

# ❌ 错误：硬编码密钥
api_key = "sk-1234567890abcdef"  # 密钥泄露
database_password = "password123"  # 密码泄露

# ❌ 错误：日志记录敏感信息
logger.info(f"用户登录：{username}, 密码：{password}")  # 密码记录到日志
```

#### 修复建议

```python
# 修复前（明文密码）
def register_user(username, password):
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, password)  # 明文存储
    )

# 修复后（加密密码）
import bcrypt

def register_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed)  # 加密存储
    )
```

---

### 5. 权限校验（权重 20%）

#### 检查项
- [ ] 所有接口登录校验
- [ ] 所有操作权限校验
- [ ] 无越权风险（水平/垂直越权）
- [ ] 敏感操作二次验证

#### 安全检查

```python
# ✅ 正确：登录校验
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "需要登录"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/user/profile')
@login_required
def get_profile():
    return jsonify(current_user.profile)

# ✅ 正确：权限校验
def delete_user(current_user, target_user_id):
    if not current_user.is_admin:
        raise PermissionError("需要管理员权限")
    if current_user.id != target_user_id and not current_user.is_admin:
        raise PermissionError("不能删除其他用户")
    # 执行删除

# ✅ 正确：防止越权
def get_user_data(current_user, user_id):
    if current_user.id != user_id and not current_user.is_admin:
        raise PermissionError("不能访问其他用户数据")
    return get_data(user_id)

# ❌ 错误：无登录校验
@app.route('/api/user/profile')
def get_profile():
    # 任何人都可以访问
    return jsonify(user_profile)

# ❌ 错误：无权限校验
def delete_user(target_user_id):
    # 任何人都可以删除任何用户
    cursor.execute("DELETE FROM users WHERE id = %s", (target_user_id,))

# ❌ 错误：越权风险
def get_user_data(user_id):
    # 可以访问任何用户数据
    return get_data(user_id)
```

#### 修复建议

```python
# 修复前（无权限校验）
@app.route('/api/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return 'OK'

# 修复后（添加权限校验）
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return 'OK'
```

---

## 🔧 安全工具

### 静态分析工具

```bash
# Python 安全扫描
bandit -r src/
safety check
pip-audit

# JavaScript 安全扫描
npm audit
yarn audit
snyk test

# 依赖检查
pip list --outdated
npm outdated
```

### 动态分析工具

```bash
# OWASP ZAP 扫描
zap-cli quick-scan http://localhost:8080

# SQLMap 测试（仅授权环境）
sqlmap -u "http://localhost:8080/api/user?id=1"

# Burp Suite 手动测试
```

### CI/CD 集成

```yaml
# GitHub Actions 安全扫描
name: Security Scan

on: [pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Bandit Scan
        run: bandit -r src/
      
      - name: Safety Check
        run: safety check
      
      - name: NPM Audit
        run: npm audit
```

---

## 📊 风险等级

| 等级 | 说明 | 处理 |
|------|------|------|
| **严重** | SQL 注入/认证绕过 | 立即修复，禁止上线 |
| **高危** | XSS/CSRF/权限问题 | 必须修复，否则不批准 |
| **中危** | 敏感信息泄露 | 建议修复，可讨论 |
| **低危** | 最佳实践 | 可选修复 |

---

## 🎯 常见问题

### Q: 如何防止 SQL 注入？

**A**:
1. **使用参数化查询** - 永远不要拼接 SQL
2. **使用 ORM** - SQLAlchemy/Django ORM
3. **输入验证** - 验证类型/长度/格式
4. **最小权限** - 数据库用户最小权限

```python
# 最佳实践
from sqlalchemy import text

# 参数化查询
cursor.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})

# ORM 查询
User.objects.filter(id=user_id)
```

---

### Q: 如何防止 XSS 攻击？

**A**:
1. **输出转义** - 所有用户输入转义
2. **使用安全模板** - Jinja2/React（自动转义）
3. **Content-Security-Policy** - 限制资源加载
4. **HTTPOnly Cookie** - 防止 JS 读取 Cookie

```python
# 最佳实践
from html import escape
from jinja2 import Template

# 转义输出
safe_output = escape(user_input)

# 安全模板
template = Template("Hello {{ name }}")  # 自动转义
```

---

### Q: 如何防止越权？

**A**:
1. **登录校验** - 所有接口登录验证
2. **权限校验** - 操作前权限验证
3. **资源归属** - 验证资源归属
4. **最小权限** - 用户最小权限原则

```python
# 最佳实践
def get_user_data(current_user, user_id):
    # 登录校验
    if not current_user.is_authenticated:
        raise AuthenticationError("需要登录")
    
    # 权限校验
    if current_user.id != user_id and not current_user.is_admin:
        raise PermissionError("不能访问其他用户数据")
    
    # 资源归属验证
    data = get_data(user_id)
    if data.owner_id != current_user.id and not current_user.is_admin:
        raise PermissionError("不能访问其他用户数据")
    
    return data
```

---

## 📚 参考资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Security Code Review](https://owasp.org/www-project-security-code-review/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Python 安全最佳实践](https://docs.python.org/3/library/security.html)

---

**🎀 创建者**: 年年  
**📅 创建时间**: 2026-04-05  
**📁 存放位置**: 🎀 年年 - 大总管 目录 → Skills  
**🔄 版本**: v1.0