#!/usr/bin/env python3
"""
小说创作工作流 v3.0 - 进度持久化模块
核心功能：
1. WorkflowProgress - 进度持久化，重启可恢复
2. IdempotentChecker - 幂等检查，防重复创建飞书文档
"""

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# ==================== 项目规范（必须遵守）====================
"""
📁 项目目录结构规范

本地目录（workspace-jinghong/projects/）：
```
projects/
└── {项目编号}-{书名}/
    ├── 大纲+角色卡.md              # PRD 文档
    ├── progress/
    │   ├── {项目编号}.json         # 进度持久化
    │   └── doc_index.json          # 飞书文档索引
    ├── chapters/
    │   ├── 第01章-{标题}.md
    │   ├── 第02章-{标题}.md
    │   └── ...
    └── 审查报告/
        ├── 第01章审查报告.md
        └── ...
```

飞书知识库结构（在「小说写作项目」wiki 下）：
```
小说写作项目/
└── {项目编号}-{书名}/
    ├── 大纲+角色卡
    ├── 第01章-{标题}
    ├── 第02章-{标题}
    └── ...
```

⚠️ 铁律：
1. 必须先建目录，再创作内容
2. 飞书文档必须建在 wiki_node 的目录下，不能直接扔根目录
3. 先检查已有项目结构（ls projects/001-*/），模仿已有规范
4. 创作前必须初始化 progress/{项目编号}.json
5. 创作前必须先创建飞书子目录

🔄 创作流程（严格按顺序）：
1. 读取创意库 → 确认选题
2. 检查已有项目目录结构 → 模仿规范
3. 本地创建项目目录结构
4. 飞书知识库创建子目录（wiki_node 下）
5. 创建 PRD（大纲+角色卡）→ 写入本地+飞书
6. 初始化 progress/{项目编号}.json
7. 确认大纲 OK → 开始第 1 章
8. 每章写完 → 调用虚拟读者 v3.0 审稿
9. 审稿≥85分 → 下一章
10. 审稿<85分 → 按改稿方案修改 → 重新审稿

🚫 禁止行为：
- ❌ 没有目录结构就直接写章节
- ❌ 飞书文档扔在 wiki_node 根目录
- ❌ 没有初始化 progress.json 就开始创作
- ❌ 没有调用虚拟读者审稿就进入下一章
- ❌ 中途频繁汇报（写完再报，先做完再汇报）

📦 归档规范

本地目录结构（项目完成前）：
```
{编号}-{书名}/
├── 大纲+角色卡.md
├── progress/{编号}.json
├── progress/doc_index.json
├── chapters/
│   ├── 第01章-{标题}.md
│   └── ...
└── 审查报告/
    └── 第XX章审查报告.md
```

本地目录结构（项目完成后）：
```
{编号}-{书名}/
├── 大纲+角色卡.md
├── progress/{编号}.json
├── final/                          # 定稿目录
│   ├── 大纲+角色卡.md
│   ├── 第01章-{标题}.md
│   └── ...
└── drafts/                         # 草稿备份
    └── ...
```

飞书知识库结构：
```
小说写作项目/
├── 进行中/
│   └── {编号}-{书名}/
│       ├── 大纲+角色卡
│       ├── 第01章-{标题}
│       └── ...
└── 已归档/
    ├── 001-全家反派读心后/
    ├── 002-我在修仙界开网约车/
    └── ...
```

🔄 完整创作流程（先写后改版）：
1. 读取创意库 → 确认选题
2. 检查已有项目目录结构 → 模仿规范
3. 本地创建项目目录结构（projects/{编号}-{书名}/）
4. 飞书知识库在"进行中/"下创建子目录
5. 创建 PRD（大纲+角色卡）→ 写入本地+飞书
6. 初始化 progress/{项目编号}.json
7. 试水章：第 1 章 → 快速审稿（方向/文风/人设）→ 方向 OK
8. 批量创作：第 2-12 章一气呵成，中间不停！不审稿！
9. 集中审稿：虚拟读者 v3.0 一次性读 12 章 → 输出全局问题清单
10. 批量修改：按清单逐章修改 → 统一再审 → 定稿
11. 归档：
    - 本地：chapters/ → final/，更新 progress.json 为 completed
    - 飞书："进行中/" → "已归档/"
    - 更新选题创意库状态 → 🔵已使用
12. 项目结案

📊 归档触发条件：
- 全部 12 章审稿通过（≥85 分）
- progress.json 中所有章节 status=completed
- 主人确认可以归档

📝 归档时执行：
1. 本地创建 final/ 目录，复制所有章节
2. 飞书移动文档到"已归档/"目录
3. 更新选题创意合集状态为 🔵已使用
4. 写入项目总结（字数/均分/耗时/经验教训）
5. 记录到 memory/daily/YYYY-MM-DD.md

🔄 Agent 自我评估+重试机制（2026-04-09 新增）

每次完成一个任务后，Agent 必须执行自我评估：

1. 检查成功标准：
   - 文件存在？→ ls 确认
   - 内容正确？→ read 确认
   - 语法无误？→ python3 运行测试
   - 飞书文档创建成功？→ feishu_fetch_doc 确认

2. 评估结果：
   - ✅ 成功 → 继续下一步
   - ❌ 失败 → 自动重试（最多 3 次）

3. 重试策略（每次换方法）：
   - 第 1 次失败：检查错误信息，修复后重试
   - 第 2 次失败：换一种实现方式
   - 第 3 次失败：**强制降级**，报告给年年，不要继续死磕

4. 失败报告格式：
   ```
   [失败] 任务：xxx | 已重试 3 次 | 错误：xxx | 建议：xxx
   ```

📸 Checkpoint 机制（2026-04-09 新增）

每个 Agent 在执行长任务时，必须定期写入 checkpoint：

1. 每完成一个子步骤，写入 checkpoint：
   ```
   progress/checkpoint.json
   {
     "task": "批量创作第2-12章",
     "step": "第 5 章已完成",
     "completed": 5,
     "total": 12,
     "timestamp": "2026-04-09T08:40:00+08:00",
     "next": "继续写第 6 章"
   }
   ```

2. Gateway 重启恢复流程：
   - 读取 checkpoint.json
   - 确认已完成的步骤
   - 从下一步继续，不重复

3. 创作场景的 checkpoint：
   - 每写完一章 → 写入 checkpoint
   - 每完成一次审稿 → 更新 checkpoint
   - 每次修改完成 → 更新 checkpoint

4. 检查点验证：
   - checkpoint 记录的步骤 → 对应的文件必须存在
   - 如果文件不存在 → 该步骤视为未完成，重新执行
"""


# ==================== 数据模型 ====================

VALID_STATUSES = {"pending", "writing", "reviewing", "review_failed", "completed"}


@dataclass
class ChapterState:
    """单章状态"""
    chapter_num: int
    status: str = "pending"           # pending/writing/reviewing/review_failed/completed
    title: str = ""                   # 章节名
    doc_url: str = ""                 # 飞书文档链接
    doc_id: str = ""                  # 飞书文档ID
    score: Optional[float] = None     # 审查评分
    virtual_reader_score: Optional[float] = None  # 虚拟读者评分
    review_count: int = 0             # 审查次数
    created_at: str = ""              # 创建时间
    updated_at: str = ""              # 更新时间
    last_error: str = ""              # 最后一次错误信息


@dataclass
class ProjectProgress:
    """项目整体进度"""
    project_id: str = ""
    novel_name: str = ""
    total_chapters: int = 0
    chapters: list = field(default_factory=list)
    current_chapter: int = 0          # 当前进行到的章节
    started_at: str = ""
    completed_at: str = ""
    last_active: str = ""
    error_count: int = 0
    metadata: dict = field(default_factory=dict)  # 扩展字段


# ==================== 进度持久化 ====================

class WorkflowProgress:
    """进度持久化 - 重启可恢复"""

    def __init__(self, project_id: str, progress_dir: str = "progress"):
        self.project_id = project_id
        self.progress_dir = Path(progress_dir)
        self.progress_file = self.progress_dir / f"{project_id}.json"
        self.progress: Optional[ProjectProgress] = None

        # 确保目录存在
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def init_project(self, novel_name: str, total_chapters: int, metadata: dict = None) -> None:
        """初始化项目进度"""
        now = datetime.now().isoformat()
        chapters = [
            ChapterState(chapter_num=i, title=f"第 {i:02d} 章")
            for i in range(1, total_chapters + 1)
        ]
        self.progress = ProjectProgress(
            project_id=self.project_id,
            novel_name=novel_name,
            total_chapters=total_chapters,
            chapters=[asdict(c) for c in chapters],
            started_at=now,
            last_active=now,
            metadata=metadata or {}
        )
        self.save()

    def load(self) -> Optional[ProjectProgress]:
        """从文件加载进度"""
        if not self.progress_file.exists():
            return None

        with open(self.progress_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.progress = ProjectProgress(**data)
        return self.progress

    def save(self) -> str:
        """保存到文件，返回文件路径"""
        if self.progress is None:
            raise RuntimeError("进度未初始化，请先调用 init_project()")

        self.progress.last_active = datetime.now().isoformat()

        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.progress) if isinstance(self.progress, ProjectProgress) else self.progress, f, ensure_ascii=False, indent=2)

        return str(self.progress_file)

    def _ensure_loaded(self):
        """确保进度已加载"""
        if self.progress is None:
            loaded = self.load()
            if loaded is None:
                raise RuntimeError(f"进度文件不存在: {self.progress_file}")

    def _find_chapter(self, chapter_num: int) -> Optional[dict]:
        """查找指定章节的状态记录"""
        self._ensure_loaded()
        for ch in self.progress.chapters:
            if ch["chapter_num"] == chapter_num:
                return ch
        return None

    def update_chapter(
        self,
        chapter_num: int,
        status: str,
        score: Optional[float] = None,
        doc_url: str = "",
        doc_id: str = "",
        title: str = "",
        virtual_reader_score: Optional[float] = None,
        last_error: str = ""
    ) -> dict:
        """
        更新章节状态

        Args:
            chapter_num: 章节号
            status: pending/writing/reviewing/review_failed/completed
            score: 审查评分
            doc_url: 飞书文档链接
            doc_id: 飞书文档ID
            title: 章节名
            virtual_reader_score: 虚拟读者评分
            last_error: 错误信息

        Returns:
            更新后的章节状态
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"无效状态: {status}, 必须是 {VALID_STATUSES}")

        self._ensure_loaded()
        chapter = self._find_chapter(chapter_num)
        if chapter is None:
            raise ValueError(f"章节不存在: {chapter_num}")

        now = datetime.now().isoformat()

        # 更新字段
        chapter["status"] = status
        chapter["updated_at"] = now

        if score is not None:
            chapter["score"] = score
        if doc_url:
            chapter["doc_url"] = doc_url
        if doc_id:
            chapter["doc_id"] = doc_id
        if title:
            chapter["title"] = title
        if virtual_reader_score is not None:
            chapter["virtual_reader_score"] = virtual_reader_score
        if last_error:
            chapter["last_error"] = last_error

        # 审查次数
        if status in ("reviewing", "review_failed"):
            chapter["review_count"] += 1

        # 更新当前章节指针
        if chapter_num > self.progress.current_chapter:
            self.progress.current_chapter = chapter_num

        # 检查是否全部完成
        all_completed = all(c["status"] == "completed" for c in self.progress.chapters)
        if all_completed and not self.progress.completed_at:
            self.progress.completed_at = now

        self.save()
        return chapter

    def get_next_pending(self) -> Optional[dict]:
        """获取下一个待处理的章节（pending 或 review_failed 需要重试）"""
        self._ensure_loaded()
        for ch in self.progress.chapters:
            if ch["status"] in ("pending", "review_failed"):
                return ch
        return None

    def resume(self) -> dict:
        """
        断点恢复：返回从哪章继续

        Returns:
            {
                "can_resume": bool,
                "next_chapter": int,
                "next_status": str,
                "completed_count": int,
                "total_count": int,
                "chapter_info": dict or None
            }
        """
        self._ensure_loaded()

        completed = [c for c in self.progress.chapters if c["status"] == "completed"]
        next_ch = self.get_next_pending()

        result = {
            "can_resume": next_ch is not None,
            "next_chapter": next_ch["chapter_num"] if next_ch else None,
            "next_status": next_ch["status"] if next_ch else None,
            "completed_count": len(completed),
            "total_count": self.progress.total_chapters,
            "chapter_info": next_ch,
            "project_id": self.progress.project_id,
            "novel_name": self.progress.novel_name,
        }

        if next_ch is None and len(completed) == self.progress.total_chapters:
            result["message"] = "所有章节已完成！"
        elif next_ch is None:
            result["message"] = "无待处理章节"

        return result

    def get_summary(self) -> dict:
        """获取项目进度摘要"""
        self._ensure_loaded()

        status_count = {}
        for ch in self.progress.chapters:
            s = ch["status"]
            status_count[s] = status_count.get(s, 0) + 1

        scores = [ch["score"] for ch in self.progress.chapters if ch["score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "project_id": self.progress.project_id,
            "novel_name": self.progress.novel_name,
            "total_chapters": self.progress.total_chapters,
            "status_count": status_count,
            "completed": status_count.get("completed", 0),
            "avg_score": round(avg_score, 1),
            "started_at": self.progress.started_at,
            "last_active": self.progress.last_active,
            "completed_at": self.progress.completed_at,
        }

    def reset_chapter(self, chapter_num: int) -> dict:
        """重置章节状态为 pending（用于强制重新创作）"""
        self._ensure_loaded()
        chapter = self._find_chapter(chapter_num)
        if chapter is None:
            raise ValueError(f"章节不存在: {chapter_num}")

        chapter["status"] = "pending"
        chapter["score"] = None
        chapter["virtual_reader_score"] = None
        chapter["review_count"] = 0
        chapter["last_error"] = ""
        chapter["updated_at"] = datetime.now().isoformat()

        self.save()
        return chapter


# ==================== 幂等检查 ====================

class IdempotentChecker:
    """幂等检查 - 防重复创建飞书文档"""

    def __init__(self, folder_token: str, doc_index: str = None):
        """
        Args:
            folder_token: 飞书文件夹 token
            doc_index: 本地文档索引文件路径（可选，加速检查）
        """
        self.folder_token = folder_token
        self.index_file = Path(doc_index) if doc_index else Path("progress/doc_index.json")
        self.doc_index = self._load_index()

    def _load_index(self) -> dict:
        """加载本地文档索引"""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """保存本地文档索引"""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.doc_index, f, ensure_ascii=False, indent=2)

    def _make_key(self, chapter_num: int, title: str) -> str:
        """生成文档唯一键"""
        return f"ch{chapter_num:02d}_{title}"

    def check_exists(self, chapter_num: int, title: str) -> dict:
        """
        检查飞书文档是否已存在（本地索引检查）

        Args:
            chapter_num: 章节号
            title: 章节名

        Returns:
            {
                "exists": bool,
                "doc_id": str or None,
                "doc_url": str or None,
                "source": "local_index" | "needs_remote_check"
            }
        """
        key = self._make_key(chapter_num, title)

        if key in self.doc_index:
            entry = self.doc_index[key]
            return {
                "exists": True,
                "doc_id": entry.get("doc_id"),
                "doc_url": entry.get("doc_url"),
                "source": "local_index"
            }

        return {
            "exists": False,
            "doc_id": None,
            "doc_url": None,
            "source": "local_index"
        }

    def before_create(self, chapter_num: int, title: str) -> dict:
        """
        创建前检查，已存在则跳过

        Args:
            chapter_num: 章节号
            title: 章节名

        Returns:
            {
                "should_create": bool,
                "existing_doc_id": str or None,
                "existing_doc_url": str or None,
                "reason": str
            }
        """
        check = self.check_exists(chapter_num, title)

        if check["exists"]:
            return {
                "should_create": False,
                "existing_doc_id": check["doc_id"],
                "existing_doc_url": check["doc_url"],
                "reason": f"第 {chapter_num:02d} 章已存在，跳过创建"
            }

        return {
            "should_create": True,
            "existing_doc_id": None,
            "existing_doc_url": None,
            "reason": f"第 {chapter_num:02d} 章文档不存在，可以创建"
        }

    def register_created(self, chapter_num: int, title: str, doc_id: str, doc_url: str):
        """
        注册已创建的文档到索引

        Args:
            chapter_num: 章节号
            title: 章节名
            doc_id: 飞书文档ID
            doc_url: 飞书文档链接
        """
        key = self._make_key(chapter_num, title)
        self.doc_index[key] = {
            "doc_id": doc_id,
            "doc_url": doc_url,
            "chapter_num": chapter_num,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "folder_token": self.folder_token,
        }
        self._save_index()

    def list_all(self) -> list:
        """列出所有已注册的文档"""
        return list(self.doc_index.values())


# ==================== 集成辅助函数 ====================

def create_progress_and_checker(project_id: str, novel_name: str, total_chapters: int,
                                folder_token: str, progress_dir: str = "progress") -> tuple:
    """一键创建进度管理器和幂等检查器"""
    progress = WorkflowProgress(project_id=project_id, progress_dir=progress_dir)
    progress.init_project(novel_name=novel_name, total_chapters=total_chapters)

    checker = IdempotentChecker(folder_token=folder_token)

    return progress, checker


def generate_resume_instruction(resume_info: dict) -> str:
    """根据恢复信息生成执行指令"""
    if not resume_info["can_resume"]:
        if "message" in resume_info:
            return f"[工作流] {resume_info['message']}"
        return "[工作流] 无待处理章节"

    ch = resume_info["chapter_info"]
    if ch["status"] == "review_failed":
        return (
            f"[工作流] 断点恢复：第 {ch['chapter_num']} 章审查未通过，需要修改后重新提交\n"
            f"章节名：{ch['title']}\n"
            f"上次错误：{ch.get('last_error', '无')}\n"
            f"审查次数：{ch['review_count']}"
        )
    else:
        return (
            f"[工作流] 断点恢复：从第 {ch['chapter_num']} 章开始创作\n"
            f"章节名：{ch['title']}\n"
            f"已完成：{resume_info['completed_count']}/{resume_info['total_count']}"
        )


# ==================== 测试 ====================

def test_workflow_progress():
    """测试 WorkflowProgress 类"""
    import tempfile
    import shutil

    print("=" * 60)
    print("测试 WorkflowProgress")
    print("=" * 60)

    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    project_id = "test_novel_001"

    try:
        # 1. 初始化项目
        print("\n[1] 初始化项目...")
        progress = WorkflowProgress(project_id=project_id, progress_dir=test_dir)
        progress.init_project(
            novel_name="测试小说",
            total_chapters=5,
            metadata={"author": "惊鸿", "genre": "玄幻"}
        )
        print(f"  ✅ 项目初始化: {project_id}")
        print(f"  ✅ 进度文件: {progress.progress_file}")

        # 2. 更新章节状态
        print("\n[2] 更新章节状态...")
        ch1 = progress.update_chapter(1, "writing")
        print(f"  ✅ 第1章 → writing: {ch1['status']}")

        ch1 = progress.update_chapter(
            1, "completed",
            score=92.5,
            doc_url="https://www.feishu.cn/docx/abc123",
            doc_id="abc123",
            title="第 01 章-穿越",
            virtual_reader_score=88.0
        )
        print(f"  ✅ 第1章 → completed, 评分: {ch1['score']}, 文档: {ch1['doc_url']}")

        # 批量更新多个章节
        for i in range(2, 4):
            progress.update_chapter(i, "writing")
            progress.update_chapter(i, "completed", score=85.0 + i)

        print(f"  ✅ 第2-3章已完成")

        # 第4章创作中
        progress.update_chapter(4, "writing")
        print(f"  ✅ 第4章 → writing")

        # 第5章待处理
        print(f"  ✅ 第5章 → pending (默认)")

        # 3. 获取下一个待处理
        print("\n[3] 获取下一个待处理章节...")
        next_ch = progress.get_next_pending()
        print(f"  ✅ 下一章: 第 {next_ch['chapter_num']} 章, 状态: {next_ch['status']}")

        # 4. 断点恢复
        print("\n[4] 断点恢复...")
        resume = progress.resume()
        print(f"  ✅ 可恢复: {resume['can_resume']}")
        print(f"  ✅ 从第 {resume['next_chapter']} 章继续 ({resume['next_status']})")
        print(f"  ✅ 进度: {resume['completed_count']}/{resume['total_count']}")

        # 5. 保存摘要
        print("\n[5] 项目摘要...")
        summary = progress.get_summary()
        print(f"  ✅ 项目: {summary['novel_name']}")
        print(f"  ✅ 已完成: {summary['completed']}/{summary['total_chapters']}")
        print(f"  ✅ 平均分: {summary['avg_score']}")
        print(f"  ✅ 状态分布: {summary['status_count']}")

        # 6. 模拟重启（从文件加载）
        print("\n[6] 模拟重启（从文件加载）...")
        progress2 = WorkflowProgress(project_id=project_id, progress_dir=test_dir)
        loaded = progress2.load()
        assert loaded is not None, "加载失败"
        print(f"  ✅ 加载成功: {loaded.novel_name}, {loaded.total_chapters}章")
        assert len(loaded.chapters) == 5, "章节数不对"
        assert loaded.chapters[0]["status"] == "completed", "第1章状态不对"
        assert loaded.chapters[3]["status"] == "writing", "第4章状态不对"
        print(f"  ✅ 第1章状态: {loaded.chapters[0]['status']}")
        print(f"  ✅ 第4章状态: {loaded.chapters[3]['status']}")

        # 7. 测试 review_failed 重试
        print("\n[7] 测试审查不通过重试...")
        progress2.update_chapter(2, "review_failed", last_error="P0: 逻辑bug - 主角能力前后矛盾")
        next_ch = progress2.get_next_pending()
        assert next_ch["chapter_num"] == 2, "应该返回审查失败的章节"
        assert next_ch["status"] == "review_failed", "状态不对"
        print(f"  ✅ 返回第 {next_ch['chapter_num']} 章 (review_failed)")

        # 8. 测试重置章节
        print("\n[8] 测试重置章节...")
        reset_ch = progress2.reset_chapter(3)
        assert reset_ch["status"] == "pending", "重置后应该是 pending"
        assert reset_ch["score"] is None, "重置后评分应为 None"
        print(f"  ✅ 第3章已重置: {reset_ch['status']}")

        # 9. 测试状态校验
        print("\n[9] 测试无效状态校验...")
        try:
            progress2.update_chapter(1, "invalid_status")
            print("  ❌ 应该抛出异常")
        except ValueError as e:
            print(f"  ✅ 正确拒绝无效状态: {e}")

        # 10. 测试全部完成检测
        print("\n[10] 测试全部完成检测...")
        for i in range(1, 6):
            if i == 2:
                progress2.update_chapter(i, "review_failed")
                progress2.update_chapter(i, "completed", score=80.0)
            elif i == 3:
                progress2.update_chapter(i, "completed", score=85.0)
            elif i == 4:
                progress2.update_chapter(i, "completed", score=90.0)
            elif i == 5:
                progress2.update_chapter(i, "completed", score=88.0)

        resume = progress2.resume()
        assert not resume["can_resume"], "全部完成后不应该再恢复"
        assert "message" in resume, "应该有完成消息"
        print(f"  ✅ {resume['message']}")

        print("\n" + "=" * 60)
        print("WorkflowProgress: 全部测试通过 ✅")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir)


def test_idempotent_checker():
    """测试 IdempotentChecker 类"""
    import tempfile
    import shutil

    print("\n" + "=" * 60)
    print("测试 IdempotentChecker")
    print("=" * 60)

    test_dir = tempfile.mkdtemp()
    index_file = os.path.join(test_dir, "doc_index.json")

    try:
        # 1. 创建检查器
        print("\n[1] 创建幂等检查器...")
        checker = IdempotentChecker(folder_token="test_folder_001", doc_index=index_file)
        print(f"  ✅ 检查器创建成功, folder: {checker.folder_token}")

        # 2. 检查不存在的文档
        print("\n[2] 检查不存在的文档...")
        check = checker.check_exists(1, "穿越")
        assert check["exists"] is False, "应该不存在"
        print(f"  ✅ 第1章不存在: exists={check['exists']}")

        # 3. 创建前检查
        print("\n[3] 创建前检查...")
        result = checker.before_create(1, "穿越")
        assert result["should_create"] is True, "应该允许创建"
        print(f"  ✅ 可以创建: {result['reason']}")

        # 4. 注册已创建的文档
        print("\n[4] 注册已创建文档...")
        checker.register_created(
            chapter_num=1,
            title="穿越",
            doc_id="doc_abc123",
            doc_url="https://www.feishu.cn/docx/abc123"
        )
        print(f"  ✅ 已注册: ch1-穿越 -> doc_abc123")

        # 5. 再次检查（应存在）
        print("\n[5] 再次检查（应存在）...")
        check = checker.check_exists(1, "穿越")
        assert check["exists"] is True, "应该存在"
        assert check["doc_id"] == "doc_abc123", "doc_id 不对"
        print(f"  ✅ 已存在: doc_id={check['doc_id']}")

        # 6. 创建前检查（应跳过）
        print("\n[6] 创建前检查（应跳过）...")
        result = checker.before_create(1, "穿越")
        assert result["should_create"] is False, "应该跳过"
        assert result["existing_doc_id"] == "doc_abc123", "已有文档ID不对"
        print(f"  ✅ 跳过创建: {result['reason']}")

        # 7. 批量注册
        print("\n[7] 批量注册多个文档...")
        for i in range(2, 4):
            checker.register_created(
                chapter_num=i,
                title=f"章节{i}",
                doc_id=f"doc_{i}",
                doc_url=f"https://www.feishu.cn/docx/doc_{i}"
            )
        print(f"  ✅ 已注册第2-3章")

        # 8. 列出所有
        print("\n[8] 列出所有已注册文档...")
        all_docs = checker.list_all()
        assert len(all_docs) == 3, f"应该有3个文档, 实际 {len(all_docs)}"
        print(f"  ✅ 共 {len(all_docs)} 个文档")
        for doc in all_docs:
            print(f"    - 第 {doc['chapter_num']} 章: {doc['doc_id']}")

        # 9. 索引持久化
        print("\n[9] 索引持久化测试...")
        checker2 = IdempotentChecker(folder_token="test_folder_001", doc_index=index_file)
        check = checker2.check_exists(1, "穿越")
        assert check["exists"] is True, "持久化后应该能找到"
        print(f"  ✅ 重新加载后找到第1章: {check['doc_id']}")

        # 10. 不同章节名
        print("\n[10] 不同章节名不冲突...")
        check = checker.check_exists(5, "决战")
        assert check["exists"] is False, "第5章应该不存在"
        print(f"  ✅ 第5章不存在，可以创建")

        print("\n" + "=" * 60)
        print("IdempotentChecker: 全部测试通过 ✅")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir)


def test_integration():
    """集成测试：进度 + 幂等检查"""
    import tempfile
    import shutil

    print("\n" + "=" * 60)
    print("集成测试: WorkflowProgress + IdempotentChecker")
    print("=" * 60)

    test_dir = tempfile.mkdtemp()

    try:
        # 一键创建
        progress, checker = create_progress_and_checker(
            project_id="novel_001",
            novel_name="测试集成",
            total_chapters=3,
            folder_token="folder_test",
            progress_dir=test_dir
        )
        print("  ✅ 进度管理器和幂等检查器创建成功")

        # 模拟完整流程
        for ch_num in range(1, 4):
            # 幂等检查
            can_create = checker.before_create(ch_num, f"第 {ch_num:02d} 章")
            assert can_create["should_create"] is True
            print(f"\n  📝 第 {ch_num} 章: {can_create['reason']}")

            # 模拟创建飞书文档
            doc_id = f"doc_{ch_num}"
            doc_url = f"https://feishu.cn/docx/{ch_num}"
            checker.register_created(ch_num, f"第 {ch_num:02d} 章", doc_id, doc_url)

            # 更新进度
            progress.update_chapter(ch_num, "writing")
            progress.update_chapter(
                ch_num, "completed",
                score=80 + ch_num,
                doc_url=doc_url,
                doc_id=doc_id
            )
            print(f"    ✅ 完成, 评分: {80 + ch_num}")

        # 恢复检查
        resume = progress.resume()
        assert not resume["can_resume"]
        print(f"\n  🎉 {resume['message']}")

        # 摘要
        summary = progress.get_summary()
        print(f"  📊 总章节: {summary['total_chapters']}, 已完成: {summary['completed']}")

        # 重复执行幂等检查
        print("\n  🔄 重复执行测试...")
        for ch_num in range(1, 4):
            check = checker.before_create(ch_num, f"第 {ch_num:02d} 章")
            assert check["should_create"] is False, f"第 {ch_num} 章应该被跳过"
            print(f"    ✅ 第 {ch_num} 章跳过: {check['reason']}")

        print("\n" + "=" * 60)
        print("集成测试: 全部通过 ✅")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_workflow_progress()
    test_idempotent_checker()
    test_integration()

    print("\n" + "🎉" * 30)
    print("所有测试通过！v3.0 进度持久化模块可用")
    print("🎉" * 30)
