# 📡 Agent 互相发消息 - 快速参考卡片

> 创建时间：2026-04-06 10:45 AM  
> 用途：快速查阅如何给其他 Agent 发消息

---

## 🎯 一句话总结

**用 `sessions_send` + `sessionKey` 给其他 Agent 发消息**

```python
sessions_send(
    sessionKey="agent:目标 Agent:main",
    message="[消息类型] 来源：我 | 优先级：🔴 | 内容：xxx"
)
```

---

## 📋 完整示例

### 示例 1：给太一发消息
```python
sessions_send(
    sessionKey="agent:taiyi:main",
    message="[求助] 来源：霓裳 | 目标：太一 | 问题：API 架构设计 | 紧急度：高"
)
```

### 示例 2：给年年汇报进度
```python
sessions_send(
    sessionKey="agent:main:main",
    message="[进度] 来源：玄机 | 任务：功能开发 | 状态：已完成 | 完成度：100%"
)
```

### 示例 3：给灵犀发送创意请求
```python
sessions_send(
    sessionKey="agent:lingxi:main",
    message="[求助] 来源：望舒 | 目标：灵犀 | 需求：漫剧创意方案 | 紧急度：中"
)
```

---

## 📞 Agent sessionKey 速查表

| 接收者 | sessionKey |
|--------|------------|
| **年年** | `agent:main:main` |
| **霓裳** (前端) | `agent:frontend_dev:main` |
| **望舒** (产品) | `agent:product_manager:main` |
| **玄机** (开发) | `agent:dev_engineer:main` |
| **鉴微** (测试) | `agent:qa_engineer:main` |
| **岁岁** (可爱官) | `agent:chief_cute_officer:main` |
| **太一** (战略) | `agent:taiyi:main` |
| **灵犀** (创意) | `agent:lingxi:main` |
| **惊鸿** (内容) | `agent:jinghong:main` |
| **天工** (架构) | `agent:tiangong:main` |
| **司辰** (时间) | `agent:shichen:main` |
| **月影** (视觉) | `agent:yueying:main` |
| **执明** (安全) | `agent:zhiming:main` |

---

## 📝 消息格式模板

### [任务分发]
```
[任务分发] 来源：年年 | 优先级：🔴 | 任务：xxx | 截止：xxx | 验收标准：xxx
```

### [学习汇报]
```
[学习汇报] 来源：Agent 名 | 领域：xxx | 价值：🔴/🟡/🟢 | 核心收获：xxx | 用在哪：xxx | 预期改善：xxx
```

### [求助]
```
[求助] 来源：Agent 名 | 目标：Agent 名 | 问题：xxx | 紧急度：高/中/低
```

### [进度]
```
[进度] 来源：Agent 名 | 任务：xxx | 状态：进行中/已完成/阻塞 | 完成度：xx% | 问题：xxx
```

### [反哺]
```
[反哺] 来源：年年 | 知识点：xxx | 对你的价值：xxx | 建议：xxx
```

### [催促]
```
[催促] 来源：年年 | 任务：xxx | 原截止：xxx | 新截止：xxx | 原因：xxx
```

---

## ⚠️ 常见错误

### ❌ 错误 1：用 agentId 而不是 sessionKey
```python
# 错误！
sessions_send(agentId="taiyi", message="...")

# 正确！
sessions_send(sessionKey="agent:taiyi:main", message="...")
```

### ❌ 错误 2：用 label 而不是 sessionKey
```python
# 错误！
sessions_send(label="agent:taiyi:main", message="...")

# 正确！
sessions_send(sessionKey="agent:taiyi:main", message="...")
```

### ❌ 错误 3：用飞书私信
```python
# 错误！绝对禁止！
feishu_im_user_message(receive_id="ou_xxx", message="...")

# 正确！
sessions_send(sessionKey="agent:taiyi:main", message="...")
```

---

## 🎯 响应时间 SLA

| 优先级 | 颜色 | 响应时间 |
|--------|------|----------|
| P0 | 🔴 | 15 分钟 |
| P1 | 🟠 | 1 小时 |
| P2 | 🟡 | 4 小时 |
| P3 | 🟢 | 24 小时 |

---

## 📚 详细文档

完整通讯规范：`AGENT_COMMUNICATION.md`

---

**打印这张卡片，随时查阅！** 📡
