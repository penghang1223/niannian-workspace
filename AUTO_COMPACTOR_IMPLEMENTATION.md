# AutoCompactor - 长对话自动压缩机制

基于 Claude Code autocompact 机制实现的 Python 版本，用于自动监控和压缩长对话，防止超出上下文窗口限制。

## 🎯 核心功能

- **Token 监控**: 实时估算对话 token 使用量
- **自动压缩**: 超过阈值时自动触发压缩
- **LLM 摘要**: 调用 LLM 生成高质量历史摘要
- **消息替换**: 用摘要替换旧消息，保留近期上下文
- **PTL 重试**: Prompt-too-long 时自动截断重试
- **灵活配置**: 支持多种压缩策略配置

## 📁 文件结构

```
workspace/
├── scripts/auto_compactor.py          # 核心实现
├── auto_compact_config.json          # 配置文件
├── scripts/auto_compactor_example.py # 使用示例
└── README.md                         # 本文档
```

## 🔧 配置说明

配置文件 `auto_compact_config.json` 包含以下关键参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_context_tokens` | 200000 | 上下文窗口上限 |
| `compact_threshold_ratio` | 0.80 | 触发压缩的 token 比例 |
| `preserve_last_n_messages` | 6 | 压缩后保留最近消息数 |
| `max_summary_output_tokens` | 4096 | 摘要生成最大输出 token |
| `max_ptl_retries` | 3 | PTL 错误最大重试次数 |
| `model` | "claude-sonnet-4-20250514" | 摘要生成模型 |
| `api_key_env` | "ANTHROPIC_API_KEY" | API key 环境变量 |

## 🚀 使用方法

### 1. 基础集成

```python
from scripts.auto_compactor import AutoCompactor

# 初始化
compactor = AutoCompactor(config_path="auto_compact_config.json")

# 在对话循环中每轮检查
messages, result = compactor.check_and_compact(messages, system_prompt)
if result:
    print(f"压缩完成: {result.pre_compact_tokens} → {result.post_compact_tokens}")
```

### 2. 自定义摘要指令

```python
messages, result = compactor.check_and_compact(
    messages, 
    system_prompt,
    custom_instructions="关注代码变更和错误修复过程"
)
```

### 3. 强制压缩

```python
from scripts.auto_compactor import compact_conversation

# 不检查阈值，强制执行压缩
messages, result = compact_conversation(
    messages, 
    config_path="auto_compact_config.json", 
    force=True
)
```

### 4. 上下文分析

```python
# 仅分析 token 分布，不执行压缩
usage = compactor.get_token_usage(messages)
stats = compactor.analyze_context(messages)
```

## 🔍 实现细节

### Token 估算
- 基于 Claude Code 的 4 bytes/token 比率进行粗略估算
- 支持多种消息类型（text, tool_use, tool_result 等）
- 无需调用 API，快速实时计算

### 摘要生成提示词
- 参考 Claude Code 的 `getCompactPrompt` 实现
- 包含 `<analysis>` 草稿区和 `<summary>` 结构化摘要
- 自动生成包含请求意图、技术概念、文件变更等的详细摘要

### PTL 重试机制
- 当压缩请求本身超出 token 限制时自动处理
- 参考 Claude Code 的 `truncateHeadForPTLRetry`
- 每次重试截断 20% 最旧消息，最多重试 3 次

### 消息结构
压缩后的消息结构遵循 Claude Code 模式：
```
[compact_boundary_marker, summary_message, preserved_recent_messages...]
```

## 🧪 测试与验证

```bash
# 运行演示
python scripts/auto_compactor.py --demo

# 运行使用示例
python scripts/auto_compactor_example.py basic

# 分析上下文
python scripts/auto_compactor_example.py analyze

# 模拟对话循环
python scripts/auto_compactor_example.py loop
```

## 🛠️ 环境要求

- Python 3.8+
- Anthropic API key（用于摘要生成）
- 网络访问权限（调用 LLM API）

## 📊 统计信息

`compactor.stats` 提供以下统计：
- `total_compactions`: 总压缩次数
- `total_tokens_saved`: 节省的 token 总数  
- `total_retries`: PTL 重试总次数

## 🎨 设计哲学

- **参考 Claude Code**: 严格遵循原版 autocompact 的设计理念和实现细节
- **最小依赖**: 仅使用标准库和 urllib，易于集成
- **灵活配置**: 支持各种压缩策略调整
- **健壮重试**: 完善的错误处理和恢复机制
- **透明过程**: 详细的日志和统计信息

## 🔗 与 Claude Code 的对应关系

| Claude Code | AutoCompactor |
|-------------|---------------|
| `compactConversation` | `_compact_messages` |
| `getCompactPrompt` | `_build_summary_prompt` |
| `formatCompactSummary` | `_format_summary` |
| `truncateHeadForPTLRetry` | `_truncate_head_for_ptl_retry` |
| `buildPostCompactMessages` | `_build_compacted_messages` |

---

实现完成！AutoCompactor 提供了与 Claude Code autocompact 相同的核心功能，包括：
✅ Token 监控和阈值触发
✅ LLM 驱动的高质量摘要生成  
✅ PTL 重试机制
✅ 灵活配置
✅ 完整的统计和分析功能