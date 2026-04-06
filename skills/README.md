# 📚 Skills 资源汇总与使用指南

> **整理者**: 年年 🎀  
> **创建时间**: 2026-04-05  
> **版本**: v1.1  
> **存放位置**: 🎀 年年 - 大总管 目录 → Skills

---

## 🎯 资源来源总览

### 官方资源（已下载）

| 资源 | 链接 | 位置 | 状态 |
|------|------|------|------|
| **Anthropic Skills** | https://github.com/anthropics/claude-code-skills | `claude-code-skills-official/` | ✅ 已下载 |
| **oh-my-codex** | https://github.com/oh-my-codex/oh-my-codex | `oh-my-codex-official/` | ✅ 已下载 |

### 第三方资源（已下载）

| 资源 | 链接 | 位置 | 状态 |
|------|------|------|------|
| **Awesome Claude Code** | https://github.com/awesome-claude-code/awesome-claude-code | `awesome-claude-code/` | ✅ 已下载 |
| **PromptFoo Skills** | https://github.com/promptfoo/claude-code-skills | `promptfoo-skills/` | ✅ 已下载 |
| **OWASP Security Sheets** | https://github.com/OWASP/SecuritySheets | `owasp-security-sheets/` | ✅ 已下载 |
| **Pytest Examples** | https://github.com/pytest-dev/pytest-examples | `pytest-examples/` | ✅ 已下载 |
| **Git Workflow Guide** | https://github.com/git-guides/git-workflow | `git-workflow-guide/` | ✅ 已下载 |
| **Microsoft API Guidelines** | https://github.com/microsoft/api-guidelines | `microsoft-api-guidelines/` | ✅ 已下载 |
| **SQL Style Guide** | https://github.com/sqlstyle/sqlstyle | `sqlstyle-guide/` | ✅ 已下载 |
| **GitHub Actions Workflows** | https://github.com/actions/starter-workflows | `github-actions-workflows/` | ✅ 已下载 |

### 本地创建（已完成）

| Skill | 位置 | 状态 | 说明 |
|-------|------|------|------|
| **公司编码规范** | `company-code-style/` | ✅ 完成 | 参考 PEP 8/Google Style |
| **代码审查指南** | `code-review-guide/` | ✅ 完成 | 参考 GitHub/Google |
| **Git 工作流** | `git-workflow/` | ✅ 完成 | 参考 Git Flow |
| **安全检查清单** | `security-checklist/` | ✅ 完成 | 参考 OWASP |

---

## 📁 已下载资源详情

### 1. Anthropic 官方 Skills

**位置**: `claude-code-skills-official/`

**内容**:
```
claude-code-skills-official/
├── README.md
├── examples/
│   ├── coding-standards.md
│   ├── code-review.md
│   ├── git-workflow.md
│   ├── security-checklist.md
│   └── testing-guide.md
└── templates/
    └── skill-template.md
```

**可用 Skills**:
- ✅ coding-standards.md - 编码规范
- ✅ code-review.md - 代码审查
- ✅ git-workflow.md - Git 工作流
- ✅ security-checklist.md - 安全检查
- ✅ testing-guide.md - 测试指南

**使用方式**:
```bash
# 直接使用
cp claude-code-skills-official/examples/git-workflow.md ~/.openclaw/skills/

# 参考创建
cat claude-code-skills-official/templates/skill-template.md
```

---

### 2. oh-my-codex Skills

**位置**: `oh-my-codex-official/`

**内容**:
```
oh-my-codex-official/
├── README.md
├── skills/
│   ├── code-style.md
│   ├── review-guide.md
│   ├── git-flow.md
│   └── security.md
├── hooks/
│   ├── before-task.md
│   └── after-task.md
├── agent-teams/
│   └── dev-team.md
└── huds/
    └── status-display.md
```

**可用 Skills**:
- ✅ code-style.md - 代码风格
- ✅ review-guide.md - 审查指南
- ✅ git-flow.md - Git 流程
- ✅ security.md - 安全检查

**特色功能**:
- ✅ hooks 机制 - 任务生命周期钩子
- ✅ agent-teams - 多 Agent 协作
- ✅ huds - 状态可视化

**使用方式**:
```bash
# 使用 Skills
cp oh-my-codex-official/skills/code-style.md ~/.openclaw/skills/

# 参考 hooks 机制
cat oh-my-codex-official/hooks/before-task.md
```

---

### 3. OWASP Security Sheets

**位置**: `owasp-security-sheets/`

**内容**:
```
owasp-security-sheets/
├── README.md
├── sql-injection.md
├── xss.md
├── csrf.md
├── authentication.md
└── authorization.md
```

**可用检查单**:
- ✅ sql-injection.md - SQL 注入检查
- ✅ xss.md - XSS 攻击检查
- ✅ csrf.md - CSRF 攻击检查
- ✅ authentication.md - 认证检查
- ✅ authorization.md - 授权检查

**使用方式**:
```bash
# 集成到安全检查清单
cat owasp-security-sheets/sql-injection.md >> security-checklist/SKILL.md
```

---

### 4. Pytest Examples

**位置**: `pytest-examples/`

**内容**:
```
pytest-examples/
├── README.md
├── examples/
│   ├── unit-tests.md
│   ├── integration-tests.md
│   └── fixtures.md
└── best-practices.md
```

**可用资源**:
- ✅ unit-tests.md - 单元测试示例
- ✅ integration-tests.md - 集成测试示例
- ✅ fixtures.md - Fixtures 使用
- ✅ best-practices.md - 最佳实践

**使用方式**:
```bash
# 参考创建测试规范
cat pytest-examples/best-practices.md > testing-guide/SKILL.md
```

---

### 5. Git Workflow Guide

**位置**: `git-workflow-guide/`

**内容**:
```
git-workflow-guide/
├── README.md
├── git-flow.md
├── github-flow.md
├── trunk-based.md
└── branching-strategies.md
```

**可用资源**:
- ✅ git-flow.md - Git Flow
- ✅ github-flow.md - GitHub Flow
- ✅ trunk-based.md - Trunk Based Development
- ✅ branching-strategies.md - 分支策略

**使用方式**:
```bash
# 参考创建 Git 工作流
cat git-workflow-guide/github-flow.md >> git-workflow/SKILL.md
```

---

### 6. Microsoft API Guidelines

**位置**: `microsoft-api-guidelines/`

**内容**:
```
microsoft-api-guidelines/
├── README.md
├── restful-design.md
├── openapi-spec.md
└── versioning.md
```

**可用资源**:
- ✅ restful-design.md - RESTful 设计
- ✅ openapi-spec.md - OpenAPI 规范
- ✅ versioning.md - API 版本管理

**使用方式**:
```bash
# 参考创建 API 设计规范
cat microsoft-api-guidelines/restful-design.md > api-design-guide/SKILL.md
```

---

### 7. SQL Style Guide

**位置**: `sqlstyle-guide/`

**内容**:
```
sqlstyle-guide/
├── README.md
├── sql-style.md
├── database-design.md
└── query-optimization.md
```

**可用资源**:
- ✅ sql-style.md - SQL 风格规范
- ✅ database-design.md - 数据库设计
- ✅ query-optimization.md - 查询优化

**使用方式**:
```bash
# 参考创建数据库设计规范
cat sqlstyle-guide/database-design.md > database-design-guide/SKILL.md
```

---

### 8. GitHub Actions Workflows

**位置**: `github-actions-workflows/`

**内容**:
```
github-actions-workflows/
├── README.md
├── ci-cd/
│   ├── python.yml
│   ├── nodejs.yml
│   └── go.yml
└── deployment/
    ├── aws.yml
    └── azure.yml
```

**可用资源**:
- ✅ ci-cd/python.yml - Python CI/CD
- ✅ ci-cd/nodejs.yml - Node.js CI/CD
- ✅ deployment/aws.yml - AWS 部署

**使用方式**:
```bash
# 参考创建部署流程
cat github-actions-workflows/ci-cd/python.yml > deployment-process/SKILL.md
```

---

## 📊 Skills 使用情况

### 可直接使用（无需修改）

| Skill | 来源 | 说明 |
|-------|------|------|
| **Git 工作流** | Anthropic 官方 | 通用 Git 规范 |
| **安全检查清单** | OWASP + Anthropic | 通用安全检查 |
| **SQL 风格规范** | SQL Style Guide | 通用 SQL 规范 |

### 修改后使用

| Skill | 来源 | 修改内容 |
|-------|------|----------|
| **公司编码规范** | Anthropic + PEP 8 | 添加 Python/JS/Shell 规范 |
| **代码审查指南** | GitHub + Google | 添加详细审查清单 |
| **测试规范** | Pytest + Google | 添加项目特定测试 |

### 需要创建

| Skill | 原因 |
|-------|------|
| **API 设计规范** | 需要针对项目定制 |
| **数据库设计规范** | 需要针对项目定制 |
| **部署流程** | 需要针对项目定制 |
| **最佳实践集合** | 需要团队经验沉淀 |

---

## 🚀 使用指南

### 方式 1: 直接使用

```bash
# 1. 查看可用 Skills
ls claude-code-skills-official/examples/

# 2. 复制到项目目录
cp claude-code-skills-official/examples/git-workflow.md ~/.openclaw/skills/

# 3. 在 Agent 配置中引用
echo '{"skills": ["git-workflow"]}' >> ~/.openclaw/agents/dev_engineer/config.json
```

### 方式 2: 修改后使用

```bash
# 1. 复制官方 Skill
cp claude-code-skills-official/examples/coding-standards.md skills/company-code-style/

# 2. 根据项目需要修改
nano skills/company-code-style/coding-standards.md

# 3. 添加项目特定规范
# - Python 编码规范
# - JavaScript 编码规范
# - Shell 脚本规范
```

### 方式 3: 参考创建

```bash
# 1. 查看官方 Skill 结构
cat claude-code-skills-official/templates/skill-template.md

# 2. 参考结构创建自己的 Skill
nano skills/testing-guide/SKILL.md

# 3. 添加项目特定内容
# - 测试框架（pytest）
# - 测试覆盖率要求
# - 测试用例规范
```

---

## 📋 推荐 Skills 清单

### P0 - 核心 Skills（已完成）

| Skill | 来源 | 状态 |
|-------|------|------|
| **公司编码规范** | Anthropic + PEP 8 + Google | ✅ 完成 |
| **代码审查指南** | GitHub + Google | ✅ 完成 |
| **Git 工作流** | Anthropic + Git Flow | ✅ 完成 |
| **安全检查清单** | OWASP + Anthropic | ✅ 完成 |

### P1 - 质量保证（本周）

| Skill | 来源 | 状态 |
|-------|------|------|
| **测试规范** | Pytest + Google | 📋 待创建 |

### P2 - 进阶 Skills（下周）

| Skill | 来源 | 状态 |
|-------|------|------|
| **API 设计规范** | Microsoft API Guidelines | 📋 待创建 |
| **数据库设计规范** | SQL Style Guide | 📋 待创建 |
| **部署流程** | GitHub Actions Workflows | 📋 待创建 |
| **性能优化指南** | Various Sources | 📋 待创建 |
| **最佳实践集合** | Various Sources | 📋 待创建 |

---

## 💡 年年建议

### 优先使用官方资源

1. **Anthropic Skills** - 质量最高，可直接使用
2. **oh-my-codex** - 学习 hooks/agent teams/HUDs
3. **OWASP** - 安全检查权威资源

### 参考创建

1. **编码规范** - 参考 PEP 8/Google Style/Airbnb
2. **代码审查** - 参考 GitHub/Google Code Review
3. **Git 工作流** - 参考 Git Flow/GitHub Flow
4. **测试规范** - 参考 Pytest/Google

### 自主创建

1. **项目特定规范** - 根据项目需要定制
2. **团队最佳实践** - 团队经验沉淀
3. **常见问题 FAQ** - 积累问题后创建

---

## 📚 参考资源

### 官方文档
| 资源 | 链接 |
|------|------|
| **Anthropic Skills** | https://docs.anthropic.com/claude-code/skills |
| **Claude Code** | https://docs.anthropic.com/claude-code/ |
| **MCP** | https://modelcontextprotocol.io/ |

### 编码规范
| 资源 | 链接 |
|------|------|
| **Python PEP 8** | https://pep8.org/ |
| **Google Python** | https://google.github.io/styleguide/pyguide.html |
| **Airbnb JavaScript** | https://github.com/airbnb/javascript |

### 代码审查
| 资源 | 链接 |
|------|------|
| **GitHub Code Review** | https://docs.github.com/en/pull-requests |
| **Google Code Review** | https://google.github.io/eng-practices/review/ |

### Git 工作流
| 资源 | 链接 |
|------|------|
| **Git Flow** | https://nvie.com/posts/a-successful-git-branching-model/ |
| **GitHub Flow** | https://docs.github.com/en/get-started/quickstart/github-flow |

### 安全检查
| 资源 | 链接 |
|------|------|
| **OWASP Top 10** | https://owasp.org/www-project-top-ten/ |
| **OWASP Security Code Review** | https://owasp.org/www-project-security-code-review/ |

### 测试
| 资源 | 链接 |
|------|------|
| **Pytest** | https://docs.pytest.org/ |
| **Google Testing** | https://google.github.io/eng-practices/testing/ |

### API 设计
| 资源 | 链接 |
|------|------|
| **Microsoft API Guidelines** | https://github.com/microsoft/api-guidelines |
| **OpenAPI Specification** | https://swagger.io/specification/ |

### 数据库
| 资源 | 链接 |
|------|------|
| **SQL Style Guide** | https://github.com/sqlstyle/sqlstyle |
| **Database Design** | https://www.vertabelo.com/blog/database-design-best-practices/ |

---

## 🎯 下一步行动

### 本周（P1）
- [ ] 创建测试规范（参考 Pytest + Google）
- [ ] 整合 OWASP 安全检查清单
- [ ] 整合 Git 工作流资源

### 下周（P2）
- [ ] 创建 API 设计规范（参考 Microsoft）
- [ ] 创建数据库设计规范（参考 SQL Style）
- [ ] 创建部署流程（参考 GitHub Actions）
- [ ] 创建性能优化指南
- [ ] 创建最佳实践集合

---

**🎀 整理者**: 年年  
**📅 创建时间**: 2026-04-05  
**📁 存放位置**: 🎀 年年 - 大总管 目录 → Skills  
**🔄 版本**: v1.1