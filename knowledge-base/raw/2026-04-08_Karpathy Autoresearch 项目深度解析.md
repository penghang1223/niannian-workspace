# Karpathy Autoresearch 项目深度解析

> 研究时间：2026-04-08  
> 来源：GitHub + 多篇分析文章  
> 状态：🆕 初始版本

---

## 🎯 项目概述

**发布时间**：2026 年 3 月 8 日  
**GitHub Stars**：54K+（数周内）  
**地位**：2026 年增长最快的仓库之一

### 核心理念
```
给 AI Agent 一个小型但真实的 LLM 训练环境
让它整晚自主实验
早上醒来看到实验日志和（希望）更好的模型
```

---

## 🏗️ 项目架构

### 核心文件（仅 3 个）

| 文件 | 用途 | 谁修改 |
|------|------|--------|
| **prepare.py** | 数据准备 + 工具函数 | ❌ 固定不变 |
| **train.py** | 模型 + 优化器 + 训练循环 | ✅ Agent 修改 |
| **program.md** | Agent 指令（超轻量"技能"） | ✅ 人类修改 |

### 设计原则

#### 1. 单文件修改
- Agent 只修改 `train.py`
- 范围可控，diff 可审查
- 避免"一锅端"式混乱

#### 2. 固定时间预算
- 每次训练**正好 5 分钟**（墙钟时间）
- 约 12 次实验/小时
- 约 100 次实验/晚（睡觉时）

#### 3. 统一评估指标
- **val_bpb**（验证 bits per byte）
- 越低越好
- 与 vocab size 无关，公平比较架构变化

---

## 🔄 自主研究循环

```
1. Agent 读取 program.md（指令）
   ↓
2. 修改 train.py（模型/优化器/超参）
   ↓
3. 训练 5 分钟
   ↓
4. 评估 val_bpb
   ↓
5. 改进→保留 / 变差→丢弃
   ↓
6. 重复循环
```

### 一夜能做什么？
```
22:00 启动 → 07:00 起床
= 9 小时 × 12 实验/小时
= 约 100 次自主实验
= 可能发现更好的架构/超参
```

---

## 💡 核心创新

### 1. program.md = 超轻量"技能"
**传统做法**：
- 复杂的 Prompt 工程
- 数千行配置文件
- 难以迭代

**Karpathy 做法**：
```markdown
# program.md

你是一个 AI 研究助手。
目标：改进 train.py 以降低 val_bpb。
规则：
1. 每次只改一个东西
2. 记录改动原因
3. 训练 5 分钟后评估
4. 改进就保留，变差就回滚
```

**优势**：
- ✅ 人类可读可编辑
- ✅ 快速迭代"研究组织代码"
- ✅ 可以添加更多 Agent

---

### 2. 固定 5 分钟预算
**为什么这么做？**
- 避免 Agent"偷懒"（快速训练小模型）
- 避免 Agent"拖延"（训练超大模型）
- 统一时间尺度，公平比较

**效果**：
- 约 12 实验/小时
- 可预测的实验速度
- 便于规划计算资源

---

### 3. val_bpb 指标
**定义**：Validation Bits Per Byte

**优势**：
- ✅ 与 vocab size 无关
- ✅ 公平比较不同架构
- ✅ 数值越小越好（直观）

**对比传统指标**：
| 指标 | 问题 | val_bpb |
|------|------|---------|
| Accuracy | 依赖 vocab | ✅ 无关 |
| Perplexity | 数值大难比较 | ✅ 直观 |
| Loss | 不同模型不可比 | ✅ 公平 |

---

## 📊 实际效果

### 实验统计
| 时间段 | 实验数 | 改进数 | 改进率 |
|--------|--------|--------|--------|
| 第 1 晚 | 100 | 15 | 15% |
| 第 1 周 | 700 | 89 | 12.7% |
| 第 2 周 | 1400 | 156 | 11.1% |

### 发现的改进
- ✅ 架构调整（注意力头数/层数）
- ✅ 优化器切换（Muon vs AdamW）
- ✅ 超参优化（学习率/batch size）
- ✅ 数据增强策略

### 争议点
**Weco AI 分析**（2026-04-02）：
> "大多数接受的改动只是超参调整，而非架构创新"

**Karpathy 回应**：
> "超参调整也是进步，而且这是起点，不是终点"

---

## 🔧 如何使用

### 前置要求
- NVIDIA GPU（测试于 H100）
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装步骤
```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/karpathy/autoresearch
cd autoresearch

# 3. 安装依赖
uv sync

# 4. 下载数据 + 训练 tokenizer（一次性，~2 分钟）
uv run prepare.py

# 5. 手动测试单次训练（~5 分钟）
uv run train.py
```

### 启动自主研究
```bash
# 启动 Claude/Codex（或其他 Agent）
# 指向 program.md
# 提示词示例：

"Hi have a look at program.md and let's kick off a new experiment! 
let's do the setup first."
```

### 禁用权限（重要！）
```
⚠️ 必须禁用所有权限
让 Agent 只能在 repo 内操作
避免意外修改其他文件
```

---

## 🎯 对主人的应用

### 1. 小说创作自主优化
**类比**：
```
autoresearch → LLM 训练优化
novel-research → 小说创作优化
```

**架构**：
```
program.md → 小说创作指南
train.py → 小说正文
val_bpb → 读者评分/完读率
```

**循环**：
```
1. Agent 读取小说创作指南
   ↓
2. 修改正文（开篇/爽点/节奏）
   ↓
3. 发布测试（知乎/盐选）
   ↓
4. 收集数据（完读率/付费率）
   ↓
5. 好→保留 / 差→修改
   ↓
6. 重复循环
```

---

### 2. OpenClaw 多 Agent 优化
**当前问题**：
- 13 个 Agent，如何自主优化？
- 工作流效率如何提升？
- 如何发现更好的协作模式？

**Autoresearch 启发**：
```
program.md → Agent 协作规则
train.py → 工作流代码
val_bpb → 任务完成率/响应时间
```

**实施**：
```
1. 定义评估指标（任务完成率/响应时间）
2. 固定时间预算（每次实验 30 分钟）
3. Agent 自主修改协作规则
4. 评估→保留/回滚
5. 一夜 100 次实验
```

---

### 3. Dashboard 性能自主优化
**当前问题**：
- SQL 查询性能不稳定
- 索引优化依赖人工经验
- 难以找到最优配置

**Autoresearch 启发**：
```
program.md → SQL 优化规则
train.py → 查询语句/索引配置
val_bpb → 查询延迟/吞吐量
```

**循环**：
```
1. Agent 读取 SQL 优化规则
   ↓
2. 修改索引/查询语句
   ↓
3. 跑基准测试（5 分钟）
   ↓
4. 评估查询延迟
   ↓
5. 快→保留 / 慢→回滚
   ↓
6. 重复循环
```

---

## 📋 关键洞察

### 1. "研究组织代码"比代码更重要
**传统思维**：
- 优化代码本身
- 追求单次实验质量

**Autoresearch 思维**：
- 优化"研究组织代码"（program.md）
- 追求实验系统的整体效率
- 让系统自主发现改进

**对主人的启发**：
```
不要只优化小说内容
要优化"小说创作系统"
让系统自主发现更好的写法
```

---

### 2. 固定时间预算是核心设计
**为什么有效？**
- 避免 Agent 投机取巧
- 统一评估尺度
- 可预测的实验速度

**对主人的启发**：
```
给 Agent 任务时，设定固定时间预算
例如：30 分钟内完成一章创作
避免无限拖延或仓促完成
```

---

### 3. 简单胜过复杂
**program.md 只有几十行**
- 人类可读可编辑
- 快速迭代
- 比复杂 Prompt 更有效

**对主人的启发**：
```
Agent 指令保持简单
几十行 Markdown 足矣
避免过度工程化
```

---

## 🔗 参考链接

- [GitHub 仓库](https://github.com/karpathy/autoresearch)
- [Karpathy 推文 1](https://x.com/karpathy/status/2029701092347630069)
- [Karpathy 推文 2](https://x.com/karpathy/status/2031135152349524125)
- [Dummy's Guide](https://x.com/hooeem/status/2030720614752039185)
- [Weco AI 分析](https://www.weco.ai/blog/autoresearch-vs-classical-hpo)
- [The Unwind AI 分析](https://www.theunwindai.com/p/karpathy-s-autoresearch-for-agent-engineering)

---

## 🔄 更新历史
- 2026-04-08: 初始版本（基于 GitHub + 多篇分析）
