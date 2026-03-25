# 主动记忆提取脚本

> 年年的记忆提取工具 | 基于 Python | memU 理念实现

---

## 📋 功能说明

此脚本用于：
1. 分析对话内容
2. 识别可记忆的信息
3. 自动分类并创建记忆项
4. 建立交叉引用
5. 更新 MEMORY.md 索引

---

## 🎯 使用方式

### 方式一：年年手动调用（当前）
年年在对话中识别到重要信息后，手动创建记忆项文件。

### 方式二：自动化脚本（未来）
```bash
# 从对话日志提取记忆
python extract_memory.py --input conversation.md --output memory/items/

# 从飞书表格提取
python extract_memory.py --feishu --app_token XXX --table_id XXX

# 批量处理日常日志
python extract_memory.py --batch memory/daily/ --output memory/items/
```

---

## 📝 提取逻辑伪代码

```python
def extract_memory(conversation):
    memories = []
    
    for message in conversation:
        # 识别偏好
        if contains(message, ["我喜欢", "偏好", "希望"]):
            memory = create_preference(message)
            memories.append(memory)
        
        # 识别意图
        elif contains(message, ["帮我", "我要", "需要"]):
            memory = create_intent(message)
            memories.append(memory)
        
        # 识别知识
        elif contains(message, ["明白了", "学习了", "理解了"]):
            memory = create_knowledge(message)
            memories.append(memory)
        
        # 识别关系
        elif contains(message, ["公司", "配置", "API"]):
            memory = create_relationship(message)
            memories.append(memory)
        
        # 识别技能
        elif contains(message, ["学会了", "可以", "完成了"]):
            memory = create_skill(message)
            memories.append(memory)
    
    # 去重、建立链接、更新索引
    return process_memories(memories)
```

---

## 🔗 交叉引用生成

```python
def create_cross_references(new_memory, existing_memories):
    references = []
    
    # 关键词匹配
    for existing in existing_memories:
        if has_common_keywords(new_memory, existing):
            references.append(existing.path)
    
    # 分类匹配
    if new_memory.category in existing_categories:
        references.append(f"../categories/{new_memory.category}")
    
    return references
```

---

## 📊 提取统计

```python
def generate_stats():
    stats = {
        "total": count_all_memories(),
        "by_category": count_by_category(),
        "by_confidence": count_by_confidence(),
        "cross_refs": count_cross_references(),
        "today": count_today_memories()
    }
    return stats
```

---

## 🎯 年年的提取流程

### 步骤 1：识别
在对话过程中实时识别可记忆的信息

### 步骤 2：分类
判断信息属于哪个类别（偏好/意图/知识/关系/技能）

### 步骤 3：创建
按照模板创建记忆项文件

### 步骤 4：链接
建立与现有记忆的交叉引用

### 步骤 5：更新
更新 MEMORY.md 索引和统计

---

## 💡 优化方向

1. **LLM 辅助提取** - 用 LLM 自动识别和分类
2. **向量化去重** - 用 embedding 检测相似记忆
3. **自动摘要** - 长对话自动摘要后提取
4. **定时提取** - 心跳时批量处理未提取对话

---

**版本**：1.0  
**创建**：2026-03-02  
**状态**：手动执行 → 未来自动化
