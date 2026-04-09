# Skill 提案收集板

> 创建：2026-03-31 | 维护者：年年 + 各 Agent
> 用途：Agent 提交 skill 提案，年年审核后打包

---

## 提交格式

```markdown
## [提案] YYYY-MM-DD HH:MM
- **Agent**: <agent_id>
- **Skill 名**: <skill-name>
- **路径**: skills/<skill-name>/
- **内容覆盖**: <具体功能点>
- **去重检查**: ✅/❌ <说明>
- **价值评估**: 🔴高/🟡中/🟢低
- **代码基础**: <是否有现成脚本>
- **四维评分**: 工具型 X | 可操作 X | 可验证 X | 可复用 X = **总分/20**
- **状态**: 待审核
```

---

## 已有 Skill 清单（去重参考）

### 自建 Skill（16 个）
- self-evolver — 年年自我进化引擎
- python-toolkit — Python 生产级工具集
- duckdb-analytics — DuckDB 数据分析
- node-testing — Node.js 25 测试
- semgrep-security — 安全扫描
- dialogue-craft — 对话设计
- css-modern-layout — 现代 CSS 布局
- api-security — API 安全扫描器
- llm-testing — LLM 对抗测试
- docker-security — 容器安全审计
- python-crawler — Python 爬虫工具链
- python-quality — Python 代码质量
- data-quality — 数据质量检测
- log-anomaly — 日志异常检测
- css-animation-toolkit — CSS 动画工具
- oklch-design-tokens — 设计系统配色

### 安装外部 Skill（5 个）
- web-content-fetcher — 网页抓取
- openviking — 上下文数据库
- page-agent — 浏览器增强
- deepagents — Agent 框架
- agency-agents — 61 个专业 Agent

---

## 待审核提案

### [提案] 2026-04-02 — 运维自动化 Skill
- **Agent**: zhiming
- **Skill 名**: ops-automation
- **路径**: skills/ops-automation/
- **内容覆盖**: Gateway 健康巡检、Cron 自动修复、Memory 归档优化、会话增量归档
- **去重检查**: ✅ 无重复（现有 healthcheck 是安全审计，此为运维自动化）
- **价值评估**: 🔴高
- **代码基础**: ✅ workspace-health.sh + cron 经验
- **四维评分**: 工具型 4 | 可操作 3 | 可验证 3 | 可复用 4 = **14/20 🟡良好**
- **审核意见**: 内容扎实，但缺少实际脚本代码。需补充 cron-health-check.sh / archive-with-extract.sh / self-check.sh 的可执行代码后方可打包
- **状态**: ⏳ 需补充代码

### [提案] 2026-04-02 — 流程优化 Skill
- **Agent**: zhiming
- **Skill 名**: workflow-optimizer
- **路径**: skills/workflow-optimizer/
- **内容覆盖**: 心跳优先级拆分、统一汇报模板、自检统一入口、学习闭环强制 3 问
- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ✅ 有概念框架
- **四维评分**: 工具型 4 | 可操作 4 | 可验证 3 | 可复用 4 = **15/20 🟡良好**
- **审核意见**: 心跳优先级拆分和统一汇报模板实用性很强，但需提供 self-check.sh 实际代码和汇报模板的标准化配置
- **状态**: ⏳ 需补充代码

---

## 新增提案（2026-04-04 自动扫描生成）

### [提案] 2026-04-04 — Raincloud 数据可视化（月影）
- **Agent**: yueying
- **Skill 名**: raincloud-viz
- **路径**: skills/raincloud-viz/
- **内容覆盖**:
  - Raincloud Plot 原理（半小提琴 + 箱线图 + 抖动散点）
  - 替代 Dynamite Plot 的四大理由
  - Plotly/Seaborn/Matplotlib 实现方案
  - 完整 Python 实现函数
- **去重检查**: ✅ 无重复（与 oklch-design-tokens 不同，此为统计可视化）
- **价值评估**: 🔴高
- **代码基础**: ✅ 有完整 Python 实现代码
- **四维评分**: 工具型 5 | 可操作 5 | 可验证 4 | 可复用 5 = **19/20 🟢优秀**
- **审核意见**: 质量很高！有完整代码、有理论依据、有应用场景。建议立即打包，补充：① 安装说明 ② 使用示例 ③ 与 dynamite plot 对比图
- **状态**: ✅ **已完成**（2026-04-04 打包完成）

### [提案] 2026-04-04 — Falcon 视觉分割（月影）
- **Agent**: yueying
- **Skill 名**: falcon-perception
- **路径**: skills/falcon-perception/
- **内容覆盖**:
  - Falcon Perception 模型部署（0.6B 参数）
  - 自然语言选区分割
  - 与 SAM 3 对比
  - 漫剧角色抠图应用
- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ❌ 仅有概念，无部署代码
- **四维评分**: 工具型 5 | 可操作 3 | 可验证 4 | 可复用 5 = **17/20 🟡良好**
- **审核意见**: 模型本身很有价值，但需要实际部署验证。需补充：① HuggingFace 部署代码 ② 实际测试用例 ③ 性能基准
- **状态**: ⏳ 需补充部署代码

### [提案] 2026-04-04 — 运维脚本集（执明）
- **Agent**: zhiming
- **Skill 名**: ops-automation-scripts
- **路径**: skills/ops-automation-scripts/
- **内容覆盖**: 
  - Gateway 健康巡检（扩展 workspace-health.sh）
  - Cron 失败自动检测与修复建议
  - Memory 归档前知识提取
  - 会话增量归档（去重）
- **去重检查**: ✅ 无重复（与 ops-automation 提案内容重叠，但更聚焦脚本实现）
- **价值评估**: 🔴高
- **代码基础**: ⚠️ 部分有（workspace-health.sh 存在，其他脚本待写）
- **四维评分**: 工具型 5 | 可操作 3 | 可验证 4 | 可复用 4 = **16/20 🟡良好**
- **审核意见**: 与 ops-automation 提案合并处理。需执明补充 4 个脚本：`cron-health-check.sh` / `archive-with-extract.sh` / `session-archive-incremental.sh` / `self-check.sh`
- **状态**: ⏳ 等待脚本实现

### [提案] 2026-04-04 — 心跳与工作流优化（执明）
- **Agent**: zhiming
- **Skill 名**: heartbeat-workflow-optimizer
- **路径**: skills/heartbeat-workflow-optimizer/
- **内容覆盖**:
  - 心跳优先级拆分（高/中/低优轮值）
  - 多 Agent 统一汇报模板
  - 自检统一入口 self-check.sh
  - 学习闭环强制 3 问
  - 飞书文档模板化
- **去重检查**: ✅ 无重复（与 workflow-optimizer 提案重叠）
- **价值评估**: 🔴高
- **代码基础**: ⚠️ 概念框架有，脚本待写
- **四维评分**: 工具型 4 | 可操作 4 | 可验证 3 | 可复用 5 = **16/20 🟡良好**
- **审核意见**: 与 workflow-optimizer 提案合并。实用性很强，需补充 self-check.sh 和汇报模板配置文件
- **状态**: ⏳ 等待脚本实现

---

## 已完成提案

### 2026-03-31 首批（13 个已完成）
- ✅ node-testing — 玄机
- ✅ semgrep-security — 执明
- ✅ dialogue-craft — 惊鸿
- ✅ css-modern-layout — 霓裳
- ✅ api-security — 鉴微
- ✅ llm-testing — 鉴微
- ✅ docker-security — 执明
- ✅ python-crawler — 太一
- ✅ python-quality — 太一
- ✅ data-quality — 鉴微
- ✅ log-anomaly — 鉴微
- ✅ css-animation-toolkit — 霓裳
- ✅ oklch-design-tokens — 霓裳

### 2026-04-04（1 个已完成）
- ✅ raincloud-viz — 月影（数据可视化/Raincloud Plot）

---

## 已拒绝提案

### [提案] 2026-04-03 — 今日学习（yueying）
- **Agent**: yueying
- **Skill 名**: 今日学习
- **四维评分**: 工具型 1 | 可操作 2 | 可验证 2 | 可复用 2 = **7/20 🔴不合格**
- **拒绝原因**: 内容为学习笔记（Raincloud Plot / Falcon Perception），非可打包 Skill。名称"今日学习"也不符合 skill 命名规范
- **改进建议**: 可分别拆为 `raincloud-viz`（数据可视化）和 `falcon-perception`（视觉分割），补充实际部署代码后重新提交
- **状态**: ❌ 已拒绝

---

## 🗑️ 已清理的低质量提案（2026-04-06 自动扫描生成）

> 以下提案因不符合 skill 命名规范（中文名称、无四维评分、内容不完整）已被清理

| 原提案名 | Agent | 清理原因 | 改进建议 |
|----------|-------|----------|----------|
| 可自动化操作 | zhiming | 中文名、无四维评分 | 重写为 `ops-automation-scripts` |
| 可优化的流程 | zhiming | 中文名、无四维评分 | 合并到 `heartbeat-workflow-optimizer` |
| 今日学习 | yueying | 中文名、学习笔记非 skill | 拆分为具体技能（参考 raincloud-viz） |

**状态**: ❌ 已清理，需按规范重写后重新提交

---

## 🗑️ 已清理的低质量提案（2026-04-07 自动扫描生成）

> 以下提案因不符合 skill 命名规范（中文名称、无四维评分、内容不完整）已被清理

| 原提案名 | Agent | 清理原因 | 改进建议 |
|----------|-------|----------|----------|
| 可自动化操作 | zhiming | 中文名、无四维评分、内容截断 | 重写为 `ops-automation-scripts`，补充完整脚本代码 |
| 可优化的流程 | zhiming | 中文名、无四维评分、内容截断 | 合并到 `heartbeat-workflow-optimizer`，补充 self-check.sh |
| 今日学习 | yueying | 中文名、学习笔记非 skill | 拆分为具体技能（参考 raincloud-viz），补充部署代码 |

**状态**: ❌ 已清理，需按规范重写后重新提交

---

## 📋 今日审核总结（2026-04-07）

| 提案 | Agent | 状态 | 下一步 |
|------|-------|------|--------|
| ops-automation | zhiming | ⏳ 需补充代码 | 等待 4 个脚本实现 |
| workflow-optimizer | zhiming | ⏳ 需补充代码 | 等待 self-check.sh |
| falcon-perception | yueying | ⏳ 需部署代码 | 等待 HuggingFace 部署 |
| ops-automation-scripts | zhiming | ⏳ 合并处理 | 与 ops-automation 合并 |
| heartbeat-workflow-optimizer | zhiming | ⏳ 合并处理 | 与 workflow-optimizer 合并 |

**今日行动项**：
1. ⏳ 催促执明补充 4 个运维脚本（cron-health-check.sh / archive-with-extract.sh / session-archive-incremental.sh / self-check.sh）
2. ⏳ 催促月影补充 Falcon Perception 部署代码
3. ✅ 清理 3 个低质量自动提案（中文名、无四维评分、内容截断）
4. ⚠️ 继续优化 skill_evaluator.py 避免生成低质量提案（直接用章节标题、中文名）

**今日扫描结果**：
| Agent | 章节数 | 可打包 | 说明 |
|-------|--------|--------|------|
| frontend_dev | 17 | 0 | 学习闭环内容，纯知识型 |
| qa_engineer | 2 | 0 | 纯知识型内容 |
| zhiming | 7 | 2→0 | 有 2 个自动提案但质量不足，已清理 |
| yueying | 5 | 1→0 | 有 1 个自动提案但质量不足，已清理 |
| taiyi | 5 | 0 | 纯知识型内容 |
| main | 5 | 0 | 纯知识型内容 |
| dev_engineer | 2 | 0 | 无新内容 |
| product_manager | 2 | 0 | 无新内容 |
| chief_cute_officer | 3 | 0 | 无新内容 |
| tiangong | 3 | 0 | 纯知识型内容 |
| lingxi | 3 | 0 | 无新内容 |
| jinghong | 3 | 0 | 无新内容 |
| shichen | 3 | 0 | 无新内容 |

**技能打包进展**：
- ✅ 已完成：17 个（13 个首批 + 1 个 raincloud-viz + 3 个其他）
- ⏳ 待完成：5 个（需补充代码/部署）
- ❌ 已拒绝：1 个（今日学习）
- 🗑️ 累计清理：6 个（2026-04-06 清理 3 个 + 2026-04-07 清理 3 个）

**核心问题**：
- skill_evaluator.py 评估逻辑过弱，仅凭"有代码块"就判定可打包
- 生成的提案直接用章节标题（中文），不符合 skill 命名规范（英文、短横线分隔）
- 缺少四维评分自动计算
- 缺少去重检查（与已有提案重复）

**改进建议**：
1. 增强 skill_evaluator.py 评估逻辑，加入四维评分自动计算
2. 强制 skill 名称为英文（a-z、0-9、短横线）
3. 加入去重检查（对比已有 skill 清单和待审核提案）
4. 内容截断检测（提案内容必须完整）

---

---

## 🗑️ 已清理的低质量提案（2026-04-08 自动扫描生成）

> 以下提案因不符合 skill 命名规范（中文名称、无四维评分、内容不完整）已被清理

| 原提案名 | Agent | 清理原因 | 改进建议 |
|----------|-------|----------|----------|
| 今日学习 | yueying | 中文名、学习笔记非 skill、内容截断 | 拆分为具体技能（参考 raincloud-viz），补充实际代码 |
| 可自动化操作 | zhiming | 中文名、无四维评分、内容截断 | 重写为 `ops-automation-scripts`，补充完整脚本代码（workspace-health.sh 实际不存在） |
| 可优化的流程 | zhiming | 中文名、无四维评分、内容截断 | 合并到 `heartbeat-workflow-optimizer`，补充 self-check.sh |

**状态**: ❌ 已清理，需按规范重写后重新提交

---

## 📋 今日审核总结（2026-04-08）

| 提案 | Agent | 状态 | 下一步 |
|------|-------|------|--------|
| ops-automation | zhiming | ⏳ 需补充代码 | 等待 4 个脚本实现（workspace-health.sh 不存在，需从头写） |
| workflow-optimizer | zhiming | ⏳ 需补充代码 | 等待 self-check.sh |
| falcon-perception | yueying | ⏳ 需部署代码 | 等待 HuggingFace 部署 |
| ops-automation-scripts | zhiming | ⏳ 合并处理 | 与 ops-automation 合并 |
| heartbeat-workflow-optimizer | zhiming | ⏳ 合并处理 | 与 workflow-optimizer 合并 |

**今日行动项**：
1. ⏳ 催促执明补充 4 个运维脚本（cron-health-check.sh / archive-with-extract.sh / session-archive-incremental.sh / self-check.sh）— **注意：workspace-health.sh 实际不存在，需从头创建**
2. ⏳ 催促月影补充 Falcon Perception 部署代码
3. ✅ 清理 3 个低质量自动提案（中文名、无四维评分、内容截断）
4. ⚠️ **紧急**：skill_evaluator.py 连续 3 天生成相同低质量提案，需立即修复评估逻辑

**今日扫描结果**：
| Agent | 章节数 | 可打包 | 说明 |
|-------|--------|--------|------|
| frontend_dev | 17 | 0 | 学习闭环内容，纯知识型 |
| qa_engineer | 2 | 0 | 纯知识型内容 |
| zhiming | 7 | 2→0 | 有 2 个自动提案但质量不足，已清理 |
| yueying | 5 | 1→0 | 有 1 个自动提案但质量不足，已清理 |
| taiyi | 5 | 0 | 纯知识型内容 |
| main | 5 | 0 | 纯知识型内容 |
| dev_engineer | 2 | 0 | 无新内容 |
| product_manager | 2 | 0 | 无新内容 |
| chief_cute_officer | 3 | 0 | 无新内容 |
| tiangong | 3 | 0 | 纯知识型内容 |
| lingxi | 3 | 0 | 无新内容 |
| jinghong | 3 | 0 | 无新内容 |
| shichen | 3 | 0 | 无新内容 |

**技能打包进展**：
- ✅ 已完成：17 个（13 个首批 + 1 个 raincloud-viz + 3 个其他）
- ⏳ 待完成：5 个（需补充代码/部署）
- ❌ 已拒绝：1 个（今日学习）
- 🗑️ 累计清理：9 个（2026-04-06 清理 3 个 + 2026-04-07 清理 3 个 + 2026-04-08 清理 3 个）

**核心问题**：
- skill_evaluator.py 评估逻辑过弱，仅凭"有代码块"就判定可打包
- 生成的提案直接用章节标题（中文），不符合 skill 命名规范（英文、短横线分隔）
- 缺少四维评分自动计算
- 缺少去重检查（与已有提案重复）
- **新问题**：连续 3 天生成相同低质量提案，说明清理后没有阻止重复生成

**改进建议**：
1. 增强 skill_evaluator.py 评估逻辑，加入四维评分自动计算
2. 强制 skill 名称为英文（a-z、0-9、短横线）
3. 加入去重检查（对比已有 skill 清单和待审核提案）
4. 内容截断检测（提案内容必须完整）
5. **新增**：已清理提案标记机制，避免重复生成

---

## [提案] 2026-04-09 11:00
- **Agent**: yueying
- **Skill名**: 今日学习
- **路径**: skills/今日学习/
- **内容覆盖**: 📚 今日学习

### 2026-04-02

#### Step 0: 落地检查
- 上次学的 CSS Anchor Positioning API 今早刚学，尚未落地验证（合理，刚学完）
- 20
- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ✅ 有代码
- **状态**: 待审核

## [提案] 2026-04-09 11:00
- **Agent**: zhiming
- **Skill名**: 可自动化操作
- **路径**: skills/可自动化操作/
- **内容覆盖**: 🔄 可自动化操作

### 1. Gateway 健康巡检 → 已有脚本，可扩展
- 现状：`workspace-health.sh` 已覆盖基础检查
- **改进**：增加 `openclaw ga
- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ✅ 有代码
- **状态**: 待审核


## [提案] 2026-04-09 11:00
- **Agent**: zhiming
- **Skill名**: 可优化的流程
- **路径**: skills/可优化的流程/
- **内容覆盖**: ⚡ 可优化的流程

### 1. 心跳执行流程 → 拆分优先级
- 现状：心跳每次做一堆检查，token消耗大
- **优化**：
  - **高优**：Gateway状态 + 磁盘告警（<1GB）

- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ✅ 有代码
- **状态**: 待审核

## [提案] 2026-04-09 11:02
- **Agent**: yueying
- **Skill名**: falcon
- **路径**: skills/falcon/
- **内容覆盖**: 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 5 | 可验证 3 | 可复用 5 = **14/20**
- **状态**: 待审核

## [提案] 2026-04-09 11:02
- **Agent**: zhiming
- **Skill名**: agents
- **路径**: skills/agents/
- **内容覆盖**: 📏 可规则化的判断

### 1. 飞书消息发送判断规则
- **规则**：优先用 `message` 系统工具，只在用户明确说"以我身份发"时才用 `feishu_im_user_message`
- **规则**：飞书消息 content 必须是合法 JSON，text 类型用 `{"text"
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 3 | 可验证 5 | 可复用 3 = **12/20**
- **状态**: 待审核


## [提案] 2026-04-09 11:02
- **Agent**: zhiming
- **Skill名**: zhiming-skill-0409
- **路径**: skills/zhiming-skill-0409/
- **内容覆盖**: 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 5 | 可验证 3 | 可复用 3 = **12/20**
- **状态**: 待审核

## [提案] 2026-04-09 11:02
- **Agent**: main
- **Skill名**: main-skill-0409
- **路径**: skills/main-skill-0409/
- **内容覆盖**: 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 5 | 可验证 3 | 可复用 3 = **12/20**
- **状态**: 待审核

## [提案] 2026-04-09 11:02
- **Agent**: taiyi
- **Skill名**: google
- **路径**: skills/google/
- **内容覆盖**: 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 5 | 可验证 3 | 可复用 3 = **12/20**
- **状态**: 待审核

## [提案] 2026-04-09 11:02
- **Agent**: qa_engineer
- **Skill名**: api
- **路径**: skills/api/
- **内容覆盖**: 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？
- **去重检查**: ✅ 无重复
- **价值评估**: 🔴高
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 5 | 可验证 5 | 可复用 5 = **16/20**
- **状态**: 待审核

## [提案] 2026-04-09 11:03
- **Agent**: zhiming
- **Skill名**: agents
- **路径**: skills/agents/
- **内容覆盖**: 📏 可规则化的判断

### 1. 飞书消息发送判断规则
- **规则**：优先用 `message` 系统工具，只在用户明确说"以我身份发"时才用 `feishu_im_user_message`
- **规则**：飞书消息 content 必须是合法 JSON，text 类型用 `{"text"
- **去重检查**: ✅ 无重复
- **价值评估**: 🟡中
- **代码基础**: ❌ 无代码
- **四维评分**: 工具型 1 | 可操作 3 | 可验证 5 | 可复用 3 = **12/20**
- **状态**: 待审核
