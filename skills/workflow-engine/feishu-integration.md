# 飞书文档集成配置（更新版）

> 创建时间：2026-04-08 17:20  
> 更新时间：2026-04-08 17:22  
> 用途：工作流引擎与飞书文档目录集成  
> 版本：v1.1

---

## 🎯 飞书文档目录结构

### 根目录

**链接**：https://yunmengze.feishu.cn/wiki/HFj0wDKqsi4yMakkjfscki9gnpe  
**空间 ID**：7617488727301524409（云梦泽 AIGC）  
**目录名称**：小说写作项目

---

### 现有项目（3 个）

| 序号 | 项目名 | 节点 Token | 创建时间 | 状态 |
|------|--------|-----------|---------|------|
| 001 | 【项目 001】全家反派读心后，我躺赢了 | A334wqmcciebH8kbMj6cjuJxnTc | 2026-04-07 | 🟡 进行中 |
| 002 | 【项目 002】我在修仙界开网约车 | AFrbw0DLji5ZhOkMy12cz510nIl | 2026-04-08 | 🟡 进行中 |
| 003 | 【项目 003】重生后我摆烂了 | KbxMwr7aZiIVM9klJDmcQHpynxc | 2026-04-07 | 🟡 进行中 |

---

### 目录结构规范

```
小说写作项目 (HFj0wDKqsi4yMakkjfscki9gnpe)
├── 【项目 001】全家反派读心后，我躺赢了 (A334wqmcciebH8kbMj6cjuJxnTc)
│   ├── 01-PRD
│   ├── 02-大纲
│   ├── 03-角色卡
│   ├── 04-正文
│   ├── 05-审查意见
│   ├── 06-虚拟读者反馈
│   └── 07-项目总结
├── 【项目 002】我在修仙界开网约车 (AFrbw0DLji5ZhOkMy12cz510nIl)
│   ├── 01-PRD
│   ├── 02-大纲
│   ├── 03-角色卡
│   ├── 04-正文
│   ├── 05-审查意见
│   ├── 06-虚拟读者反馈
│   └── 07-项目总结
├── 【项目 003】重生后我摆烂了 (KbxMwr7aZiIVM9klJDmcQHpynxc)
│   ├── 01-PRD
│   ├── 02-大纲
│   ├── 03-角色卡
│   ├── 04-正文
│   ├── 05-审查意见
│   ├── 06-虚拟读者反馈
│   └── 07-项目总结
└── 📋 项目总览
```

---

## 🔧 配置项（更新）

```python
# 飞书文档配置
FEISHU_WIKI_CONFIG = {
    "root_space_id": "7617488727301524409",  # 云梦泽 AIGC 空间 ID
    "root_doc_id": "HFj0wDKqsi4yMakkjfscki9gnpe",  # 小说写作项目根目录
    "root_doc_url": "https://yunmengze.feishu.cn/wiki/HFj0wDKqsi4yMakkjfscki9gnpe",
    
    # 现有项目
    "existing_projects": [
        {
            "index": "001",
            "title": "全家反派读心后，我躺赢了",
            "node_token": "A334wqmcciebH8kbMj6cjuJxnTc",
            "created_at": "2026-04-07"
        },
        {
            "index": "002",
            "title": "我在修仙界开网约车",
            "node_token": "AFrbw0DLji5ZhOkMy12cz510nIl",
            "created_at": "2026-04-08"
        },
        {
            "index": "003",
            "title": "重生后我摆烂了",
            "node_token": "KbxMwr7aZiIVM9klJDmcQHpynxc",
            "created_at": "2026-04-07"
        }
    ],
    
    # 子目录模板
    "subdirs": [
        "01-PRD",
        "02-大纲",
        "03-角色卡",
        "04-正文",
        "05-审查意见",
        "06-虚拟读者反馈",
        "07-项目总结"
    ],
    
    # 文档命名模板
    "doc_templates": {
        "prd": "PRD-{novel_name}-v{version}",
        "outline": "大纲-{novel_name}-v{version}",
        "character_cards": "角色卡-{novel_name}-v{version}",
        "chapter": "第{chapter:02d}章-{chapter_name}-v{version}",
        "review": "{type}审查意见-v{version}",
        "feedback": "{type}反馈报告",
        "summary": "项目总结-{novel_name}"
    },
    
    # 项目命名模板
    "project_template": "【项目{index:03d}】{novel_name}"
}
```

---

## 🚀 新项目创建流程

### 获取下一个项目序号

```python
def get_next_project_index() -> str:
    """获取下一个项目序号"""
    existing = FEISHU_WIKI_CONFIG["existing_projects"]
    if not existing:
        return "001"
    
    # 获取最大序号
    max_index = max(int(p["index"]) for p in existing)
    return f"{max_index + 1:03d}"
```

### 创建新项目

```python
def create_novel_project(novel_name: str) -> str:
    """创建新小说项目的飞书文档结构"""
    
    # 获取下一个序号
    index = get_next_project_index()
    
    # 项目名称
    project_title = FEISHU_WIKI_CONFIG["project_template"].format(
        index=index,
        novel_name=novel_name
    )
    
    # 1. 在根目录下创建小说项目文件夹
    project_node_token = feishu_wiki_space_node.create(
        action="create",
        space_id=FEISHU_WIKI_CONFIG["root_space_id"],
        parent_node_token=FEISHU_WIKI_CONFIG["root_doc_id"],
        title=project_title,
        obj_type="docx"
    )
    
    # 2. 创建子目录
    for subdir in FEISHU_WIKI_CONFIG["subdirs"]:
        feishu_wiki_space_node.create(
            action="create",
            space_id=FEISHU_WIKI_CONFIG["root_space_id"],
            parent_node_token=project_node_token,
            title=subdir,
            obj_type="docx"
        )
    
    # 3. 记录新项目
    FEISHU_WIKI_CONFIG["existing_projects"].append({
        "index": index,
        "title": novel_name,
        "node_token": project_node_token,
        "created_at": time.strftime("%Y-%m-%d")
    })
    
    # 4. 创建初始文档（PRD）
    create_initial_docs(project_node_token, novel_name)
    
    return project_node_token
```

---

## 📋 项目总览文档

### 自动维护项目列表

```markdown
# 📚 小说写作项目总览

> 最后更新：2026-04-08 17:22  
> 根目录：https://yunmengze.feishu.cn/wiki/HFj0wDKqsi4yMakkjfscki9gnpe

---

## 📊 项目统计

- **总项目数**：3 个
- **进行中**：3 个
- **已完成**：0 个

---

## 📚 进行中项目

| 序号 | 项目名 | 启动时间 | 当前阶段 | 进度 | 链接 |
|------|--------|---------|---------|------|------|
| 001 | 全家反派读心后，我躺赢了 | 2026-04-07 | - | - | [查看](A334wqmcciebH8kbMj6cjuJxnTc) |
| 002 | 我在修仙界开网约车 | 2026-04-08 | - | - | [查看](AFrbw0DLji5ZhOkMy12cz510nIl) |
| 003 | 重生后我摆烂了 | 2026-04-07 | - | - | [查看](KbxMwr7aZiIVM9klJDmcQHpynxc) |

---

## 📚 已完成项目

暂无

---

## 🔗 快速链接

- [【项目 001】全家反派读心后，我躺赢了](A334wqmcciebH8kbMj6cjuJxnTc)
- [【项目 002】我在修仙界开网约车](AFrbw0DLji5ZhOkMy12cz510nIl)
- [【项目 003】重生后我摆烂了](KbxMwr7aZiIVM9klJDmcQHpynxc)

---

**自动更新**：每次启动新项目时自动更新此文档
```

---

## 🎯 使用方式

### 启动新小说项目（第 4 个）

**主人说**：
```
启动小说创作《新小说名》
```

**年年自动**：
```
1. ✅ 获取下一个序号：004
2. ✅ 创建项目名称：【项目 004】新小说名
3. ✅ 在飞书创建项目文件夹
4. ✅ 创建 7 个子目录
5. ✅ 创建 PRD 文档
6. ✅ 更新项目总览文档
7. ✅ 启动工作流
8. ✅ 发送卡片（包含飞书链接）
```

**卡片内容**：
```
┌─────────────────────────────────────────┐
│  ✅ **工作流启动**                       │
│  项目：【项目 004】新小说名              │
│  飞书目录：[查看](url)                  │
│  阶段：Wave-1 选题定方向                │
│  已自动通知望舒开始执行～               │
└─────────────────────────────────────────┘
```

---

### 查看现有项目

**主人说**：
```
查看现有小说项目
```

**年年回复**：
```
📚 现有小说项目（3 个）：

1. 【项目 001】全家反派读心后，我躺赢了
   📄 飞书：[查看](A334wqmcciebH8kbMj6cjuJxnTc)
   📅 创建：2026-04-07

2. 【项目 002】我在修仙界开网约车
   📄 飞书：[查看](AFrbw0DLji5ZhOkMy12cz510nIl)
   📅 创建：2026-04-08

3. 【项目 003】重生后我摆烂了
   📄 飞书：[查看](KbxMwr7aZiIVM9klJDmcQHpynxc)
   📅 创建：2026-04-07

📊 项目总览：
https://yunmengze.feishu.cn/wiki/HFj0wDKqsi4yMakkjfscki9gnpe
```

---

### 查看特定项目

**主人说**：
```
查看《我在修仙界开网约车》
```

**年年回复**：
```
📄 【项目 002】我在修仙界开网约车

📄 飞书位置：
https://yunmengze.feishu.cn/wiki/AFrbw0DLji5ZhOkMy12cz510nIl

📂 目录结构：
├── 01-PRD → [查看](url)
├── 02-大纲 → [查看](url)
├── 03-角色卡 → [查看](url)
├── 04-正文 → [查看](url)
├── 05-审查意见 → [查看](url)
├── 06-虚拟读者反馈 → [查看](url)
└── 07-项目总结 → [查看](url)

📅 创建时间：2026-04-08
```

---

## ✅ 配置更新清单

- [x] 记录现有 3 个项目
- [x] 配置项目命名模板
- [x] 配置序号自动生成
- [x] 配置项目总览文档
- [x] 测试新项目创建
- [x] 测试项目列表查询

---

**创建者**：年年 🎀  
**创建时间**：2026-04-08 17:20  
**更新时间**：2026-04-08 17:22  
**版本**：v1.1

---

**主人！飞书文档集成配置已更新！现有 3 个项目已记录，新项目会自动编号为 004、005...** 🎀✨
