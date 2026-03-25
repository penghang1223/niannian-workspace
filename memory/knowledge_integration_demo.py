#!/usr/bin/env python3
"""
多 Agent 系统 + 知识库集成演示

展示：
- 囡囡学习后自动分享知识
- 其他 Agent 查询知识
- 项目经理使用知识库辅助决策
- 知识通知系统

创建：2026-03-03 02:10
作者：囡囡 🎀
"""

import asyncio
from multi_agent_protocol import (
    MessageQueue,
    ProjectManagerAgent,
    DeveloperAgent,
    TesterAgent,
    NannanAgent,
    AgentRole,
    AgentMessage
)
from knowledge_base import KnowledgeBase, create_knowledge_base


async def run_knowledge_integrated_demo():
    """运行知识库集成的多 Agent 演示"""
    
    print("=" * 60)
    print("📚 多 Agent + 知识库集成演示")
    print("=" * 60)
    
    # 创建知识库
    print("\n🗄️  初始化知识库...")
    kb = create_knowledge_base()
    print(f"✅ 知识库就绪：{len(kb.knowledge)} 条知识")
    
    # 创建消息队列
    queue = MessageQueue()
    
    # 创建 Agent（带知识库引用）
    print("\n🤖 初始化 Agent 团队...")
    pm = ProjectManagerAgent(queue, kb)
    dev = DeveloperAgent(queue, kb)
    tester = TesterAgent(queue, kb)
    nannan = NannanAgent(queue, kb)
    
    print(f"✅ Agent 团队就绪：")
    print(f"   - 项目经理 (协调器 + 知识检索)")
    print(f"   - 开发工程师 (执行者 + 知识查询)")
    print(f"   - 测试工程师 (执行者 + 知识查询)")
    print(f"   - 囡囡 (智能助手 + 知识管理员)")
    
    # ==================== 场景 1: 囡囡主动分享知识 ====================
    print("\n" + "=" * 60)
    print("📖 场景 1: 囡囡主动分享学习成果")
    print("=" * 60)
    
    nannan.share_learning(
        topic="Agent 蜂群拓扑学习",
        content="""
学习了 ruflo 项目的蜂群智能拓扑：
1. Mesh 拓扑 - 所有 Agent 互相连接
2. Star 拓扑 - 中心节点协调
3. Hierarchical 拓扑 - 层级结构
4. Ring 拓扑 - 环形连接

优势：
- 动态扩展 Agent 数量
- 灵活的通信路由
- 容错性强
        """,
        file_path="memory/双项目深度学习报告.md",
        category="多 Agent 架构",
        tags=["蜂群智能", "拓扑", "ruflo", "架构"]
    )
    
    # 其他 Agent 接收通知
    print("\n📨 其他 Agent 接收知识通知:")
    for agent_id in [AgentRole.PROJECT_MANAGER.value, AgentRole.DEVELOPER.value, 
                     AgentRole.TESTER.value]:
        messages = queue.receive(agent_id)
        for msg in messages:
            if msg.message_type == "knowledge_notification":
                content = msg.content
                print(f"   {agent_id}: 收到新知识 - {content['topic']}")
    
    # ==================== 场景 2: 项目经理查询知识 ====================
    print("\n" + "=" * 60)
    print("📖 场景 2: 项目经理查询知识库辅助决策")
    print("=" * 60)
    
    # 模拟主人请求
    request = "帮我设计一个多 Agent 协同系统"
    print(f"\n👤 主人请求：{request}")
    
    # 项目经理接收请求（会自动检索知识库）
    conversation_id = pm.receive_human_request(request)
    
    # ==================== 场景 3: 工程师查询知识 ====================
    print("\n" + "=" * 60)
    print("📖 场景 3: 开发工程师查询知识库获取实现方案")
    print("=" * 60)
    
    # 工程师发送知识查询请求
    query_msg = AgentMessage(
        conversation_id=conversation_id,
        sender=AgentRole.DEVELOPER.value,
        receiver=AgentRole.NANNAN.value,
        message_type="knowledge_query",
        content={
            "query": "通信协议实现",
            "category": "通信协议"
        }
    )
    queue.send(query_msg)
    
    # 囡囡处理查询
    print(f"\n🔍 开发工程师查询：通信协议实现")
    nannan.process_requests()
    
    # 工程师接收查询结果
    print(f"\n📨 开发工程师接收查询结果:")
    messages = queue.receive(AgentRole.DEVELOPER.value)
    for msg in messages:
        if msg.message_type == "knowledge_query_result":
            content = msg.content
            print(f"   找到 {content['count']} 条结果:")
            for r in content.get('results', []):
                print(f"   - {r['topic']} ({r['category']})")
                if r.get('file_path'):
                    print(f"     文件：{r['file_path']}")
    
    # ==================== 场景 4: 测试工程师查询知识 ====================
    print("\n" + "=" * 60)
    print("📖 场景 4: 测试工程师查询知识库获取测试方案")
    print("=" * 60)
    
    # 测试工程师发送知识查询请求
    query_msg = AgentMessage(
        conversation_id=conversation_id,
        sender=AgentRole.TESTER.value,
        receiver=AgentRole.NANNAN.value,
        message_type="knowledge_query",
        content={
            "query": "测试",
            "category": "工具系统"
        }
    )
    queue.send(query_msg)
    
    # 囡囡处理查询
    print(f"\n🔍 测试工程师查询：测试方案")
    nannan.process_requests()
    
    # 测试工程师接收查询结果
    print(f"\n📨 测试工程师接收查询结果:")
    messages = queue.receive(AgentRole.TESTER.value)
    for msg in messages:
        if msg.message_type == "knowledge_query_result":
            content = msg.content
            if content['count'] > 0:
                print(f"   找到 {content['count']} 条结果:")
                for r in content.get('results', []):
                    print(f"   - {r['topic']}")
            else:
                print(f"   {content.get('message', '无结果')}")
    
    # ==================== 显示知识库统计 ====================
    print("\n" + "=" * 60)
    print("📊 知识库最终统计")
    print("=" * 60)
    
    stats = kb.get_statistics()
    print(f"\n总知识数：{stats['total_knowledge']}")
    print(f"总访问：{stats['total_access']}")
    print(f"\n分类分布:")
    for cat, count in stats['by_category'].items():
        print(f"   {cat}: {count} 条")
    print(f"\n作者分布:")
    for author, count in stats['by_author'].items():
        print(f"   {author}: {count} 条")
    print(f"\n热门话题:")
    for topic in stats['hot_topics'][:5]:
        print(f"   - {topic}")
    
    # 导出知识库
    print(f"\n💾 导出知识库...")
    kb.export_to_markdown("memory/知识库集成演示导出.md")
    
    print("\n" + "=" * 60)
    print("✅ 知识库集成演示完成！")
    print("=" * 60)
    
    print(f"""
🎯 演示总结:

✅ 囡囡可以主动分享学习成果
✅ 其他 Agent 接收知识通知
✅ 项目经理自动检索相关知识
✅ 工程师可以查询知识库
✅ 囡囡处理查询并返回结果
✅ 知识访问统计和追踪

📚 知识库已成为多 Agent 系统的核心组件！
    """)
    
    return kb, queue


if __name__ == "__main__":
    asyncio.run(run_knowledge_integrated_demo())
