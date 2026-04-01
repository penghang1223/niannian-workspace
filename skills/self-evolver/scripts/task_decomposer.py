"""
任务分解器 — 自动分析任务依赖，生成波次执行计划
Usage: python3 task_decomposer.py "开发登录系统"
"""

import sys
import json
from pathlib import Path

# 关键词 → Agent 映射
KEYWORD_AGENT_MAP = {
    # 技术类
    "前端": "frontend_dev", "页面": "frontend_dev", "UI": "frontend_dev", "CSS": "frontend_dev",
    "React": "frontend_dev", "Vue": "frontend_dev", "组件": "frontend_dev",
    "后端": "dev_engineer", "API": "dev_engineer", "数据库": "dev_engineer",
    "Python": "dev_engineer", "Node": "dev_engineer", "脚本": "dev_engineer",
    "测试": "qa_engineer", "TDD": "qa_engineer", "验证": "qa_engineer",
    "安全": "zhiming", "审计": "zhiming", "漏洞": "zhiming",
    # 产品类
    "需求": "product_manager", "PRD": "product_manager", "分析": "product_manager",
    "竞品": "product_manager", "用户": "product_manager",
    # 内容类
    "文案": "chief_cute_officer", "创意": "chief_cute_officer", "营销": "chief_cute_officer",
    "小说": "jinghong", "故事": "jinghong", "角色": "jinghong",
    "视觉": "lingxi", "图片": "lingxi", "AI生成": "lingxi",
    # 数据类
    "数据": "yueying", "分析": "yueying", "统计": "yueying",
}

# 依赖关系模板
DEPENDENCY_TEMPLATES = {
    "开发登录系统": {
        "wave_1": [("数据库模型设计", "dev_engineer"), ("JWT配置方案", "dev_engineer"), ("测试用例框架", "qa_engineer")],
        "wave_2": [("认证API开发", "dev_engineer"), ("登录页UI", "frontend_dev")],
        "wave_3": [("集成测试", "qa_engineer")],
    },
    "电商网站": {
        "wave_1": [("数据库设计", "dev_engineer"), ("UI原型", "frontend_dev"), ("API接口设计", "dev_engineer")],
        "wave_2": [("商品模块", "dev_engineer"), ("购物车模块", "dev_engineer"), ("商品页UI", "frontend_dev")],
        "wave_3": [("订单模块", "dev_engineer"), ("支付集成", "dev_engineer"), ("订单页UI", "frontend_dev")],
        "wave_4": [("集成测试", "qa_engineer"), ("性能测试", "qa_engineer")],
    },
}


def decompose(task_description: str) -> dict:
    """
    分解任务，生成波次执行计划
    
    Args:
        task_description: 任务描述
    
    Returns:
        波次执行计划
    """
    # 检查是否有预设模板
    for template_name, template in DEPENDENCY_TEMPLATES.items():
        if template_name in task_description:
            return _format_plan(template_name, template)
    
    # 通用分解：根据关键词推断
    waves = _generic_decompose(task_description)
    return _format_plan(task_description, waves)


def _generic_decompose(task: str) -> dict:
    """通用任务分解"""
    wave_1 = []
    wave_2 = []
    wave_3 = []
    
    # 简单规则：设计/规划先于开发，开发先于测试
    if any(k in task for k in ["设计", "规划", "需求"]):
        wave_1.append(("需求分析", "product_manager"))
    
    if any(k in task for k in ["数据库", "模型", "架构"]):
        wave_1.append(("架构设计", "tiangong"))
    
    if any(k in task for k in ["前端", "页面", "UI"]):
        wave_2.append(("前端开发", "frontend_dev"))
    
    if any(k in task for k in ["后端", "API", "服务"]):
        wave_2.append(("后端开发", "dev_engineer"))
    
    if any(k in task for k in ["测试", "验证"]):
        wave_3.append(("测试验证", "qa_engineer"))
    
    # 默认：单波次，全给玄机
    if not wave_1 and not wave_2:
        wave_1.append((task, "dev_engineer"))
    
    return {"wave_1": wave_1, "wave_2": wave_2, "wave_3": wave_3}


def _format_plan(task: str, waves: dict) -> dict:
    """格式化执行计划"""
    agent_names = {
        "frontend_dev": "霓裳", "dev_engineer": "玄机", "qa_engineer": "鉴微",
        "product_manager": "望舒", "chief_cute_officer": "岁岁", "taiyi": "太一",
        "lingxi": "灵犀", "jinghong": "惊鸿", "tiangong": "天工", "yueying": "月影",
        "zhiming": "执明",
    }
    
    plan = {"task": task, "waves": []}
    
    for wave_name, tasks in sorted(waves.items()):
        if not tasks:
            continue
        
        wave_num = int(wave_name.split("_")[1])
        wave_tasks = []
        
        for task_name, agent_id in tasks:
            wave_tasks.append({
                "name": task_name,
                "agent": agent_id,
                "agent_name": agent_names.get(agent_id, agent_id),
            })
        
        plan["waves"].append({
            "wave": wave_num,
            "parallel": True,
            "tasks": wave_tasks,
        })
    
    return plan


def print_plan(plan: dict):
    """打印执行计划"""
    print(f"\n📋 任务分解：{plan['task']}")
    print("=" * 50)
    
    for wave in plan["waves"]:
        print(f"\n🌊 Wave {wave['wave']} {'（并行）' if wave['parallel'] else '（串行）'}")
        for task in wave["tasks"]:
            print(f"   → {task['name']} → {task['agent_name']}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 task_decomposer.py <task_description>")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    plan = decompose(task)
    print_plan(plan)
