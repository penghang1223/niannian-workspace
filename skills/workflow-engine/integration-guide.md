# 工作流引擎 - 实际 Agent 集成指南

> 创建时间：2026-04-08 17:10  
> 用途：将工作流引擎集成到 OpenClaw Agent 系统  
> 版本：v1.0

---

## 🎯 集成目标

将工作流引擎集成到 OpenClaw 的 Agent 系统中，实现：
- ✅ 自动触发下一环节
- ✅ 自动进度监控
- ✅ 自动超时催促
- ✅ 自动决策分支

---

## 📁 集成位置

### 年年（main Agent）

**文件位置**：`~/.openclaw/agents/main/` 或 `~/.openclaw/workspace/agents/main/`

**需要修改的文件**：
- `message_handler.py` - 消息处理
- `callbacks.py` - 回调函数

---

## 🔧 集成步骤

### 步骤 1：导入工作流模块

在年子的主模块中添加：

```python
# 导入工作流引擎
import sys
import os

workflow_engine_path = os.path.join(
    os.path.dirname(__file__), 
    '../../skills/workflow-engine'
)
sys.path.insert(0, workflow_engine_path)

from workflow_integration import (
    workflow_integration,
    on_nianian_message,
    on_wangshu_complete,
    on_lingxi_complete,
    on_jinghong_complete,
    on_jianwei_complete
)

# 设置实际回调
workflow_integration.send_message_callback = lambda target, msg: sessions_send(sessionKey=target, message=msg)
workflow_integration.send_card_callback = lambda content: message(action="send", message=content)
```

---

### 步骤 2：修改消息处理

在年子的消息处理函数中：

```python
def handle_message(message: str, sender: str):
    """处理主人消息"""
    
    # 检查工作流相关命令
    workflow_keywords = ["启动", "工作流", "进度", "状态", "确认", "继续", "催促"]
    
    if any(keyword in message for keyword in workflow_keywords):
        # 交给工作流引擎处理
        result = on_nianian_message(message, sender)
        
        if "error" not in result:
            return result
    
    # 否则按正常逻辑处理
    return normal_handle(message, sender)
```

---

### 步骤 3：修改 Agent 完成回调

在每个 Agent 的完成回调中：

```python
# 望舒完成回调
def on_wangshu_task_complete(output: dict):
    """望舒完成任务"""
    # 先执行原有逻辑
    normal_wangshu_complete(output)
    
    # 再执行工作流逻辑
    result = workflow_integration.on_agent_task_complete(
        project_id=get_current_project_id(),
        agent="望舒",
        output=output
    )
    
    return result

# 灵犀完成回调
def on_lingxi_task_complete(output: dict):
    """灵犀完成任务"""
    normal_lingxi_complete(output)
    return workflow_integration.on_agent_task_complete(
        project_id=get_current_project_id(),
        agent="灵犀",
        output=output
    )

# 惊鸿完成回调
def on_jinghong_task_complete(output: dict):
    """惊鸿完成任务"""
    normal_jinghong_complete(output)
    return workflow_integration.on_agent_task_complete(
        project_id=get_current_project_id(),
        agent="惊鸿",
        output=output
    )

# 鉴微完成回调
def on_jianwei_task_complete(output: dict):
    """鉴微完成任务"""
    normal_jianwei_complete(output)
    return workflow_integration.on_agent_task_complete(
        project_id=get_current_project_id(),
        agent="鉴微",
        output=output
    )
```

---

### 步骤 4：获取当前项目 ID

```python
# 全局变量存储当前项目
_current_project_id = None

def get_current_project_id() -> str:
    """获取当前项目 ID"""
    return _current_project_id

def set_current_project_id(project_id: str):
    """设置当前项目 ID"""
    global _current_project_id
    _current_project_id = project_id
```

---

## 📋 完整示例

### 示例：年年消息处理

```python
# ~/.openclaw/agents/main/message_handler.py

from workflow_integration import workflow_integration, on_nianian_message

def handle_user_message(message: str, sender: str) -> dict:
    """
    处理用户消息
    
    Args:
        message: 用户消息内容
        sender: 发送者 ID
    
    Returns:
        处理结果字典
    """
    # 1. 检查工作流命令
    if is_workflow_command(message):
        result = on_nianian_message(message, sender)
        
        if "error" not in result:
            # 更新当前项目 ID
            if "project_id" in result:
                set_current_project_id(result["project_id"])
            return result
    
    # 2. 正常处理
    return normal_handle(message, sender)

def is_workflow_command(message: str) -> bool:
    """判断是否是工作流命令"""
    keywords = [
        "启动小说创作",
        "启动工作流",
        "查询进度",
        "查询状态",
        "确认继续",
        "继续",
        "催促"
    ]
    return any(keyword in message for keyword in keywords)
```

---

### 示例：望舒 Agent 完成回调

```python
# ~/.openclaw/agents/product_manager/callbacks.py

from workflow_integration import workflow_integration

def on_task_complete(output: dict) -> dict:
    """
    任务完成回调
    
    Args:
        output: 任务输出
    
    Returns:
        处理结果
    """
    # 1. 执行原有逻辑
    result = normal_complete(output)
    
    # 2. 执行工作流逻辑
    project_id = get_current_project_id()
    if project_id:
        workflow_result = workflow_integration.on_agent_task_complete(
            project_id=project_id,
            agent="望舒",
            output=output
        )
        
        # 合并结果
        result.update(workflow_result)
    
    return result
```

---

## 🧪 测试验证

### 测试 1：启动工作流

**操作**：
```
启动小说创作《测试小说》
```

**预期结果**：
```
📤 发送消息给 望舒：[工作流] 选题定方向 - 开始执行：分析题材数据
📋 发送卡片：✅ **工作流启动** 项目：测试小说 ...
```

### 测试 2：查询进度

**操作**：
```
查询进度
```

**预期结果**：
```
📊 项目状态
项目：测试小说
当前阶段：Wave-1 选题定方向
总体进度：50%
当前步骤：2/4
```

### 测试 3：确认继续

**操作**：
```
确认继续
```

**预期结果**：
```
📤 发送消息给 惊鸿：[工作流] 大纲 + 人设 - 开始执行：生成大纲 + 角色卡
📋 发送卡片：✅ **Wave-2 启动** 阶段：大纲 + 人设 ...
```

---

## ⚠️ 注意事项

### 1. 回调函数设置

必须在启动前设置回调函数：

```python
workflow_integration.send_message_callback = lambda target, msg: sessions_send(sessionKey=target, message=msg)
workflow_integration.send_card_callback = lambda content: message(action="send", message=content)
```

### 2. 项目 ID 管理

确保在启动工作流时设置项目 ID：

```python
def start_workflow(novel_name: str):
    project_id = f"novel_{int(time.time())}"
    set_current_project_id(project_id)
    return workflow_integration.start_novel_workflow(project_id, novel_name, owner_id)
```

### 3. 错误处理

确保处理工作流引擎的错误：

```python
result = on_nianian_message(message, sender)

if "error" in result:
    # 工作流引擎错误，降级到正常处理
    return normal_handle(message, sender)
```

---

## 🎯 集成检查清单

- [ ] 导入工作流模块
- [ ] 设置回调函数
- [ ] 修改消息处理
- [ ] 修改 Agent 完成回调
- [ ] 添加项目 ID 管理
- [ ] 测试启动工作流
- [ ] 测试查询进度
- [ ] 测试确认继续
- [ ] 测试超时监控
- [ ] 测试决策节点

---

## 📞 集成支持

**创建者**：年年 🎀  
**创建时间**：2026-04-08 17:10  
**版本**：v1.0

---

**工作流引擎 - 让多 Agent 协作自动化！** 🚀
