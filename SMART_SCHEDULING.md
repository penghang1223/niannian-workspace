# SMART_SCHEDULING.md - 智能调度系统

> 创建时间：2026-03-27
> 维护者：年年（main agent）
> 目标：从"手动分配"升级为"能力匹配+负载均衡"

---

## 🧠 调度架构

### 旧模式（手动）
```
年年收到任务 → 凭感觉分配 → Agent执行 → 汇报
```
问题：不知道谁擅长什么，谁在忙

### 新模式（智能）
```
年年收到任务 → 分析任务类型 → 查询Agent能力 → 匹配最佳Agent → 分配 → 跟踪
```

---

## 📊 能力匹配算法

### 匹配因子

| 因子 | 权重 | 说明 |
|------|------|------|
| **能力分数** | 40% | capability.json 中的能力评分 |
| **经验匹配** | 30% | 是否做过类似任务 |
| **当前负载** | 20% | 是否正在执行其他任务 |
| **学习需求** | 10% | 是否需要通过此任务提升能力 |

### 匹配公式
```
匹配分 = (能力分 × 0.4) + (经验分 × 0.3) + (负载分 × 0.2) + (学习分 × 0.1)

能力分 = 相关能力维度的平均分（1-5）
经验分 = 做过类似任务的数量归一化（0-5）
负载分 = 5 - 当前任务数（空闲=5，满载=0）
学习分 = 如果是弱项且需要提升，加分（0-3）
```

---

## 🔄 调度流程

```
主人下达任务
    ↓
年年分析任务类型
    ↓
确定需要哪些能力维度
    ↓
查询所有Agent的capability.json
    ↓
计算每个Agent的匹配分
    ↓
选择匹配分最高的Agent
    ↓
检查负载是否超限（同时最多3个任务）
    ↓
如果超限 → 选择次优Agent 或 排队等待
    ↓
分配任务 + 记录分配原因
    ↓
跟踪执行进度
    ↓
完成后更新Agent能力评估
```

---

## 📋 Agent 负载状态表

> 每次心跳更新

```yaml
# memory/agent_load.json
{
  "updated_at": "2026-03-27T00:30:00+08:00",
  "agents": {
    "main": {
      "status": "active",
      "current_tasks": ["architecture_upgrade"],
      "task_count": 1,
      "max_tasks": 5
    },
    "product_manager": {
      "status": "idle",
      "current_tasks": [],
      "task_count": 0,
      "max_tasks": 3
    },
    "dev_engineer": {
      "status": "idle",
      "current_tasks": [],
      "task_count": 0,
      "max_tasks": 3
    },
    "qa_engineer": {
      "status": "idle",
      "current_tasks": [],
      "task_count": 0,
      "max_tasks": 3
    },
    "frontend_dev": {
      "status": "idle",
      "current_tasks": [],
      "task_count": 0,
      "max_tasks": 3
    },
    "chief_cute_officer": {
      "status": "idle",
      "current_tasks": [],
      "task_count": 0,
      "max_tasks": 2
    }
  }
}
```

---

## 🎯 任务类型 → Agent 映射

| 任务类型 | 首选Agent | 次选Agent | 能力维度 |
|---------|----------|----------|---------|
| 需求分析 | product_manager | main | requirement_analysis |
| PRD撰写 | product_manager | main | prd_writing |
| 后端开发 | dev_engineer | main | code_implementation |
| 前端开发 | frontend_dev | dev_engineer | ui_implementation |
| 测试设计 | qa_engineer | main | test_design |
| Bug分析 | qa_engineer | dev_engineer | bug_analysis |
| 代码审查 | dev_engineer | qa_engineer | code_review |
| 架构设计 | dev_engineer | main | architecture_design |
| 文档撰写 | main | product_manager | knowledge_coordination |
| 氛围营造 | chief_cute_officer | main | interaction |

---

## 📈 学习路径自动规划

### 触发条件
1. Agent某能力维度 < 3分
2. 有合适的任务可以提升该能力
3. Agent当前负载允许

### 规划流程
```
发现Agent弱项（capability.json）
    ↓
匹配可以提升该能力的任务
    ↓
如果任务紧急 → 分配给高能力Agent
如果任务不紧急 → 分配给弱项Agent（带指导）
    ↓
任务完成后评估是否提升
    ↓
更新capability.json
```

### 示例
```
本尔的 automation 能力只有 2 分
    ↓
发现一个"编写自动化测试脚本"的任务（非紧急）
    ↓
分配给本尔，同时提供学习资源
    ↓
本尔完成后，automation 提升到 3 分
```

---

## ⚠️ 调度边界

### 可以智能调度
- ✅ 常规开发/测试/设计任务
- ✅ 学习型任务（提升Agent能力）
- ✅ 协作型任务（多Agent配合）

### 需要人工干预
- ❌ 紧急/高风险任务（主人指定）
- ❌ 全新领域任务（无经验参考）
- ❌ Agent间冲突（需仲裁）

---

**版本：** v1.0
**最后更新：** 2026-03-27
