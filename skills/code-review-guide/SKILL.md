# 代码审查指南

> **版本**: 1.0  
> **作者**: 年年 🎀  
> **创建时间**: 2026-04-05  
> **适用 Agent**: 鉴微（测试工程师）/玄机（开发工程师）/霓裳（前端开发）  
> **触发条件**: 自动触发（检测到 PR/MR）/手动触发（@code-review）

---

## 🎯 审查目标

通过代码审查，确保：
1. **代码质量** - 符合编码规范，无低级错误
2. **安全性** - 无安全漏洞，权限校验完整
3. **性能** - 无性能问题，资源使用合理
4. **可维护性** - 代码清晰，易于理解和维护

---

## 📋 审查清单

### 1. 代码质量（权重 30%）

#### 命名规范
- [ ] 类名使用大驼峰（UserService）
- [ ] 函数/变量使用小驼峰/蛇形（get_user_by_id）
- [ ] 常量使用全大写（MAX_RETRY_COUNT）
- [ ] 命名描述性，避免无意义名称

```python
# ✅ 正确
class UserService:
    def get_user_by_id(self, user_id: int) -> User:
        pass

# ❌ 错误
class user_service:
    def get(self, id):  # 太简短
        pass
```

#### 代码简洁
- [ ] 无冗余代码（未使用的变量/导入）
- [ ] 无重复代码（DRY 原则）
- [ ] 方法长度合理（<50 行）
- [ ] 函数单一职责（SRP 原则）

```python
# ✅ 正确：职责单一
class UserService:
    def get_user(self, user_id):
        pass
    
    def create_user(self, user_data):
        pass

# ❌ 错误：职责过多
class UserService:
    def process_user(self, user_id, user_data, action):
        # 既有获取，又有创建，还有删除
        if action == "get":
            pass
        elif action == "create":
            pass
        elif action == "delete":
            pass
```

#### 代码格式
- [ ] 缩进一致（Python 4 空格，JS 2 空格）
- [ ] 行宽不超过 120 字符
- [ ] 适当的空行分隔
- [ ] 无尾随空格

---

### 2. 安全性（权重 30%）

#### SQL 注入
- [ ] 使用参数化查询/ORM
- [ ] 不拼接 SQL 字符串
- [ ] 输入验证和过滤

```python
# ✅ 正确：参数化查询
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ 错误：SQL 拼接
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL 注入风险
```

#### XSS 攻击
- [ ] 用户输入过滤
- [ ] 输出转义
- [ ] 使用安全的模板引擎

```python
# ✅ 正确：输出转义
from html import escape
user_input = escape(request.args.get('name'))

# ❌ 错误：直接输出
user_input = request.args.get('name')  # XSS 风险
```

#### 敏感信息
- [ ] 密码/密钥不硬编码
- [ ] 使用环境变量/配置文件
- [ ] 敏感数据加密存储

```python
# ✅ 正确：使用环境变量
import os
api_key = os.getenv("API_KEY")

# ❌ 错误：硬编码
api_key = "sk-1234567890abcdef"  # 密钥泄露
```

#### 权限校验
- [ ] 登录校验完整
- [ ] 权限验证完整
- [ ] 无越权风险（水平/垂直越权）

```python
# ✅ 正确：权限校验
def delete_user(current_user, target_user_id):
    if not current_user.is_admin:
        raise PermissionError("需要管理员权限")
    if current_user.id != target_user_id and not current_user.is_admin:
        raise PermissionError("不能删除其他用户")

# ❌ 错误：无权限校验
def delete_user(target_user_id):
    # 任何人都可以删除任何用户
    pass
```

---

### 3. 性能（权重 20%）

#### 数据库查询
- [ ] 无 N+1 查询问题
- [ ] 使用索引优化查询
- [ ] 避免全表扫描
- [ ] 合理使用缓存

```python
# ✅ 正确：批量查询
user_ids = [1, 2, 3]
users = User.objects.filter(id__in=user_ids)

# ❌ 错误：N+1 查询
for user_id in [1, 2, 3]:
    user = User.objects.get(id=user_id)  # 每次都查询数据库
```

#### 资源管理
- [ ] 数据库连接及时关闭
- [ ] 文件流及时关闭
- [ ] 使用连接池
- [ ] 无内存泄漏风险

```python
# ✅ 正确：上下文管理器
with open('file.txt', 'r') as f:
    content = f.read()

# ❌ 错误：忘记关闭
f = open('file.txt', 'r')
content = f.read()
# 忘记 f.close()
```

#### 循环优化
- [ ] 避免大循环内的重操作
- [ ] 使用列表推导式/生成器
- [ ] 避免不必要的复制

```python
# ✅ 正确：列表推导式
squares = [x**2 for x in range(1000)]

# ❌ 错误：低效循环
squares = []
for x in range(1000):
    squares.append(x**2)
```

---

### 4. 测试（权重 20%）

#### 单元测试
- [ ] 核心逻辑有单元测试
- [ ] 测试覆盖率达标（>80%）
- [ ] 测试独立（不依赖外部服务）
- [ ] 测试可重复执行

```python
# ✅ 正确：完整的单元测试
def test_get_user_by_id():
    # Arrange
    user_id = 1
    expected_name = "张三"
    
    # Act
    user = user_service.get_user_by_id(user_id)
    
    # Assert
    assert user is not None
    assert user.name == expected_name

# ❌ 错误：测试不完整
def test_get_user():
    user = user_service.get_user(1)
    # 没有断言
```

#### 边界测试
- [ ] 空值测试
- [ ] 极值测试（最大/最小）
- [ ] 异常测试
- [ ] 并发测试（如适用）

```python
# ✅ 正确：边界测试
def test_get_user_with_invalid_id():
    # 空 ID
    with pytest.raises(ValueError):
        user_service.get_user_by_id(None)
    
    # 负数 ID
    with pytest.raises(ValueError):
        user_service.get_user_by_id(-1)
    
    # 超大 ID
    with pytest.raises(ValueError):
        user_service.get_user_by_id(999999999)
```

---

## 📊 审查流程

### 阶段 1: 自动检查（CI/CD）

```yaml
# GitHub Actions 示例
name: Code Review CI

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Lint Check
        run: flake8 .
      
      - name: Test
        run: pytest --cov=src --cov-report=xml
      
      - name: Security Scan
        run: bandit -r src/
      
      - name: Coverage Check
        run: |
          coverage report --fail-under=80
```

**检查项**:
- [ ] 代码编译通过
- [ ] 单元测试通过
- [ ] 代码规范检查通过
- [ ] 安全扫描通过
- [ ] 测试覆盖率达标

---

### 阶段 2: 同事审查

**审查者**: 至少 1 名同事

**审查内容**:
- [ ] 代码质量检查
- [ ] 安全性检查
- [ ] 性能检查
- [ ] 测试检查
- [ ] 填写审查意见

**审查意见模板**:

```markdown
## 审查结果

### ✅ 优点
1. 代码质量高
2. 测试覆盖完整
3. 文档齐全

### ⚠️ 建议
1. xxx 函数可以优化性能
2. 建议添加边界测试

### ❌ 需要修改
1. [严重] xxx 安全问题（SQL 注入风险）
2. [重要] xxx 性能问题（N+1 查询）
```

---

### 阶段 3: 技术负责人审查

**审查者**: 技术负责人/架构师

**审查内容**:
- [ ] 架构合理性
- [ ] 技术选型合理性
- [ ] 风险评估
- [ ] 最终批准

---

### 阶段 4: 合并

**合并前检查**:
- [ ] 所有审查意见已解决
- [ ] 所有冲突已解决
- [ ] CI/CD 全部通过
- [ ] 至少 1 人批准

**合并策略**:
- **小功能**: Squash and merge（压缩提交）
- **大功能**: Merge commit（保留历史）
- **保持清晰**: Rebase and merge（变基合并）

**合并后**:
- [ ] 删除功能分支
- [ ] 验证生产环境
- [ ] 通知相关人员

---

## 📝 审查意见规范

### 严重级别

| 级别 | 说明 | 处理 |
|------|------|------|
| **严重** | 安全漏洞/严重 Bug | 必须修复，否则不批准 |
| **重要** | 性能问题/设计问题 | 建议修复，可讨论 |
| **建议** | 代码优化/最佳实践 | 可选修复 |

### 意见格式

```markdown
[严重] SQL 注入风险
- 位置：src/user_service.py:45
- 问题：使用字符串拼接 SQL
- 建议：使用参数化查询
- 参考：https://owasp.org/www-community/attacks/SQL_Injection
```

### 回复格式

```markdown
已修复

修改内容：
1. 使用参数化查询替代字符串拼接
2. 添加输入验证

测试：
- 已添加 SQL 注入测试用例
- 已验证修复有效
```

---

## 🎯 常见问题

### Q: 如何处理大 PR？

**A**: 
1. **拆分 PR** - 按功能模块拆分成多个小 PR
2. **每个 PR 只做一件事** - 保持 PR 聚焦
3. **按提交历史拆分** - 如果提交清晰，可以按提交拆分
4. **先合并主干** - 先合并公共部分，再合并功能部分

**大 PR 的特征**:
- 变更文件 > 10 个
- 变更行数 > 500 行
- 涉及多个功能模块

---

### Q: 如何处理争议？

**A**:
1. **参考编码规范** - 以规范为准
2. **组织团队讨论** - 集体决策
3. **技术负责人决策** - 负责人最终决定
4. **记录到规范文档** - 避免下次争议

**常见争议**:
- 命名风格（驼峰 vs 蛇形）
- 架构设计（分层 vs 微服务）
- 技术选型（框架 A vs 框架 B）

---

### Q: 如何平衡质量和速度？

**A**:
1. **核心代码严格审查** - 核心业务/安全相关代码严格审查
2. **非核心代码适当放宽** - 工具脚本/临时代码可以放宽
3. **紧急修复先合并后审查** - 生产紧急修复可以先合并，事后补审查
4. **建立分级审查机制** - 根据风险等级分级审查

**分级审查**:
- **P0（高风险）**: 核心业务/安全相关 - 严格审查
- **P1（中风险）**: 普通业务代码 - 标准审查
- **P2（低风险）**: 工具脚本/文档 - 简化审查

---

### Q: 如何保证审查效率？

**A**:
1. **小步快跑** - 小 PR 快速审查
2. **自动化检查** - CI/CD 自动检查
3. **审查时限** - 设定审查时限（如 24 小时内）
4. **审查轮值** - 团队成员轮流审查

**审查时限**:
- **P0 PR**: 4 小时内响应
- **P1 PR**: 24 小时内响应
- **P2 PR**: 48 小时内响应

---

## 📚 参考资源

- [GitHub Code Review Guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests)
- [Google Code Review Guide](https://google.github.io/eng-practices/review/)
- [Phabricator Code Review](https://secure.phabricator.com/book/phabricator/article/code_review/)
- [OWASP Security Code Review](https://owasp.org/www-project-security-code-review/)

---

**🎀 创建者**: 年年  
**📅 创建时间**: 2026-04-05  
**📁 存放位置**: 🎀 年年 - 大总管 目录 → Skills  
**🔄 版本**: v1.0