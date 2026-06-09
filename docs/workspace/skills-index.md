# 🎯 OpenClaw 技能使用指南

> 最后更新：2026-03-01 | 技能总数：102

---

## 📖 快速开始

### 按场景查找技能

| 我想... | 推荐技能 | 优先级 |
|---------|---------|--------|
| **搜索信息** | `tavily-search`, `brave-api-search` | ⭐⭐⭐ |
| **看 YouTube** | `youtube-watcher` | ⭐⭐⭐ |
| **管理笔记** | `obsidian`, `notion` | ⭐⭐⭐ |
| **语音转文字** | `openai-whisper` | ⭐⭐⭐ |
| **文字转语音** | `mac-tts` (免费) | ⭐⭐⭐ |
| **处理 PDF** | `nano-pdf` | ⭐⭐⭐ |
| **Git 操作** | `git` | ⭐⭐⭐ |
| **Docker** | `docker` | ⭐⭐⭐ |
| **远程 SSH** | `ssh-essentials` | ⭐⭐⭐ |
| **长期记忆** | `elite-longterm-memory` | ⭐⭐⭐ |

---

## 🗂️ 技能分类索引

### 🔍 搜索引擎 (7 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `tavily-search` | Tavily AI 搜索，为 AI 优化 | ✅ 已配置 | ⭐⭐⭐ |
| `brave-api-search` | Brave Search API，隐私保护 | ✅ 已配置 | ⭐⭐⭐ |
| `baidu-search` | 百度搜索，中文内容 | ❌ | ⭐⭐ |
| `ddg-web-search` | DuckDuckGo，隐私搜索 | ❌ | ⭐⭐ |
| `web-search-pro` | 高级网页搜索 | ❌ | ⭐⭐ |
| `multi-search-engine` | 多引擎聚合搜索 | ❌ | ⭐ |
| `file-search` | 本地文件搜索 | ❌ | ⭐⭐ |

**使用示例：**
```
主人：搜索一下 2025 年 AI 发展趋势
→ 年年会使用 tavily-search

主人：用 brave 搜索 AI agent
→ 年年会使用 brave-api-search
```

---

### 📹 视频平台 (6 个)

| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `youtube-watcher` | YouTube 观看和摘要 | Cookie | ⭐⭐⭐ |
| `youtube-transcript` | 获取 YouTube 字幕 | ❌ | ⭐⭐⭐ |
| `youtube-api-skill` | YouTube API 操作 | API Key | ⭐⭐ |
| `youtube-iu` | YouTube 视频总结 | ❌ | ⭐⭐ |
| `video` | 通用视频处理 | ❌ | ⭐⭐ |
| `video-frames` | 提取视频帧 | ❌ | ⭐⭐ |

**使用示例：**
```
主人：总结这个 YouTube 视频：[URL]
→ 年年会使用 youtube-watcher

主人：提取这个视频的字幕
→ 年年会使用 youtube-transcript
```

---

### 🎵 音乐与语音 (10 个)

#### TTS (文字转语音)
| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `mac-tts` | macOS 本地 TTS，免费 | ❌ | ⭐⭐⭐ |
| `edge-tts` | 微软 Edge TTS，免费 | ❌ | ⭐⭐⭐ |
| `openai-tts` | OpenAI TTS，高质量 | ✅ | ⭐⭐ |
| `kokoro-tts` | 本地 TTS，日语优化 | ❌ | ⭐⭐ |

#### 语音处理
| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `openai-whisper` | Whisper 本地语音转文字 | ❌ | ⭐⭐⭐ |
| `openai-whisper-api` | Whisper API 版本 | ✅ | ⭐⭐ |
| `voice-wake-say` | 语音唤醒 | ❌ | ⭐⭐ |
| `jarvis-voice` | Jarvis 语音助手 | ❌ | ⭐⭐ |

#### 音乐生成
| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `music-generation` | AI 音乐生成 | ❌ | ⭐⭐ |
| `elevenlabs-music` | ElevenLabs 音乐 | ✅ | ⭐⭐ |
| `ace-music` | ACE 免费音乐生成 | ❌ | ⭐⭐⭐ |

---

### 📧 邮件与通讯 (9 个)

#### 邮件
| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `imap-smtp-email` | IMAP/SMTP 邮件收发 | 账号密码 | ⭐⭐⭐ |
| `email-daily-summary` | 每日邮件摘要 | 账号密码 | ⭐⭐ |
| `sendclaw-email` | SendClaw 邮件服务 | API Key | ⭐ |
| `porteden-email` | PortEden 安全邮件 | API Key | ⭐⭐ |

#### 即时通讯
| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `telegram` | Telegram 基础功能 | Bot Token | ⭐⭐⭐ |
| `telegram-bot` | Telegram 机器人 | Bot Token | ⭐⭐⭐ |
| `telegram-history` | Telegram 历史记录 | Bot Token | ⭐⭐ |
| `telegram-voice-group` | Telegram 语音组 | Bot Token | ⭐⭐ |
| `discord-chat` | Discord 聊天 | Bot Token | ⭐⭐ |
| `discord-hub` | Discord 管理中心 | Bot Token | ⭐⭐ |
| `discord-voice` | Discord 语音 | Bot Token | ⭐⭐ |
| `slack` | Slack 集成 | Bot Token | ⭐⭐ |

---

### 📅 日历与日程 (3 个)

| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `gcalcli-calendar` | Google Calendar (CLI) | OAuth | ⭐⭐⭐ |
| `lark-calendar` | 飞书日历 | API Key | ⭐⭐ |
| `calendar` | 通用日历 | ❌ | ⭐ |

---

### 🧠 记忆系统 (8 个)

| 技能 | 描述 | 存储 | 推荐度 |
|------|------|------|--------|
| `elite-longterm-memory` | 精英长期记忆 | 本地 | ⭐⭐⭐ |
| `memory-setup` | 记忆系统初始化 | 本地 | ⭐⭐⭐ |
| `memory-hygiene` | 记忆清理维护 | 本地 | ⭐⭐ |
| `neural-memory` | 神经网络记忆 | 本地 | ⭐⭐ |
| `agent-memory` | Agent 记忆管理 | 本地 | ⭐⭐ |
| `memory-tiering` | 记忆分层存储 | 本地 | ⭐⭐ |
| `session-memory` | 会话记忆 | 本地 | ⭐⭐ |
| `memory-qdrant` | Qdrant 向量记忆 | Qdrant | ⭐⭐ |

**推荐组合：** `memory-setup` + `elite-longterm-memory`

---

### 📄 文档处理 (6 个)

#### PDF
| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `nano-pdf` | PDF 编辑和处理 | ❌ | ⭐⭐⭐ |
| `pdf-extract` | PDF 内容提取 | ❌ | ⭐⭐ |
| `pdf-text-extractor` | PDF 文本提取 | ❌ | ⭐⭐ |

#### 文档管理
| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `notion` | Notion 文档管理 | ✅ | ⭐⭐⭐ |
| `obsidian` | Obsidian 笔记 | ❌ | ⭐⭐⭐ |
| `summarize` | 内容总结 | ❌ | ⭐⭐⭐ |

---

### 🔧 开发工具 (11 个)

#### Git
| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `git` | Git 完整版 | SSH/Token | ⭐⭐⭐ |
| `git-essentials` | Git 基础操作 | SSH/Token | ⭐⭐ |
| `git-workflows` | Git 工作流 | SSH/Token | ⭐⭐ |
| `git-helper` | Git 助手 | SSH/Token | ⭐⭐ |
| `github` | GitHub 操作 | Token | ⭐⭐⭐ |

#### Docker
| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `docker` | Docker 完整版 | Docker | ⭐⭐⭐ |
| `docker-essentials` | Docker 基础 | Docker | ⭐⭐ |
| `docker-compose` | Docker Compose | Docker | ⭐⭐ |
| `docker-ctl` | Docker 控制 | Docker | ⭐⭐ |

#### SSH
| 技能 | 描述 | 认证 | 推荐度 |
|------|------|------|--------|
| `ssh-essentials` | SSH 基础操作 | SSH Key | ⭐⭐⭐ |
| `ssh-exec` | SSH 远程执行 | SSH Key | ⭐⭐ |
| `ssh-tunnel` | SSH 隧道 | SSH Key | ⭐⭐ |

---

### 🎨 图像处理 (6 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `antigravity-image-gen` | Antigravity 图像生成 | API Key | ⭐⭐⭐ |
| `gemini-image-simple` | Gemini 图像生成 | API Key | ⭐⭐⭐ |
| `qwen-image` | Qwen 图像生成 | API Key | ⭐⭐ |
| `image-edit` | 图像编辑 | ❌ | ⭐⭐ |
| `best-image-generation` | 最佳图像生成 | ❌ | ⭐⭐ |
| `image-cog` | 图像 COG 处理 | ❌ | ⭐ |

---

### 📊 金融数据 (4 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `stock-watcher` | 股票监控 | ❌ | ⭐⭐⭐ |
| `stock-info-explorer` | 股票信息查询 | ❌ | ⭐⭐⭐ |
| `crypto-market-data` | 加密货币市场数据 | ❌ | ⭐⭐⭐ |
| `crypto-trading-bot` | 加密货币交易机器人 | ❌ | ⭐⭐ |

---

### 📰 新闻资讯 (6 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `news` | 通用新闻 | ❌ | ⭐⭐ |
| `news-summary` | 新闻摘要 | ❌ | ⭐⭐⭐ |
| `cctv-news-fetcher` | CCTV 新闻获取 | ❌ | ⭐⭐ |
| `ai-news-zh` | AI 行业新闻（中文） | ❌ | ⭐⭐⭐ |
| `opennews-mcp` | 开放新闻 MCP | ❌ | ⭐⭐ |
| `tech-news-digest` | 科技新闻摘要 | ❌ | ⭐⭐⭐ |

---

### 🤖 AI 与 MCP (10 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `agent-browser` | 浏览器自动化 | ❌ | ⭐⭐⭐ |
| `browser-use` | Browser Use | ❌ | ⭐⭐⭐ |
| `playwright-mcp` | Playwright MCP | ❌ | ⭐⭐⭐ |
| `atlassian-mcp` | Atlassian (Jira/Confluence) | API Key | ⭐⭐ |
| `clickup-mcp` | ClickUp 项目管理 | API Key | ⭐⭐ |
| `snowflake-mcp` | Snowflake 数据仓库 | API Key | ⭐⭐ |
| `microsoft-ads-mcp` | 微软广告 | API Key | ⭐ |
| `wordpress-mcp` | WordPress | API Key | ⭐⭐ |
| `diagram` | 图表生成 | ❌ | ⭐⭐⭐ |
| `find-skills` | 查找技能 | ❌ | ⭐⭐⭐ |

---

### 🌐 其他工具 (10 个)

| 技能 | 描述 | API Key | 推荐度 |
|------|------|---------|--------|
| `weather` | 天气查询 | ❌ | ⭐⭐⭐ |
| `translate` | 翻译服务 | ❌ | ⭐⭐⭐ |
| `personal-assistant` | 个人助理 | ❌ | ⭐⭐ |
| `x-twitter` | X/Twitter 操作 | API Key | ⭐⭐⭐ |
| `reddit-readonly` | Reddit 只读 | ❌ | ⭐⭐⭐ |
| `telegram` | Telegram | Bot Token | ⭐⭐⭐ |
| `slack` | Slack | Bot Token | ⭐⭐ |
| `lark-calendar` | 飞书日历 | API Key | ⭐⭐ |
| `video-generation` | 视频生成 | API Key | ⭐⭐ |
| `video-subtitles` | 视频字幕 | ❌ | ⭐⭐ |

---

## 🔑 API Key 配置状态

### ✅ 已配置

| 服务 | 环境变量 | 状态 |
|------|---------|------|
| Brave Search | `BRAVE_API_KEY` | ✅ |
| Tavily Search | `TAVILY_API_KEY` | ✅ |

### ⚠️ 待配置

| 服务 | 环境变量 | 获取地址 |
|------|---------|---------|
| Notion | `NOTION_API_KEY` | https://notion.so/my-integrations |
| X/Twitter | `X_API_KEY` 等 | https://developer.twitter.com |
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com |
| Telegram Bot | `TELEGRAM_BOT_TOKEN` | https://t.me/BotFather |
| Discord Bot | `DISCORD_BOT_TOKEN` | https://discord.com/developers |

---

## 💡 使用技巧

### 1. 明确指定技能
```
主人：用 tavily 搜索 AI 发展
主人：用 youtube-watcher 总结这个视频
```

### 2. 自然语言触发
```
主人：搜索一下今天的 AI 新闻
→ 自动选择 tavily-search 或 ai-news-zh

主人：帮我把这个 PDF 转成文字
→ 自动选择 nano-pdf 或 pdf-text-extractor
```

### 3. 组合使用
```
主人：搜索 AI agent 的最新进展，然后总结成笔记保存到 Obsidian
→ tavily-search + summarize + obsidian
```

---

## 🗑️ 建议精简的技能

以下技能功能重叠，可以考虑删除：

### 搜索类（保留 2 个）
- ❌ `baidu-search`
- ❌ `ddg-web-search`
- ❌ `web-search-pro`
- ❌ `multi-search-engine`

### YouTube（保留 2 个）
- ❌ `youtube`
- ❌ `youtube-api-skill`
- ❌ `youtube-iu`

### 记忆（保留 2 个）
- ❌ `neural-memory`
- ❌ `agent-memory`
- ❌ `memory-tiering`
- ❌ `session-memory`
- ❌ `memory-qdrant`

### TTS（保留 2 个）
- ❌ `openai-tts`
- ❌ `kokoro-tts`

### Git（保留 1 个）
- ❌ `git-essentials`
- ❌ `git-workflows`
- ❌ `git-helper`

### Docker（保留 1 个）
- ❌ `docker-essentials`
- ❌ `docker-compose`
- ❌ `docker-ctl`

**精简后总数：约 60 个技能**

---

## 📝 更新日志

- **2026-03-01** - 初始版本，收录 102 个技能
- 后续根据使用情况持续更新

---

**生成时间：** 2026-03-01 10:45
**技能目录：** `~/.openclaw/workspace/skills/`
**配置文件：** `~/.config/openclaw/api_keys`
