# Git 工作流规范

> **版本**: 1.0  
> **作者**: 年年 🎀  
> **创建时间**: 2026-04-05  
> **适用 Agent**: 所有开发相关 Agent（玄机/霓裳/鉴微/天工）  
> **触发条件**: 自动触发（Git 相关操作）/手动触发（@git-workflow）

---

## 🎯 适用范围

本规范适用于 OpenClaw 项目的所有 Git 操作，包括：
- 分支管理
- 代码提交
- 合并请求
- 版本发布

---

## 📁 分支规范

### 分支类型

| 类型 | 命名 | 说明 | 生命周期 |
|------|------|------|----------|
| **主分支** | `main` | 生产环境代码 | 永久 |
| **开发分支** | `develop` | 日常开发分支 | 永久 |
| **功能分支** | `feature/xxx` | 功能开发 | 功能完成后删除 |
| **修复分支** | `bugfix/xxx` | Bug 修复 | 修复后删除 |
| **紧急修复** | `hotfix/xxx` | 生产紧急修复 | 修复后删除 |
| **发布分支** | `release/v1.0` | 发布准备 | 发布后删除 |

### 分支命名

```bash
# ✅ 正确：清晰的命名
feature/user-login          # 用户登录功能
feature/add-payment-module  # 添加支付模块
bugfix/fix-login-error      # 修复登录错误
hotfix/fix-production-bug   # 生产紧急修复
release/v1.2.0              # v1.2.0 版本发布

# ❌ 错误：不清晰的命名
feature-1                   # 什么功能？
fix-bug                     # 什么 bug？
test                        # 测试分支？
my-branch                   # 我的分支？
```

### 分支保护

#### main 分支
- ❌ 禁止直接推送
- ✅ 必须 PR 审查
- ✅ 至少 1 人批准
- ✅ CI/CD 必须通过
- ✅ 测试覆盖率达标

#### develop 分支
- ❌ 禁止直接推送
- ✅ 需要 PR 审查
- ✅ 至少 1 人批准
- ✅ CI/CD 必须通过

### 分支生命周期

```
feature/xxx 创建
    ↓
开发中...
    ↓
提交 PR/MR
    ↓
审查通过
    ↓
合并到 develop
    ↓
删除 feature/xxx 分支
    ↓
定期发布到 main
```

---

## 📝 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(user): 添加用户登录 |
| `fix` | 修复 bug | fix(order): 修复订单金额计算 |
| `docs` | 文档更新 | docs(readme): 更新安装说明 |
| `style` | 代码格式 | style(format): 格式化代码 |
| `refactor` | 重构 | refactor(auth): 重构认证模块 |
| `test` | 测试 | test(user): 添加用户测试 |
| `chore` | 构建/工具 | chore(deps): 更新依赖 |
| `perf` | 性能优化 | perf(query): 优化查询性能 |
| `ci` | CI/CD | ci(github): 添加 GitHub Actions |

### Scope 范围

| Scope | 说明 |
|-------|------|
| `user` | 用户模块 |
| `order` | 订单模块 |
| `product` | 产品模块 |
| `auth` | 认证模块 |
| `common` | 公共模块 |
| `api` | API 模块 |
| `ui` | 前端 UI |
| `config` | 配置文件 |

### Subject 主题

**规则**:
- ✅ 使用现在时态（add 不是 added）
- ✅ 首字母不大写
- ✅ 结尾不加句号
- ✅ 长度不超过 50 字符

```bash
# ✅ 正确
feat(user): add user login feature
fix(order): fix order amount calculation

# ❌ 错误
feat(user): Added user login feature  # 过去时
feat(User): Add user login feature  # 首字母大写
feat(user): add user login feature.  # 结尾句号
feat(user): this is a very very very long subject that exceeds 50 characters  # 太长
```

### Body 正文（可选）

**内容**:
- 详细说明变更内容
- 解释为什么这样改
- 说明影响范围

```bash
feat(user): add user login feature

- 实现用户名密码登录
- 实现手机号登录
- 添加登录日志
- 添加登录失败限流

影响范围:
- 新增 user/login 接口
- 修改 user 表结构
- 新增 login_log 表
```

### Footer 页脚（可选）

**关联 Issue**:
```bash
Closes #123
Fixes #456
Refs #789
```

**破坏性变更**:
```bash
BREAKING CHANGE: 修改登录接口参数
- 旧参数：username, password
- 新参数：login_type, credentials
```

### 完整示例

```bash
feat(user): add user login feature

- 实现用户名密码登录
- 实现手机号登录
- 添加登录日志
- 添加登录失败限流

影响范围:
- 新增 user/login 接口
- 修改 user 表结构
- 新增 login_log 表

Closes #123
```

---

## 🔄 合并规范

### PR/MR 要求

**必须满足**:
- [ ] 至少 1 人审查
- [ ] CI/CD 通过
- [ ] 无冲突
- [ ] 测试覆盖达标（>80%）
- [ ] 文档已更新

**审查清单**:
- [ ] 代码质量检查
- [ ] 安全性检查
- [ ] 性能检查
- [ ] 测试检查

### 合并策略

| 策略 | 适用场景 | 说明 |
|------|----------|------|
| `Squash and merge` | 小功能 | 多个提交压缩为一个 |
| `Merge commit` | 大功能 | 保留完整历史 |
| `Rebase and merge` | 保持清晰 | 变基后合并 |

#### Squash and merge

**适用场景**:
- 功能分支有多个小提交
- 提交历史不清晰
- 想保持主分支历史简洁

```bash
# 合并前（功能分支）
commit 1: feat: add login
commit 2: fix: fix login bug
commit 3: style: fix format

# 合并后（主分支）
commit 1: feat: add user login feature（压缩为一个提交）
```

#### Merge commit

**适用场景**:
- 大功能开发
- 想保留完整历史
- 多人协作的功能

```bash
# 合并前
main:    A --- B
              \
feature:       C --- D --- E

# 合并后
main:    A --- B --- F
              \       \
feature:       C --- D --- E

F 是合并提交，保留了完整历史
```

#### Rebase and merge

**适用场景**:
- 保持线性历史
- 功能分支基于旧版本
- 想保持历史清晰

```bash
# 合并前
main:    A --- B --- C
              \
feature:       D --- E

# Rebase 后
main:    A --- B --- C
                      \
feature:               D' --- E'

# 合并后
main:    A --- B --- C --- D' --- E'
```

### 合并后

**必须完成**:
- [ ] 删除功能分支
- [ ] 验证生产环境
- [ ] 通知相关人员

```bash
# 删除本地分支
git branch -d feature/user-login

# 删除远程分支
git push origin --delete feature/user-login
```

---

## 🛠️ 常用操作

### 创建分支

```bash
# 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-login

# 从 main 创建紧急修复分支
git checkout main
git pull origin main
git checkout -b hotfix/fix-production-bug
```

### 提交代码

```bash
# 查看变更
git status
git diff

# 添加文件
git add src/user_service.py
git add .  # 添加所有变更

# 提交
git commit -m "feat(user): add user login feature"

# 推送到远程
git push origin feature/user-login
```

### 同步主干

```bash
# 同步 develop 到功能分支
git checkout feature/user-login
git fetch origin develop
git rebase origin/develop

# 或者合并
git merge origin/develop
```

### 解决冲突

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 查看冲突文件
git status

# 3. 手动解决冲突文件
# 编辑冲突文件，解决 <<<<<<< 和 >>>>>>> 之间的冲突

# 4. 标记解决
git add src/conflicted_file.py

# 5. 完成合并
git commit -m "resolve merge conflict"

# 或者取消合并
git merge --abort
```

### 撤销提交

```bash
# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD~1

# 撤销已推送的提交（使用 revert）
git revert <commit-hash>
git push origin main

# 强制推送（谨慎使用）
git push origin main --force
```

### 查看历史

```bash
# 查看提交历史
git log
git log --oneline  # 简洁模式
git log --graph    # 图形模式

# 查看某人提交
git log --author="年年"

# 查看某文件历史
git log src/user_service.py

# 查看变更
git show <commit-hash>
```

---

## 🎯 最佳实践

### 1. 小步提交

```bash
# ✅ 正确：小提交
git commit -m "feat: add user model"
git commit -m "feat: add user login"
git commit -m "test: add user tests"

# ❌ 错误：大提交
git commit -m "add everything"  # 一次提交所有内容
```

### 2. 清晰的提交信息

```bash
# ✅ 正确：清晰描述
git commit -m "feat(user): add user login feature"

# ❌ 错误：模糊描述
git commit -m "update"
git commit -m "fix bug"
git commit -m "wip"
```

### 3. 及时同步主干

```bash
# ✅ 正确：每天同步
git checkout feature/user-login
git rebase origin/develop

# ❌ 错误：长时间不同步
# 开发一周后才同步，导致大量冲突
```

### 4. 删除已合并分支

```bash
# ✅ 正确：合并后删除
git push origin --delete feature/user-login

# ❌ 错误：不删除
# 分支越积越多，难以管理
```

---

## 📊 常见问题

### Q: 如何处理紧急修复？

**A**:

```bash
# 1. 从 main 创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/fix-production-bug

# 2. 修复 bug
# ... 修复代码

# 3. 提交
git commit -m "fix: fix production login bug"

# 4. 创建紧急 PR
# 标记为紧急，快速审查

# 5. 合并到 main 和 develop
git checkout main
git merge hotfix/fix-production-bug
git push origin main

git checkout develop
git merge hotfix/fix-production-bug
git push origin develop

# 6. 删除 hotfix 分支
git branch -d hotfix/fix-production-bug
git push origin --delete hotfix/fix-production-bug
```

---

### Q: 如何处理大功能开发？

**A**:

```bash
# 1. 从 develop 创建功能分支
git checkout -b feature/big-feature

# 2. 开发中定期提交
git commit -m "feat: add module A"
git commit -m "feat: add module B"

# 3. 定期同步 develop
git rebase origin/develop

# 4. 功能完成后创建 PR
# 如果太大，考虑拆分成多个小 PR

# 5. 审查通过后合并
```

---

### Q: 如何处理冲突？

**A**:

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 查看冲突文件
git status

# 3. 手动解决冲突
# 编辑冲突文件，解决 <<<<<<< 和 >>>>>>> 之间的冲突

# 冲突标记
<<<<<<< HEAD
// 当前分支的代码
=======
// 要合并的代码
>>>>>>> main

# 4. 标记解决
git add src/conflicted_file.py

# 5. 完成合并
git commit -m "resolve merge conflict"
```

---

## 📚 参考资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**🎀 创建者**: 年年  
**📅 创建时间**: 2026-04-05  
**📁 存放位置**: 🎀 年年 - 大总管 目录 → Skills  
**🔄 版本**: v1.0