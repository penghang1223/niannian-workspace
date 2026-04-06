# OpenRouter 免费模型切换指南

**创建时间**: 2026-04-06 20:17  
**适用**: 小说创作项目

---

## 🎯 可用免费模型清单

| 模型 ID | 提供商 | 状态 | 适合用途 |
|--------|--------|------|----------|
| `qwen/qwen3.6-plus:free` | 阿里 | ⚠️ Rate Limit | 中文网文创作 |
| `minimax/minimax-m2.5:free` | MiniMax | ✅ 稳定 | 中文网文创作 |
| `z-ai/glm-4.5-air:free` | 智谱 | ✅ 稳定 | 大纲/逻辑 |
| `google/gemma-3-27b-it:free` | Google | ⚠️ Rate Limit | 英文创作 |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta | ⚠️ Rate Limit | 通用 |
| `openrouter/free` | OpenRouter | ✅ 稳定 | 测试用 |

---

## 🔄 切换方法

### 方法 1: API 调用时指定（推荐）

**curl 示例**：

```bash
# 使用 MiniMax M2.5
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "minimax/minimax-m2.5:free", "messages": [...]}'

# 使用 GLM-4.5-Air
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "z-ai/glm-4.5-air:free", "messages": [...]}'

# 使用 Qwen3.6-Plus（如果 rate limit 解除）
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3.6-plus:free", "messages": [...]}'
```

---

### 方法 2: OpenClaw 配置文件

**编辑** `~/.openclaw/openclaw.json`：

```json
{
  "models": {
    "providers": {
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": "sk-or-v1-xxx",
        "api": "openai-completions",
        "models": [
          {
            "id": "minimax/minimax-m2.5:free",
            "name": "MiniMax M2.5 (免费)",
            "reasoning": false,
            "cost": {"input": 0, "output": 0}
          },
          {
            "id": "z-ai/glm-4.5-air:free",
            "name": "GLM-4.5-Air (免费)",
            "reasoning": false,
            "cost": {"input": 0, "output": 0}
          },
          {
            "id": "qwen/qwen3.6-plus:free",
            "name": "Qwen3.6-Plus (免费)",
            "reasoning": true,
            "cost": {"input": 0, "output": 0}
          }
        ]
      }
    },
    "defaults": {
      "model": "minimax/minimax-m2.5:free"
    }
  }
}
```

**切换默认模型**：
```bash
# 修改 defaults.model 字段
# 然后重启 OpenClaw
openclaw gateway restart
```

---

### 方法 3: 运行时命令（推荐）

**在聊天中使用**：

```
/model minimax/minimax-m2.5:free
```

或

```
/model z-ai/glm-4.5-air:free
```

**创建新会话时指定**：

```
/new minimax/minimax-m2.5:free
```

---

## 📋 小说创作推荐配置

### 按 Agent 分配模型

| Agent | 推荐模型 | 切换命令 |
|-------|----------|----------|
| **惊鸿** (章节撰写) | MiniMax M2.5:free | `/model minimax/minimax-m2.5:free` |
| **灵犀** (创意策划) | MiniMax M2.5:free | `/model minimax/minimax-m2.5:free` |
| **望舒** (大纲规划) | GLM-4.5-Air:free | `/model z-ai/glm-4.5-air:free` |
| **鉴微** (质量审查) | GLM-4.5-Air:free | `/model z-ai/glm-4.5-air:free` |
| **岁岁** (润色编辑) | MiniMax M2.5:free | `/model minimax/minimax-m2.5:free` |

---

## ⚠️ Rate Limit 应对策略

### 当前状态（2026-04-06 20:15）

| 模型 | 状态 | 重试建议 |
|------|------|----------|
| Qwen3.6-Plus:free | ❌ 429 Rate Limit | 等 5-10 分钟重试 |
| MiniMax M2.5:free | ✅ 正常 | 可正常使用 |
| GLM-4.5-Air:free | ✅ 正常 | 可正常使用 |
| Llama 3.3:free | ❌ 429 Rate Limit | 等 5-10 分钟重试 |
| Gemma 3:free | ❌ 429 Rate Limit | 等 5-10 分钟重试 |

### 智能切换策略

**方案 A：主备模型**
```
主模型：MiniMax M2.5:free
备用：GLM-4.5-Air:free
```

**方案 B：轮询使用**
```
第 1 章：MiniMax M2.5:free
第 2 章：GLM-4.5-Air:free
第 3 章：MiniMax M2.5:free
...
```

**方案 C：按用途分配**
```
创意/章节：MiniMax M2.5:free
大纲/质检：GLM-4.5-Air:free
```

---

## 🚀 快速开始模板

### Python 脚本示例

```python
import requests

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"

def generate_text(model, prompt):
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一位专业的网文作家。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# 使用 MiniMax 创作章节
chapter = generate_text(
    "minimax/minimax-m2.5:free",
    "写一个战神归来第一章的开头，300 字左右。"
)

# 使用 GLM-4.5-Air 审查
review = generate_text(
    "z-ai/glm-4.5-air:free",
    f"请审查以下小说章节的逻辑和连贯性：{chapter}"
)
```

---

## 📊 成本对比

| 模型 | 成本/万字 | 日产 5 万字 | 月成本 |
|------|----------|------------|--------|
| MiniMax M2.5:free | ¥0 | ¥0 | **¥0** |
| GLM-4.5-Air:free | ¥0 | ¥0 | **¥0** |
| Qwen3.6-Plus:free | ¥0 | ¥0 | **¥0** |
| GLM-4.5 (付费) | ¥0.5 | ¥25 | ¥750 |
| GPT-4o | ¥2.0 | ¥100 | ¥3000 |

**月节省**: ¥750-3000（使用免费模型）

---

## 🎯 最佳实践

1. **优先使用 MiniMax M2.5:free** - 中文创作质量最好
2. **备用 GLM-4.5-Air:free** - 逻辑审查/大纲规划
3. **避开高峰期** - Qwen3.6-Plus 晚上 8-10 点容易 rate limit
4. **批量创作** - 一次生成多章，减少 API 调用次数
5. **本地缓存** - 保存已生成内容，避免重复生成

---

**文档完成** ✅  
**下次更新**: 2026-04-07 或模型有变化时
