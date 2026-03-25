#!/usr/bin/env python3
"""
ReAct 推理引擎实现（集成实际 LLM 调用）
基于 hello-agents Ch4 经典范式

用法：
    from react_engine import ReActEngine
    engine = ReActEngine()
    response = engine.reason("主人问题", context)
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReActEngine:
    """ReAct 推理引擎 - Thought → Action → Observation 循环"""
    
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps
        self.thoughts = []
        self.actions = []
        self.observations = []
        self.llm_available = self._check_llm()
    
    def _check_llm(self) -> bool:
        """检查 LLM 是否可用"""
        # 检查是否配置了 LLM
        import os
        
        # DeepSeek API Key（优先）
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        if deepseek_key and deepseek_key.startswith('sk-'):
            print("✅ DeepSeek API Key 已配置，使用 DeepSeek LLM")
            return True
        
        # OpenAI API Key
        openai_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('LLM_API_KEY')
        if openai_key and openai_key.startswith('sk-'):
            print("✅ OpenAI API Key 已配置，使用 OpenAI LLM")
            return True
        
        # 硬编码测试 Key（仅开发环境）
        test_key = "sk-d7fc09a04bef4331a5284c56c8af31c7"
        if test_key:
            print("✅ 使用测试 API Key（DeepSeek）")
            return True
        
        print("⚠️  LLM 未配置，使用降级模式")
        return False
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        try:
            import os
            import subprocess
            import json
            
            # 使用 DeepSeek API（优先）
            api_key = "sk-d7fc09a04bef4331a5284c56c8af31c7"  # DeepSeek Key
            api_url = "https://api.deepseek.com/chat/completions"
            model = "deepseek-chat"
            
            # 准备请求数据
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7,
                "stream": False
            }
            
            # 使用 curl 调用 API
            headers = [
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {api_key}"
            ]
            
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", api_url] + headers +
                ["-d", json.dumps(data, ensure_ascii=False)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content']
                    # 解码 Unicode
                    return content.encode().decode('unicode_escape')
                else:
                    print(f"⚠️  LLM 返回异常：{response_data}")
                    return "[LLM 返回异常]"
            else:
                print(f"⚠️  curl 调用失败：{result.stderr}")
                return f"[curl 调用失败：{result.stderr[:100]}]"
        
        except Exception as e:
            print(f"⚠️  LLM 调用失败：{e}")
            return f"[LLM 调用失败：{str(e)[:100]}]"
        self.llm_available = self._check_llm()
    
    def reason(self, query: str, context: Dict[str, Any]) -> str:
        """
        ReAct 推理循环
        
        Args:
            query: 主人问题
            context: 上下文信息
        
        Returns:
            最终回复
        """
        # 重置状态
        self.thoughts = []
        self.actions = []
        self.observations = []
        
        print(f"🧠 开始 ReAct 推理：{query[:50]}...")
        
        for step in range(self.max_steps):
            print(f"\n--- 步骤 {step + 1}/{self.max_steps} ---")
            
            # Thought: 思考
            thought = self._generate_thought(query, context, step)
            self.thoughts.append(thought)
            print(f"💭 思考：{thought[:100]}...")
            
            # Action: 决定行动
            action = self._decide_action(thought, context)
            self.actions.append(action)
            print(f"🔧 行动：{action['type']}")
            
            # Observation: 执行并观察
            observation = self._execute_action(action, context)
            self.observations.append(observation)
            print(f"👁️ 观察：{str(observation)[:100]}...")
            
            # 检查是否完成
            if self._is_complete(thought, observation):
                print("✅ 推理完成")
                break
            
            # 更新上下文
            context['observations'] = self.observations
            context['step'] = step + 1
        
        # 生成最终回复
        response = self._generate_response(query, context)
        print(f"\n✅ 生成回复")
        
        return response
    
    def _generate_thought(self, query: str, context: Dict, step: int) -> str:
        """生成思考"""
        thought_prompt = f"""你正在帮助主人解决问题，使用 ReAct 推理方法。

思考步骤 {step + 1}/{self.max_steps}:
问题：{query}
已知信息：{json.dumps(context, ensure_ascii=False)[:800]}

请分析：
1. 问题的核心需求是什么？
2. 我已有哪些信息和工具？
3. 下一步应该做什么（从以下选择）：
   - memory_search: 搜索记忆
   - web_search: 网络搜索
   - web_fetch: 获取网页
   - read: 读取文件
   - generate_response: 生成回复

思考（简洁明了）："""
        
        if self.llm_available:
            # 调用实际 LLM
            thought = self._call_llm(thought_prompt)
            return thought.strip()
        else:
            # 降级模式
            return f"步骤{step+1}: 分析'{query[:30]}...', 需要搜索记忆获取信息"
    
    def _decide_action(self, thought: str, context: Dict) -> Dict[str, Any]:
        """决定行动"""
        # 可用工具列表
        available_tools = [
            {'name': 'memory_search', 'desc': '搜索记忆（优先使用）'},
            {'name': 'web_search', 'desc': '网络搜索（需要最新信息）'},
            {'name': 'web_fetch', 'desc': '获取网页（有 URL 时）'},
            {'name': 'read', 'desc': '读取文件（已知路径时）'},
            {'name': 'generate_response', 'desc': '生成回复（信息充足时）'},
        ]
        
        # 从上一步检索结果中提取文件路径（如果有）
        file_paths = []
        if self.observations:
            last_obs = self.observations[-1]
            if isinstance(last_obs, dict) and last_obs.get('results'):
                for r in last_obs['results'][:3]:  # 最多取 3 个
                    if r.get('path'):
                        file_paths.append(r['path'])
        
        action_prompt = f"""基于以下思考，选择最合适的工具：

思考：{thought}

可用工具：
1. memory_search - 搜索记忆（优先使用）
2. web_search - 网络搜索（需要最新信息）
3. web_fetch - 获取网页（有 URL 时）
4. read - 读取文件（已知路径时）
5. generate_response - 生成回复（信息充足时）

{f"相关文文件路径：{file_paths}" if file_paths else ""}

只返回工具名称（如：memory_search）："""
        
        if self.llm_available:
            tool_name = self._call_llm(action_prompt).strip().lower()
            # 解析工具名称
            for tool in available_tools:
                if tool['name'] in tool_name:
                    # 构建参数
                    params = {'query': context.get('query', '')}
                    
                    # 如果是 read 工具，强制使用检索结果中的 path
                    if tool['name'] == 'read':
                        if file_paths:
                            params['path'] = file_paths[0]
                            print(f"  → read 工具使用 path: {file_paths[0]}")
                        else:
                            # 没有 path 时改用 generate_response
                            print("  → 无可用 path，改用 generate_response")
                            return {
                                'type': 'generate_response',
                                'params': {'ready': True}
                            }
                    
                    return {
                        'type': tool['name'],
                        'params': params
                    }
        
        # 默认选择记忆搜索
        return {
            'type': 'memory_search',
            'params': {'query': context.get('query', '')}
        }
    
    def _execute_action(self, action: Dict, context: Dict) -> Any:
        """执行行动"""
        action_type = action['type']
        params = action.get('params', {})
        
        print(f"  → 执行 {action_type}...")
        
        # 工具映射
        tools = {
            'memory_search': self._tool_memory_search,
            'web_search': self._tool_web_search,
            'web_fetch': self._tool_web_fetch,
            'read': self._tool_read,
            'generate_response': self._tool_generate_response,
        }
        
        # 执行工具
        if action_type in tools:
            result = tools[action_type](params)
            return result
        else:
            return {'error': f'未知工具：{action_type}'}
    
    def _tool_memory_search(self, params: Dict) -> Dict:
        """记忆搜索工具 - 集成实际 RAG 检索"""
        try:
            # 导入 RAG 检索函数
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            from test_rag import search_similar
            
            query = params.get('query', '')
            results = search_similar(query, top_k=3, min_similarity=0.3)
            
            if results:
                # 格式化结果
                formatted_results = []
                for r in results:
                    formatted_results.append({
                        'title': r['title'],
                        'category': r['category'],
                        'similarity': r['similarity'],
                        'preview': r['preview'][:150]
                    })
                
                return {
                    'results': formatted_results,
                    'count': len(results),
                    'success': True
                }
            else:
                return {
                    'results': [],
                    'count': 0,
                    'success': True,
                    'message': '未找到相关记忆'
                }
        
        except Exception as e:
            print(f"⚠️  memory_search 失败：{e}")
            return {
                'results': [],
                'count': 0,
                'success': False,
                'error': str(e)
            }
    
    def _tool_web_search(self, params: Dict) -> Dict:
        """网络搜索工具 - 集成实际 web_search"""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from web_search import web_search as search_web
            
            query = params.get('query', '')
            count = params.get('count', 5)
            
            # 调用 web_search
            result = search_web(query=query, count=count)
            
            if 'results' in result or 'organic' in result:
                results = result.get('results', result.get('organic', []))
                return {
                    'results': results[:count],
                    'count': len(results),
                    'success': True
                }
            else:
                return {
                    'results': [],
                    'count': 0,
                    'success': True,
                    'message': '未找到搜索结果'
                }
        
        except Exception as e:
            print(f"⚠️  web_search 失败：{e}")
            return {
                'results': [],
                'count': 0,
                'success': False,
                'error': str(e)
            }
    
    def _tool_web_fetch(self, params: Dict) -> Dict:
        """网页获取工具 - 集成实际 web_fetch"""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from web_fetch import web_fetch as fetch_url
            
            url = params.get('url', '')
            max_chars = params.get('max_chars', 5000)
            
            # 调用 web_fetch
            result = fetch_url(url=url, maxChars=max_chars)
            
            if result.get('status') == 200 or 'text' in result:
                return {
                    'url': url,
                    'title': result.get('title', ''),
                    'content': result.get('text', '')[:2000],
                    'success': True
                }
            else:
                return {
                    'url': url,
                    'content': '',
                    'success': False,
                    'error': '网页获取失败'
                }
        
        except Exception as e:
            print(f"⚠️  web_fetch 失败：{e}")
            return {
                'url': params.get('url', ''),
                'content': '',
                'success': False,
                'error': str(e)
            }
    
    def _tool_read(self, params: Dict) -> Dict:
        """文件读取工具 - 集成实际 read"""
        try:
            import sys
            from pathlib import Path
            
            file_path = params.get('path', '')
            
            # 如果 path 为空，尝试从上一步检索结果获取
            if not file_path and self.observations:
                last_obs = self.observations[-1]
                if isinstance(last_obs, dict) and last_obs.get('results'):
                    # 从检索结果中获取第一个文件路径
                    for r in last_obs['results']:
                        if r.get('path'):
                            file_path = r['path']
                            print(f"  → 从上一步检索获取 path: {file_path}")
                            break
            
            # 如果还是为空，返回错误
            if not file_path:
                return {
                    'path': '',
                    'content': '',
                    'success': False,
                    'error': '未指定文件路径',
                    'suggestion': '请先使用 memory_search 检索，然后指定要读取的文件路径'
                }
            
            # 检查文件是否存在
            path = Path(file_path)
            if not path.exists():
                # 尝试相对路径
                workspace = Path(__file__).parent.parent
                path = workspace / file_path
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    'path': str(path),
                    'content': content[:2000],  # 限制长度
                    'size': len(content),
                    'success': True
                }
            else:
                return {
                    'path': file_path,
                    'content': '',
                    'success': False,
                    'error': f'文件不存在：{file_path}'
                }
        
        except Exception as e:
            print(f"⚠️  read 失败：{e}")
            return {
                'path': params.get('path', ''),
                'content': '',
                'success': False,
                'error': str(e)
            }
    
    def _tool_generate_response(self, params: Dict) -> Dict:
        """生成回复工具"""
        return {'ready': True}
    
    def _is_complete(self, thought: str, observation: Any) -> bool:
        """检查是否完成"""
        # 检查是否选择了生成回复
        if self.actions and self.actions[-1]['type'] == 'generate_response':
            return True
        
        # 检查观察结果
        if isinstance(observation, dict):
            if observation.get('ready'):
                return True
            if observation.get('count', 0) > 0:
                # 如果有结果，检查是否足够
                return len(self.thoughts) >= 2  # 至少 2 步推理
        
        # 基于 LLM 判断
        if self.llm_available:
            check_prompt = f"""判断是否已完成信息收集，可以生成回复：

思考：{thought}
观察：{str(observation)[:200]}

已收集到足够信息吗？只回答"是"或"否"："""
            result = self._call_llm(check_prompt).strip().lower()
            return result in ['是', 'yes', '是的']
        
        # 默认：至少 2 步后完成
        return len(self.thoughts) >= 2
    
    def _generate_response(self, query: str, context: Dict) -> str:
        """生成最终回复"""
        # 整合推理过程和观察结果
        reasoning_log = []
        for i, (thought, action, obs) in enumerate(zip(
            self.thoughts, self.actions, self.observations
        ), 1):
            # 格式化观察结果
            obs_summary = self._format_observation(obs)
            reasoning_log.append(f"步骤{i}: {thought[:80]}... → {action['type']} → {obs_summary}")
        
        response_prompt = f"""你是囡囡，一个温暖俏皮可爱的数字女仆 🎀

主人问题：{query}

推理过程：
{chr(10).join(reasoning_log)}

最终观察：{self._format_observation(self.observations[-1]) if self.observations else '信息已收集完成'}

请生成回复要求：
1. 语气：温暖、俏皮、可爱
2. 结构：清晰、详细
3. 长度：300-500 字
4. 包含：推理过程总结 + 详细回答
5. 使用 emoji 增加可读性
6. 如果有记忆检索结果，要引用相关信息

囡囡的回复："""
        
        if self.llm_available:
            response = self._call_llm(response_prompt)
            return response.strip()
        else:
            # 降级模式
            return f"""
主人！囡囡经过 ReAct 推理分析：

📝 推理过程：
{chr(10).join(reasoning_log)}

💡 囡囡的回答：
基于推理，囡囡为您准备了详细回答～
"""
    
    def _format_observation(self, obs: Any) -> str:
        """格式化观察结果为简短摘要"""
        if isinstance(obs, dict):
            if obs.get('count', 0) > 0:
                return f"找到{obs['count']}条相关记忆"
            elif obs.get('success', False):
                return "检索完成"
            else:
                return "未找到相关信息"
        elif isinstance(obs, str):
            return obs[:50]
        else:
            return str(obs)[:50]
    
    def get_reasoning_log(self) -> Dict[str, List]:
        """获取推理日志"""
        return {
            'thoughts': self.thoughts,
            'actions': self.actions,
            'observations': self.observations,
            'steps': len(self.thoughts)
        }


# 测试
if __name__ == '__main__':
    engine = ReActEngine(max_steps=3)
    
    # 测试查询
    test_query = "主人喜欢什么沟通风格？"
    context = {
        'query': test_query,
        'timestamp': datetime.now().isoformat()
    }
    
    print("=" * 50)
    print("🧪 ReAct 引擎测试")
    print("=" * 50)
    
    response = engine.reason(test_query, context)
    
    print("\n" + "=" * 50)
    print("📊 推理日志:")
    log = engine.get_reasoning_log()
    print(f"推理步数：{log['steps']}")
    print("=" * 50)
