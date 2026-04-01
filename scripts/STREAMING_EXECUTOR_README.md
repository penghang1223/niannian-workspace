# StreamingToolExecutor - 流式并行工具执行器

参考 Claude Code 的 StreamingToolExecutor 实现，实现了高效的流式工具并行执行机制。

## 核心特性

### 1. 流式检测
- 从 LLM 流式响应中实时检测 `tool_use` blocks
- 不等待完整响应，边收边执行
- 支持复杂的 JSON 流解析

### 2. 并发控制
- 并发安全的工具自动并行执行
- 非并发工具独占执行（如 Bash 命令）
- 结果按工具接收顺序返回

### 3. 错误隔离
- 一个工具失败不影响其他并发工具
- Bash 错误可选级联取消其他 Bash 工具
- 优雅的错误处理和恢复

### 4. 高级功能
- 超时控制和自动重试
- 进度消息实时推送
- 配置化控制各项行为

## 架构设计

```
LLM Stream → StreamingToolDetector → StreamingToolExecutor → Parallel Execution
     ↓                    ↓                      ↓
  tool_use           JSON Parsing            Concurrency
  blocks            → ToolBlocks           Control & Results
```

## 使用方法

### 基础使用
```python
from streaming_executor import StreamingToolExecutor, ToolDefinition, create_tool_block

# 定义工具
tools = {
    "read_file": ToolDefinition(
        name="read_file",
        executor=read_file_executor,
        is_concurrency_safe=True,  # 可并行
    ),
    "bash": ToolDefinition(
        name="bash", 
        executor=bash_executor,
        is_concurrency_safe=False,  # 不可并行
    )
}

# 创建执行器
executor = StreamingToolExecutor(tools)

# 添加工具调用
executor.add_tool(create_tool_block("read_file", {"file_path": "/path"}))

# 流式获取结果
async for update in executor.get_results():
    if update.result:
        print(f"结果: {update.result.content}")
```

### 流式检测使用
```python
from streaming_executor import StreamingToolDetector

# 创建检测器
detector = StreamingToolDetector(executor)

# 模拟从 LLM 流式响应中接收数据
for chunk in llm_stream:
    detected_tools = detector.feed(chunk)  # 自动添加到执行器
    for tool in detected_tools:
        print(f"检测到工具: {tool.name}")
```

## 配置选项

配置文件: `streaming_config.json`

```json
{
  "max_concurrent_tools": 5,           // 最大并行数
  "tool_timeout_seconds": 120,         // 工具超时时间
  "retry_max_attempts": 2,             // 重试次数
  "error_isolation": true,             // 错误隔离
  "bash_error_cascades": true,         // Bash 错误级联
  "progress_enabled": true             // 启用进度推送
}
```

## 参考 Claude Code 实现特点

1. **流式优先**: 边接收边执行，提高响应速度
2. **并发智能**: 根据工具类型自动决定并行策略
3. **错误韧性**: 一个工具失败不影响整体流程
4. **资源保护**: 防止并发冲突和资源竞争

## 示例输出解读

- `🟢并发`: 并发安全工具，可与其他并发工具并行
- `🔴独占`: 非并发安全工具，独占执行
- `✅成功/❌失败`: 执行结果状态
- 时间戳显示实际执行顺序和并发效果

## 应用场景

- LLM 工具调用并行执行
- API 客户端批量请求
- 文件操作批处理
- 任何需要流式处理和并行执行的场景

该实现完全兼容 Claude Code 的设计理念，同时针对 Python 生态进行了优化。