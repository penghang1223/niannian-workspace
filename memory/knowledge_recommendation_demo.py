#!/usr/bin/env python3
"""
知识推荐系统演示

展示：
- 基于上下文的智能推荐
- 基于任务的推荐
- 相似知识推荐
- 基于角色的个性化推荐

创建：2026-03-03 02:15
作者：囡囡 🎀
"""

from knowledge_base import create_knowledge_base


def demo_context_based_recommendation():
    """演示基于上下文的推荐"""
    print("=" * 60)
    print("📖 场景 1: 基于上下文的智能推荐")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 场景：项目经理正在处理多 Agent 协同任务
    context = """
    我正在设计一个多 Agent 协同系统，需要实现 Agent 之间的通信。
    希望了解不同的通信协议和架构模式，特别是蜂群智能相关的。
    """
    
    print(f"\n📝 上下文：{context.strip()[:100]}...")
    print(f"\n🤖 囡囡推荐：")
    
    recommendations = kb.recommend(context, limit=5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['topic']}")
        print(f"   分类：{rec['category']}")
        print(f"   推荐分数：{rec['score']:.1f}")
        print(f"   推荐原因：{', '.join(rec['reasons'])}")
        print(f"   摘要：{rec['summary'][:80]}...")
        if rec.get('file_path'):
            print(f"   文件：{rec['file_path']}")


def demo_task_based_recommendation():
    """演示基于任务的推荐"""
    print("\n" + "=" * 60)
    print("📖 场景 2: 基于任务的推荐（不同角色）")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    task = "实现用户登录 API，需要支持 OAuth2.0 和 JWT 认证"
    
    print(f"\n📝 任务：{task}")
    
    # 不同角色的推荐
    roles = [
        ("project_manager", "项目经理"),
        ("developer", "开发工程师"),
        ("tester", "测试工程师")
    ]
    
    for role, role_name in roles:
        print(f"\n{'─' * 60}")
        print(f"👤 {role_name} 的个性化推荐：")
        print(f"{'─' * 60}")
        
        recommendations = kb.recommend_for_task(task, agent_role=role)
        
        if recommendations:
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"\n{i}. {rec['topic']}")
                print(f"   分数：{rec['score']:.1f}")
                print(f"   原因：{', '.join(rec['reasons'])}")
        else:
            print("   暂无相关推荐")


def demo_similar_knowledge():
    """演示相似知识推荐"""
    print("\n" + "=" * 60)
    print("📖 场景 3: 相似知识推荐（看了这个的人还看了...）")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 假设用户正在查看"Ch10 通信协议学习"
    current_topic = "Ch10 通信协议学习"
    
    # 找到知识 ID
    current_item = kb.query(current_topic)
    if not current_item:
        print(f"⚠️  未找到知识：{current_topic}")
        return
    
    print(f"\n📖 当前查看：{current_item.topic}")
    print(f"   分类：{current_item.category}")
    print(f"   标签：{', '.join(current_item.tags)}")
    
    print(f"\n🤖 囡囡推荐相似知识：")
    
    similar = kb.recommend_similar(current_item.id, limit=3)
    
    for i, rec in enumerate(similar, 1):
        print(f"\n{i}. {rec['topic']}")
        print(f"   分类：{rec['category']}")
        print(f"   相似度：{rec['score']:.1f}")
        print(f"   原因：{', '.join(rec['reasons'])}")


def demo_real_time_recommendation():
    """演示实时推荐（对话中）"""
    print("\n" + "=" * 60)
    print("📖 场景 4: 实时推荐（对话中智能推荐）")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 模拟对话
    conversations = [
        "我想了解一下 Agent 之间怎么通信",
        "有没有测试相关的最佳实践？",
        "飞书机器人怎么配置事件订阅？",
        "记忆系统应该怎么设计？"
    ]
    
    for i, context in enumerate(conversations, 1):
        print(f"\n{'─' * 60}")
        print(f"💬 对话 {i}: {context}")
        print(f"{'─' * 60}")
        
        recommendations = kb.recommend(context, limit=2)
        
        if recommendations:
            print(f"🤖 囡囡推荐：")
            for rec in recommendations:
                print(f"   📚 {rec['topic']} ({rec['category']})")
                print(f"      原因：{', '.join(rec['reasons'][:2])}")
        else:
            print("🤖 囡囡：暂时没有找到相关知识呢～")


def demo_recommendation_with_feedback():
    """演示带反馈的推荐（强化学习）"""
    print("\n" + "=" * 60)
    print("📖 场景 5: 带反馈的推荐（越用越聪明）")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    context = "多 Agent 通信协议实现"
    
    print(f"\n📝 上下文：{context}")
    print(f"\n🔄 第一轮推荐：")
    
    recs1 = kb.recommend(context, limit=3)
    for i, rec in enumerate(recs1, 1):
        print(f"   {i}. {rec['topic']} (分数：{rec['score']:.1f})")
    
    # 模拟用户点击了第一个推荐
    if recs1:
        print(f"\n👆 用户点击了：{recs1[0]['topic']}")
        
        # 模拟访问（增加 access_count）
        kb._record_access(recs1[0]['knowledge_id'])
        
        print(f"\n🔄 第二轮推荐（考虑用户行为）：")
        recs2 = kb.recommend(context, limit=3, use_collaborative=True)
        for i, rec in enumerate(recs2, 1):
            print(f"   {i}. {rec['topic']} (分数：{rec['score']:.1f})")
            if rec['knowledge_id'] == recs1[0]['knowledge_id']:
                print(f"      ⬆️ 因为您之前看过，排名提升了！")


def show_recommendation_stats():
    """显示推荐统计"""
    print("\n" + "=" * 60)
    print("📊 推荐系统统计")
    print("=" * 60)
    
    kb = create_knowledge_base()
    stats = kb.get_statistics()
    
    print(f"\n知识库概览:")
    print(f"   总知识数：{stats['total_knowledge']}")
    print(f"   总访问：{stats['total_access']}")
    
    print(f"\n推荐能力:")
    print(f"   ✅ 基于上下文推荐")
    print(f"   ✅ 基于任务推荐")
    print(f"   ✅ 相似知识推荐")
    print(f"   ✅ 基于角色推荐")
    print(f"   ✅ 实时推荐")
    print(f"   ✅ 反馈强化")
    
    print(f"\n热门知识（被推荐最多）:")
    for topic in stats['hot_topics'][:5]:
        item = kb.query(topic)
        if item:
            print(f"   📚 {topic} (访问：{item.access_count} 次)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎯 知识推荐系统演示")
    print("=" * 60)
    
    # 运行所有演示
    demo_context_based_recommendation()
    demo_task_based_recommendation()
    demo_similar_knowledge()
    demo_real_time_recommendation()
    demo_recommendation_with_feedback()
    show_recommendation_stats()
    
    print("\n" + "=" * 60)
    print("✅ 推荐系统演示完成！")
    print("=" * 60)
    
    print(f"""
🎯 推荐系统总结:

✅ 基于上下文智能推荐（关键词/标签/分类匹配）
✅ 基于任务的个性化推荐（不同角色不同推荐）
✅ 相似知识推荐（看了这个的人还看了...）
✅ 实时对话推荐（对话中智能推荐）
✅ 反馈强化推荐（越用越聪明）

📚 囡囡的推荐系统已经可以：
   - 理解上下文语义
   - 根据角色个性化
   - 学习用户行为
   - 持续优化推荐

🎀 主人满意吗？
    """)
