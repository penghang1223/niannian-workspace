# OpenClaw 架构与使用

> 最后更新：2026-04-08  
> 状态：🆕 初始化  
> 来源：Karpathy Dobby 项目 + 实际使用经验

---

## 📎 来源
- [Karpathy Dobby - OpenClaw Agent](https://newclawtimes.com/articles/andrej-karpathy-dobby-openclaw-agent-replaces-home-software-apps/)
- 实际使用经验

---

## 🎯 核心概念

### OpenClaw 是什么？
**定义**：个人 AI 助理框架，支持多 Agent 协作

**核心理念**：
- ✅ 本地优先（onboard 运行）
- ✅ 多 Agent 协作
- ✅ 技能可扩展
- ✅ 全平台支持（macOS/Linux/Windows）

---

## 🏗️ 架构组成

### 1. Gateway（网关）
**职责**：
- 消息路由
- 认证授权
- 会话管理

**配置**：
```json
{
  "port": 18789,
  "mode": "local",
  "bind": "loopback",
  "auth": {
    "mode": "token"
  }
}
```

---

### 2. Agents（Agent 系统）
**默认 Agent**：
| ID | 名称 | 职责 |
|----|------|------|
| main | 年年 | 协调员 + 主人专属助理 |
| dev_engineer | 玄机 | 后端开发 + 业务逻辑 |
| frontend_dev | 霓裳 | 前端/UI |
| qa_engineer | 鉴微 | 测试/质量 |
| product_manager | 望舒 | 需求/PRD |
| taiyi | 太一 | 战略决策 + 学习研究 |
| lingxi | 灵犀 | 创意策划 + 概念设计 |
| jinghong | 惊鸿 | 内容执行 + 故事构建 |

**Agent 配置**：
```json
{
  "id": "main",
  "default": true,
  "workspace": "~/.openclaw/workspace",
  "heartbeat": {
    "every": "30m",
    "target": "last"
  }
}
```

---

### 3. Skills（技能系统）
**技能类型**：
- 🛠️ 工具型：web_search/browser/exec
- 📚 知识型：小说创作/技术文档
- 🤖 Agent 型：多 Agent 协作流程

**技能位置**：
```
~/.openclaw/skills/          # 内置技能
~/.openclaw/workspace/skills/ # 自定义技能
~/.openclaw/extensions/       # 扩展技能
```

---

### 4. Channels（渠道系统）
**支持渠道**：
- 💬 Feishu（飞书）
- 💬 Telegram
- 💬 Discord
- 💬 WhatsApp
- 💬 Slack

**配置示例**：
```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "accounts": {
        "main": {
          "appId": "cli_xxx",
          "appSecret": "xxx"
        }
      }
    }
  }
}
```

---

## 🔧 核心功能

### 1. 多 Agent 协作
**通信方式**：
```
sessions_send(sessionKey, message)
```

**示例**：
```python
# 年年分配任务给望舒
sessions_send(
    sessionKey="agent:product_manager:main",
    message="[任务] 分析知乎盐选热门题材"
)
```

---

### 2. 心跳系统
**配置**：
```json
{
  "heartbeat": {
    "every": "30m",
    "activeHours": {
      "start": "08:00",
      "end": "23:00"
    }
  }
}
```

**心跳任务**：
- 记忆同步
- 主动消息扫描
- 知识整理
- 日程任务执行

---

### 3. 记忆系统
**记忆类型**：
- 📝 短期记忆：`memory/YYYY-MM-DD.md`
- 🧠 长期记忆：`MEMORY.md`
- 🤖 Agent 记忆：`memory/agents/<agent_id>/`

**记忆提取规则**：
- 决策/教训 → MEMORY.md
- 日常记录 → memory/YYYY-MM-DD.md
- Agent 经验 → memory/agents/<agent_id>/lessons.md

---

### 4. 技能扩展
**安装方式**：
```bash
# 从 clawhub 安装
clawhub install <skill-name>

# 本地开发
~/.openclaw/workspace/skills/<skill-name>/
```

**技能结构**：
```
skill-name/
├── SKILL.md        # 技能说明
├── scripts/        # 脚本文件
├── references/     # 参考资料
└── tests/          # 测试文件
```

---

## 💡 Karpathy 的 Dobby 项目

### 项目概述
**时间**：2026-04-01  
**作者**：Andrej Karpathy  
**目标**：用 1 个 Agent 替代 6 个 App

### 技术实现
```
1. 网络扫描
   → 发现本地设备（Sonos/灯光/安防）
   
2. API 逆向
   → 逆向工程未公开协议
   
3. 自然语言控制
   → "播放爵士乐" → 自动执行
```

### 核心创新
- ✅ **统一入口**：一个 Agent 控制所有设备
- ✅ **自动发现**：设备即插即用
- ✅ **无需 App**：不再需要下载多个 App
- ✅ **自然语言**：说话就能控制

---

## 🎯 对主人的应用

### 1. 小说创作
```
多 Agent 协作：
望舒（产品）→ 选题分析
灵犀（创意）→ 脑洞生成
惊鸿（内容）→ 正文创作
鉴微（测试）→ 审查过稿
年年（协调）→ 汇总汇报
```

### 2. 技术学习
```
知识库建设：
raw/技术文章 → library/技术栈 → output/代码项目
```

### 3. 家庭自动化（参考 Dobby）
```
未来可扩展：
- 扫描家庭网络设备
- 控制智能家居
- 统一语音控制
```

---

## 📋 常用命令

### 安装/配置
```bash
# 安装 OpenClaw
npm install -g openclaw

# 初始化
openclaw init

# 查看状态
openclaw status
```

### 技能管理
```bash
# 安装技能
clawhub install <skill-name>

# 列出技能
clawhub list

# 更新技能
clawhub update <skill-name>
```

### 会话管理
```bash
# 查看会话
openclaw sessions list

# 查看历史
openclaw sessions history <sessionKey>
```

---

## 🔗 相关条目
- [[多 Agent 协作流程]]
- [[技能开发指南]]
- [[记忆系统使用]]
- [[Karpathy 第二大脑]]

---

## 🔄 更新历史
- 2026-04-08: 初始版本（基于 Karpathy Dobby 项目 + 实际使用）
