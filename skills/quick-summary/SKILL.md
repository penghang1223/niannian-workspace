---
name: quick-summary
description: 快速摘要技能 - 将长文本/URL 内容精简为要点摘要
tags: [productivity, summary, learning]
metadata:
  {
    "openclaw":
      {
        "emoji": "📝",
      },
  }
---

# Quick Summary 技能 📝

将长文本或网页内容快速提取为 3-5 个要点摘要。

## 使用方法

当用户说以下内容时触发：
- "帮我总结一下"
- "提取要点"
- "摘要"

## 执行流程

1. **获取内容**：使用 `web_fetch` 获取 URL 内容，或读取文件内容
2. **调用脚本**：使用 `exec` 运行摘要提取脚本
3. **输出结果**：将结果格式化后返回给用户

## 脚本调用

```bash
node {baseDir}/scripts/extract.js "<text>"
```

## 输出格式

```
📋 内容摘要：

1. [要点一]
2. [要点二]
3. [要点三]

📊 字数：XXX 字 → 压缩至 XXX 字
⏱️ 阅读时间：约 X 分钟
```

## 注意事项

- 网页内容需要先用 `web_fetch` 获取
- 最大处理长度：50,000 字符
- 保持原意，不添加主观判断
