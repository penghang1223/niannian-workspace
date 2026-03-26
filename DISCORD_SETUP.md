# Discord 机器人配置

> 配置指南 | 最后更新：2026-03-02

---

## 📋 需要的信息

### 从 Discord Developer Portal 获取

1. **Bot Token**
   - 访问：https://discord.com/developers/applications
   - 选择你的应用 → Bot → Reset Token（或 Copy Token）
   - 格式：`MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.GJKLmN.opqrstUVWXYZabcdefGHIJKL`

2. **Application ID**
   - 应用页面顶部 → "Application ID"
   - 格式：`1234567890123456789`

3. **服务器 ID (Guild ID)**
   - Discord 中右键服务器 → 复制服务器 ID
   - 需要先开启开发者模式：用户设置 → 高级 → 开发者模式

4. **频道 ID**
   - Discord 中右键频道 → 复制频道 ID
   - 格式：`1234567890123456789`

---

## 🔐 存储凭证

将以下信息告诉年年，年年会帮主人配置：

```
Discord Bot Token: [你的 token]
Application ID: [你的应用 ID]
服务器 ID: [可选，用于特定服务器]
默认频道：#general 或频道 ID
```

---

## 📝 配置后的测试命令

配置完成后，可以用以下命令测试：

```bash
# 发送测试消息
message action=send channel=discord target="#general" message="测试消息"

# 读取最近消息
message action=read channel=discord target="#general" limit=5

# 搜索消息
message action=search channel=discord channelId="频道 ID" query="关键词"
```

---

**状态**：⏳ 等待凭证配置
