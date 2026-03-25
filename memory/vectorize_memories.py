#!/usr/bin/env python3
"""
记忆向量化脚本
为所有记忆项生成 embedding 并存储向量索引

依赖：pip install sentence-transformers numpy
"""

from sentence_transformers import SentenceTransformer
import json
import os
from pathlib import Path
from datetime import datetime

# 配置
MODEL_NAME = 'all-MiniLM-L6-v2'  # 384 维，90MB，快速
MEMORY_DIR = Path('/Users/narain/.openclaw/workspace/memory/items')
OUTPUT_FILE = Path('/Users/narain/.openclaw/workspace/memory/记忆向量索引.json')

print(f"🚀 开始向量化记忆系统...")
print(f"模型：{MODEL_NAME}")
print(f"记忆目录：{MEMORY_DIR}")
print()

# 加载模型
print("📥 加载 embedding 模型...")
model = SentenceTransformer(MODEL_NAME)
print(f"✅ 模型加载完成")
print()

def extract_content(file_path):
    """提取 markdown 文件内容（去除元数据和标题）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 跳过元数据行（以 > 开头的行）和标题
    lines = content.split('\n')
    content_lines = []
    skip_until_divider = True
    
    for line in lines:
        if line.strip() == '---' and skip_until_divider:
            skip_until_divider = False
            continue
        if not skip_until_divider:
            # 跳过空行和元数据
            if line.strip() and not line.startswith('>'):
                content_lines.append(line)
    
    return '\n'.join(content_lines)

def generate_vectors():
    """为所有记忆项生成向量"""
    vectors = {}
    documents = {}
    categories_found = set()
    
    # 遍历所有记忆项
    categories = ['preferences', 'knowledge', 'skills', 'relationships']
    
    for category in categories:
        category_dir = MEMORY_DIR / category
        
        if not category_dir.exists():
            print(f"⚠️  目录不存在：{category_dir}")
            continue
        
        md_files = list(category_dir.glob('*.md'))
        print(f"📁 处理分类：{category} ({len(md_files)} 个文件)")
        
        for md_file in md_files:
            try:
                # 提取内容
                content = extract_content(md_file)
                
                if not content.strip():
                    print(f"  ⚠️  空内容：{md_file.name}")
                    continue
                
                # 生成向量
                vector = model.encode(content).tolist()
                
                # 存储
                key = f"{category}/{md_file.stem}"
                vectors[key] = vector
                documents[key] = {
                    'path': str(md_file),
                    'category': category,
                    'title': md_file.stem,
                    'content_preview': content[:300],  # 前 300 字符
                    'content_length': len(content),
                    'vectorized_at': datetime.now().isoformat()
                }
                
                categories_found.add(category)
                print(f"  ✅ {key}")
                
            except Exception as e:
                print(f"  ❌ 错误 {md_file.name}: {e}")
    
    print()
    
    # 保存索引
    output = {
        'model': MODEL_NAME,
        'dimension': 384,
        'vectorized_at': datetime.now().isoformat(),
        'categories': list(categories_found),
        'count': len(vectors),
        'vectors': vectors,
        'documents': documents
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"🎉 完成！")
    print(f"📊 统计信息:")
    print(f"   - 分类数：{len(categories_found)}")
    print(f"   - 记忆项数：{len(vectors)}")
    print(f"   - 向量维度：384")
    print(f"   - 索引文件大小：{os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")
    print(f"📄 索引文件：{OUTPUT_FILE}")
    
    return output

if __name__ == '__main__':
    try:
        generate_vectors()
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
