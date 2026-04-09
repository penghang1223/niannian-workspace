#!/usr/bin/env python3
"""
虚拟读者 Skill v3.0 - 跨章记忆 + 严格编辑团队
在 v2.0 基础上新增：跨章记忆、角色追踪、时间线校验、伏笔管理、修改验证
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


# ═══════════════════════════════════════════════════════════
# 第一部分：跨章记忆系统
# ═══════════════════════════════════════════════════════════


class ForeshadowStatus(Enum):
    """伏笔状态"""
    PLANTED = "已埋"      # 伏笔已埋下
    RESOLVED = "已收"     # 伏笔已回收
    UNRESOLVED = "未收"   # 伏笔应收未收（超期）


@dataclass
class CharacterState:
    """角色状态快照"""
    name: str
    location: str = "未知"
    emotion: str = "平静"
    abilities: list = field(default_factory=list)
    relationships: dict = field(default_factory=dict)  # {角色名: 关系描述}
    status: str = "正常"  # 正常/受伤/死亡/昏迷 等
    last_chapter: int = 0

    def to_context(self) -> str:
        """生成角色上下文描述"""
        parts = [f"【{self.name}】"]
        parts.append(f"  位置：{self.location}")
        parts.append(f"  情绪：{self.emotion}")
        parts.append(f"  状态：{self.status}")
        if self.abilities:
            parts.append(f"  能力：{', '.join(self.abilities)}")
        if self.relationships:
            rels = [f"{k}({v})" for k, v in self.relationships.items()]
            parts.append(f"  关系：{', '.join(rels)}")
        parts.append(f"  最后出场：第{self.last_chapter}章")
        return "\n".join(parts)


@dataclass
class TimelineEvent:
    """时间线事件"""
    chapter: int
    time_marker: str  # 时间标记（如"第三天黎明"、"一个月后"）
    event: str
    characters: list = field(default_factory=list)

    def to_context(self) -> str:
        return f"  第{self.chapter}章 [{self.time_marker}] {self.event}（涉及：{', '.join(self.characters)}）"


@dataclass
class Foreshadowing:
    """伏笔"""
    id: str
    description: str
    planted_chapter: int
    planted_text: str  # 埋伏笔的原文
    expected_resolve_chapter: Optional[int] = None  # 预期回收章节
    resolved_chapter: Optional[int] = None
    resolved_text: Optional[str] = None
    status: ForeshadowStatus = ForeshadowStatus.PLANTED

    def to_context(self) -> str:
        status_icon = {"已埋": "🟡", "已收": "🟢", "未收": "🔴"}
        icon = status_icon.get(self.status.value, "⚪")
        line = f"  {icon} [{self.id}] {self.description}（第{self.planted_chapter}章埋下）"
        if self.status == ForeshadowStatus.RESOLVED:
            line += f" → 第{self.resolved_chapter}章回收"
        elif self.expected_resolve_chapter:
            line += f" → 预期第{self.expected_resolve_chapter}章回收"
        return line


@dataclass
class ChapterSummary:
    """章节摘要"""
    chapter_num: int
    title: str = ""
    summary: str = ""
    key_events: list = field(default_factory=list)
    characters_appeared: list = field(default_factory=list)
    cliffhanger: str = ""  # 章末悬念
    word_count: int = 0
    score: Optional[float] = None


class CharacterTracker:
    """角色状态追踪器"""

    def __init__(self):
        self.characters: dict[str, CharacterState] = {}

    def update(self, name: str, chapter: int, **kwargs) -> CharacterState:
        """更新角色状态"""
        if name not in self.characters:
            self.characters[name] = CharacterState(name=name)
        char = self.characters[name]
        char.last_chapter = chapter
        for key, value in kwargs.items():
            if key == "abilities" and isinstance(value, str):
                if value not in char.abilities:
                    char.abilities.append(value)
            elif key == "relationships" and isinstance(value, dict):
                char.relationships.update(value)
            elif hasattr(char, key):
                setattr(char, key, value)
        return char

    def get(self, name: str) -> Optional[CharacterState]:
        return self.characters.get(name)

    def get_all_context(self) -> str:
        """生成所有角色的上下文"""
        if not self.characters:
            return "暂无角色记录。"
        return "\n".join(c.to_context() for c in self.characters.values())

    def check_consistency(self, name: str, chapter: int, **proposed) -> list[str]:
        """检查角色状态一致性，返回矛盾列表"""
        issues = []
        char = self.characters.get(name)
        if not char:
            return issues

        # 死亡角色不应再出场（除非有复活设定）
        if char.status == "死亡" and proposed.get("location") and proposed.get("status") != "复活":
            issues.append(
                f"⚠️ 角色矛盾：{name}在第{char.last_chapter}章已死亡，"
                f"但第{chapter}章仍在活动（位置：{proposed.get('location')}）"
            )

        # 昏迷角色不应正常行动
        if char.status == "昏迷" and proposed.get("emotion") not in (None, "昏迷", "苏醒"):
            issues.append(
                f"⚠️ 角色矛盾：{name}在第{char.last_chapter}章处于昏迷状态，"
                f"但第{chapter}章情绪为「{proposed.get('emotion')}」，未交代苏醒"
            )

        # 能力突然出现
        new_ability = proposed.get("abilities")
        if new_ability and isinstance(new_ability, str):
            if new_ability not in char.abilities and len(char.abilities) > 0:
                issues.append(
                    f"⚠️ 能力疑问：{name}在第{chapter}章突然使用新能力「{new_ability}」，"
                    f"已有能力为{char.abilities}，是否需要铺垫？"
                )

        return issues

    def to_dict(self) -> dict:
        return {name: asdict(char) for name, char in self.characters.items()}

    def from_dict(self, data: dict):
        for name, char_data in data.items():
            self.characters[name] = CharacterState(**char_data)


class TimelineTracker:
    """时间线追踪器"""

    def __init__(self):
        self.events: list[TimelineEvent] = []
        self._time_order: list[str] = []  # 时间标记顺序

    def add_event(self, chapter: int, time_marker: str, event: str,
                  characters: Optional[list] = None) -> TimelineEvent:
        """添加时间线事件"""
        te = TimelineEvent(
            chapter=chapter,
            time_marker=time_marker,
            event=event,
            characters=characters or []
        )
        self.events.append(te)
        if time_marker not in self._time_order:
            self._time_order.append(time_marker)
        return te

    def check_contradictions(self, chapter: int, time_marker: str,
                             event: str, characters: Optional[list] = None) -> list[str]:
        """检查时间线矛盾"""
        issues = []
        characters = characters or []

        # 检查同一角色是否在同一时间出现在不同地点
        for existing in self.events:
            if existing.time_marker == time_marker:
                common_chars = set(existing.characters) & set(characters)
                for char in common_chars:
                    if existing.event != event:
                        issues.append(
                            f"⚠️ 时间矛盾：{char}在「{time_marker}」同时出现在两个场景——"
                            f"第{existing.chapter}章「{existing.event}」vs "
                            f"第{chapter}章「{event}」"
                        )

        # 检查因果倒置（后果先于原因出现）
        # 这里用简单的章节序检查
        for existing in self.events:
            if existing.chapter > chapter and existing.time_marker == time_marker:
                issues.append(
                    f"⚠️ 时序疑问：第{chapter}章的事件「{event}」"
                    f"与第{existing.chapter}章的「{existing.event}」使用相同时间标记「{time_marker}」，"
                    f"请确认时间线是否合理"
                )

        return issues

    def get_context(self, last_n: int = 10) -> str:
        """获取最近 N 条时间线"""
        if not self.events:
            return "暂无时间线记录。"
        recent = self.events[-last_n:]
        return "\n".join(e.to_context() for e in recent)

    def to_dict(self) -> list:
        return [asdict(e) for e in self.events]

    def from_dict(self, data: list):
        self.events = [TimelineEvent(**e) for e in data]
        self._time_order = []
        for e in self.events:
            if e.time_marker not in self._time_order:
                self._time_order.append(e.time_marker)


class ForeshadowingTracker:
    """伏笔追踪器"""

    def __init__(self):
        self.foreshadowings: dict[str, Foreshadowing] = {}
        self._counter = 0

    def plant(self, description: str, chapter: int, planted_text: str,
              expected_resolve: Optional[int] = None) -> Foreshadowing:
        """埋下伏笔"""
        self._counter += 1
        fid = f"F{self._counter:03d}"
        fs = Foreshadowing(
            id=fid,
            description=description,
            planted_chapter=chapter,
            planted_text=planted_text,
            expected_resolve_chapter=expected_resolve,
            status=ForeshadowStatus.PLANTED
        )
        self.foreshadowings[fid] = fs
        return fs

    def resolve(self, fid: str, chapter: int, resolved_text: str) -> Optional[Foreshadowing]:
        """回收伏笔"""
        fs = self.foreshadowings.get(fid)
        if not fs:
            return None
        fs.status = ForeshadowStatus.RESOLVED
        fs.resolved_chapter = chapter
        fs.resolved_text = resolved_text
        return fs

    def check_overdue(self, current_chapter: int, tolerance: int = 10) -> list[Foreshadowing]:
        """检查超期未收的伏笔"""
        overdue = []
        for fs in self.foreshadowings.values():
            if fs.status != ForeshadowStatus.PLANTED:
                continue
            # 有预期回收章节且已超期
            if fs.expected_resolve_chapter and current_chapter > fs.expected_resolve_chapter:
                fs.status = ForeshadowStatus.UNRESOLVED
                overdue.append(fs)
            # 无预期但埋了太久
            elif current_chapter - fs.planted_chapter > tolerance:
                fs.status = ForeshadowStatus.UNRESOLVED
                overdue.append(fs)
        return overdue

    def get_planted(self) -> list[Foreshadowing]:
        """获取所有已埋未收的伏笔"""
        return [f for f in self.foreshadowings.values()
                if f.status == ForeshadowStatus.PLANTED]

    def get_context(self) -> str:
        """生成伏笔上下文"""
        if not self.foreshadowings:
            return "暂无伏笔记录。"
        lines = []
        for status_label in ["已埋", "未收", "已收"]:
            group = [f for f in self.foreshadowings.values() if f.status.value == status_label]
            if group:
                lines.append(f"\n{'='*20} {status_label}伏笔 {'='*20}")
                for f in group:
                    lines.append(f.to_context())
        return "\n".join(lines)

    def to_dict(self) -> dict:
        result = {}
        for fid, fs in self.foreshadowings.items():
            d = asdict(fs)
            d["status"] = fs.status.value
            result[fid] = d
        return result

    def from_dict(self, data: dict):
        for fid, d in data.items():
            d["status"] = ForeshadowStatus(d["status"])
            self.foreshadowings[fid] = Foreshadowing(**d)
        if self.foreshadowings:
            max_num = max(int(fid[1:]) for fid in self.foreshadowings)
            self._counter = max_num


class ChapterMemory:
    """跨章记忆系统 - 统一管理章节摘要、角色、时间线、伏笔"""

    def __init__(self):
        self.summaries: dict[int, ChapterSummary] = {}
        self.characters = CharacterTracker()
        self.timeline = TimelineTracker()
        self.foreshadowing = ForeshadowingTracker()

    def add_chapter_summary(self, chapter_num: int, **kwargs) -> ChapterSummary:
        """添加/更新章节摘要"""
        if chapter_num in self.summaries:
            cs = self.summaries[chapter_num]
            for k, v in kwargs.items():
                if hasattr(cs, k):
                    setattr(cs, k, v)
        else:
            cs = ChapterSummary(chapter_num=chapter_num, **kwargs)
            self.summaries[chapter_num] = cs
        return cs

    def get_recent_summaries(self, current_chapter: int, n: int = 5) -> list[ChapterSummary]:
        """获取最近 N 章摘要"""
        chapters = sorted(self.summaries.keys())
        recent = [c for c in chapters if c < current_chapter][-n:]
        return [self.summaries[c] for c in recent]

    def build_context_prompt(self, current_chapter: int) -> str:
        """为当前章节构建完整的跨章上下文 prompt"""
        sections = []

        # 1. 最近章节摘要
        recent = self.get_recent_summaries(current_chapter, n=5)
        if recent:
            sections.append("═══ 最近章节摘要 ═══")
            for cs in recent:
                sections.append(
                    f"第{cs.chapter_num}章{f'「{cs.title}」' if cs.title else ''}："
                    f"{cs.summary}"
                )
                if cs.cliffhanger:
                    sections.append(f"  → 章末悬念：{cs.cliffhanger}")

        # 2. 角色状态
        char_ctx = self.characters.get_all_context()
        if char_ctx != "暂无角色记录。":
            sections.append("\n═══ 角色当前状态 ═══")
            sections.append(char_ctx)

        # 3. 时间线
        tl_ctx = self.timeline.get_context(last_n=10)
        if tl_ctx != "暂无时间线记录。":
            sections.append("\n═══ 时间线（最近10条）═══")
            sections.append(tl_ctx)

        # 4. 伏笔
        planted = self.foreshadowing.get_planted()
        overdue = self.foreshadowing.check_overdue(current_chapter)
        if planted or overdue:
            sections.append("\n═══ 伏笔追踪 ═══")
            if overdue:
                sections.append("🔴 超期未收伏笔（请重点关注）：")
                for f in overdue:
                    sections.append(f.to_context())
            if planted:
                sections.append("🟡 待回收伏笔：")
                for f in planted:
                    sections.append(f.to_context())

        return "\n".join(sections) if sections else "（首章，无历史记录）"

    def save(self, filepath: str):
        """持久化到 JSON"""
        data = {
            "summaries": {str(k): asdict(v) for k, v in self.summaries.items()},
            "characters": self.characters.to_dict(),
            "timeline": self.timeline.to_dict(),
            "foreshadowing": self.foreshadowing.to_dict(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str):
        """从 JSON 恢复"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.summaries = {}
        for k, v in data.get("summaries", {}).items():
            self.summaries[int(k)] = ChapterSummary(**v)

        self.characters = CharacterTracker()
        self.characters.from_dict(data.get("characters", {}))

        self.timeline = TimelineTracker()
        self.timeline.from_dict(data.get("timeline", []))

        self.foreshadowing = ForeshadowingTracker()
        self.foreshadowing.from_dict(data.get("foreshadowing", {}))


# ═══════════════════════════════════════════════════════════
# 第二部分：修改验证
# ═══════════════════════════════════════════════════════════


def _text_hash(text: str) -> str:
    """生成文本指纹"""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()[:12]


def verify_revision(original_text: str, revised_text: str,
                    p0_issues: list[str], p1_issues: list[str]) -> dict:
    """
    验证修改后的文本是否解决了已知问题。

    返回：
    {
        "text_changed": bool,           # 文本是否确实修改了
        "original_hash": str,
        "revised_hash": str,
        "change_ratio": float,          # 修改幅度（0.0~1.0）
        "verification_prompt": str,     # 用于 AI 验证的 prompt
        "warnings": list[str],          # 警告信息
    }
    """
    result = {
        "text_changed": False,
        "original_hash": _text_hash(original_text),
        "revised_hash": _text_hash(revised_text),
        "change_ratio": 0.0,
        "verification_prompt": "",
        "warnings": [],
    }

    # 1. 检查是否确实修改了
    if result["original_hash"] == result["revised_hash"]:
        result["warnings"].append("❌ 文本未修改！原文与修改稿完全一致。")
        return result

    result["text_changed"] = True

    # 2. 计算修改幅度
    orig_chars = set(original_text)
    rev_chars = set(revised_text)
    len_diff = abs(len(revised_text) - len(original_text))
    avg_len = max((len(original_text) + len(revised_text)) / 2, 1)
    result["change_ratio"] = round(min(len_diff / avg_len, 1.0), 3)

    if result["change_ratio"] < 0.01:
        result["warnings"].append("⚠️ 修改幅度极小（<1%），可能只是微调标点，请确认 P0 问题是否真正解决。")
    elif result["change_ratio"] > 0.8:
        result["warnings"].append("⚠️ 修改幅度过大（>80%），接近重写，请确认是否保留了原文优点。")

    # 3. 构建验证 prompt
    p0_text = "\n".join(f"  - {issue}" for issue in p0_issues) if p0_issues else "  （无）"
    p1_text = "\n".join(f"  - {issue}" for issue in p1_issues) if p1_issues else "  （无）"

    result["verification_prompt"] = f"""
═══════════════════════════════════════
修改验证任务
═══════════════════════════════════════

你是修改验证编辑。请对比原文和修改稿，逐一检查以下问题是否已解决。

【P0 必改问题】：
{p0_text}

【P1 建议改问题】：
{p1_text}

【原文】：
{original_text[:2000]}{'...(截断)' if len(original_text) > 2000 else ''}

【修改稿】：
{revised_text[:2000]}{'...(截断)' if len(revised_text) > 2000 else ''}

═══════════════════════════════════════
请逐条验证：
═══════════════════════════════════════

对每个 P0/P1 问题，回答：
- ✅ 已解决：简述如何解决的
- ❌ 未解决：指出仍存在的问题
- ⚠️ 部分解决：指出改了什么、还差什么

最终结论：通过 / 需继续修改

如果有 P0 未解决，结论必须是"需继续修改"。
"""

    return result


# ═══════════════════════════════════════════════════════════
# 第三部分：评分校准 + Prompt 系统
# ═══════════════════════════════════════════════════════════


SCORE_CALIBRATION_RULES = """
═══════════════════════════════════════
评分校准规则（v3.0 强制执行）
═══════════════════════════════════════

1. 【硬性上限】综合评分不得超过 90 分
   - 90 分 = 几乎无可挑剔的杰作级章节
   - 80-89 = 优秀，少量可改进之处
   - 70-79 = 良好，有明显改进空间
   - 60-69 = 及格，需要较大修改
   - <60 = 不及格，建议重写

2. 【P1 下限】每章至少找出 2 个 P1 级别问题
   - 如果真的找不到 P1，必须在报告中写明：
     "本章经反复审查，未发现 P1 级问题，以下为 P2 级改进建议"
   - 但这种情况应极为罕见（<5% 的章节）

3. 【禁止通胀】
   - 不得因为"写得不错"就给 85+
   - 不得因为"比上一章好"就加分
   - 每个维度独立评分，不互相拉高

4. 【评分锚定】
   - 完读率 70% = 及格线（网文读者耐心有限）
   - 付费意愿 50% = 及格线（愿意花钱才是真认可）
   - 技巧/设定/去AI味 70 分 = 及格线
"""


VIRTUAL_READER_V3_PROMPT = """
你现在是一个专业的虚拟读者审稿系统 v3.0（含跨章记忆）。

{score_calibration}

═══════════════════════════════════════
跨章记忆上下文
═══════════════════════════════════════
{chapter_context}

═══════════════════════════════════════
第一部分：虚拟读者评估（30位读者）
═══════════════════════════════════════

模拟30位不同类型的读者阅读本章，统计以下数据：

1. 完读率：多少读者读完了整章？（0-100%）
2. 付费意愿：读完后愿意付费看下一章的比例？（0-100%）
3. 推荐意愿：愿意推荐给朋友的比例？（0-100%）
4. 情感共鸣：被打动/感动的比例？（0-100%）
5. 爽点满足：觉得"爽到了"的比例？（0-100%）
6. 记忆点：读完后还能记住的情节/台词？（列出top3）
7. 最喜欢的段落：（引用原文）
8. 最想吐槽的段落：（引用原文）

═══════════════════════════════════════
第二部分：编辑团队严格审稿（6位编辑）
═══════════════════════════════════════

在虚拟读者评估基础上，由6位专业编辑逐一审稿。
每位编辑必须同时指出亮点和问题，问题必须给出具体修改方案。

═══════════════════════════════════════
6位编辑角色：
═══════════════════════════════════════

📖 编辑A：普通读者（看完读率）
- 模拟普通读者阅读体验
- 哪里想划走？哪里想退出？（标出具体段落）
- 开头能不能3秒抓住我？
- 读完想不想看下一章？
- 亮点：最吸引我的1-2处
- 问题：最想划走的1-2处 → 改进建议

📝 编辑B：网文编辑（看商业性）
- 爽点够不够密？来得够不够快？
- 付费卡点设在哪里？够不够强？
- 读者愿不愿意掏钱看下一章？
- 标题/开头能不能在信息流里脱颖而出？
- 亮点：商业性最强的1-2处
- 问题：商业性最弱的1-2处 → 改进建议

🎭 编辑C：专业作家（看技巧）
- 人物动机合不合理？
- 对话像不像真人说的？
- 情节逻辑有没有漏洞？
- 反转有没有铺垫？
- 节奏是否合理（快慢交替）？
- 亮点：技巧最好的1-2处
- 问题：技巧最弱的1-2处 → 改进建议

🔍 编辑D：挑刺读者（找bug+AI味）
- 前后矛盾的细节（结合跨章记忆上下文对比）
- 不合常理的行为/设定
- AI味重的段落（标出具体句子，说明为什么像AI写的）
- 用词重复/表达僵硬
- 世界观/设定不合理之处
- 角色行为是否符合人设
- 亮点：最真实自然的1-2处
- 问题：最不合理的1-2处 → 改进建议

🏗️ 编辑E：设定审查 + 跨章一致性（v3.0 增强）
- 角色性格是否前后一致？（参考跨章记忆中的角色状态）
- 角色能力是否符合设定？（参考角色能力列表）
- 世界观规则是否自洽？
- 时间线是否合理？（参考时间线追踪）
- 空间/地理是否合理？
- 人物关系是否与前文一致？（参考角色关系网）
- 伏笔处理：本章是否回收了应收的伏笔？是否埋了新伏笔？
- 亮点：设定最精妙的1-2处
- 问题：设定最矛盾的1-2处 → 改进建议

💡 编辑F：改稿编辑（给方案）
- 针对A-E发现的每个问题，给出具体修改方案
- 不是"建议优化"，是"改成xxx"
- 给出修改前后对比
- 优先级排序：P0必改 / P1建议改 / P2可选改
- 【v3.0 强制】每章至少给出 2 个 P1 级问题

═══════════════════════════════════════
第三部分：跨章专项检查（v3.0 新增）
═══════════════════════════════════════

基于跨章记忆上下文，额外检查：

1. 【角色一致性】本章出场角色的状态是否与上次出场一致？
   - 位置变化是否有交代？
   - 情绪变化是否有原因？
   - 能力使用是否符合设定？

2. 【时间线校验】本章的时间线是否与前文衔接？
   - 时间跨度是否合理？
   - 是否存在时间矛盾？

3. 【伏笔检查】
   - 本章是否有应收未收的伏笔？（标红提醒）
   - 本章新埋的伏笔是否记录？
   - 已回收的伏笔回收方式是否自然？

4. 【悬念衔接】
   - 上一章的悬念是否得到回应？
   - 本章结尾是否留有新悬念？

═══════════════════════════════════════
输出格式（必须严格遵守）：
═══════════════════════════════════════

## 第一部分：虚拟读者数据

| 指标 | 数值 | 说明 |
|------|------|------|
| 完读率 | XX% | 30位读者中读完的比例 |
| 付费意愿 | XX% | 愿意付费看下一章 |
| 推荐意愿 | XX% | 愿意推荐给朋友 |
| 情感共鸣 | XX% | 被打动/感动 |
| 爽点满足 | XX% | 觉得爽到了 |

### 记忆点 Top3：
1. xxx
2. xxx
3. xxx

### 最喜欢的段落：
「引用原文」

### 最想吐槽的段落：
「引用原文」→ 原因：xxx

---

## 第二部分：编辑团队审稿

### 📖 编辑A（普通读者）
**亮点**：
1. xxx
**问题**：
1. 第X段：「原文」→ 问题：xxx → 建议：xxx

### 📝 编辑B（网文编辑）
**亮点**：
1. xxx
**问题**：
1. xxx → 建议：xxx

### 🎭 编辑C（专业作家）
**亮点**：
1. xxx
**问题**：
1. 「角色/情节/对话」：xxx → 建议：xxx

### 🔍 编辑D（挑刺读者）
**亮点**：
1. xxx
**问题**：
1. AI味：「原文句子」→ 改为：「修改后」
2. 不合理：xxx → 建议：xxx

### 🏗️ 编辑E（设定审查 + 跨章一致性）
**亮点**：
1. xxx
**问题**：
1. 角色矛盾：xxx → 建议：xxx
2. 时间线问题：xxx → 建议：xxx
3. 伏笔问题：xxx → 建议：xxx

### 💡 编辑F（改稿方案）
**P0 必改**：
1. 原文：「xxx」→ 改为：「xxx」
**P1 建议改**（至少2个）：
1. 原文：「xxx」→ 改为：「xxx」
2. 原文：「xxx」→ 改为：「xxx」
**P2 可选改**：
1. 原文：「xxx」→ 改为：「xxx」

---

## 第三部分：跨章专项报告

### 角色一致性
- ✅/❌ [角色名]：xxx

### 时间线校验
- ✅/❌ xxx

### 伏笔检查
- 🟡 待回收：[伏笔ID] xxx
- 🔴 超期未收：[伏笔ID] xxx
- 🟢 本章已收：[伏笔ID] xxx
- 🆕 本章新埋：xxx

### 悬念衔接
- 上章悬念回应：✅/❌ xxx
- 本章新悬念：xxx

---

## 第四部分：综合评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 完读率 | XX% | |
| 付费意愿 | XX% | |
| 技巧 | XX/100 | |
| 设定一致性 | XX/100 | |
| 去AI味 | XX/100 | |
| 跨章连贯性 | XX/100 | v3.0新增 |
| **综合** | **XX/100** | **上限90** |

### 结论：通过 / 需修改 / 重写
### P0清单：（必须修改才能通过）
### P1清单：（至少2个，建议修改）

═══════════════════════════════════════
注意事项：
═══════════════════════════════════════
- 综合评分上限 90，超过必须说明理由
- 每章至少 2 个 P1 级问题
- 禁止纯吹捧！
- 编辑D和E必须结合跨章记忆上下文检查一致性
"""


# ═══════════════════════════════════════════════════════════
# 第四部分：对外接口
# ═══════════════════════════════════════════════════════════


def get_virtual_reader_prompt(chapter_content: str, chapter_num: int,
                              novel_name: str,
                              memory: Optional[ChapterMemory] = None) -> str:
    """
    生成虚拟读者 v3.0 审稿指令。

    Args:
        chapter_content: 章节正文
        chapter_num: 章节号
        novel_name: 小说名
        memory: 跨章记忆对象（可选，首章可不传）

    Returns:
        完整的审稿 prompt
    """
    # 构建跨章上下文
    if memory:
        chapter_context = memory.build_context_prompt(chapter_num)
    else:
        chapter_context = "（首章或无历史记录，跳过跨章检查）"

    # 填充 prompt 模板
    prompt_body = VIRTUAL_READER_V3_PROMPT.format(
        score_calibration=SCORE_CALIBRATION_RULES,
        chapter_context=chapter_context,
    )

    return f"""
{prompt_body}

═══════════════════════════════════════
待审稿章节：
═══════════════════════════════════════

小说名：《{novel_name}》
章节：第{chapter_num}章

正文内容：
{chapter_content}

═══════════════════════════════════════
请6位编辑逐一发表意见，严格按输出格式！
禁止纯吹捧！每位编辑至少找出1个问题！
综合评分上限90！每章至少2个P1！
═══════════════════════════════════════
"""


def get_verification_prompt(original: str, revised: str,
                            p0_issues: list[str],
                            p1_issues: list[str]) -> dict:
    """
    生成修改验证 prompt。

    Args:
        original: 原文
        revised: 修改稿
        p0_issues: P0 问题列表
        p1_issues: P1 问题列表

    Returns:
        verify_revision() 的完整结果
    """
    return verify_revision(original, revised, p0_issues, p1_issues)


# ═══════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════


if __name__ == "__main__":
    print("=" * 60)
    print("虚拟读者 Skill v3.0 - 跨章记忆 + 严格编辑团队")
    print("=" * 60)

    # ---- 测试 ChapterMemory ----
    print("\n【测试1】ChapterMemory 跨章记忆")
    mem = ChapterMemory()

    # 添加章节摘要
    mem.add_chapter_summary(
        1, title="觉醒", summary="主角林风在废墟中觉醒灵力",
        key_events=["觉醒灵力", "遇到老者"], characters_appeared=["林风", "老者"],
        cliffhanger="老者消失，留下神秘玉佩"
    )
    mem.add_chapter_summary(
        2, title="入门", summary="林风持玉佩拜入天玄宗",
        key_events=["入宗", "被分配到外门"], characters_appeared=["林风", "宗主", "师姐苏婉"],
        cliffhanger="苏婉认出玉佩，表情大变"
    )
    print(f"  ✅ 已添加 {len(mem.summaries)} 章摘要")

    # 角色追踪
    mem.characters.update("林风", 1, location="废墟", emotion="震惊",
                          abilities="灵力感知", status="正常")
    mem.characters.update("林风", 2, location="天玄宗外门",
                          emotion="期待", relationships={"苏婉": "师姐"})
    mem.characters.update("苏婉", 2, location="天玄宗内门",
                          emotion="震惊", abilities="剑术",
                          relationships={"林风": "师弟"})
    print(f"  ✅ 已追踪 {len(mem.characters.characters)} 个角色")

    # 角色一致性检查
    issues = mem.characters.check_consistency("林风", 3, location="魔域", abilities="瞬移")
    print(f"  ✅ 角色一致性检查：发现 {len(issues)} 个问题")
    for i in issues:
        print(f"    {i}")

    # 时间线
    mem.timeline.add_event(1, "第一天黎明", "林风觉醒", ["林风"])
    mem.timeline.add_event(1, "第一天黄昏", "遇到老者", ["林风", "老者"])
    mem.timeline.add_event(2, "第三天清晨", "入宗仪式", ["林风", "宗主"])

    # 时间线矛盾检查
    tl_issues = mem.timeline.check_contradictions(
        3, "第一天黄昏", "林风在魔域战斗", ["林风"]
    )
    print(f"  ✅ 时间线矛盾检查：发现 {len(tl_issues)} 个问题")
    for i in tl_issues:
        print(f"    {i}")

    # 伏笔
    f1 = mem.foreshadowing.plant(
        "神秘玉佩的来历", 1, "老者将一枚温润玉佩塞入林风手中", expected_resolve=5
    )
    f2 = mem.foreshadowing.plant(
        "苏婉认出玉佩", 2, "苏婉看到玉佩的瞬间，瞳孔骤缩", expected_resolve=4
    )
    print(f"  ✅ 已埋下 {len(mem.foreshadowing.foreshadowings)} 个伏笔")

    # 伏笔超期检查
    overdue = mem.foreshadowing.check_overdue(6)
    print(f"  ✅ 超期伏笔检查（第6章时）：{len(overdue)} 个超期")
    for f in overdue:
        print(f"    {f.to_context()}")

    # 回收伏笔
    mem.foreshadowing.resolve(f2.id, 3, "苏婉揭示玉佩是上古传承信物")
    print(f"  ✅ 已回收伏笔 {f2.id}")

    # 生成上下文
    print("\n【测试2】生成第3章跨章上下文")
    ctx = mem.build_context_prompt(3)
    print(ctx[:500] + "..." if len(ctx) > 500 else ctx)

    # ---- 测试持久化 ----
    print("\n【测试3】持久化 save/load")
    import tempfile
    import os
    tmpfile = os.path.join(tempfile.gettempdir(), "vr3_test_memory.json")
    mem.save(tmpfile)
    print(f"  ✅ 已保存到 {tmpfile}")

    mem2 = ChapterMemory()
    mem2.load(tmpfile)
    assert len(mem2.summaries) == 2
    assert len(mem2.characters.characters) == 2
    assert len(mem2.timeline.events) == 3
    assert len(mem2.foreshadowing.foreshadowings) == 2
    print("  ✅ 加载并验证成功")
    os.remove(tmpfile)

    # ---- 测试 verify_revision ----
    print("\n【测试4】verify_revision 修改验证")
    original = "他的眼神中充满了不可思议的震惊，仿佛整个世界都在这一刻发生了翻天覆地的变化。"
    revised = "他瞳孔骤缩，后退半步。"
    result = verify_revision(original, revised, ["AI味过重：原文表达僵硬"], ["可增加动作细节"])
    print(f"  ✅ 文本已修改：{result['text_changed']}")
    print(f"  ✅ 修改幅度：{result['change_ratio']}")
    print(f"  ✅ 警告数：{len(result['warnings'])}")
    for w in result["warnings"]:
        print(f"    {w}")

    # 测试未修改的情况
    result2 = verify_revision(original, original, ["问题1"], [])
    assert not result2["text_changed"]
    assert any("未修改" in w for w in result2["warnings"])
    print("  ✅ 未修改检测通过")

    # ---- 测试 Prompt 生成 ----
    print("\n【测试5】完整 Prompt 生成")
    prompt = get_virtual_reader_prompt(
        "这是测试章节内容...", 3, "测试小说", mem
    )
    assert "跨章记忆上下文" in prompt
    assert "评分校准规则" in prompt
    assert "上限90" in prompt
    assert "至少2个P1" in prompt or "至少 2 个 P1" in prompt
    assert "30位" in prompt
    assert "6位编辑" in prompt
    print(f"  ✅ Prompt 长度：{len(prompt)} 字符")
    print("  ✅ 包含：跨章上下文 ✓ 评分校准 ✓ 上限90 ✓ P1下限 ✓ 30读者 ✓ 6编辑 ✓")

    # ---- 测试评分校准 ----
    print("\n【测试6】评分校准规则检查")
    assert "不得超过 90" in SCORE_CALIBRATION_RULES
    assert "至少找出 2 个 P1" in SCORE_CALIBRATION_RULES
    assert "禁止通胀" in SCORE_CALIBRATION_RULES
    print("  ✅ 评分校准规则完整")

    # ---- 无记忆时的 prompt（首章场景） ----
    print("\n【测试7】首章（无跨章记忆）")
    prompt_first = get_virtual_reader_prompt("首章内容...", 1, "测试小说")
    assert "首章或无历史记录" in prompt_first
    print("  ✅ 首章 prompt 正常")

    print("\n" + "=" * 60)
    print("✅ 全部测试通过！虚拟读者 v3.0 就绪。")
    print("=" * 60)

    print("\n核心能力清单：")
    print("1. ✅ ChapterMemory - 跨章记忆（摘要+角色+时间线+伏笔）")
    print("2. ✅ CharacterTracker - 角色状态追踪（位置/情绪/能力/关系）")
    print("3. ✅ TimelineTracker - 时间线追踪（矛盾检测）")
    print("4. ✅ ForeshadowingTracker - 伏笔追踪（已埋/已收/未收）")
    print("5. ✅ verify_revision() - 修改后验证")
    print("6. ✅ 评分校准 - 上限90，每章至少2个P1")
    print("7. ✅ 保留30位虚拟读者 + 6位编辑团队 prompt")
    print("8. ✅ 持久化 save/load（JSON）")
