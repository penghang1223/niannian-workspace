#!/usr/bin/env python3
"""
多 Agent 共享知识库

支持：
- 知识添加/查询/更新/删除
- 知识分类管理
- 知识共享消息
- 访问统计和热度追踪

创建：2026-03-03 02:05
作者：囡囡 🎀
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib


# ==================== 数据类定义 ====================

@dataclass
class KnowledgeItem:
    """知识项"""
    
    # 基本信息
    id: str = ""                      # 知识 ID (唯一)
    topic: str = ""                   # 主题/标题
    category: str = ""                # 分类
    content: str = ""                 # 内容
    
    # 元数据
    author: str = ""                  # 作者 (哪个 Agent)
    created_at: float = field(default_factory=time.time)  # 创建时间
    updated_at: float = field(default_factory=time.time)  # 更新时间
    tags: List[str] = field(default_factory=list)         # 标签
    
    # 使用统计
    access_count: int = 0             # 访问次数
    last_accessed: Optional[float] = None  # 最后访问时间
    usefulness_score: float = 0.0     # 有用性评分 (0-5)
    
    # 关联
    related_topics: List[str] = field(default_factory=list)  # 相关主题
    file_path: Optional[str] = None   # 关联文件路径
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeItem':
        """从字典创建"""
        return cls(**data)


@dataclass
class KnowledgeCategory:
    """知识分类"""
    
    name: str                         # 分类名称
    description: str = ""             # 分类描述
    parent: Optional[str] = None      # 父分类
    subcategories: List[str] = field(default_factory=list)  # 子分类
    knowledge_count: int = 0          # 知识数量


# ==================== 知识库核心类 ====================

class KnowledgeBase:
    """共享知识库"""
    
    # 默认分类
    DEFAULT_CATEGORIES = {
        "通信协议": "MCP/A2A/ANP 等 Agent 通信协议知识",
        "多 Agent 架构": "多 Agent 协同、蜂群智能等架构知识",
        "记忆系统": "记忆管理、RAG 检索、遗忘曲线等",
        "上下文工程": "上下文窗口管理、情境理解等",
        "性能评估": "KPI 指标、质量评估体系等",
        "工具系统": "MCP 工具、插件系统等",
        "飞书集成": "飞书机器人配置、事件订阅等",
        "项目参考": "ruflo、hello-agents 等项目学习"
    }
    
    def __init__(self, storage_path: str = "memory/knowledge_base.json"):
        self.storage_path = storage_path
        self.knowledge: Dict[str, KnowledgeItem] = {}
        self.categories: Dict[str, KnowledgeCategory] = {}
        
        # 加载或初始化
        self._load()
        if not self.knowledge:
            self._init_categories()
    
    # ==================== 核心操作 ====================
    
    def add(self, topic: str, content: str, author: str, 
            category: str = "通用", tags: List[str] = None,
            file_path: str = None, related_topics: List[str] = None) -> str:
        """添加知识"""
        # 生成唯一 ID
        knowledge_id = hashlib.md5(
            f"{topic}_{author}_{time.time()}".encode()
        ).hexdigest()[:12]
        
        # 创建知识项
        item = KnowledgeItem(
            id=knowledge_id,
            topic=topic,
            category=category,
            content=content,
            author=author,
            tags=tags or [],
            file_path=file_path,
            related_topics=related_topics or []
        )
        
        # 存储
        self.knowledge[knowledge_id] = item
        
        # 更新分类计数
        if category in self.categories:
            self.categories[category].knowledge_count += 1
        
        # 保存
        self._save()
        
        print(f"✅ 知识已添加：{topic} (ID: {knowledge_id})")
        return knowledge_id
    
    def query(self, topic: str) -> Optional[KnowledgeItem]:
        """查询知识（按主题）"""
        # 精确匹配
        for item in self.knowledge.values():
            if item.topic.lower() == topic.lower():
                self._record_access(item.id)
                return item
        
        # 模糊匹配
        for item in self.knowledge.values():
            if topic.lower() in item.topic.lower():
                self._record_access(item.id)
                return item
        
        return None
    
    def search(self, query: str, category: str = None, 
               tags: List[str] = None, limit: int = 10) -> List[KnowledgeItem]:
        """搜索知识"""
        results = []
        
        for item in self.knowledge.values():
            # 分类过滤
            if category and item.category != category:
                continue
            
            # 标签过滤
            if tags and not any(tag in item.tags for tag in tags):
                continue
            
            # 关键词匹配
            score = 0
            if query.lower() in item.topic.lower():
                score += 3
            if query.lower() in item.content.lower():
                score += 1
            if any(query.lower() in tag.lower() for tag in item.tags):
                score += 2
            
            if score > 0:
                results.append((score, item))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        
        # 记录访问
        for _, item in results[:limit]:
            self._record_access(item.id)
        
        return [item for _, item in results[:limit]]
    
    def update(self, knowledge_id: str, content: str = None, 
               tags: List[str] = None, usefulness_score: float = None) -> bool:
        """更新知识"""
        if knowledge_id not in self.knowledge:
            return False
        
        item = self.knowledge[knowledge_id]
        
        if content:
            item.content = content
        if tags:
            item.tags = tags
        if usefulness_score is not None:
            item.usefulness_score = usefulness_score
        
        item.updated_at = time.time()
        
        self._save()
        print(f"✅ 知识已更新：{item.topic}")
        return True
    
    def delete(self, knowledge_id: str) -> bool:
        """删除知识"""
        if knowledge_id not in self.knowledge:
            return False
        
        item = self.knowledge[knowledge_id]
        
        # 更新分类计数
        if item.category in self.categories:
            self.categories[item.category].knowledge_count -= 1
        
        # 删除
        del self.knowledge[knowledge_id]
        
        self._save()
        print(f"✅ 知识已删除：{item.topic}")
        return True
    
    def get(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """获取知识（按 ID）"""
        if knowledge_id not in self.knowledge:
            return None
        
        item = self.knowledge[knowledge_id]
        self._record_access(knowledge_id)
        return item
    
    def list_by_category(self, category: str) -> List[KnowledgeItem]:
        """按分类列出知识"""
        items = [
            item for item in self.knowledge.values()
            if item.category == category
        ]
        return sorted(items, key=lambda x: x.access_count, reverse=True)
    
    def list_all(self, limit: int = 100) -> List[KnowledgeItem]:
        """列出所有知识"""
        items = list(self.knowledge.values())
        items.sort(key=lambda x: x.access_count, reverse=True)
        return items[:limit]
    
    # ==================== 知识推荐 ====================
    
    def recommend(self, context: str, limit: int = 5, 
                  use_collaborative: bool = True) -> List[Dict]:
        """
        基于上下文推荐知识
        
        Args:
            context: 上下文文本（如任务描述、对话内容）
            limit: 返回数量
            use_collaborative: 是否使用协同过滤（基于访问模式）
        
        Returns:
            推荐知识列表（带推荐原因和分数）
        """
        if not context:
            return []
        
        recommendations = []
        
        for item in self.knowledge.values():
            score = 0.0
            reasons = []
            
            # 1. 关键词匹配（40% 权重）
            context_lower = context.lower()
            if item.topic.lower() in context_lower:
                score += 40
                reasons.append("主题匹配")
            elif any(word.lower() in context_lower for word in item.topic.split()):
                score += 20
                reasons.append("关键词匹配")
            
            # 2. 标签匹配（30% 权重）
            for tag in item.tags:
                if tag.lower() in context_lower:
                    score += 10
                    reasons.append(f"标签匹配：{tag}")
            
            # 3. 分类匹配（20% 权重）
            # 检测上下文中是否提到分类相关词
            if item.category in context or any(
                cat_word in context for cat_word in self._get_category_keywords(item.category)
            ):
                score += 20
                reasons.append(f"分类相关：{item.category}")
            
            # 4. 协同过滤（10% 权重）- 基于访问模式
            if use_collaborative and item.access_count > 0:
                score += min(10, item.access_count)
                reasons.append("热门知识")
            
            # 5. 时效性加分（5% 权重）
            hours_since_creation = (time.time() - item.created_at) / 3600
            if hours_since_creation < 24:  # 24 小时内
                score += 5
                reasons.append("最新知识")
            
            if score > 0:
                recommendations.append({
                    "knowledge_id": item.id,
                    "topic": item.topic,
                    "category": item.category,
                    "score": score,
                    "reasons": reasons,
                    "file_path": item.file_path,
                    "summary": item.content[:150] + "..." if len(item.content) > 150 else item.content
                })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:limit]
    
    def recommend_for_task(self, task_description: str, 
                           agent_role: str = None) -> List[Dict]:
        """
        为特定任务推荐知识
        
        Args:
            task_description: 任务描述
            agent_role: Agent 角色（project_manager/developer/tester）
        
        Returns:
            推荐知识列表
        """
        # 构建上下文
        context = task_description
        if agent_role:
            context += f" {agent_role}"
        
        # 获取推荐
        recommendations = self.recommend(context, limit=5)
        
        # 根据角色过滤/排序
        if agent_role:
            role_keywords = {
                "project_manager": ["协调", "分配", "管理", "协议", "架构"],
                "developer": ["实现", "代码", "API", "开发", "工具"],
                "tester": ["测试", "用例", "验证", "质量", "评估"]
            }
            
            keywords = role_keywords.get(agent_role, [])
            for rec in recommendations:
                # 角色相关加分
                if any(kw in rec["topic"].lower() or kw in rec["category"].lower() 
                       for kw in keywords):
                    rec["score"] += 15
                    rec["reasons"].append(f"角色相关：{agent_role}")
            
            # 重新排序
            recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations
    
    def recommend_similar(self, knowledge_id: str, limit: int = 3) -> List[Dict]:
        """
        推荐相似知识（基于当前知识）
        
        Args:
            knowledge_id: 当前知识 ID
            limit: 返回数量
        
        Returns:
            相似知识列表
        """
        if knowledge_id not in self.knowledge:
            return []
        
        current_item = self.knowledge[knowledge_id]
        recommendations = []
        
        for item in self.knowledge.values():
            if item.id == knowledge_id:
                continue
            
            score = 0
            reasons = []
            
            # 相同分类
            if item.category == current_item.category:
                score += 30
                reasons.append("相同分类")
            
            # 相同标签
            common_tags = set(item.tags) & set(current_item.tags)
            if common_tags:
                score += len(common_tags) * 15
                reasons.append(f"相同标签：{', '.join(common_tags)}")
            
            # 相同作者
            if item.author == current_item.author:
                score += 10
                reasons.append("相同作者")
            
            # 相关内容
            if any(topic in current_item.related_topics for topic in [item.topic, item.id]):
                score += 25
                reasons.append("内容相关")
            
            if score > 0:
                recommendations.append({
                    "knowledge_id": item.id,
                    "topic": item.topic,
                    "category": item.category,
                    "score": score,
                    "reasons": reasons,
                    "file_path": item.file_path
                })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """获取分类关键词"""
        category_keywords = {
            "通信协议": ["MCP", "A2A", "ANP", "消息", "通信"],
            "多 Agent 架构": ["Agent", "蜂群", "拓扑", "协同", "架构"],
            "记忆系统": ["记忆", "RAG", "检索", "向量", "遗忘"],
            "上下文工程": ["上下文", "情境", "窗口", "压缩"],
            "性能评估": ["评估", "KPI", "质量", "指标"],
            "工具系统": ["工具", "MCP", "插件", "API"],
            "飞书集成": ["飞书", "机器人", "事件", "订阅"],
            "项目参考": ["ruflo", "hello-agents", "教程", "学习"]
        }
        return category_keywords.get(category, [])
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self.knowledge)
        total_access = sum(item.access_count for item in self.knowledge.values())
        
        by_category = {}
        for item in self.knowledge.values():
            cat = item.category
            if cat not in by_category:
                by_category[cat] = 0
            by_category[cat] += 1
        
        by_author = {}
        for item in self.knowledge.values():
            author = item.author
            if author not in by_author:
                by_author[author] = 0
            by_author[author] += 1
        
        # 最热门知识
        hot_items = sorted(
            self.knowledge.values(),
            key=lambda x: x.access_count,
            reverse=True
        )[:5]
        
        return {
            "total_knowledge": total,
            "total_access": total_access,
            "by_category": by_category,
            "by_author": by_author,
            "hot_topics": [item.topic for item in hot_items]
        }
    
    # ==================== 分类管理 ====================
    
    def add_category(self, name: str, description: str = "", 
                     parent: str = None) -> bool:
        """添加分类"""
        if name in self.categories:
            return False
        
        category = KnowledgeCategory(
            name=name,
            description=description,
            parent=parent
        )
        
        self.categories[name] = category
        
        if parent and parent in self.categories:
            self.categories[parent].subcategories.append(name)
        
        self._save()
        print(f"✅ 分类已添加：{name}")
        return True
    
    def list_categories(self) -> List[Dict]:
        """列出所有分类"""
        return [
            {
                "name": cat.name,
                "description": cat.description,
                "knowledge_count": cat.knowledge_count,
                "subcategories": cat.subcategories
            }
            for cat in self.categories.values()
        ]
    
    # ==================== 知识分享 ====================
    
    def share_to_agent(self, knowledge_id: str, agent_id: str) -> bool:
        """分享知识给指定 Agent"""
        item = self.get(knowledge_id)
        if not item:
            return False
        
        # 生成分享消息
        share_msg = {
            "type": "knowledge_share",
            "from": "nannan",
            "to": agent_id,
            "knowledge": {
                "id": item.id,
                "topic": item.topic,
                "category": item.category,
                "summary": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "file_path": item.file_path,
                "tags": item.tags
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存分享消息（实际应该发送到 Agent 消息队列）
        share_file = f"memory/shares/{agent_id}_{knowledge_id}.json"
        Path(share_file).parent.mkdir(exist_ok=True)
        with open(share_file, 'w', encoding='utf-8') as f:
            json.dump(share_msg, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 知识已分享给 {agent_id}: {item.topic}")
        return True
    
    def share_to_all_agents(self, knowledge_id: str) -> Dict[str, bool]:
        """分享给所有 Agent"""
        agents = ["project_manager", "developer", "tester", "nannan"]
        results = {}
        
        for agent in agents:
            results[agent] = self.share_to_agent(knowledge_id, agent)
        
        return results
    
    # ==================== 导入导出 ====================
    
    def import_from_file(self, file_path: str, topic: str, 
                         author: str, category: str = "项目参考") -> str:
        """从文件导入知识"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取前 500 字作为摘要
        summary = content[:500] + "..." if len(content) > 500 else content
        
        # 添加知识
        knowledge_id = self.add(
            topic=topic,
            content=summary,
            author=author,
            category=category,
            file_path=str(path),
            tags=["文件导入", path.stem]
        )
        
        print(f"✅ 知识已导入：{topic} ({file_path})")
        return knowledge_id
    
    def export_to_markdown(self, output_path: str = "memory/知识库导出.md"):
        """导出知识库为 Markdown"""
        lines = [
            "# 多 Agent 共享知识库",
            "",
            f"> 导出时间：{datetime.now().isoformat()}",
            f"> 知识总数：{len(self.knowledge)}",
            "",
            "---",
            "",
            "## 📊 统计信息",
            ""
        ]
        
        stats = self.get_statistics()
        lines.append(f"- **总知识数**: {stats['total_knowledge']}")
        lines.append(f"- **总访问次数**: {stats['total_access']}")
        lines.append("")
        
        lines.append("### 按分类统计")
        lines.append("")
        for cat, count in stats['by_category'].items():
            lines.append(f"- {cat}: {count}")
        lines.append("")
        
        lines.append("### 按作者统计")
        lines.append("")
        for author, count in stats['by_author'].items():
            lines.append(f"- {author}: {count}")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("## 📚 知识列表")
        lines.append("")
        
        for item in self.list_all(limit=100):
            lines.append(f"### {item.topic}")
            lines.append("")
            lines.append(f"- **ID**: {item.id}")
            lines.append(f"- **分类**: {item.category}")
            lines.append(f"- **作者**: {item.author}")
            lines.append(f"- **标签**: {', '.join(item.tags)}")
            lines.append(f"- **访问次数**: {item.access_count}")
            lines.append(f"- **创建时间**: {datetime.fromtimestamp(item.created_at).isoformat()}")
            lines.append("")
            lines.append("**内容摘要**:")
            lines.append("")
            lines.append(f"```")
            lines.append(item.content[:500])
            lines.append(f"```")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ 知识库已导出：{output_path}")
        return output_path
    
    # ==================== 内部方法 ====================
    
    def _record_access(self, knowledge_id: str):
        """记录访问"""
        if knowledge_id in self.knowledge:
            item = self.knowledge[knowledge_id]
            item.access_count += 1
            item.last_accessed = time.time()
            self._save()
    
    def _init_categories(self):
        """初始化分类"""
        for name, desc in self.DEFAULT_CATEGORIES.items():
            self.add_category(name, desc)
    
    def _save(self):
        """保存到文件"""
        data = {
            "knowledge": {k: v.to_dict() for k, v in self.knowledge.items()},
            "categories": {k: v.__dict__ for k, v in self.categories.items()},
            "last_updated": datetime.now().isoformat()
        }
        
        path = Path(self.storage_path)
        path.parent.mkdir(exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """从文件加载"""
        path = Path(self.storage_path)
        if not path.exists():
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载知识
        for k, v in data.get("knowledge", {}).items():
            self.knowledge[k] = KnowledgeItem.from_dict(v)
        
        # 加载分类
        for k, v in data.get("categories", {}).items():
            self.categories[k] = KnowledgeCategory(**v)
        
        print(f"✅ 知识库已加载：{len(self.knowledge)} 条知识")


# ==================== 快捷函数 ====================

def create_knowledge_base() -> KnowledgeBase:
    """创建知识库实例"""
    return KnowledgeBase()


def init_sample_knowledge(kb: KnowledgeBase):
    """初始化示例知识"""
    print("\n📚 初始化示例知识...")
    
    # 添加囡囡已学的知识
    kb.add(
        topic="Ch10 通信协议学习",
        content="""
学习了 hello-agents Ch10 通信协议，包括：
1. MCP (Model Context Protocol) - 模型上下文协议
2. A2A (Agent to Agent) - Agent 间通信协议
3. ANP (Agent Network Protocol) - Agent 网络协议

推荐方案：A2A + 自定义扩展，适合主人的 4 个 Agent 团队。

已实现完整的消息格式、消息队列、4 个 Agent 角色。
        """,
        author="nannan",
        category="通信协议",
        tags=["hello-agents", "Ch10", "A2A", "MCP"],
        file_path="memory/Ch10 通信协议学习笔记.md"
    )
    
    kb.add(
        topic="ruvnet/ruflo 项目学习",
        content="""
ruvnet/ruflo (Claude-Flow) 是领先的 Agent 编排平台：
- 66 个自学习 Agent
- 213 个 MCP 工具
- 分布式蜂群智能
- 企业级架构

囡囡可以学习：
1. 蜂群拓扑（mesh/star/hierarchical）
2. MCP 插件系统
3. CLI 工具设计
4. 分布式部署
        """,
        author="nannan",
        category="项目参考",
        tags=["ruflo", "Claude-Flow", "蜂群智能", "MCP"],
        file_path="memory/双项目深度学习报告.md"
    )
    
    kb.add(
        topic="多 Agent 通信协议实现",
        content="""
囡囡已实现完整的多 Agent 通信协议：
- AgentMessage 类：完整消息格式
- MessageQueue 类：消息队列管理
- ProjectManagerAgent：项目经理协调器
- DeveloperAgent：开发工程师
- TesterAgent：测试工程师
- NannanAgent：囡囡智能助手（意图预测 + 质量评估）

测试通过，可以立即使用！
        """,
        author="nannan",
        category="多 Agent 架构",
        tags=["协议实现", "Python", "测试通过"],
        file_path="memory/multi_agent_protocol.py"
    )
    
    kb.add(
        topic="飞书多机器人配置教程",
        content="""
囡囡编写了完整的飞书多机器人配置教程：
1. 创建飞书应用（4 个）
2. 配置机器人
3. 配置事件订阅
4. 配置权限
5. 部署后端服务
6. 添加应用到群
7. 测试验证
8. 故障排查

包含完整的 Flask 后端代码和配置示例。
        """,
        author="nannan",
        category="飞书集成",
        tags=["飞书", "机器人", "配置教程", "Flask"],
        file_path="memory/飞书多机器人配置教程.md"
    )
    
    kb.add(
        topic="ReAct+Reflection 决策引擎",
        content="""
基于 hello-agents Ch4 经典范式：
- ReAct (Reasoning + Acting)
- Plan-and-Solve
- Reflection (反思改进)

囡囡可以优化当前决策逻辑：
当前：主人问题 → 意图识别 → 工具调用 → 回复
优化：主人问题 → ReAct 推理 → 工具调用 → 反思 → 回复

预期决策质量提升 30%
        """,
        author="nannan",
        category="记忆系统",
        tags=["ReAct", "Reflection", "决策优化"],
        related_topics=["Ch10 通信协议学习", "多 Agent 通信协议实现"]
    )
    
    print(f"✅ 已添加 {len(kb.knowledge)} 条示例知识")


# ==================== 运行示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("📚 多 Agent 共享知识库演示")
    print("=" * 60)
    
    # 创建知识库
    kb = create_knowledge_base()
    
    # 初始化示例知识
    init_sample_knowledge(kb)
    
    # 显示统计
    print("\n📊 知识库统计:")
    stats = kb.get_statistics()
    print(f"   总知识数：{stats['total_knowledge']}")
    print(f"   总访问：{stats['total_access']}")
    print(f"   分类：{len(stats['by_category'])}")
    print(f"   作者：{len(stats['by_author'])}")
    
    # 搜索演示
    print("\n🔍 搜索演示:")
    results = kb.search("通信协议", limit=3)
    for item in results:
        print(f"   - {item.topic} (访问：{item.access_count})")
    
    # 分类演示
    print("\n📁 分类演示:")
    for cat in kb.list_categories():
        print(f"   - {cat['name']}: {cat['knowledge_count']} 条")
    
    # 分享演示
    print("\n📨 分享演示:")
    if kb.knowledge:
        first_id = list(kb.knowledge.keys())[0]
        kb.share_to_all_agents(first_id)
    
    # 导出演示
    print("\n💾 导出演示:")
    kb.export_to_markdown("memory/知识库导出.md")
    
    print("\n" + "=" * 60)
    print("✅ 知识库演示完成！")
    print("=" * 60)
