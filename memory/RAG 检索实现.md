# RAG 快速检索实现

> 向量化记忆检索 | 版本：v1.0 | 创建：2026-03-02

---

## 🎯 目标

实现毫秒级记忆检索，成本降低 60%：
- ✅ 为所有记忆项生成向量表示
- ✅ 实现余弦相似度搜索
- ✅ 对话中自动检索相关记忆
- ✅ 优先返回缓存记忆，减少 LLM 调用

---

## 📊 检索流程

```
主人提问
    ↓
1. 检查问题类型
    ├─ 事实性问题 → RAG 检索
    ├─ 偏好性问题 → 检索 preferences/
    ├─ 知识性问题 → 检索 knowledge/
    └─ 创造性问题 → LLM 推理
    ↓
2. 生成问题向量（embedding）
    ↓
3. 相似度搜索（Top-K）
    ↓
4. 返回最相关记忆
    ↓
5. 如有需要，LLM 整合答案
```

---

## 🔧 实现方案

### 方案选择

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **本地 embedding** | 免费、快速 | 需要安装模型 | ✅ 首选 |
| **API embedding** | 无需安装 | 有成本、延迟 | 备选 |
| **关键词匹配** | 最简单 | 效果差 | ❌ 不选 |

### 推荐模型

| 模型 | 维度 | 大小 | 速度 | 推荐度 |
|------|------|------|------|--------|
| **all-MiniLM-L6-v2** | 384 | 90MB | 快 | ⭐⭐⭐⭐⭐ |
| **bge-small-zh** | 512 | 130MB | 快 | ⭐⭐⭐⭐ (中文优化) |
| **text-embedding-3-small** | 1536 | API | - | ⭐⭐⭐ (有成本) |

---

## 📝 向量化所有记忆

### 记忆项列表

当前需要向量化的记忆项（9 个）：

**preferences/**
- 沟通风格.md
- 文档格式.md
- 学习方式.md

**knowledge/**
- AI 编程趋势.md
- ruflo 学习.md
- memU 学习.md

**skills/**
- 年年技能树.md
- 多 Agent 架构.md

**relationships/**
- 服务配置.md

### 向量化脚本

```python
#!/usr/bin/env python3
"""
记忆向量化脚本
为所有记忆项生成 embedding 并存储
"""

from sentence_transformers import SentenceTransformer
import json
import os
from pathlib import Path

# 加载模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 记忆项路径
MEMORY_DIR = Path('/Users/narain/.openclaw/workspace/memory/items')
OUTPUT_FILE = Path('/Users/narain/.openclaw/workspace/memory/记忆向量索引.json')

def extract_content(file_path):
    """提取 markdown 文件内容（去除元数据）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 跳过元数据行（以 > 开头的行）
    lines = content.split('\n')
    content_lines = []
    skip_until = '---'
    found_first = False
    
    for line in lines:
        if line.strip() == '---':
            if not found_first:
                found_first = True
                continue
            else:
                break
        if found_first:
            content_lines.append(line)
    
    return '\n'.join(content_lines)

def generate_vectors():
    """为所有记忆项生成向量"""
    vectors = {}
    documents = {}
    
    # 遍历所有记忆项
    for category in ['preferences', 'knowledge', 'skills', 'relationships']:
        category_dir = MEMORY_DIR / category
        
        if not category_dir.exists():
            continue
        
        for md_file in category_dir.glob('*.md'):
            # 提取内容
            content = extract_content(md_file)
            
            # 生成向量
            vector = model.encode(content).tolist()
            
            # 存储
            key = f"{category}/{md_file.stem}"
            vectors[key] = vector
            documents[key] = {
                'path': str(md_file),
                'category': category,
                'title': md_file.stem,
                'content_preview': content[:200]
            }
            
            print(f"✅ 向量化：{key}")
    
    # 保存索引
    output = {
        'model': 'all-MiniLM-L6-v2',
        'dimension': 384,
        'vectors': vectors,
        'documents': documents,
        'count': len(vectors)
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 完成！共向量化 {len(vectors)} 个记忆项")
    print(f"索引文件：{OUTPUT_FILE}")
    
    return output

if __name__ == '__main__':
    generate_vectors()
```

---

## 🔍 相似度搜索

### 余弦相似度计算

```python
import numpy as np
from numpy.linalg import norm

def cosine_similarity(vec1, vec2):
    """计算两个向量的余弦相似度"""
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def search_similar(query, index_file, top_k=3):
    """搜索最相关的记忆"""
    # 加载索引
    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # 生成查询向量
    query_vector = model.encode(query).tolist()
    
    # 计算所有相似度
    similarities = {}
    for key, vector in index['vectors'].items():
        sim = cosine_similarity(query_vector, vector)
        similarities[key] = sim
    
    # 排序取 Top-K
    sorted_sims = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    top_results = sorted_sims[:top_k]
    
    # 返回结果
    results = []
    for key, sim in top_results:
        doc = index['documents'][key]
        results.append({
            'key': key,
            'similarity': float(sim),
            'title': doc['title'],
            'category': doc['category'],
            'path': doc['path'],
            'preview': doc['content_preview']
        })
    
    return results
```

---

## 💬 对话集成

### 检索触发条件

| 场景 | 触发 | 检索范围 |
|------|------|----------|
| 主人提问 | 问题包含"什么"/"怎么"/"为什么" | 全部记忆 |
| 提到偏好 | 包含"喜欢"/"偏好"/"习惯" | preferences/ |
| 提到学习 | 包含"学习"/"研究"/"理解" | knowledge/ |
| 提到技能 | 包含"可以"/"能够"/"技能" | skills/ |
| 提到配置 | 包含"配置"/"API"/"服务" | relationships/ |

### 回复整合

```python
def generate_response(query, rag_results):
    """根据 RAG 结果生成回复"""
    
    if not rag_results:
        # 无相关记忆，调用 LLM
        return call_llm(query)
    
    # 有相关记忆，整合答案
    context = []
    for result in rag_results:
        if result['similarity'] > 0.7:  # 高相关
            context.append(f"[{result['title']}]: {result['preview']}")
    
    if context:
        # 基于记忆回答
        response = f"年年找到相关记忆：\n\n"
        for i, ctx in enumerate(context, 1):
            response += f"{i}. {ctx}\n"
        response += f"\n主人需要年年详细解释吗？"
        return response
    else:
        # 相关度低，调用 LLM
        return call_llm(query)
```

---

## 📊 成本优化

### 检索策略

```
查询分类 → 路由到不同处理方式：

1. 事实性查询（60%）
   → RAG 检索 → 直接返回记忆 ✅ 无需 LLM

2. 关联查询（30%）
   → RAG 检索 + 简单整合 ✅ 低成本

3. 复杂推理（10%）
   → RAG 提供上下文 → LLM 深度推理 ⚠️ 高成本
```

### 预计成本节省

| 查询类型 | 占比 | 当前成本 | 优化后 | 节省 |
|----------|------|----------|--------|------|
| 事实性 | 60% | 100% LLM | 0% LLM | -60% |
| 关联性 | 30% | 100% LLM | 30% LLM | -21% |
| 复杂性 | 10% | 100% LLM | 100% LLM | 0% |
| **总计** | 100% | - | - | **-60%** |

---

## 🎯 实施步骤

### Step 1: 安装依赖（1 分钟）
```bash
pip install sentence-transformers numpy
```

### Step 2: 向量化记忆（5 分钟）
```bash
python memory/vectorize_memories.py
```

### Step 3: 测试检索（5 分钟）
```bash
python memory/test_rag.py "主人喜欢什么沟通风格"
```

### Step 4: 集成对话（30 分钟）
- 修改对话处理逻辑
- 添加 RAG 检索触发
- 测试各种场景

---

## 📝 测试用例

```python
# 测试查询
test_queries = [
    "主人喜欢什么沟通风格",  # 应检索 preferences/沟通风格
    "memU 的核心理念是什么",  # 应检索 knowledge/memU 学习
    "年年有哪些技能",  # 应检索 skills/年年技能树
    "飞书怎么配置",  # 应检索 relationships/服务配置
    "多 Agent 架构怎么设计",  # 应检索 skills/多 Agent 架构
]

# 预期结果
for query in test_queries:
    results = search_similar(query, index_file)
    print(f"查询：{query}")
    print(f"Top 结果：{results[0]['title']} (相似度：{results[0]['similarity']:.2f})")
    print()
```

---

## 🔗 相关文件

- [[../EXTRACTION_RULES.md]] - 记忆提取规则
- [[../话题热度.json]] - 话题数据
- [[../优化日志.md]] - 优化日志

---

**版本**：v1.0  
**创建**：2026-03-02  
**状态**：设计完成 → 待执行
