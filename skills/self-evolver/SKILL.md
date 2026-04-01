---
name: self-evolver
description: 年年自我进化引擎 — 自我监控、Agent匹配、任务分解、决策追踪。让年年持续变强的元技能。
---

# Self-Evolver — 年年自我进化引擎

## 核心模块

### 1. 自我监控 (`self_monitor.py`)
每次心跳自动检查年年的状态：

```bash
python3 <SKILL_DIR>/scripts/self_monitor.py
```

检查项：
- 📚 学习连续性 — 今日是否有学习记录
- 📁 文件健康度 — 关键文件是否完整
- 🔄 错误模式 — 是否重复犯错
- 🤝 协调效率 — 学习汇报数量

### 2. Agent匹配器 (`agent_matcher.py`)
自动分析任务类型，匹配最适合的Agent：

```bash
python3 <SKILL_DIR>/scripts/agent_matcher.py
```

```python
from scripts.agent_matcher import match_agent
result = match_agent("写React组件")
# Returns: {"agent_id": "frontend_dev", "name": "霓裳", "score": 9.2}
```

### 3. 任务分解器 (`task_decomposer.py`)
自动分析任务依赖，生成波次执行计划：

```bash
python3 <SKILL_DIR>/scripts/task_decomposer.py "开发登录系统"
```

输出：
```yaml
waves:
  - wave: 1 (并行)
    - 数据库模型设计 → 玄机
    - JWT配置方案 → 玄机
    - 测试用例框架 → 鉴微
  - wave: 2 (依赖Wave 1)
    - 认证API开发 → 玄机
    - 登录页UI → 霓裳
  - wave: 3 (依赖Wave 2)
    - 集成测试 → 鉴微
```

### 4. 决策追踪器 (`decision_tracker.py`)
记录决策依据，支持复盘：

```bash
python3 <SKILL_DIR>/scripts/decision_tracker.py record "选择React而非Vue" "团队熟悉度+生态"
python3 <SKILL_DIR>/scripts/decision_tracker.py review
```

## 使用场景

- **心跳时**：运行自我监控，发现问题自动修复
- **分配任务时**：运行Agent匹配器，找到最佳Agent
- **复杂项目时**：运行任务分解器，生成波次计划
- **做决策时**：运行决策追踪器，记录依据备复盘

## 文件

- `scripts/self_monitor.py` — 自我监控
- `scripts/agent_matcher.py` — Agent匹配
- `scripts/task_decomposer.py` — 任务分解
- `scripts/decision_tracker.py` — 决策追踪
