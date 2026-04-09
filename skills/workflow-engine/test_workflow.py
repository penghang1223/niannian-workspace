#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流测试脚本
测试工作流引擎的核心功能
"""

from workflow_engine import (
    WorkflowEngine,
    Workflow,
    LoopWorkflow,
    Step,
    DecisionNode,
    create_wave_1,
    create_wave_2,
    create_wave_3
)


def test_wave_1():
    """测试 Wave-1：选题定方向"""
    print("=" * 60)
    print("测试 Wave-1：选题定方向")
    print("=" * 60)
    
    engine = WorkflowEngine()
    engine.register_workflow("wave_1", create_wave_1())
    
    # 启动工作流
    result = engine.start_workflow(
        workflow_name="wave_1",
        project_id="test_001",
        context={"novel_name": "测试小说"}
    )
    print(f"启动结果：{result}")
    
    # 模拟步骤完成
    # Step 1: 望舒完成
    result = engine.on_step_complete(
        agent="望舒",
        output={"prd": "PRD-v1.0", "competitor_analysis": {...}}
    )
    print(f"望舒完成：{result}")
    
    # Step 2: 灵犀完成
    result = engine.on_step_complete(
        agent="灵犀",
        output={"creative_ideas": ["创意 1", "创意 2", "创意 3"]}
    )
    print(f"灵犀完成：{result}")
    
    # Step 3: 灵犀投票完成
    result = engine.on_step_complete(
        agent="灵犀",
        output={"vote_result": "创意 1 得票 60%"}
    )
    print(f"灵犀投票完成：{result}")
    
    # Step 4: 年年汇报（等待主人确认）
    result = engine.on_step_complete(
        agent="年年",
        output={"report_sent": True}
    )
    print(f"年年汇报：{result}")
    
    print(f"\nWave-1 完成！状态：{engine.active_instance.workflow.status}")
    print("=" * 60)


def test_wave_2_pass():
    """测试 Wave-2：大纲 + 人设（审查通过）"""
    print("=" * 60)
    print("测试 Wave-2：大纲 + 人设（审查通过）")
    print("=" * 60)
    
    engine = WorkflowEngine()
    engine.register_workflow("wave_2", create_wave_2())
    
    # 启动工作流
    result = engine.start_workflow(
        workflow_name="wave_2",
        project_id="test_002",
        context={"novel_name": "测试小说"}
    )
    print(f"启动结果：{result}")
    
    # Step 1: 惊鸿完成大纲
    result = engine.on_step_complete(
        agent="惊鸿",
        output={"outline": "大纲 v1.0", "character_cards": "角色卡 v1.0"}
    )
    print(f"惊鸿完成：{result}")
    
    # Step 2: 鉴微审查（通过）
    result = engine.on_step_complete(
        agent="鉴微",
        output={"p0_issues": 0, "p1_issues": 2, "passed": True}
    )
    print(f"鉴微审查（通过）：{result}")
    
    # Step 3: 决策节点（自动走向年年）
    # Step 4: 年年汇报
    result = engine.on_step_complete(
        agent="年年",
        output={"report_sent": True}
    )
    print(f"年年汇报：{result}")
    
    print(f"\nWave-2 完成！状态：{engine.active_instance.workflow.status}")
    print("=" * 60)


def test_wave_2_fail():
    """测试 Wave-2：大纲 + 人设（审查不通过）"""
    print("=" * 60)
    print("测试 Wave-2：大纲 + 人设（审查不通过）")
    print("=" * 60)
    
    engine = WorkflowEngine()
    engine.register_workflow("wave_2", create_wave_2())
    
    # 启动工作流
    result = engine.start_workflow(
        workflow_name="wave_2",
        project_id="test_003",
        context={"novel_name": "测试小说"}
    )
    print(f"启动结果：{result}")
    
    # Step 1: 惊鸿完成大纲
    result = engine.on_step_complete(
        agent="惊鸿",
        output={"outline": "大纲 v1.0", "character_cards": "角色卡 v1.0"}
    )
    print(f"惊鸿完成：{result}")
    
    # Step 2: 鉴微审查（不通过）
    result = engine.on_step_complete(
        agent="鉴微",
        output={"p0_issues": 3, "p1_issues": 5, "passed": False, "comments": "需要修改"}
    )
    print(f"鉴微审查（不通过）：{result}")
    
    # Step 3: 决策节点（自动走向惊鸿_revision）
    # Step 4: 惊鸿修改
    result = engine.on_step_complete(
        agent="惊鸿_revision",
        output={"outline": "大纲 v2.0", "character_cards": "角色卡 v2.0"}
    )
    print(f"惊鸿修改：{result}")
    
    # Step 5: 鉴微重新审查（通过）
    result = engine.on_step_complete(
        agent="鉴微_re_review",
        output={"p0_issues": 0, "p1_issues": 1, "passed": True}
    )
    print(f"鉴微重新审查（通过）：{result}")
    
    # Step 6: 决策节点（自动走向年年）
    # Step 7: 年年汇报
    result = engine.on_step_complete(
        agent="年年",
        output={"report_sent": True}
    )
    print(f"年年汇报：{result}")
    
    print(f"\nWave-2 完成！状态：{engine.active_instance.workflow.status}")
    print("=" * 60)


def test_wave_3_loop():
    """测试 Wave-3：章节创作（循环 3 次简化测试）"""
    print("=" * 60)
    print("测试 Wave-3：章节创作（简化测试 3 章）")
    print("=" * 60)
    
    engine = WorkflowEngine()
    
    # 创建简化版 Wave-3（只循环 3 次）
    wave_3 = create_wave_3()
    wave_3.iterations = 3
    wave_3.loop_condition = "current_iteration <= 3"
    
    engine.register_workflow("wave_3", wave_3)
    
    # 启动工作流
    result = engine.start_workflow(
        workflow_name="wave_3",
        project_id="test_004",
        context={"novel_name": "测试小说"}
    )
    print(f"启动结果：{result}")
    
    # 模拟 3 章创作
    for chapter in range(1, 4):
        print(f"\n--- 第{chapter}章 ---")
        
        # Step 1: 惊鸿创作
        result = engine.on_step_complete(
            agent="惊鸿",
            output={"chapter": f"第{chapter}章", "word_count": 3500}
        )
        print(f"惊鸿创作：{result}")
        
        # Step 2: 鉴微审查（通过）
        result = engine.on_step_complete(
            agent="鉴微",
            output={"p0_issues": 0, "p1_issues": 1, "passed": True}
        )
        print(f"鉴微审查：{result}")
        
        # Step 3: 决策节点（通过）
        # Step 4: 年年汇报
        result = engine.on_step_complete(
            agent="年年",
            output={"report_sent": True}
        )
        print(f"年年汇报：{result}")
    
    print(f"\nWave-3 完成！状态：{engine.active_instance.workflow.status}")
    print(f"总迭代次数：{engine.active_instance.workflow.current_iteration - 1}")
    print("=" * 60)


def test_decision_node():
    """测试决策节点"""
    print("=" * 60)
    print("测试决策节点")
    print("=" * 60)
    
    decision = DecisionNode(
        conditions={"pass": "P0 问题=0", "fail": "P0 问题>0"},
        branches={"pass": "next_agent", "fail": "revision_agent"}
    )
    
    # 测试通过情况
    result = decision.evaluate({"p0_issues": 0})
    print(f"P0=0 → {result}（期望：next_agent）")
    assert result == "next_agent", f"Expected 'next_agent', got '{result}'"
    
    # 测试不通过情况
    result = decision.evaluate({"p0_issues": 3})
    print(f"P0=3 → {result}（期望：revision_agent）")
    assert result == "revision_agent", f"Expected 'revision_agent', got '{result}'"
    
    print("\n决策节点测试通过！")
    print("=" * 60)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("工作流引擎测试套件")
    print("=" * 60 + "\n")
    
    test_decision_node()
    test_wave_1()
    test_wave_2_pass()
    test_wave_2_fail()
    test_wave_3_loop()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
