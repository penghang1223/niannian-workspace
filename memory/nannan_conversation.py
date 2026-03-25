#!/usr/bin/env python3
"""
囡囡对话处理器 v2.0 - 集成 ReAct 推理引擎

用法：
    from nannan_conversation import NannanConversation
    conv = NannanConversation()
    response = conv.process("主人问题")
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 导入 ReAct 引擎
from react_engine import ReActEngine

# 导入评估器
from nannan_evaluator import NannanEvaluator

# 导入记忆检索
try:
    from test_rag import search_similar
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG 检索不可用，使用降级模式")

class NannanConversation:
    """囡囡对话处理器 v2.0（集成 ReAct 引擎）"""
    
    def __init__(self, config_file: str = None):
        # 配置
        self.config = self._load_config(config_file)
        
        # 初始化组件
        self.react_engine = ReActEngine(max_steps=self.config.get('max_react_steps', 5))
        self.evaluator = NannanEvaluator(
            history_file='memory/评估历史.json'
        )
        
        # 对话上下文
        self.context = {
            'conversation_history': [],
            'topic_sequence': [],
            'user_preferences': {},
            'observations': []
        }
        
        # 性能统计
        self.stats = {
            'total_conversations': 0,
            'react_used': 0,
            'rag_used': 0,
            'avg_response_time': 0.0
        }
        
        print("🎀 囡囡对话处理器 v2.0 启动完成")
        print(f"   - ReAct 引擎：✅ (max_steps={self.config.get('max_react_steps', 5)})")
        print(f"   - RAG 检索：{'✅' if RAG_AVAILABLE else '⚠️'}")
        print(f"   - 质量评估：✅")
    
    def _load_config(self, config_file: str = None) -> Dict:
        """加载配置"""
        default_config = {
            'max_react_steps': 5,
            'use_react_for_complex': True,  # 复杂问题使用 ReAct
            'complex_threshold': 0.6,  # 复杂度阈值
            'enable_rag': True,
            'enable_evaluation': True,
        }
        
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                default_config.update(custom_config)
        
        return default_config
    
    def process(self, query: str) -> str:
        """
        处理主人问题
        
        Args:
            query: 主人的问题
        
        Returns:
            囡囡的回复
        """
        start_time = datetime.now()
        self.stats['total_conversations'] += 1
        
        print(f"\n{'='*50}")
        print(f"🗣️  主人：{query}")
        print(f"{'='*50}")
        
        # 1. 判断问题复杂度
        complexity = self._analyze_complexity(query)
        use_react = complexity >= self.config['complex_threshold']
        
        print(f"📊 问题复杂度：{complexity:.2f}")
        print(f"🔧 使用 ReAct: {'✅ 是' if use_react else '❌ 否'}")
        
        # 2. 根据复杂度选择处理方式
        if use_react:
            # 复杂问题：使用 ReAct 推理
            print("\n🧠 启动 ReAct 推理引擎...")
            response = self._process_with_react(query)
            self.stats['react_used'] += 1
        else:
            # 简单问题：直接回复
            print("\n⚡ 快速回复模式...")
            response = self._process_simple(query)
        
        # 3. RAG 检索增强（可选）
        if self.config['enable_rag'] and RAG_AVAILABLE:
            print("\n🔍 RAG 检索增强...")
            rag_context = self._enhance_with_rag(query)
            if rag_context:
                response = self._merge_rag_context(response, rag_context)
                self.stats['rag_used'] += 1
        
        # 4. 更新上下文
        self._update_context(query, response)
        
        # 5. 质量评估
        end_time = datetime.now()
        if self.config['enable_evaluation']:
            self.evaluator.evaluate(
                query=query,
                response=response,
                start_time=start_time,
                end_time=end_time,
                memory_used=self.stats['rag_used'] > 0,
                prediction_correct=False  # TODO: 意图预测集成
            )
        
        # 6. 更新统计
        response_time = (end_time - start_time).total_seconds()
        self.stats['avg_response_time'] = (
            self.stats['avg_response_time'] * (self.stats['total_conversations'] - 1) + 
            response_time
        ) / self.stats['total_conversations']
        
        # 7. 输出
        print(f"\n{'='*50}")
        print(f"🎀 囡囡：{response[:200]}...")
        print(f"⏱️  响应时间：{response_time:.2f}s")
        print(f"{'='*50}\n")
        
        return response
    
    def _analyze_complexity(self, query: str) -> float:
        """
        分析问题复杂度（0-1）
        
        复杂度因素：
        - 问题长度
        - 是否包含多个子问题
        - 是否需要多步推理
        - 是否涉及多个知识领域
        """
        score = 0.0
        
        # 因素 1：问题长度
        if len(query) > 50:
            score += 0.2
        if len(query) > 100:
            score += 0.2
        
        # 因素 2：多子问题（包含多个问号或连接词）
        if query.count('?') + query.count('？') > 1:
            score += 0.2
        if any(word in query for word in ['并且', '还有', '另外', '同时']):
            score += 0.1
        
        # 因素 3：需要推理（包含"为什么"、"怎么"、"如何"等）
        if any(word in query for word in ['为什么', '怎么', '如何', '分析', '对比']):
            score += 0.2
        
        # 因素 4：涉及多领域
        domains = ['记忆', 'Agent', '架构', 'RAG', '检索', '评估', '协议']
        domain_count = sum(1 for d in domains if d in query)
        if domain_count > 1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _process_with_react(self, query: str) -> str:
        """使用 ReAct 引擎处理复杂问题"""
        # 准备上下文
        context = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'conversation_history': self.context['conversation_history'][-5:],
            'topic_sequence': self.context['topic_sequence'][-3:],
            'observations': []
        }
        
        # 调用 ReAct 引擎
        response = self.react_engine.reason(query, context)
        
        return response
    
    def _process_simple(self, query: str) -> str:
        """处理简单问题"""
        # TODO: 实现简单回复逻辑
        # 目前返回占位符
        response = f"""
主人！囡囡收到您的问题啦～ 🎀

关于"{query}"，囡囡正在思考中...

（这是简单回复模式的占位符，后续会集成 LLM 生成实际回复）
"""
        return response
    
    def _enhance_with_rag(self, query: str) -> Optional[Dict]:
        """RAG 检索增强"""
        try:
            results = search_similar(query, top_k=3, min_similarity=0.3)
            if results:
                return {
                    'results': results,
                    'count': len(results)
                }
        except Exception as e:
            print(f"⚠️  RAG 检索失败：{e}")
        return None
    
    def _merge_rag_context(self, response: str, rag_context: Dict) -> str:
        """合并 RAG 上下文到回复"""
        # TODO: 智能合并 RAG 结果到回复
        # 目前简单追加
        if rag_context and rag_context.get('results'):
            memory_info = "\n\n📚 囡囡从记忆中找到了相关信息～"
            return response + memory_info
        return response
    
    def _update_context(self, query: str, response: str):
        """更新对话上下文"""
        # 记录对话
        self.context['conversation_history'].append({
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # 限制历史长度
        if len(self.context['conversation_history']) > 50:
            self.context['conversation_history'] = self.context['conversation_history'][-50:]
        
        # 提取话题
        topic = self._extract_topic(query)
        self.context['topic_sequence'].append({
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        })
    
    def _extract_topic(self, query: str) -> str:
        """提取话题"""
        # TODO: 实现话题提取
        # 简化实现：返回前 10 个字符
        return query[:10]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'evaluator_metrics': self.evaluator.metrics,
            'context_size': len(self.context['conversation_history'])
        }
    
    def get_evaluator_report(self) -> str:
        """获取评估报告"""
        return self.evaluator.get_report()


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("🧪 囡囡对话处理器 v2.0 测试")
    print("=" * 60)
    
    # 创建处理器
    conv = NannanConversation()
    
    # 测试查询
    test_queries = [
        "主人喜欢什么沟通风格？",  # 简单问题
        "帮我分析一下店小秘适合用什么 AI 落地方案，需要考虑哪些因素？",  # 复杂问题
        "memU 和 ruflo 有什么异同？",  # 对比问题
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'='*60}")
        print(f"测试 {i}/{len(test_queries)}")
        print(f"{'='*60}")
        
        response = conv.process(query)
        
        print(f"\n✅ 测试完成")
    
    # 输出统计
    print("\n\n" + "=" * 60)
    print("📊 统计信息:")
    print("=" * 60)
    stats = conv.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 评估报告
    print("\n" + "=" * 60)
    print("📋 评估报告:")
    print("=" * 60)
    print(conv.get_evaluator_report())
