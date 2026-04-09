#!/usr/bin/env python3
"""
小说创作工作流 v2.0 - 真正的多Agent协同
优化点：
1. Agent直接通信，年年不当传话筒
2. 流水线并行：创作和审查同时进行
3. 虚拟读者必须调用
4. 审查严格化
5. 防重复机制
"""

# ==================== 工作流配置 ====================

NOVEL_WORKFLOW_V2 = {
    "version": "2.0",
    "name": "小说创作工作流",
    
    # 飞书配置
    "feishu": {
        "root_wiki_node": "HFj0wDKqsi4yMakkjfscki9gnpe",
        "space_id": "7617488727301524409"
    },
    
    # Agent 配置
    "agents": {
        "coordinator": {
            "id": "main",
            "session_key": "agent:main:main",
            "role": "只负责启动和最终汇报，不参与中间环节"
        },
        "writer": {
            "id": "jinghong",
            "session_key": "agent:jinghong:main",
            "role": "主笔作家，创作正文"
        },
        "reviewer": {
            "id": "qa_engineer",
            "session_key": "agent:qa_engineer:main",
            "role": "质量审查，严格评分"
        },
        "creative": {
            "id": "lingxi",
            "session_key": "agent:lingxi:main",
            "role": "创意总监，人设和创意"
        },
        "product": {
            "id": "product_manager",
            "session_key": "agent:product_manager:main",
            "role": "产品分析，选题和PRD"
        }
    },
    
    # 审查标准（严格化）
    "review_standards": {
        "min_word_count": 3000,
        "max_word_count": 4000,
        "min_hooks_per_chapter": 2,
        "min_reversals_total": 3,
        "max_perfect_score_ratio": 0.3,  # 最多30%章节可以满分
        "min_rejection_ratio": 0.2,  # 至少20%章节需要打回修改
        "must_call_virtual_reader": True,  # 必须调用虚拟读者
        "virtual_reader_min_score": 85,  # 虚拟读者最低分
        "payment_willingness_min": 80  # 付费意愿最低80%
    },
    
    # 流水线配置
    "pipeline": {
        "mode": "parallel",  # parallel=流水线并行, serial=串行
        "max_parallel_chapters": 2,  # 最多同时处理2章（1章创作+1章审查）
        "direct_communication": True,  # Agent直接通信
        "coordinator_involvement": "start_and_end_only"  # 年年只参与启动和结束
    }
}


# ==================== 启动指令模板 ====================

def generate_writer_instruction(novel_name, outline_url, character_url, wiki_node, total_chapters=12):
    """生成给惊鸿的完整指令（一次性分发，不再中转）"""
    
    return f"""[工作流 v2.0] 小说创作全自动执行

你是惊鸿（主笔作家），现在启动《{novel_name}》全自动创作流程。

【重要】这是全自动工作流，从第1章写到第{total_chapters}章，中间不经过年年！

大纲文档：{outline_url}
角色卡文档：{character_url}

═══════════════════════════════════════
每章执行流程（你自己完成，不需要年年中转）：
═══════════════════════════════════════

Step 1：创作本章正文
- 字数：3000-4000字
- 至少2个爽点
- 结尾钩子
- 创建飞书文档，命名：第 XX 章-章节名-v1.0
- wiki_node：{wiki_node}

Step 2：调用虚拟读者Skill（5位严格编辑团队）
- 编辑A（普通读者）：完读率评估，标出想划走的地方
- 编辑B（网文编辑）：付费意愿评估，爽点密度分析
- 编辑C（专业作家）：人物/情节/对话问题
- 编辑D（挑刺读者）：找AI味重的句子，前后矛盾
- 编辑E（改稿编辑）：给出具体修改方案（修改前后对比）
- 每章至少找出5个问题，禁止纯吹捧！
- 综合评分<85 → 按编辑E方案修改后重新评估
- AI味评分>50 → 必须重写AI味重的段落

Step 3：直接发给鉴微审查（不经过年年！）
- sessions_send 发给 agent:qa_engineer:main
- 消息格式：[审查请求] 第X章 | 链接：xxx | 虚拟读者评分：xx

Step 4：等待鉴微审查结果
- 鉴微会直接 sessions_send 回复你
- 通过 → 开始下一章（回到Step 1）
- 不通过 → 按意见修改 → 重新发给鉴微

Step 5：第{total_chapters}章完成后
- sessions_send 通知年年（agent:main:main）
- 格式：[全书完成] 惊鸿 | 总章节：{total_chapters} | 总字数：xxx | 飞书链接列表

═══════════════════════════════════════
防重复机制：
═══════════════════════════════════════
- 创建文档前先检查目录下是否已有同名文档
- 如果有 → 跳过，不重复创建
- 如果没有 → 创建新文档

═══════════════════════════════════════
命名规范：
═══════════════════════════════════════
- 统一格式：第 XX 章-章节名-v1.0
- XX 用两位数：01, 02, ... 12
- 不要用其他格式！

立即开始第1章！全自动执行到第{total_chapters}章！"""


def generate_reviewer_instruction(novel_name, total_chapters=12):
    """生成给鉴微的完整指令（一次性分发，不再中转）"""
    
    return f"""[工作流 v2.0] 小说审查全自动执行

你是鉴微（质量审查），现在启动《{novel_name}》全自动审查流程。

【重要】这是全自动工作流，惊鸿会直接发章节给你审查，你审查完直接回复惊鸿！不经过年年！

═══════════════════════════════════════
审查流程（每章）：
═══════════════════════════════════════

Step 1：收到惊鸿的审查请求
- 格式：[审查请求] 第X章 | 链接：xxx | 虚拟读者评分：xx

Step 2：读取飞书文档完整正文（必须读完整！）

Step 3：严格审查（7个标准）
1. 开篇300字有冲突？
2. 每2000字至少1个爽点？
3. 结尾有钩子？
4. 角色一致性？
5. 无逻辑bug？
6. 无敏感内容？
7. 虚拟读者评分≥85？

Step 4：调用虚拟读者Skill验证
- 独立评估完读率/付费意愿
- 与惊鸿的自评对比

Step 5：给出审查结论
- 直接 sessions_send 回复惊鸿（agent:jinghong:main）
- 不经过年年！

═══════════════════════════════════════
审查严格化要求：
═══════════════════════════════════════

【铁律】不能每章都给高分！
- 至少20%的章节必须打回修改（{total_chapters}章至少打回2-3章）
- 每章至少给出2个P1问题
- 满分（100分）最多给30%的章节
- 发现P0问题必须打回

审查回复格式：
[审查结果] 第X章 | 结论：通过/不通过 | P0：X个 | P1：X个 | 评分：X/100 | 虚拟读者：X分

如果不通过：
[审查结果] 第X章 | 结论：不通过 | P0：X个 | 修改要求：1.xxx 2.xxx 3.xxx

═══════════════════════════════════════
第{total_chapters}章审查完成后：
═══════════════════════════════════════
- sessions_send 通知年年（agent:main:main）
- 格式：[全书审查完成] 鉴微 | 通过率：X% | 打回率：X% | 平均评分：X

立即等待惊鸿的第1章审查请求！"""


def generate_start_command(novel_name, outline_url, character_url, wiki_node, total_chapters=12):
    """生成完整启动命令"""
    
    writer_cmd = generate_writer_instruction(novel_name, outline_url, character_url, wiki_node, total_chapters)
    reviewer_cmd = generate_reviewer_instruction(novel_name, total_chapters)
    
    return {
        "writer": writer_cmd,
        "reviewer": reviewer_cmd
    }


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 生成启动命令
    commands = generate_start_command(
        novel_name="测试小说",
        outline_url="https://www.feishu.cn/docx/xxx",
        character_url="https://www.feishu.cn/docx/yyy",
        wiki_node="HFj0wDKqsi4yMakkjfscki9gnpe",
        total_chapters=12
    )
    
    print("=" * 60)
    print("惊鸿指令预览（前500字）：")
    print("=" * 60)
    print(commands["writer"][:500])
    
    print("\n" + "=" * 60)
    print("鉴微指令预览（前500字）：")
    print("=" * 60)
    print(commands["reviewer"][:500])
    
    print("\n" + "=" * 60)
    print("v2.0 核心改进：")
    print("=" * 60)
    print("1. ✅ Agent直接通信，年年不当传话筒")
    print("2. ✅ 惊鸿自主循环12章，不需要年年中转")
    print("3. ✅ 虚拟读者必须调用")
    print("4. ✅ 审查严格化（至少打回20%）")
    print("5. ✅ 防重复机制")
    print("6. ✅ 统一命名规范")
