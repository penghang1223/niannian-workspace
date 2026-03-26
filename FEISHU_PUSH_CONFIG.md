# 📧 飞书推送配置

> 用于 AI 学习日报、系统通知等飞书消息推送

---

## 🔑 飞书 Webhook 配置

### 获取方法

1. **打开飞书** - 进入任意群聊或私聊
2. **添加机器人** - 群设置 → 机器人 → 添加自定义机器人
3. **获取 Webhook** - 复制 Webhook URL
4. **设置环境变量**

### 设置环境变量

**方式 1：临时设置**
```bash
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx'
```

**方式 2：永久设置**（推荐）
```bash
# 添加到 ~/.zshrc
echo "export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx'" >> ~/.zshrc
source ~/.zshrc
```

---

## 📅 定时任务配置

### AI 学习日报（每天 23:30）

```bash
# 编辑 crontab
crontab -e

# 添加以下行
30 23 * * * ~/.openclaw/workspace/ai-learning-feishu-report.sh
```

### AI 学习提醒（每天 00:00）

```bash
# 已配置
0 0 * * * ~/.openclaw/workspace/ai-learning-reminder.sh
```

---

## 📊 推送内容

### AI 学习日报包含：

1. **📚 今日学习总结**
   - 学习的 GitHub 项目
   - 阅读的文档/源码

2. **💡 知识收获**
   - 新技术/新架构
   - 解决的问题

3. **🔧 自我优化**
   - 系统改进
   - 流程优化
   - 知识体系完善

4. **📎 快捷链接**
   - 查看学习计划
   - 查看记忆系统

---

## 🎯 推送时间

| 任务 | 时间 | 内容 |
|------|------|------|
| **学习提醒** | 00:00 | 提醒开始学习 |
| **学习日报** | 23:30 | 总结当天学习 |

---

## 📝 测试推送

```bash
# 测试飞书推送
cd ~/.openclaw/workspace
./ai-learning-feishu-report.sh
```

---

## 🔍 查看推送日志

```bash
# 查看推送历史
cat ~/.openclaw/workspace/ai-learning-log.txt

# 查看 crontab 配置
crontab -l
```

---

**配置完成后，年年会每天自动推送学习报告！** 🎀
