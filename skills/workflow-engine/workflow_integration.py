#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流引擎 - Agent 系统集成模块
将工作流引擎集成到 OpenClaw Agent 系统
"""

import sys
import os

# 添加工作流引擎路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'workflow-engine'))

from workflow_engine import (
    WorkflowEngine,
    create_wave_1,
    create_wave_2,
    create_wave_3,
    WorkflowInstance
)


class WorkflowIntegration:
    """工作流引擎与 Agent 系统集成类"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
        self.active_projects = {}
        
        # 注册预定义工作流
        self.engine.register_workflow("wave_1", create_wave_1())
        self.engine.register_workflow("wave_2", create_wave_2())
        self.engine.register_workflow("wave_3", create_wave_3())
        
        # 设置回调函数
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """设置回调函数"""
        # 设置消息发送回调
        self.engine.send_message_callback = self.send_message
        self.engine.send_card_callback = self.send_card
        self.engine.progress_tracker.send_message_callback = self.send_message
        self.engine.progress_tracker.send_card_callback = self.send_card
    
    def send_message(self, target: str, message: str):
        """发送消息回调"""
        # 使用 sessions_send 发送消息
        try:
            from sessions_send import sessions_send
            sessions_send(sessionKey=target, message=message)
            print(f"📤 已发送消息给 {target}: {message[:50]}...")
        except ImportError:
            print(f"📤 [模拟] 发送消息给 {target}: {message}")
    
    def send_card(self, content: str):
        """发送卡片回调"""
        # 使用 message 发送卡片
        try:
            from message import message
            message(action="send", message=content)
            print(f"📋 已发送卡片：{content[:50]}...")
        except ImportError:
            print(f"📋 [模拟] 发送卡片：{content}")
    
    def start_novel_workflow(self, project_id: str, novel_name: str, owner_id: str):
        """启动小说创作工作流"""
        # 创建工作流实例
        self.active_projects[project_id] = {
            "novel_name": novel_name,
            "owner_id": owner_id,
            "current_wave": "wave_1",
            "status": "starting"
        }
        
        # 启动 Wave-1
        result = self.engine.start_workflow(
            workflow_name="wave_1",
            project_id=project_id,
            context={
                "novel_name": novel_name,
                "owner_id": owner_id
            }
        )
        
        # 发送启动通知
        self.send_card(
            f"✅ **工作流启动**\n\n"
            f"项目：{novel_name}\n"
            f"ID: {project_id}\n"
            f"阶段：Wave-1 选题定方向\n"
            f"状态：{result['status']}"
        )
        
        return result
    
    def on_agent_task_complete(self, project_id: str, agent: str, output: dict):
        """Agent 任务完成回调"""
        if project_id not in self.active_projects:
            return {"error": f"Project {project_id} not found"}
        
        # 调用工作流引擎
        result = self.engine.on_step_complete(agent=agent, output=output)
        
        # 更新项目状态
        if self.engine.active_instance:
            workflow = self.engine.active_instance.workflow
            self.active_projects[project_id]["current_step"] = workflow.current_step_index
            self.active_projects[project_id]["status"] = workflow.status.value
        
        return result
    
    def on_owner_confirm(self, project_id: str):
        """主人确认回调"""
        if project_id not in self.active_projects:
            return {"error": f"Project {project_id} not found"}
        
        project = self.active_projects[project_id]
        current_wave = project["current_wave"]
        
        # 根据当前波次，启动下一波次
        if current_wave == "wave_1":
            # Wave-1 完成，启动 Wave-2
            project["current_wave"] = "wave_2"
            result = self.engine.start_workflow(
                workflow_name="wave_2",
                project_id=project_id,
                context=project
            )
            self.send_card(
                f"✅ **Wave-2 启动**\n\n"
                f"项目：{project['novel_name']}\n"
                f"阶段：大纲 + 人设\n"
                f"状态：{result['status']}"
            )
            return result
        
        elif current_wave == "wave_2":
            # Wave-2 完成，启动 Wave-3
            project["current_wave"] = "wave_3"
            result = self.engine.start_workflow(
                workflow_name="wave_3",
                project_id=project_id,
                context=project
            )
            self.send_card(
                f"✅ **Wave-3 启动**\n\n"
                f"项目：{project['novel_name']}\n"
                f"阶段：章节创作（12 章循环）\n"
                f"状态：{result['status']}"
            )
            return result
        
        elif current_wave == "wave_3":
            # Wave-3 完成，项目完成
            project["status"] = "completed"
            self.send_card(
                f"🎉 **项目完成**\n\n"
                f"项目：{project['novel_name']}\n"
                f"总章节：12 章\n"
                f"状态：已完成"
            )
            return {"status": "completed"}
        
        return {"error": f"Unknown wave: {current_wave}"}
    
    def get_project_status(self, project_id: str) -> dict:
        """获取项目状态"""
        if project_id not in self.active_projects:
            return {"error": f"Project {project_id} not found"}
        
        project = self.active_projects[project_id]
        
        # 获取工作流进度
        if self.engine.active_instance and self.engine.active_instance.project_id == project_id:
            workflow = self.engine.active_instance.workflow
            return {
                "project_id": project_id,
                "novel_name": project["novel_name"],
                "current_wave": project["current_wave"],
                "workflow_status": workflow.status.value,
                "current_step": workflow.current_step_index,
                "total_steps": len(workflow.steps),
                "progress": f"{workflow.current_step_index}/{len(workflow.steps)}"
            }
        
        return {
            "project_id": project_id,
            "novel_name": project["novel_name"],
            "current_wave": project["current_wave"],
            "status": project["status"]
        }
    
    def list_projects(self) -> list:
        """列出所有项目"""
        return [
            {
                "project_id": pid,
                "novel_name": p["novel_name"],
                "current_wave": p["current_wave"],
                "status": p["status"]
            }
            for pid, p in self.active_projects.items()
        ]


# ==================== 全局单例 ====================

# 创建工作流集成单例
workflow_integration = WorkflowIntegration()


# ==================== Agent 回调函数 ====================

def on_nianian_message(message: str, sender: str):
    """
    年年消息处理回调
    当收到主人消息时调用
    """
    # 检查是否是启动工作流命令
    if "启动小说创作" in message or "启动工作流" in message:
        # 提取小说名（如果有）
        novel_name = "我在修仙界开网约车"  # 默认值
        if "《" in message and "》" in message:
            novel_name = message[message.index("《")+1:message.index("》")]
        
        # 生成项目 ID
        import time
        project_id = f"novel_{int(time.time())}"
        
        # 启动工作流
        result = workflow_integration.start_novel_workflow(
            project_id=project_id,
            novel_name=novel_name,
            owner_id=sender
        )
        
        return result
    
    # 检查是否是确认命令
    elif "确认" in message or "继续" in message:
        # 获取当前项目
        projects = workflow_integration.list_projects()
        if projects:
            # 取第一个项目进行确认
            project_id = projects[0]["project_id"]
            result = workflow_integration.on_owner_confirm(project_id)
            return result
    
    # 检查是否是状态查询
    elif "状态" in message or "进度" in message:
        projects = workflow_integration.list_projects()
        if projects:
            project_id = projects[0]["project_id"]
            status = workflow_integration.get_project_status(project_id)
            return status
    
    return {"error": "Unknown command"}


def on_wangshu_complete(output: dict):
    """望舒完成任务回调"""
    # 获取当前项目
    projects = workflow_integration.list_projects()
    if projects:
        project_id = projects[0]["project_id"]
        return workflow_integration.on_agent_task_complete(project_id, "望舒", output)
    return {"error": "No active project"}


def on_lingxi_complete(output: dict):
    """灵犀完成任务回调"""
    projects = workflow_integration.list_projects()
    if projects:
        project_id = projects[0]["project_id"]
        return workflow_integration.on_agent_task_complete(project_id, "灵犀", output)
    return {"error": "No active project"}


def on_jinghong_complete(output: dict):
    """惊鸿完成任务回调"""
    projects = workflow_integration.list_projects()
    if projects:
        project_id = projects[0]["project_id"]
        return workflow_integration.on_agent_task_complete(project_id, "惊鸿", output)
    return {"error": "No active project"}


def on_jianwei_complete(output: dict):
    """鉴微完成任务回调"""
    projects = workflow_integration.list_projects()
    if projects:
        project_id = projects[0]["project_id"]
        return workflow_integration.on_agent_task_complete(project_id, "鉴微", output)
    return {"error": "No active project"}


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("工作流引擎 - Agent 系统集成测试")
    print("=" * 60)
    
    # 测试启动工作流
    print("\n1. 测试启动工作流")
    result = on_nianian_message("启动小说创作《测试小说》", "owner_001")
    print(f"启动结果：{result}")
    
    # 测试望舒完成
    print("\n2. 测试望舒完成")
    result = on_wangshu_complete({"prd": "PRD-v1.0", "competitor_analysis": {}})
    print(f"望舒完成：{result}")
    
    # 测试灵犀完成
    print("\n3. 测试灵犀完成")
    result = on_lingxi_complete({"creative_ideas": ["创意 1", "创意 2"]})
    print(f"灵犀完成：{result}")
    
    # 测试状态查询
    print("\n4. 测试状态查询")
    result = on_nianian_message("查询状态", "owner_001")
    print(f"状态：{result}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
