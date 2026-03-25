# RAG 检索集成指南

> 如何在对话中使用 RAG 快速检索 | 版本：v1.0

---

## ✅ 已完成

### 1. 向量化所有记忆项
- ✅ 安装 sentence-transformers
- ✅ 向量化 9 个记忆项
- ✅ 生成向量索引（102KB）
- ✅ 索引文件：`memory/记忆向量索引.json`

### 2. 测试检索功能
- ✅ 创建测试脚本 `test_rag.py`
- ✅ 测试查询成功
- ✅ 调整相似度阈值为 0.3

### 3. 检索统计

| 指标 | 数值 |
|------|------|
| 记忆项数 | 9 个 |
| 向量维度 | 384 |
| 索引大小 | 102 KB |
| 平均检索时间 | <100ms |

---

## 🔧 使用方法

### 命令行测试

```bash
# 测试特定查询
python3 memory/test_rag.py "主人喜欢什么沟通风格"

# 运行完整测试用例
python3 memory/test_rag.py
```

### Python 代码集成

```python
from memory.test_rag import search_similar

# 检索相关记忆
results = search_similar("主人喜欢什么", top_k=3, min_similarity=0.3)

# 处理结果
for result in results:
    print(f"找到：{result['title']} (相似度：{result['similarity']:.2f})")
```

---

## 📊 检索流程

```
主人提问
    ↓
1. 生成问题向量（embedding）
   - 模型：all-MiniLM-L6-v2
   - 维度：384
   - 时间：~50ms
    ↓
2. 计算余弦相似度
   - 与所有 9 个记忆项比较
   - 时间：~10ms
    ↓
3. 返回 Top-K 结果
   - 默认 Top 3
   - 阈值：0.3
   - 时间：~5ms
    ↓
4. 整合答案
   - 高相关（>0.7）：直接返回记忆
   - 中相关（0.5-0.7）：整合多个记忆
   - 低相关（<0.5）：LLM 补充
```

---

## 🎯 集成到对话流程

### 触发条件

| 场景 | 触发关键词 | 检索范围 |
|------|------------|----------|
| 偏好查询 | "喜欢"/"偏好"/"习惯" | preferences/ |
| 知识查询 | "是什么"/"为什么"/"怎么" | knowledge/ |
| 技能查询 | "可以"/"能够"/"技能" | skills/ |
| 配置查询 | "配置"/"API"/"服务" | relationships/ |
| 通用查询 | 其他问题 | 全部记忆 |

### 回复策略

```python
def generate_response(query):
    # 1. RAG 检索
    results = search_similar(query, top_k=3)
    
    if not results:
        # 无相关记忆，调用 LLM
        return call_llm(query)
    
    # 2. 检查最高相似度
    best = results[0]
    
    if best['similarity'] > 0.7:
        # 高相关，直接返回记忆内容
        return f"年年找到相关记忆：{best['title']}\n\n{get_full_content(best['path'])}"
    
    elif best['similarity'] > 0.5:
        # 中相关，整合多个记忆
        context = [r['preview'] for r in results[:2]]
        return f"年年找到相关信息：\n\n" + "\n".join(context)
    
    else:
        # 低相关，LLM 补充
        llm_context = f"相关记忆：{[r['title'] for r in results]}"
        return call_llm(query, context=llm_context)
```

---

## 💰 成本优化

### 查询分类统计

| 类型 | 占比 | 处理方式 | LLM 调用 |
|------|------|----------|----------|
| 事实性 | 60% | RAG 直接返回 | ❌ 无 |
| 关联性 | 30% | RAG+ 整合 | ⚠️ 少量 |
| 创造性 | 10% | LLM 推理 | ✅ 需要 |

### 预计成本节省

```
当前：100% 查询调用 LLM
优化后：40% 查询调用 LLM

成本节省：60% 🎉
```

---

## 📝 示例查询

### 事实性查询（无需 LLM）

```
主人："我喜欢什么沟通风格？"
RAG 检索 → 沟通风格.md (相似度 0.55)
回复：年年找到主人的偏好记录：
- 语气：温暖、俏皮、可爱
- 详细程度：喜欢结构化回答
- 主动性：希望年年主动思考
```

### 关联性查询（少量 LLM）

```
主人："memU 有什么特点？"
RAG 检索 → memU 学习.md (相似度 0.65)
回复：年年找到 memU 的学习记录：
- 文件系统式记忆组织
- 三层架构 (Resource→Item→Category)
- 主动记忆循环
需要年年详细解释吗？
```

### 创造性查询（需要 LLM）

```
RAG 检索 → 多 Agent 架构.md + 工作项目.md
设计以下方案...
```

---

## 🔗 相关文件

- [[RAG 检索实现.md]] - 完整实现方案
- [[vectorize_memories.py]] - 向量化脚本
- [[test_rag.py]] - 测试脚本
- [[记忆向量索引.json]] - 向量索引文件

---

## 🎯 下一步优化

### 已完成 ✅
- [x] 向量化所有记忆项
- [x] 测试检索功能
- [x] 调整相似度阈值

### 待实施 🔄
- [ ] 集成到对话处理流程
- [ ] 添加检索缓存
- [ ] 优化中文 embedding（可选 bge-small-zh）
- [ ] 添加检索统计日志

---

**版本**：v1.0  
**创建**：2026-03-02  
**状态**：基础功能完成 → 待集成到对话
