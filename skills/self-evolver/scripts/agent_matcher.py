"""
Agent能力匹配器 — 自动分析任务类型，匹配最适合的Agent
Usage: from agent_matcher import match_agent; agent = match_agent("写前端页面")
"""

# Agent 能力画像
AGENT_PROFILES = {
    "frontend_dev": {
        "name": "霓裳",
        "strengths": ["前端", "UI", "CSS", "JavaScript", "React", "Vue", "页面", "布局", "组件", "响应式", "可视化", "图表"],
        "weaknesses": ["后端", "数据库", "安全", "测试"],
        "speed": 8,  # 1-10
        "quality": 9,
    },
    "dev_engineer": {
        "name": "玄机",
        "strengths": ["后端", "Python", "Node.js", "API", "数据库", "脚本", "工具", "架构", "性能"],
        "weaknesses": ["前端UI", "设计", "文案"],
        "speed": 7,
        "quality": 8,
    },
    "qa_engineer": {
        "name": "鉴微",
        "strengths": ["测试", "质量", "TDD", "验证", "边界", "异常", "审查", "Bug"],
        "weaknesses": ["设计", "创意", "文案"],
        "speed": 6,
        "quality": 10,
    },
    "product_manager": {
        "name": "望舒",
        "strengths": ["需求", "PRD", "分析", "竞品", "用户", "产品", "战略", "规划"],
        "weaknesses": ["代码", "技术实现"],
        "speed": 7,
        "quality": 9,
    },
    "chief_cute_officer": {
        "name": "岁岁",
        "strengths": ["内容", "创意", "文案", "热点", "社交媒体", "营销", "气氛"],
        "weaknesses": ["技术", "代码", "测试"],
        "speed": 8,
        "quality": 7,
    },
    "taiyi": {
        "name": "太一",
        "strengths": ["研究", "学习", "技术调研", "新工具", "分析", "报告"],
        "weaknesses": ["执行", "落地"],
        "speed": 6,
        "quality": 8,
    },
    "lingxi": {
        "name": "灵犀",
        "strengths": ["创意", "内容", "视觉", "AI生成", "图片", "视频"],
        "weaknesses": ["技术细节", "代码"],
        "speed": 7,
        "quality": 8,
    },
    "jinghong": {
        "name": "惊鸿",
        "strengths": ["小说", "故事", "角色", "对话", "情节", "文学"],
        "weaknesses": ["技术", "代码"],
        "speed": 9,
        "quality": 9,
    },
    "tiangong": {
        "name": "天工",
        "strengths": ["架构", "设计模式", "系统设计", "技术方案", "复杂问题"],
        "weaknesses": ["简单任务", "快速迭代"],
        "speed": 5,
        "quality": 10,
    },
    "shichen": {
        "name": "司辰",
        "strengths": ["内容创作", "文案", "编辑", "校对", "格式"],
        "weaknesses": ["技术", "代码"],
        "speed": 7,
        "quality": 8,
    },
    "yueying": {
        "name": "月影",
        "strengths": ["数据", "分析", "统计", "可视化", "报告", "Python"],
        "weaknesses": ["前端UI", "设计"],
        "speed": 7,
        "quality": 8,
    },
    "zhiming": {
        "name": "执明",
        "strengths": ["安全", "审计", "漏洞", "合规", "OWASP", "渗透"],
        "weaknesses": ["创意", "设计"],
        "speed": 6,
        "quality": 9,
    },
}


def match_agent(task_description: str, prefer_speed: bool = False) -> dict:
    """
    根据任务描述匹配最适合的Agent
    
    Args:
        task_description: 任务描述（中文）
        prefer_speed: 是否优先速度（默认优先质量）
    
    Returns:
        包含 agent_id, name, score 的字典
    
    Example:
        result = match_agent("写一个React组件")
        # Returns: {"agent_id": "frontend_dev", "name": "霓裳", "score": 9.2}
    """
    task_lower = task_description.lower()
    scores = []
    
    for agent_id, profile in AGENT_PROFILES.items():
        score = 0
        
        # 检查优势关键词匹配
        for strength in profile["strengths"]:
            if strength in task_lower:
                score += 2
        
        # 检查劣势关键词匹配（扣分）
        for weakness in profile["weaknesses"]:
            if weakness in task_lower:
                score -= 1
        
        # 综合评分
        if prefer_speed:
            final_score = score * 0.3 + profile["speed"] * 0.7
        else:
            final_score = score * 0.5 + profile["quality"] * 0.5
        
        scores.append({
            "agent_id": agent_id,
            "name": profile["name"],
            "score": round(final_score, 1),
            "match_reason": _get_match_reason(task_lower, profile),
        })
    
    # 按分数排序
    scores.sort(key=lambda x: x["score"], reverse=True)
    
    return scores[0] if scores else None


def _get_match_reason(task: str, profile: dict) -> str:
    """生成匹配原因"""
    matched = [s for s in profile["strengths"] if s in task]
    if matched:
        return f"匹配关键词：{', '.join(matched[:3])}"
    return "综合能力匹配"


def get_top_agents(task_description: str, n: int = 3) -> list:
    """获取前N个最适合的Agent"""
    task_lower = task_description.lower()
    scores = []
    
    for agent_id, profile in AGENT_PROFILES.items():
        score = 0
        for strength in profile["strengths"]:
            if strength in task_lower:
                score += 2
        for weakness in profile["weaknesses"]:
            if weakness in task_lower:
                score -= 1
        
        final_score = score * 0.5 + profile["quality"] * 0.5
        scores.append({
            "agent_id": agent_id,
            "name": profile["name"],
            "score": round(final_score, 1),
        })
    
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:n]


# Quick test
if __name__ == "__main__":
    print("🎯 Agent能力匹配器测试")
    print("=" * 50)
    
    test_tasks = [
        "写一个React组件",
        "测试登录功能",
        "写PRD文档",
        "安全审计",
        "数据分析报告",
        "写小说章节",
        "Python脚本开发",
        "小红书内容创意",
    ]
    
    for task in test_tasks:
        result = match_agent(task)
        print(f"\n📋 任务：{task}")
        print(f"   → {result['name']}（分数：{result['score']}）")
        print(f"   {result['match_reason']}")
