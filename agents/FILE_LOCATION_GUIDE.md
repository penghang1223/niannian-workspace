# 📁 Agent 文件创建位置规范

> **版本**: v1.0  
> **创建时间**: 2026-04-05  
> **维护者**: 年年 🎀  
> **适用范围**: 所有 Agent

---

## ⚠️ 重要原则

**每个 Agent 必须记住自己的工作目录！创建文件前先确认位置！**

---

## 📂 目录结构

```
/Users/narain/.openclaw/workspace/
├── agents/                    # 各 Agent 专属工作目录
│   ├── main/                  # 年年（协调员）
│   ├── product_manager/       # 望舒（产品）
│   ├── dev_engineer/          # 玄机（后端）
│   ├── frontend_dev/          # 霓裳（前端）
│   ├── qa_engineer/           # 鉴微（测试）
│   ├── chief_cute_officer/    # 岁岁（内容）
│   └── ...
├── memory/                    # 共享记忆
│   ├── daily/                 # 每日记忆
│   ├── agents/                # Agent 专属记忆
│   └── collaboration/         # 协作记录
├── skills/                    # Skills 资源
├── docs/                      # 项目文档
└── opc-platform/              # OPC 项目
```

---

## 🎯 各 Agent 文件创建位置

### 年年 (main)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 协调记录 | `agents/main/` | 任务分发/协调日志 |
| 每日总结 | `memory/daily/YYYY-MM-DD.md` | 每日工作摘要 |
| 长期记忆 | `MEMORY.md` |  curated 长期记忆 |
| 技能汇总 | `skills/README.md` | Skills 资源汇总 |

### 望舒 (product_manager)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 产品文档 | `agents/product_manager/` | PRD/需求分析 |
| 学习汇报 | `memory/agents/product_manager/lessons.md` | 学习记录 |
| 能力评估 | `memory/agents/product_manager/capability.json` | 能力评分 |

### 玄机 (dev_engineer)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 技术文档 | `agents/dev_engineer/` | 技术方案/实现文档 |
| 学习汇报 | `memory/agents/dev_engineer/lessons.md` | 学习记录 |
| 能力评估 | `memory/agents/dev_engineer/capability.json` | 能力评分 |
| 项目代码 | `opc-platform/` | 实际项目代码 |

### 霓裳 (frontend_dev)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 设计文档 | `agents/frontend_dev/` | UI/UX 设计文档 |
| 学习汇报 | `memory/agents/frontend_dev/lessons.md` | 学习记录 |
| 能力评估 | `memory/agents/frontend_dev/capability.json` | 能力评分 |
| 前端代码 | `opc-platform/frontend/` | 前端代码 |

### 鉴微 (qa_engineer)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 测试报告 | `agents/qa_engineer/` | 质量报告/测试结果 |
| 测试用例 | `agents/qa_engineer/test-cases-library.md` | 测试用例库 |
| 学习汇报 | `memory/agents/qa_engineer/lessons.md` | 学习记录 |
| 能力评估 | `memory/agents/qa_engineer/capability.json` | 能力评分 |

### 岁岁 (chief_cute_officer / shichen)
| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 内容创作 | `agents/shichen/` | 内容/文案/时间管理 |
| 学习汇报 | `memory/agents/shichen/lessons.md` | 学习记录 |
| 能力评估 | `memory/agents/shichen/capability.json` | 能力评分 |

---

## 📋 共享目录使用规则

### memory/daily/
- **用途**: 每日工作摘要
- **格式**: `YYYY-MM-DD.md`
- **谁可以写**: 所有 Agent（通过年年协调）

### memory/agents/<agent_id>/
- **用途**: Agent 专属记忆
- **文件**: `lessons.md`, `capability.json`, `patterns.md`
- **谁可以写**: 对应 Agent

### skills/
- **用途**: Skills 资源
- **规则**: 创建新 Skill 需年年审核
- **格式**: `<skill-name>/SKILL.md`

### docs/
- **用途**: 项目文档
- **规则**: 重要文档需年年审核

---

## ❌ 禁止行为

| 行为 | 正确做法 |
|------|----------|
| ❌ 在根目录随意创建文件 | ✅ 放在对应 Agent 目录下 |
| ❌ 在其他 Agent 目录创建文件 | ✅ 放在自己目录下 |
| ❌ 直接修改 MEMORY.md | ✅ 通过年年审核后修改 |
| ❌ 在 memory/ 下创建非标准文件 | ✅ 使用标准文件名 |

---

## ✅ 创建文件前检查清单

每次创建文件前，Agent 必须自问：

1. **这个文件应该放在哪个目录？**
   - 自己的工作成果 → `agents/<agent_id>/`
   - 学习记录 → `memory/agents/<agent_id>/lessons.md`
   - 共享记忆 → 通过年年协调

2. **文件名是否符合规范？**
   - 每日记忆：`YYYY-MM-DD.md`
   - 学习记录：`lessons.md`
   - 能力评估：`capability.json`

3. **是否需要通知年年？**
   - 创建新目录 → 需要
   - 修改共享文件 → 需要
   - 重要文档 → 需要

---

## 🔄 通知机制

**Agent 创建重要文件后必须通知年年：**

```
[文件创建通知]
Agent: <agent_id>
文件: <文件路径>
用途: <说明>
```

**年年收到后：**
1. 确认位置正确
2. 记录到共享记忆
3. 必要时更新索引

---

## 📊 违规处理

| 违规次数 | 处理 |
|----------|------|
| 第 1 次 | 年年提醒纠正 |
| 第 2 次 | 年年协助迁移文件 |
| 第 3 次 | 记录到 Agent lessons.md |

---

## 💡 记忆技巧

**每个 Agent 记住一句话：**

> "自己的工作放 `agents/<agent_id>/`，学习记录放 `memory/agents/<agent_id>/lessons.md`，其他位置先问年年！"

---

**版本**: v1.0  
**创建时间**: 2026-04-05  
**下次审查**: 2026-04-12
