# Agent 任务自动分配器使用说明

## 📦 文件位置
```
/Users/narain/.openclaw/workspace/agents/dev_engineer/task_dispatcher.py
```

## 🎯 功能概述

根据任务描述（自然语言）自动分析并分发给最合适的 Agent。

### 核心功能
1. **智能分析** - 通过关键词匹配规则引擎分析任务类型
2. **自动分发** - 选择置信度最高的 Agent
3. **批量处理** - 支持同时分发多个任务
4. **sessions_send 集成** - 支持调用 sessions_send API

## 🤖 Agent 职责映射

| 关键词 | Agent ID | 职责 |
|--------|----------|------|
| 产品/需求/PRD/设计 | `product_manager` | 产品需求分析、PRD 撰写、原型设计 |
| 开发/代码/后端/API | `dev_engineer` | 技术方案、代码实现、后端开发 |
| 测试/质量/Bug | `qa_engineer` | 测试用例、质量保障、Bug 验证 |
| 前端/页面/UI/React | `frontend_dev` | 前端页面、UI 实现、交互开发 |
| 内容/写作/文案 | `chief_cute_officer` | 内容创作、文案写作、活跃气氛 |
| 架构/技术选型 | `taiyi` | 架构设计、技术选型、系统规划 |
| 首席架构/复杂系统 | `tiangong` | 首席架构师、复杂系统设计 |
| 策略/规划/商业 | `lingxi` | 策略顾问、商业分析、决策支持 |
| 协调/沟通/协作 | `zhiming` | 协调员、沟通协作、资源调度 |
| 数据/分析/报表 | `yueying` | 数据分析、报表生成、可视化 |
| 时间/日程/提醒 | `shichen` | 时间管理、日程安排、提醒服务 |

## 💻 使用方法

### 基础用法

```python
from task_dispatcher import TaskDispatcher

# 创建分配器实例
dispatcher = TaskDispatcher()

# 分析任务
task = "帮我设计一个用户登录功能的 PRD"
result = dispatcher.analyze(task)

# 查看结果
print(f"分配给：{result.agent_id}")
print(f"置信度：{result.confidence}")
print(f"匹配关键词：{result.matched_keywords}")
print(f"分发指令：{result.instruction}")
print(f"分发理由：{result.reasoning}")
```

### 带 sessions_send 分发

```python
from task_dispatcher import TaskDispatcher

def sessions_send(agentId: str, message: str):
    """你的 sessions_send 实现"""
    # 调用 OpenClaw sessions_send API
    print(f"发送给 {agentId}: {message}")

dispatcher = TaskDispatcher()
task = "需要开发一个 Python 后端 API 接口"
result = dispatcher.dispatch(task, sessions_send_callback=sessions_send)
```

### 批量分发

```python
tasks = [
    "帮我设计一个用户登录功能的 PRD",
    "需要开发一个 Python 后端 API 接口",
    "请为这个功能编写测试用例",
]

results = dispatcher.dispatch_batch(tasks, sessions_send_callback=sessions_send)
for result in results:
    print(f"任务 → {result.agent_id} (置信度：{result.confidence:.2f})")
```

### 查询 Agent 信息

```python
# 获取单个 Agent 信息
info = dispatcher.get_agent_info("dev_engineer")
print(info)
# 输出：
# {
#     'agent_id': 'dev_engineer',
#     'role_description': '技术方案、代码实现、后端开发、API 开发、系统集成',
#     'keywords': ['开发', '代码', '后端', 'API', ...]
# }

# 列出所有 Agent
all_agents = dispatcher.list_agents()
for agent in all_agents:
    print(f"{agent['agent_id']}: {agent['role_description']}")
```

## 📊 分发结果结构

```python
@dataclass
class DispatchResult:
    agent_id: str              # 目标 Agent ID
    confidence: float          # 置信度 (0.0-1.0)
    matched_keywords: List[str] # 匹配的关键词列表
    instruction: str           # 分发给 Agent 的指令
    reasoning: str             # 分发理由说明
```

## 🔧 高级配置

### 调整权重

在 `AGENT_RULES` 字典中修改每个关键词的权重：

```python
AGENT_RULES = {
    "dev_engineer": (
        "技术方案、代码实现、后端开发、API 开发、系统集成",
        ["开发", "代码", "后端", "API", ...],
        {"开发": 0.9, "代码": 1.0, "后端": 1.0, "API": 1.0, ...}  # 修改这里
    ),
    # ...
}
```

### 添加新 Agent

```python
AGENT_RULES["new_agent"] = (
    "职责描述",
    ["关键词 1", "关键词 2", ...],
    {"关键词 1": 1.0, "关键词 2": 0.8, ...}
)
```

## 🧪 测试

运行内置测试：

```bash
cd /Users/narain/.openclaw/workspace/agents/dev_engineer
python3 task_dispatcher.py
```

## 📝 集成到年年系统

年年可以在协调任务时使用此分配器：

```python
# 在年年的代码中
from agents.dev_engineer.task_dispatcher import TaskDispatcher

class Niannian:
    def __init__(self):
        self.dispatcher = TaskDispatcher()
    
    def handle_task(self, task_description: str):
        """处理主人交代的任务"""
        result = self.dispatcher.dispatch(
            task_description,
            sessions_send_callback=self.sessions_send
        )
        
        # 记录分发日志
        self.log_dispatch(result)
        
        # 等待 Agent 回复并汇总
        return self.wait_and_summarize(result.agent_id)
```

## ⚠️ 注意事项

1. **置信度阈值**：默认置信度 > 0.3 才会实际分发，低于此值会返回协调员处理
2. **关键词匹配**：使用字符串匹配，区分大小写不敏感
3. **多关键词**：匹配到多个关键词会累加得分，选择最高分的 Agent
4. **默认分配**：无匹配时默认分配给 `zhiming`（协调员）

## 🎯 最佳实践

1. **任务描述清晰**：尽量包含明确的职责关键词
2. **复杂任务拆分**：将复合任务拆分为单一职责的子任务
3. **置信度检查**：低置信度时建议人工确认
4. **日志记录**：记录所有分发决策便于优化

---

**创建日期**：2026-03-20  
**作者**：年年 (Niannian)  
**版本**：1.0.0
