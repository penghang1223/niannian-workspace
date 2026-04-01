# Inbox - Agent 消息接收队列

## 目录结构
- `pending/` - 待处理消息
- `processing/` - 处理中消息
- `done/` - 已完成消息

## 消息格式
每个消息是一个 JSON 文件，格式见 `AGENT_COMM_V2_DESIGN.md`

## 处理流程
1. Agent 完成任务 → 写入 `pending/{task_id}.json`
2. 年年心跳检查 → 移动到 `processing/`
3. 处理完成 → 移动到 `done/`
4. 定期清理 → 归档到 `archive/`
