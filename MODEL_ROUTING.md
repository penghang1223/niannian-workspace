# MODEL_ROUTING.md - 模型路由策略

> 根据任务复杂度自动选择最优模型，省钱 + 保质量
> 灵感来源：ECC Model Routing

---

## 路由规则

| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| 简单闲聊/问候 | GLM-4.5-Air | 便宜快速，够用 |
| 信息查询/搜索 | GLM-4.5-Air | 不需要深度推理 |
| 日常任务分析 | Qwen3.5-Plus（默认） | 平衡性价比 |
| 文档撰写/总结 | Qwen3.5-Plus | 中文能力强 |
| 复杂架构设计 | GPT-4.1 / O3 | 推理能力强 |
| 代码生成/审查 | Qwen-Coder-Next | 代码专精 |
| 多步骤推理 | O3 | 思维链强 |
| 图片分析 | GLM-4.6V | 多模态 |

## Agent 默认模型配置

| Agent | 模型 | 理由 |
|-------|------|------|
| 年年 (main) | Qwen3.5-Plus | 协调需要平衡能力 |
| 娜尔 (product_manager) | Qwen3.5-Plus | 需求分析需要理解力 |
| 开发工程师 (dev_engineer) | Qwen-Coder-Next | 代码专精 |
| 本尔 (qa_engineer) | Qwen3.5-Plus | 测试逻辑分析 |
| 夕尔 (frontend_dev) | Qwen-Coder-Next | 前端代码 |
| 岁岁 (chief_cute_officer) | GLM-4.5-Air | 简单互动，省钱 |

## 降级策略

当主模型不可用时：
```
Qwen3.5-Plus 不可用 → GLM-4.5 → GPT-4o-Mini
Qwen-Coder-Next 不可用 → GPT-4.1 → Qwen3.5-Plus
O3 不可用 → GPT-4.1 → Qwen3.5-Plus
```

## Token 预算意识

| 场景 | 策略 |
|------|------|
| 心跳检查 | GLM-4.5-Air（最省） |
| Cron 定时任务 | GLM-4.5-Air（简单汇总） |
| 主人主动对话 | 默认模型 |
| 深度研究/学习 | 按需升级到 GPT-4.1/O3 |

---

**原则：能用小模型解决的，不用大模型。质量不够时再升级。**
