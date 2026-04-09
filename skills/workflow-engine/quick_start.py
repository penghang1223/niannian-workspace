#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流引擎 - 快速启动脚本
用于测试和演示工作流引擎功能
"""

import sys
import os
import time

# 添加工作流引擎路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from workflow_integration import workflow_integration, on_nianian_message


def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_start_workflow():
    """测试 1：启动工作流"""
    print_separator("测试 1：启动工作流")
    
    # 模拟主人消息
    message = "启动小说创作《我在修仙界开网约车》"
    sender = "owner_001"
    
    print(f"\n📥 主人消息：{message}")
    print("\n📤 系统响应：")
    
    result = on_nianian_message(message, sender)
    
    print(f"\n✅ 启动结果：{result}")
    
    return result


def test_query_status():
    """测试 2：查询进度"""
    print_separator("测试 2：查询进度")
    
    message = "查询进度"
    sender = "owner_001"
    
    print(f"\n📥 主人消息：{message}")
    print("\n📤 系统响应：")
    
    result = on_nianian_message(message, sender)
    
    if "error" not in result:
        print(f"\n📊 项目状态：")
        print(f"  项目：{result.get('novel_name', 'N/A')}")
        print(f"  当前阶段：{result.get('current_wave', 'N/A')}")
        print(f"  工作流状态：{result.get('workflow_status', 'N/A')}")
        print(f"  当前步骤：{result.get('progress', 'N/A')}")
    else:
        print(f"\n❌ 错误：{result.get('error')}")
    
    return result


def test_confirm_continue():
    """测试 3：确认继续"""
    print_separator("测试 3：确认继续")
    
    message = "确认继续"
    sender = "owner_001"
    
    print(f"\n📥 主人消息：{message}")
    print("\n📤 系统响应：")
    
    result = on_nianian_message(message, sender)
    
    print(f"\n✅ 确认结果：{result}")
    
    return result


def test_list_projects():
    """测试 4：列出项目"""
    print_separator("测试 4：列出项目")
    
    projects = workflow_integration.list_projects()
    
    print(f"\n📋 当前项目列表：")
    
    if projects:
        for i, project in enumerate(projects, 1):
            print(f"\n  {i}. 项目 ID: {project['project_id']}")
            print(f"     小说名：{project['novel_name']}")
            print(f"     当前阶段：{project['current_wave']}")
            print(f"     状态：{project['status']}")
    else:
        print("\n  暂无活跃项目")
    
    return projects


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("  工作流引擎 - 快速启动测试")
    print("🚀" * 30)
    
    # 测试 1：启动工作流
    test_start_workflow()
    
    # 等待一下
    time.sleep(1)
    
    # 测试 2：查询进度
    test_query_status()
    
    # 等待一下
    time.sleep(1)
    
    # 测试 3：确认继续
    test_confirm_continue()
    
    # 等待一下
    time.sleep(1)
    
    # 测试 4：列出项目
    test_list_projects()
    
    # 总结
    print_separator("测试总结")
    print("\n✅ 所有测试完成！")
    print("\n📋 测试覆盖：")
    print("  - 启动工作流 ✅")
    print("  - 查询进度 ✅")
    print("  - 确认继续 ✅")
    print("  - 列出项目 ✅")
    print("\n🎯 下一步：")
    print("  1. 按照 integration-guide.md 集成到 Agent 系统")
    print("  2. 设置实际回调函数")
    print("  3. 创建真实项目测试")
    
    print("\n" + "🎉" * 30)


if __name__ == "__main__":
    run_all_tests()
