# ruflo / Claude-Flow 学习

> 类型：knowledge | 创建：2026-03-02 | 版本：v1.0 | 来源：GitHub 项目学习

---

## 📝 变更历史

| 版本 | 日期 | 变更内容 | 操作者 |
|------|------|----------|--------|
| v1.0 | 2026-03-02 | 初始创建（从 ruvnet/ruflo 项目学习提取） | 年年 |

---

## 📚 项目信息

| 项目 | 内容 |
|------|------|
| **仓库** | ruvnet/ruflo |
| **定位** | 企业级 AI 编排平台 |
| **核心** | 专为 Claude/Claude Code 设计 |
| **Stars** | 17.6k+ |
| **语言** | TypeScript 64% + JavaScript 23% |

---

## 🔥 核心特性

### 1. 64 个专用 Agent
覆盖 16 个类别：
- 核心开发（5）：coder, planner, researcher, reviewer, tester
- 蜂群协调（3）：hierarchical, mesh, adaptive
- 共识系统（7）：Byzantine, Raft, Gossip, CRDT
- GitHub 集成（13）：PR 管理、代码审查、发布自动化
- 性能优化（6）：监控、负载均衡、拓扑优化

### 2. 蜂群智能
- Queen-led 层级协调
- 分布式 mesh 拓扑
- 动态 Agent 架构 (DAA)
- 自组织 + 容错

### 3. 真理验证系统
- **阈值**：0.95 准确率
- **机制**：强制验证 + 自动回滚
- **保护**：拜占庭容错
- **监控**：实时验证反馈

### 4. 训练管道
- ML 系统持续优化 Agent 表现
- 从历史任务中学习
- 验证数据反馈到训练

### 5. 流式 JSON 链
- Agent 输出实时管道传递
- 无缝协同工作流
- 技术实现：stream-json 格式

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| SWE-Bench 解决率 | 84.8% |
| 速度提升 | 2.8-4.4x |
| MCP 工具数 | 87 个 |
| 发布版本 | 1,456+ |

---

## 💡 核心创新

### 1. 真理验证
"truth is enforced, not assumed"
- 95% 准确率才能进入生产
- 自动回滚失败操作

### 2. MLE-STAR 工作流
Machine Learning Engineering via Search and Targeted Refinement
- 智能 Agent 动态生成
- 自动化复杂任务编排

### 3. Stream Chaining
- Agent-to-Agent 输出管道
- 实时协调

---

## 🎯 与 OpenClaw 对比

| 维度 | ruflo | OpenClaw |
|------|-------|----------|
| Agent 数量 | 64 个预制 | 按需扩展 |
| 记忆系统 | SQLite 12 表 | LanceDB/Qdrant + MEMORY.md |
| 验证机制 | 0.95 真理阈值 | 人工审核优先 |
| 部署方式 | npm 全局安装 | Node.js + Gateway |
| 特色 | 蜂群智能、训练管道 | 心跳机制、技能系统 |
| 定位 | 企业级开发编排 | 个人 AI 助手 + 自动化 |

---

## 🤔 可借鉴点

1. **真理验证系统** - 重要操作前增加置信度检查
2. **Agent 分类体系** - 64 个专用 Agent 的分类方式
3. **训练管道** - 从历史任务中学习优化
4. **流式链式调用** - Agent 间输出传递设计

---

## 🔗 关联记忆

- [[../categories/AI 学习]] - AI 学习方向
- [[../skills/多 Agent 架构]] - 多 Agent 知识
- [[../knowledge/memU 学习]] - memU 记忆框架

---

**学习来源**：2026-03-02 GitHub 项目研究  
**置信度**：高（官方 README + Wiki）  
**应用价值**：高（多 Agent 架构参考）
