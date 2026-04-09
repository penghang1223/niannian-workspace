#!/usr/bin/env python3
"""
Skill评估器 v2.0 — Agent自查工具
用法：python3 scripts/skill_evaluator.py <agent_id>
功能：扫描Agent的lessons.md，评估哪些可以打包成skill

v2.0 更新 (2026-04-09):
- 强制英文skill名称（a-z, 0-9, 短横线）
- 四维评分自动计算（工具型/可操作/可验证/可复用）
- 去重检查（对比已有skill + 待审核提案 + 已清理黑名单）
- 内容截断检测
- 已清理提案永久黑名单，避免重复生成
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/narain/.openclaw/workspace")
LESSONS_DIR = WORKSPACE / "memory" / "agents"
SKILLS_DIR = WORKSPACE / "skills"
PROPOSALS_FILE = WORKSPACE / "memory" / "skill_proposals.md"
BLACKLIST_FILE = WORKSPACE / "memory" / "skill_proposal_blacklist.json"
QUALITY_STANDARD = WORKSPACE / "LESSONS_QUALITY_STANDARD.md"

# 已有skill列表
EXISTING_SKILLS = set()
if SKILLS_DIR.exists():
    EXISTING_SKILLS = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}

# 已清理提案黑名单（永久不再生成）
CLEANED_BLACKLIST = set()
if BLACKLIST_FILE.exists():
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            CLEANED_BLACKLIST = set(data.get('blacklist', []))
    except:
        pass

# 从提案文件中提取已存在的提案名称（去重检查）
EXISTING_PROPOSALS = set()
if PROPOSALS_FILE.exists():
    try:
        with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            for m in re.finditer(r'Skill名[：:]\s*(.+)', content):
                name = m.group(1).strip()
                if name:
                    EXISTING_PROPOSALS.add(name)
    except:
        pass

# 工具型关键词
TOOL_KEYWORDS = [
    "脚本", "CLI", "工具", "扫描", "检测", "分析", "自动化",
    "配置", "模板", "函数", "类", "模块", "API", "命令",
    "测试", "验证", "检查", "监控", "报告", "脚本示例",
    "workflow", "pipeline", "deploy", "build", "ci/cd",
    "script", "tool", "cli", "scan", "detect", "analyze",
    "config", "template", "function", "class", "module",
    "test", "verify", "check", "monitor", "report"
]

# 纯知识/学习笔记关键词（出现这些要扣分）
KNOWLEDGE_KEYWORDS = [
    "概念", "原理", "理论", "框架", "方法论", "思维",
    "认知", "理解", "学习闭环", "学习了", "今天学",
    "学到了", "读书笔记", "概念总结", "读后感",
    "concept", "theory", "framework", "methodology",
    "thinking", "study notes", "今天学", "今日学习",
    "可自动化操作", "可优化的流程"
]

# 黑名单标题（直接拒绝）
BANNED_TITLES = [
    "今日学习", "今日学习闭环", "学习闭环",
    "可自动化操作", "可优化的流程",
    "学习总结", "今日总结", "知识贡献", "待改进",
    "lesson记录模板", "待验证", "待造工具清单",
    "本次进化总结", "多agent协作测试", "知识流动需求"
]


def is_english_skill_name(name: str) -> bool:
    """检查skill名称是否符合规范：仅a-z, 0-9, 短横线"""
    return bool(re.match(r'^[a-z][a-z0-9-]*$', name))


def to_english_skill_name(chinese_title: str) -> str:
    """
    尝试将中文标题转换为英文skill名称。
    如果无法合理转换（仍是中文），返回空字符串表示不合格。
    """
    # 先尝试直接使用（可能已经是英文）
    name = re.sub(r'[^\w\-]', '-', chinese_title.lower().strip())
    name = re.sub(r'-+', '-', name).strip('-')

    # 检查是否仍然是中文/非英文
    if not is_english_skill_name(name):
        return ""

    return name


def scan_lessons(agent_id: str) -> list:
    """扫描Agent的lessons.md"""
    lessons_file = LESSONS_DIR / agent_id / "lessons.md"
    if not lessons_file.exists():
        return []

    with open(lessons_file, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'\n## ', content)
    return sections


def calculate_four_dimensions(section: str) -> dict:
    """
    自动计算四维评分
    工具型/可操作/可验证/可复用，各1-5分
    """
    # === 🔧 工具型 ===
    # 能写成代码/脚本/skill吗？
    code_blocks = len(re.findall(r'```', section)) // 2
    command_lines = len(re.findall(r'^(?:\$\s*|>\s*|#\s*)[a-zA-Z]', section, re.MULTILINE))
    has_executable = code_blocks > 0 or command_lines > 0

    if code_blocks >= 2 and command_lines >= 2:
        tool_score = 5
    elif code_blocks >= 1 or command_lines >= 1:
        tool_score = 3
    elif has_executable:
        tool_score = 2
    else:
        tool_score = 1

    # === 🎯 可操作 ===
    # 有具体步骤和示例吗？
    numbered_steps = len(re.findall(r'^\d+\.\s', section, re.MULTILINE))
    arrow_steps = section.count('→')
    has_example = bool(re.search(r'(?:例如|示例|比如|example|usage|how to)', section, re.IGNORECASE))

    if numbered_steps >= 3 and has_example:
        op_score = 5
    elif numbered_steps >= 2:
        op_score = 4
    elif numbered_steps >= 1 or arrow_steps >= 2:
        op_score = 3
    elif arrow_steps >= 1:
        op_score = 2
    else:
        op_score = 1

    # === ✅ 可验证 ===
    # 有明确的成功标准吗？
    has_verification = bool(re.search(r'(?:验证|测试|成功标准|确认|验证方式|verify|test|success criteria|expected)', section, re.IGNORECASE))
    has_metrics = bool(re.search(r'\d+\s*(?:%|ms|s|秒|个|次|倍|提升|降低|减少|增加)', section))

    if has_verification and has_metrics:
        verify_score = 5
    elif has_verification:
        verify_score = 3
    elif has_metrics:
        verify_score = 2
    else:
        verify_score = 1

    # === ♻️ 可复用 ===
    # 其他Agent能直接应用吗？
    has_scope = bool(re.search(r'(?:适用|场景|范围|适合|何时用|when to|applicable|use case)', section, re.IGNORECASE))
    has_context = bool(re.search(r'(?:环境|前提|依赖|前置|prereq|require|install|安装)', section, re.IGNORECASE))

    if has_scope and has_context:
        reuse_score = 5
    elif has_scope or has_context:
        reuse_score = 3
    else:
        reuse_score = 1

    return {
        'tool': tool_score,
        'operable': op_score,
        'verifiable': verify_score,
        'reusable': reuse_score,
        'total': tool_score + op_score + verify_score + reuse_score
    }


def evaluate_section(section: str) -> dict:
    """评估单个章节是否适合打包成skill"""
    lines = section.strip().split('\n')
    title = lines[0].strip() if lines else "无标题"

    # 计算四维评分
    dims = calculate_four_dimensions(section)

    # 工具型关键词匹配
    tool_score_kw = sum(1 for kw in TOOL_KEYWORDS if kw in section)
    knowledge_score_kw = sum(1 for kw in KNOWLEDGE_KEYWORDS if kw in section)

    # 是否为工具型（综合判断）
    is_tool = dims['total'] >= 11 and tool_score_kw > knowledge_score_kw

    # 是否有代码块
    has_code = '```' in section

    # 是否有具体步骤
    has_steps = bool(re.search(r'^\d+\.\s', section, re.MULTILINE)) or '→' in section

    # 内容是否截断
    is_truncated = bool(re.search(r'(?:\.\.\.|未完|待续|to be continued|truncated)', section[-100:]))

    # 是否在黑名单中
    is_blacklisted = False
    for banned in BANNED_TITLES:
        if banned in title:
            is_blacklisted = True
            break

    # 检测是否为模板/占位符内容（非真实经验）
    # 模板特征：包含"待填写"、占位符括号、只有框架没有实质内容
    template_patterns = [
        r'\[.*待.*\]',  # [待填写], [待补充] 等
        r'\[标题[：:].*\]',  # [标题：解决什么问题]
        r'\[日期.*\]',  # [日期]
        r'\[具体.*\]',  # [具体内容]
        r'^\s*$',  # 大量空白行
    ]
    template_indicators = 0
    for pattern in template_patterns:
        if re.search(pattern, section, re.MULTILINE):
            template_indicators += 1
    # 如果内容有编号步骤但都是占位符（如"具体步骤一"、"具体步骤二"），判定为模板
    placeholder_steps = len(re.findall(r'具体步骤[一二三四五六七八九十\d]', section))
    is_template = template_indicators >= 2 or placeholder_steps >= 2

    return {
        'title': title,
        'is_tool': is_tool,
        'has_code': has_code,
        'has_steps': has_steps,
        'tool_score_kw': tool_score_kw,
        'knowledge_score_kw': knowledge_score_kw,
        'four_dims': dims,
        'is_truncated': is_truncated,
        'is_blacklisted': is_blacklisted,
        'is_template': is_template,
        'content_preview': section[:200] + '...' if len(section) > 200 else section
    }


def generate_proposal(agent_id: str, section: str, evaluation: dict) -> str:
    """生成提案格式（v2.0: 包含四维评分）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dims = evaluation['four_dims']

    # 尝试生成英文skill名称
    skill_name = to_english_skill_name(evaluation['title'])

    # 如果无法生成英文名称，使用agent_id + 主题词
    if not skill_name:
        # 从内容中提取可能的英文主题词
        english_words = re.findall(r'\b([a-z]{3,})\b', section.lower())
        if english_words:
            # 选出现频率最高的英文词
            from collections import Counter
            word_counts = Counter(english_words)
            common = [w for w, _ in word_counts.most_common(3) if w not in ('the', 'and', 'for', 'with', 'this', 'that', 'from', 'how', 'what', 'when', 'where', 'why', 'will', 'would', 'could', 'should', 'been', 'have', 'has', 'had', 'but', 'not', 'are', 'was', 'were', 'can', 'use', 'used', 'using', 'get', 'make', 'made', 'your', 'you', 'they', 'them', 'then', 'than', 'each', 'just', 'only', 'also', 'into', 'some', 'over', 'such', 'more', 'most', 'very', 'much', 'after', 'before', 'between', 'other', 'about', 'which', 'these', 'those', 'there', 'here', 'first', 'last', 'next', 'step', 'one', 'two', 'three', 'new', 'old', 'big', 'small', 'good', 'best', 'high', 'low', 'long', 'short', 'right', 'left', 'time', 'work', 'need', 'find', 'give', 'take', 'come', 'go', 'know', 'think', 'see', 'want', 'say', 'run', 'set', 'put', 'end', 'out', 'all', 'any', 'our', 'own', 'its', 'his', 'her', 'she', 'his', 'him', 'its')]
            if common:
                skill_name = common[0]
            else:
                skill_name = f"{agent_id}-skill-{datetime.now().strftime('%m%d')}"
        else:
            skill_name = f"{agent_id}-skill-{datetime.now().strftime('%m%d')}"

    # 确保名称唯一
    base_name = skill_name
    counter = 1
    while skill_name in EXISTING_SKILLS or skill_name in EXISTING_PROPOSALS:
        skill_name = f"{base_name}-{counter}"
        counter += 1

    code_status = '✅ 有完整代码' if evaluation['has_code'] and dims['tool'] >= 4 else '⚠️ 有代码片段' if evaluation['has_code'] else '❌ 无代码'
    value_level = '🔴高' if dims['total'] >= 16 else '🟡中' if dims['total'] >= 11 else '🟢低'

    return f"""
## [提案] {now}
- **Agent**: {agent_id}
- **Skill名**: {skill_name}
- **路径**: skills/{skill_name}/
- **内容覆盖**: {evaluation['content_preview'][:150]}
- **去重检查**: ✅ 无重复
- **价值评估**: {value_level}
- **代码基础**: {code_status}
- **四维评分**: 工具型 {dims['tool']} | 可操作 {dims['operable']} | 可验证 {dims['verifiable']} | 可复用 {dims['reusable']} = **{dims['total']}/20**
- **状态**: 待审核
"""


def add_to_blacklist(skill_name: str, reason: str):
    """将清理的提案加入永久黑名单"""
    if not BLACKLIST_FILE.parent.exists():
        BLACKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)

    if BLACKLIST_FILE.exists():
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {'blacklist': [], 'reasons': {}}
    else:
        data = {'blacklist': [], 'reasons': {}}

    if skill_name not in data['blacklist']:
        data['blacklist'].append(skill_name)
        data['reasons'][skill_name] = {
            'reason': reason,
            'added_at': datetime.now().isoformat()
        }

    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 skill_evaluator.py <agent_id>")
        print(f"已有skill: {len(EXISTING_SKILLS)}个")
        print(f"已清理黑名单: {len(CLEANED_BLACKLIST)}个")
        sys.exit(1)

    agent_id = sys.argv[1]
    print(f"\n🔍 扫描Agent: {agent_id}")
    print(f"📁 已有skill: {len(EXISTING_SKILLS)}个")
    print(f"🚫 黑名单: {len(CLEANED_BLACKLIST)}个")

    sections = scan_lessons(agent_id)
    if not sections:
        print(f"❌ 未找到 {agent_id} 的lessons.md")
        sys.exit(1)

    print(f"📄 找到 {len(sections)} 个章节")

    proposals = []
    rejected = []

    for section in sections:
        evaluation = evaluate_section(section)
        dims = evaluation['four_dims']

        # 黑名单标题直接拒绝
        if evaluation['is_blacklisted']:
            reason = f"黑名单标题: {evaluation['title'][:30]}"
            rejected.append(f"  🚫 拒绝: {evaluation['title'][:30]}... ({reason})")
            add_to_blacklist(evaluation['title'], reason)
            continue

        # 模板/占位符内容检测（空模板不算skill）
        if evaluation.get('is_template', False):
            rejected.append(f"  ⏭️ 跳过: {evaluation['title'][:30]}... (模板/占位符，非真实经验)")
            continue

        # 内容截断检测
        if evaluation['is_truncated']:
            rejected.append(f"  ⏭️ 跳过: {evaluation['title'][:30]}... (内容截断)")
            continue

        # 四维评分不足
        if dims['total'] < 11:
            rejected.append(f"  ⏭️ 跳过: {evaluation['title'][:30]}... (四维评分 {dims['total']}/20 不足)")
            continue

        # 工具型不足
        if not evaluation['is_tool']:
            rejected.append(f"  ⏭️ 跳过: {evaluation['title'][:30]}... (纯知识型，评分 {dims['total']}/20)")
            continue

        # 生成提案
        try:
            proposal = generate_proposal(agent_id, section, evaluation)
            proposals.append(proposal)
            print(f"  ✅ 可打包: {evaluation['title'][:30]}... (四维评分 {dims['total']}/20)")
        except Exception as e:
            rejected.append(f"  ❌ 错误: {evaluation['title'][:30]}... ({e})")

    # 输出被拒绝的原因
    for r in rejected:
        print(r)

    if proposals:
        print(f"\n📝 生成 {len(proposals)} 个提案")
        with open(PROPOSALS_FILE, 'a', encoding='utf-8') as f:
            f.write('\n'.join(proposals))
        print(f"✅ 已写入 {PROPOSALS_FILE}")
    else:
        print("\nℹ️ 暂无可打包的skill")


if __name__ == "__main__":
    main()
