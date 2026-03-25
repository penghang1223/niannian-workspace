#!/usr/bin/env python3
"""
RAG 记忆检索测试脚本
测试向量化记忆的相似度搜索功能

用法：python memory/test_rag.py "查询内容"
"""

import json
import numpy as np
from numpy.linalg import norm
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 配置
MODEL_NAME = 'all-MiniLM-L6-v2'
INDEX_FILE = Path('/Users/narain/.openclaw/workspace/memory/记忆向量索引.json')

print("🔍 RAG 记忆检索测试")
print("=" * 50)

# 加载模型
print("📥 加载模型...")
model = SentenceTransformer(MODEL_NAME)
print("✅ 模型就绪")

# 加载索引
print("📥 加载向量索引...")
if not INDEX_FILE.exists():
    print(f"❌ 索引文件不存在：{INDEX_FILE}")
    print("请先运行：python memory/vectorize_memories.py")
    exit(1)

with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    index = json.load(f)

print(f"✅ 索引加载完成 ({index['count']} 个记忆项)")
print()

def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def search_similar(query, top_k=3, min_similarity=0.3):
    """搜索相关记忆"""
    # 生成查询向量
    query_vector = model.encode(query).tolist()
    
    # 计算所有相似度
    similarities = {}
    for key, vector in index['vectors'].items():
        sim = cosine_similarity(query_vector, vector)
        if sim >= min_similarity:  # 过滤低相关
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
            'preview': doc['content_preview'][:150] + '...'
        })
    
    return results

def print_results(query, results):
    """打印搜索结果"""
    print(f"🔎 查询：{query}")
    print("-" * 50)
    
    if not results:
        print("⚠️  未找到相关记忆（相似度 < 0.5）")
        return
    
    for i, result in enumerate(results, 1):
        sim_emoji = "🔥" if result['similarity'] > 0.7 else "💡" if result['similarity'] > 0.6 else "📌"
        print(f"{i}. {sim_emoji} {result['title']}")
        print(f"   分类：{result['category']}")
        print(f"   相似度：{result['similarity']:.3f}")
        print(f"   预览：{result['preview']}")
        print()

# 测试查询
test_queries = [
    "主人喜欢什么沟通风格",
    "memU 的核心理念",
    "囡囡有哪些技能",
    "飞书配置",
    "多 Agent 架构设计",
    "ruflo 的特点",
    "记忆系统重构",
]

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # 命令行查询
        query = ' '.join(sys.argv[1:])
        results = search_similar(query)
        print_results(query, results)
    else:
        # 运行测试用例
        print("🧪 运行测试用例...")
        print()
        
        for query in test_queries:
            results = search_similar(query, top_k=2)
            print_results(query, results)
            print("-" * 50)
            print()
        
        print("✅ 测试完成！")
