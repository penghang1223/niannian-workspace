#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 任务自动分配器 (Task Dispatcher)

根据任务描述自动分析并分发给最合适的 Agent。
支持关键词匹配规则引擎和 sessions_send API 调用。

作者：年年 (Niannian)
创建日期：2026-03-20
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Agent 角色枚举"""
    PRODUCT_MANAGER = "product_manager"
    DEV_ENGINEER = "dev_engineer"
    QA_ENGINEER = "qa_engineer"
    FRONTEND_DEV = "frontend_dev"
    CHIEF_CUTE_OFFICER = "chief_cute_officer"
    TAIYI = "taiyi"
    TIANGONG = "tiangong"
    LINGXI = "lingxi"
    ZHIMING = "zhiming"
    YUEYING = "yueying"
    SHICHEN = "shichen"


@dataclass
class DispatchResult:
    """分发结果"""
    agent_id: str
    confidence: float  # 置信度 0.0-1.0
    matched_keywords: List[str]
    instruction: str
    reasoning: str


class TaskDispatcher:
    """
    任务自动分配器
    
    功能：
    1. 分析任务描述（自然语言）
    2. 根据关键词匹配规则选择最合适的 Agent
    3. 生成分发指令
    4. 支持 sessions_send API 调用
    """
    
    # Agent 职责映射表
    # 格式：Agent ID -> (职责描述，关键词列表，权重)
    AGENT_RULES: Dict[str, Tuple[str, List[str], Dict[str, float]]] = {
        AgentRole.PRODUCT_MANAGER.value: (
            "产品需求分析、PRD 撰写、原型设计、功能规划",
            ["产品", "需求", "PRD", "设计", "规划", "原型", "功能", "用户故事", "场景", "业务"],
            {"产品": 1.0, "需求": 0.9, "PRD": 1.0, "设计": 0.7, "规划": 0.8, "原型": 1.0, "功能": 0.6, "用户故事": 1.0, "场景": 0.7, "业务": 0.6}
        ),
        AgentRole.DEV_ENGINEER.value: (
            "技术方案、代码实现、后端开发、API 开发、系统集成",
            ["开发", "代码", "后端", "API", "实现", "技术", "编程", "Python", "服务器", "数据库", "接口"],
            {"开发": 0.9, "代码": 1.0, "后端": 1.0, "API": 1.0, "实现": 0.8, "技术": 0.6, "编程": 0.9, "Python": 1.0, "服务器": 0.8, "数据库": 0.9, "接口": 0.8}
        ),
        AgentRole.QA_ENGINEER.value: (
            "测试用例、质量保障、Bug 验证、自动化测试",
            ["测试", "质量", "Bug", "验证", "用例", "QA", "自动化测试", "回归", "缺陷"],
            {"测试": 1.0, "质量": 0.9, "Bug": 1.0, "验证": 0.8, "用例": 0.9, "QA": 1.0, "自动化测试": 1.0, "回归": 0.9, "缺陷": 1.0}
        ),
        AgentRole.FRONTEND_DEV.value: (
            "前端页面、UI 实现、交互开发、小程序",
            ["前端", "页面", "UI", "React", "Vue", "小程序", "H5", "交互", "界面", "网页", "CSS", "HTML"],
            {"前端": 1.0, "页面": 0.9, "UI": 1.0, "React": 1.0, "Vue": 1.0, "小程序": 1.0, "H5": 0.9, "交互": 0.7, "界面": 0.8, "网页": 0.9, "CSS": 1.0, "HTML": 1.0}
        ),
        AgentRole.CHIEF_CUTE_OFFICER.value: (
            "内容创作、文案写作、活跃气氛、可爱互动",
            ["内容", "写作", "文案", "可爱", "卖萌", "气氛", "互动", "创意", "小红书", "抖音"],
            {"内容": 0.8, "写作": 1.0, "文案": 1.0, "可爱": 1.0, "卖萌": 1.0, "气氛": 0.8, "互动": 0.7, "创意": 0.7, "小红书": 0.9, "抖音": 0.9}
        ),
        AgentRole.TAIYI.value: (
            "架构设计、技术选型、系统规划",
            ["架构", "技术选型", "系统", "规划", "设计模式", "微服务", "云原生"],
            {"架构": 1.0, "技术选型": 1.0, "系统": 0.7, "规划": 0.6, "设计模式": 1.0, "微服务": 1.0, "云原生": 1.0}
        ),
        AgentRole.TIANGONG.value: (
            "首席架构师、复杂系统设计、工程化",
            ["首席架构", "复杂系统", "工程化", "DevOps", "CI/CD", "基础设施"],
            {"首席架构": 1.0, "复杂系统": 1.0, "工程化": 0.9, "DevOps": 1.0, "CI/CD": 1.0, "基础设施": 0.9}
        ),
        AgentRole.LINGXI.value: (
            "策略顾问、商业分析、决策支持",
            ["策略", "规划", "商业", "决策", "咨询", "分析", "建议"],
            {"策略": 1.0, "规划": 0.7, "商业": 0.9, "决策": 0.9, "咨询": 0.8, "分析": 0.6, "建议": 0.7}
        ),
        AgentRole.ZHIMING.value: (
            "协调员、沟通协作、资源调度",
            ["协调", "沟通", "协作", "调度", "资源", "会议", "安排"],
            {"协调": 1.0, "沟通": 1.0, "协作": 0.9, "调度": 0.9, "资源": 0.8, "会议": 0.7, "安排": 0.7}
        ),
        AgentRole.YUEYING.value: (
            "数据分析、报表生成、可视化",
            ["数据", "分析", "报表", "可视化", "图表", "统计", "指标", "BI"],
            {"数据": 0.8, "分析": 0.9, "报表": 1.0, "可视化": 1.0, "图表": 0.9, "统计": 0.9, "指标": 0.8, "BI": 1.0}
        ),
        AgentRole.SHICHEN.value: (
            "时间管理、日程安排、提醒服务",
            ["时间", "日程", "提醒", "安排", "日历", "计划", "闹钟"],
            {"时间": 0.9, "日程": 1.0, "提醒": 1.0, "安排": 0.8, "日历": 1.0, "计划": 0.7, "闹钟": 0.9}
        ),
    }
    
    def __init__(self):
        """初始化分配器"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """预编译正则表达式，提高匹配效率"""
        compiled = {}
        for agent_id, (_, keywords, _) in self.AGENT_RULES.items():
            compiled[agent_id] = [re.compile(keyword, re.IGNORECASE) for keyword in keywords]
        return compiled
    
    def analyze(self, task_description: str) -> DispatchResult:
        """
        分析任务描述并返回分发结果
        
        Args:
            task_description: 任务描述（自然语言）
            
        Returns:
            DispatchResult: 包含目标 Agent ID、置信度、匹配关键词等信息
        """
        if not task_description or not task_description.strip():
            return DispatchResult(
                agent_id=AgentRole.ZHIMING.value,
                confidence=0.0,
                matched_keywords=[],
                instruction="任务描述为空，请提供详细信息",
                reasoning="无法分析空任务，需要人工介入"
            )
        
        # 计算每个 Agent 的匹配得分
        scores: Dict[str, Tuple[float, List[str]]] = {}
        
        for agent_id, (_, _, weights) in self.AGENT_RULES.items():
            total_score = 0.0
            matched = []
            
            for keyword, weight in weights.items():
                if keyword in task_description:
                    total_score += weight
                    matched.append(keyword)
            
            if matched:
                # 归一化得分（0-1 之间）
                normalized_score = min(total_score / len(weights), 1.0)
                scores[agent_id] = (normalized_score, matched)
        
        if not scores:
            # 没有匹配到任何关键词，返回默认分配给协调员
            return DispatchResult(
                agent_id=AgentRole.ZHIMING.value,
                confidence=0.3,
                matched_keywords=[],
                instruction=task_description,
                reasoning="未匹配到明确关键词，默认分配给协调员进行人工判断"
            )
        
        # 选择得分最高的 Agent
        best_agent = max(scores.items(), key=lambda x: x[1][0])
        agent_id = best_agent[0]
        confidence, matched_keywords = best_agent[1]
        
        # 生成分发指令
        instruction = self._generate_instruction(agent_id, task_description)
        reasoning = self._generate_reasoning(agent_id, confidence, matched_keywords)
        
        return DispatchResult(
            agent_id=agent_id,
            confidence=confidence,
            matched_keywords=matched_keywords,
            instruction=instruction,
            reasoning=reasoning
        )
    
    def _generate_instruction(self, agent_id: str, task_description: str) -> str:
        """生成给目标 Agent 的指令"""
        role_desc = self.AGENT_RULES[agent_id][0]
        return f"""【任务分发】
职责范围：{role_desc}
任务内容：{task_description}

请根据您的需求分析并处理此任务，完成后回复结果。"""
    
    def _generate_reasoning(self, agent_id: str, confidence: float, matched_keywords: List[str]) -> str:
        """生成分发理由说明"""
        role_desc = self.AGENT_RULES[agent_id][0]
        keywords_str = "、".join(matched_keywords) if matched_keywords else "无明显关键词"
        return f"匹配到 Agent「{agent_id}」（{role_desc}），关键词：{keywords_str}，置信度：{confidence:.2f}"
    
    def dispatch(self, task_description: str, sessions_send_callback=None) -> DispatchResult:
        """
        分析并分发任务
        
        Args:
            task_description: 任务描述
            sessions_send_callback: sessions_send 回调函数（可选）
            
        Returns:
            DispatchResult: 分发结果
        """
        result = self.analyze(task_description)
        
        # 如果提供了回调函数，调用 sessions_send
        if sessions_send_callback and result.confidence > 0.3:
            try:
                sessions_send_callback(
                    agentId=result.agent_id,
                    message=result.instruction
                )
            except Exception as e:
                result.reasoning += f" [分发失败：{str(e)}]"
        
        return result
    
    def dispatch_batch(self, tasks: List[str], sessions_send_callback=None) -> List[DispatchResult]:
        """
        批量分发多个任务
        
        Args:
            tasks: 任务描述列表
            sessions_send_callback: sessions_send 回调函数
            
        Returns:
            List[DispatchResult]: 分发结果列表
        """
        results = []
        for task in tasks:
            result = self.dispatch(task, sessions_send_callback)
            results.append(result)
        return results
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """
        获取 Agent 信息
        
        Args:
            agent_id: Agent ID
            
        Returns:
            包含 Agent 信息的字典，如果不存在则返回 None
        """
        if agent_id in self.AGENT_RULES:
            role_desc, keywords, _ = self.AGENT_RULES[agent_id]
            return {
                "agent_id": agent_id,
                "role_description": role_desc,
                "keywords": keywords
            }
        return None
    
    def list_agents(self) -> List[Dict]:
        """
        列出所有可用的 Agent
        
        Returns:
            Agent 信息列表
        """
        return [
            {
                "agent_id": agent_id,
                "role_description": desc,
                "keywords": keywords
            }
            for agent_id, (desc, keywords, _) in self.AGENT_RULES.items()
        ]


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建分配器实例
    dispatcher = TaskDispatcher()
    
    # 测试用例
    test_tasks = [
        "帮我设计一个用户登录功能的 PRD",
        "需要开发一个 Python 后端 API 接口",
        "请为这个功能编写测试用例",
        "做一个 React 前端页面",
        "写一篇小红书文案",
        "系统架构怎么设计比较好？",
        "需要协调各部门资源开会",
        "分析上季度的销售数据",
        "提醒我明天上午 10 点开会",
    ]
    
    print("=" * 60)
    print("Agent 任务自动分配器 - 测试报告")
    print("=" * 60)
    
    for task in test_tasks:
        print(f"\n📋 任务：{task}")
        result = dispatcher.analyze(task)
        print(f"   → 分配给：{result.agent_id}")
        print(f"   → 置信度：{result.confidence:.2f}")
        print(f"   → 关键词：{', '.join(result.matched_keywords)}")
        print(f"   → 理由：{result.reasoning}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 展示所有可用 Agent
    print("\n🤖 可用 Agent 列表：")
    for agent in dispatcher.list_agents():
        print(f"   • {agent['agent_id']}: {agent['role_description']}")
