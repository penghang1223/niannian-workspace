# 📧 飞书推送配置指南

> 年年需要通过飞书 API 推送 AI 学习日报给主人

---

## 🎯 当前状态

**年年的飞书渠道**: ⚠️ 未配置

需要主人提供以下信息之一：

### 方式 1：飞书 Open API（推荐）

需要配置：
- `FEISHU_APP_ID` - 飞书应用 ID
- `FEISHU_APP_SECRET` - 飞书应用密钥
- `FEISHU_USER_ID` - 主人的飞书用户 ID

### 方式 2：飞书 Webhook

需要配置：
- `FEISHU_WEBHOOK_URL` - 飞书机器人 Webhook URL

---

## 🔧 配置步骤

### 方式 1：飞书 Open API

**步骤 1：创建飞书应用**

1. 访问 https://open.feishu.cn/
2. 登录飞书开发者后台
3. 创建企业自建应用
4. 获取 App ID 和 App Secret

**步骤 2：添加权限**

应用需要以下权限：
- `im:message` - 发送消息
- `contact:user:readonly` - 读取用户信息

**步骤 3：设置环境变量**

```bash
# 添加到 ~/.zshrc
cat >> ~/.zshrc << 'EOF'

# 飞书配置
export FEISHU_APP_ID='cli_xxxxxxxxxxxxx'
export FEISHU_APP_SECRET='xxxxxxxxxxxxxxxxx'
export FEISHU_USER_ID='ou_xxxxxxxxxxxxx'
EOF

source ~/.zshrc
```

**步骤 4：测试推送**

```bash
cd ~/.openclaw/workspace
./test-feishu-push.sh
```

---

### 方式 2：飞书 Webhook（简单）

**步骤 1：创建群聊机器人**

1. 飞书中创建群聊（可以只拉自己）
2. 群设置 → 机器人 → 添加自定义机器人
3. 复制 Webhook URL

**步骤 2：设置环境变量**

```bash
# 添加到 ~/.zshrc
cat >> ~/.zshrc << 'EOF'

# 飞书 Webhook
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxx'
EOF

source ~/.zshrc
```

**步骤 3：测试推送**

```bash
curl -X POST "$FEISHU_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'
```

---

## 📝 年年的建议

**推荐方式 2（Webhook）**：
- ✅ 配置简单
- ✅ 无需开发应用
- ✅ 立即生效

**方式 1（Open API）**：
- ✅ 功能更强大
- ✅ 可以发送富文本/卡片
- ⚠️ 配置复杂

---

## 🎯 推送内容

配置完成后，年年会每天 23:30 推送：

```
🤖 AI 学习日报 - 2026 年 03 月 09 日

📚 今日学习总结
━━━━━━━━━━━━━━━━━━━━
✅ 已记录 X 条学习日志
✅ 记忆系统：X 行

🎯 学习内容
• GitHub 高星项目学习
• 架构设计研究
• 技术文档阅读

💡 知识收获
• 新技术/新架构
• 解决问题的方法

🔧 自我优化
• 系统架构优化
• 工作流程改进

━━━━━━━━━━━━━━━━━━━━
持续学习，每天进步一点点！💪
```

---

## 💡 快速配置

**最简单的方式**：

1. 飞书创建群聊（只有主人自己）
2. 添加机器人 → 复制 Webhook URL
3. 告诉年年 Webhook URL
4. 年年帮主人配置好！

---

**主人选择哪种方式？** 🎀

年年推荐方式 2（Webhook），5 分钟就能搞定！
