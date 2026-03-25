#!/usr/bin/env python3
"""
ReAct 引擎工具测试 - web_search 和 web_fetch

用法：python3 test_web_tools.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from react_engine import ReActEngine

print('='*60)
print('🧪 ReAct 引擎 web 工具测试')
print('='*60)

engine = ReActEngine(max_steps=4)

# 测试查询 - 需要网络搜索的问题
query = '2026 年 3 月 AI 领域有什么新动态？'
context = {'query': query}

print(f'🗣️  问题：{query}')
print('-'*60)

response = engine.reason(query, context)

print()
print('='*60)
print('✅ ReAct 推理完成')
print('='*60)
print(f'📊 推理步数：{len(engine.thoughts)}')
print(f'📝 使用的工具：{[a["type"] for a in engine.actions]}')
print()
print('📋 观察结果:')
for i, obs in enumerate(engine.observations, 1):
    if isinstance(obs, dict):
        if obs.get('success'):
            if obs.get('count'):
                print(f'  步骤{i}: ✅ 找到{obs["count"]}条结果')
            elif obs.get('content'):
                print(f'  步骤{i}: ✅ 获取网页成功 ({obs.get("size", 0)} 字符)')
        else:
            print(f'  步骤{i}: ⚠️  {obs.get("error", "未知错误")}')
    else:
        print(f'  步骤{i}: {obs}')
print()
print('🎀 囡囡回复预览:')
print(response[:800] + '...' if len(response) > 800 else response)
