#!/usr/bin/env python3
"""
Skill评估器 — Agent自查工具
用法：python3 scripts/skill_evaluator.py <agent_id>
功能：扫描Agent的lessons.md，评估哪些可以打包成skill
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/narain/.openclaw/workspace")
LESSONS_DIR = WORKSPACE / "memory" / "agents"
SKILLS_DIR = WORKSPACE / "skills"
PROPOSALS_FILE = WORKSPACE / "memory" / "skill_proposals.md"
QUALITY_STANDARD = WORKSPACE / "LESSONS_QUALITY_STANDARD.md"

# 已有skill列表
EXISTING_SKILLS = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()] if SKILLS_DIR.exists() else []

# 工具型关键词（能写成代码/skill的）
TOOL_KEYWORDS = [
    "脚本", "CLI", "工具", "扫描", "检测", "分析", "自动化",
    "配置", "模板", "函数", "类", "模块", "API", "命令",
    "测试", "验证", "检查", "监控", "报告", "脚本示例",
    "script", "tool", "cli", "scan", "detect", "analyze",
    "config", "template", "function", "class", "module",
    "test", "verify", "check", "monitor", "report"
]

# 纯知识关键词（不适合打包的）
KNOWLEDGE_KEYWORDS = [
    "概念", "原理", "理论", "框架", "方法论", "思维",
    "认知", "理解", "学习", "经验", "总结", "回顾",
    "concept", "theory", "framework", "methodology", "thinking"
]


def scan_lessons(agent_id: str) -> list:
    """扫描Agent的lessons.md"""
    lessons_file = LESSONS_DIR / agent_id / "lessons.md"
    if not lessons_file.exists():
        return []

    with open(lessons_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按##分割章节
    sections = re.split(r'\n## ', content)
    return sections


def evaluate_section(section: str) -> dict:
    """评估单个章节是否适合打包成skill"""
    lines = section.strip().split('\n')
    title = lines[0] if lines else "无标题"

    # 计算工具型关键词匹配数
    tool_score = sum(1 for kw in TOOL_KEYWORDS if kw in section)
    knowledge_score = sum(1 for kw in KNOWLEDGE_KEYWORDS if kw in section)

    # 判断是否为工具型
    is_tool = tool_score > knowledge_score

    # 检查是否有代码块
    has_code = '```' in section

    # 检查是否有具体步骤
    has_steps = bool(re.search(r'\d+\.\s', section)) or '→' in section

    return {
        'title': title,
        'is_tool': is_tool,
        'has_code': has_code,
        'has_steps': has_steps,
        'tool_score': tool_score,
        'knowledge_score': knowledge_score,
        'content_preview': section[:200] + '...' if len(section) > 200 else section
    }


def check_duplicates(skill_name: str) -> bool:
    """检查是否与已有skill重复"""
    return skill_name in EXISTING_SKILLS


def generate_proposal(agent_id: str, section: str, evaluation: dict) -> str:
    """生成提案格式"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    skill_name = re.sub(r'[^\w\-]', '-', evaluation['title'].lower().strip())
    skill_name = re.sub(r'-+', '-', skill_name).strip('-')

    return f"""
## [提案] {now}
- **Agent**: {agent_id}
- **Skill名**: {skill_name}
- **路径**: skills/{skill_name}/
- **内容覆盖**: {evaluation['content_preview'][:100]}
- **去重检查**: {'❌ 重复' if check_duplicates(skill_name) else '✅ 无重复'}
- **价值评估**: {'🔴高' if evaluation['tool_score'] > 5 else '🟡中' if evaluation['tool_score'] > 2 else '🟢低'}
- **代码基础**: {'✅ 有代码' if evaluation['has_code'] else '❌ 无代码'}
- **状态**: 待审核
"""


def main():
    if len(sys.argv) < 2:
        print("用法: python3 skill_evaluator.py <agent_id>")
        print(f"已有skill: {', '.join(EXISTING_SKILLS)}")
        sys.exit(1)

    agent_id = sys.argv[1]
    print(f"\n🔍 扫描Agent: {agent_id}")
    print(f"📁 已有skill: {len(EXISTING_SKILLS)}个")

    sections = scan_lessons(agent_id)
    if not sections:
        print(f"❌ 未找到 {agent_id} 的lessons.md")
        sys.exit(1)

    print(f"📄 找到 {len(sections)} 个章节")

    proposals = []
    for section in sections:
        evaluation = evaluate_section(section)
        if evaluation['is_tool'] and evaluation['has_code']:
            proposal = generate_proposal(agent_id, section, evaluation)
            proposals.append(proposal)
            print(f"  ✅ 可打包: {evaluation['title'][:30]}...")
        else:
            print(f"  ⏭️ 跳过: {evaluation['title'][:30]}... (纯知识型)")

    if proposals:
        print(f"\n📝 生成 {len(proposals)} 个提案")
        # 追加到提案文件
        with open(PROPOSALS_FILE, 'a', encoding='utf-8') as f:
            f.write('\n'.join(proposals))
        print(f"✅ 已写入 {PROPOSALS_FILE}")
    else:
        print("\nℹ️ 暂无可打包的skill")


if __name__ == "__main__":
    main()
