# Outbox - 年年指令发送队列

## 目录结构
- `pending/` - 待分发指令
- `done/` - 已分发指令

## 指令格式
每个指令是一个 JSON 文件，格式与 inbox 类似但 from=main

## 分发流程
1. 年年写入指令 → `pending/{task_id}.json`
2. 子Agent心跳 → 检查并读取
3. 执行完成 → 移动到 `done/`
