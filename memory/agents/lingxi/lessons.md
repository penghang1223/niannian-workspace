# 灵犀（lingxi）学习记录

> 最后更新：2026-04-02
> 维护者：灵犀

---

## 📚 今日学习

### 2026-04-02

#### 1. RCCF 框架取代 Chain-of-Thought（🟡 有价值）
- **来源**：ucstrategies.com 2026-03 Prompt Engineering 终极指南
- **核心**：Role-Context-Constraint-Format 四步法。现代模型（GPT-5/Claude 4.0+）已内置推理能力，不需要 CoT 手把手引导，需要的是明确的方向约束
- **关键数据**：
  - 优化 prompt 后：任务完成 18.7分钟 vs 人工3.55小时（11.4x提速）
  - 差 prompt 反而更慢：47分钟 + 34.8%错误率
  - 首句指定输出格式 → 修改率降低 60%
  - 38.5%的AI对话需要迭代修正 = 首次尝试失败
- **评**：🟡 对臣的日常工作直接有用。臣已在 TOOLS.md 中记录了 Anthropic 官方 prompt 原则，RCCF 是更简洁的实操框架，可融合
- **用**：下次为君上献策时，用 RCCF 结构代替散装 prompt。例：`角色：创意总监 | 上下文：漫剧第一集脚本 | 约束：3幕结构+每幕≤500字 | 格式：Markdown分幕输出`

#### 2. 2026 = Agent 信任之年（🔴 高价值）
- **来源**：IndyDevDan - Top 2% Agentic Engineering Roadmap 2026
- **核心论点**：模型已不是瓶颈，**信任才是**。"How much do you trust your agents?" 决定你能走多远
- **十大赌注**：
  1. Anthropic 成为巨头（Claude Code + 最佳 tool calling + sub-agents）
  2. Tool Calling 是真正的机会（不是模型能力，是工具集成）
  3. Custom Agents 优先于通用 Agent
  4. Multi-Agent Orchestration 是下一个前沿
  5. Agent Sandboxes（安全隔离执行）
  6. In-Loop vs Out-Loop Agentic Coding
  7. Agentic Coding 2.0 = Agent 编排 Agent
  8. 基准测试崩塌
  9. Agents 吃掉 SaaS
  10. AGI 炒作消亡
- **评**：🔴 直接指导臣的架构方向。臣本身就是 subagent 架构，multi-agent orchestration 就是臣的生存环境
- **用**：在 AGENTS.md 中强化"信任构建"思维——每次心跳不是在"执行任务"，而是在"积累系统对自己的信任"。少犯错 = 更多自主权

#### 3. 约束型 Prompting 实战技巧（🟡 有价值）
- **来源**：同上 ucstrategies 文章
- **核心**：❌ "写得更专业一些" → ✅ "句子≤15词，不用形容词，包含API文档中的一个技术参数"
- **原理**：空泛形容词让模型猜你的偏好，具体约束让模型无歧义执行
- **评**：🟡 与臣已有的 prompt 知识互补，是最直接可落地的改进
- **用**：在 SOUL.md 的沟通风格中补充"约束型表达"原则——给君上提方案时，用具体数字/格式约束代替"更好的/更专业的"

---

## 📋 知识贡献

- [2026-04-02] RCCF框架(Role-Context-Constraint-Format)可融入 TOOLS.md 的 Prompt Engineering 章节
- [2026-04-02] "Agent信任之年"理念可反哺 AGENTS.md 的行为规范——每次执行都在积累信任积分

---

## 🎯 待改进

*待补充*

---

## 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？

---

### 四维评估（必须填写）

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | /5 | 能写成代码/脚本/skill吗？ |
| 🎯 可操作 | /5 | 有具体步骤和示例吗？ |
| ✅ 可验证 | /5 | 有明确的成功标准吗？ |
| 🔄 可复用 | /5 | 其他Agent能直接应用吗？ |

**总分**：/20
- 🔴 < 11：不合格，不记录
- 🟠 11-14：合格，可记录
- 🟡 15-17：良好，优先推荐
- 🟢 18-20：优秀，立即打包为skill
