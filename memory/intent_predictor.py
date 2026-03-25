#!/usr/bin/env python3
"""
意图预测引擎
分析主人话题历史，预测下一步需求，生成主动建议

用法：python memory/intent_predictor.py
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 配置
TOPIC_HISTORY_FILE = Path('/Users/narain/.openclaw/workspace/memory/话题历史记录.md')
TOPIC_HEAT_FILE = Path('/Users/narain/.openclaw/workspace/memory/话题热度.json')
MEMORY_INDEX_FILE = Path('/Users/narain/.openclaw/workspace/memory/记忆向量索引.json')
OUTPUT_FILE = Path('/Users/narain/.openclaw/workspace/memory/意图预测结果.json')

print("🧠 意图预测引擎")
print("=" * 50)

class PatternRecognizer:
    """模式识别器"""
    
    def __init__(self, topic_history: List[Dict]):
        self.history = topic_history
    
    def detect_learning_style(self) -> str:
        """检测学习风格"""
        # 分析话题深度变化
        depths = [h.get('depth', 'medium') for h in self.history]
        
        deep_count = depths.count('deep')
        if deep_count > len(depths) * 0.5:
            return 'deep_dive'  # 深度学习
        elif deep_count > len(depths) * 0.3:
            return 'balanced'  # 平衡学习
        else:
            return 'broad'  # 广泛学习
    
    def detect_execution_style(self) -> str:
        """检测执行风格"""
        # 分析学习→实践的转换
        theory_count = sum(1 for h in self.history if '学习' in h.get('topic', ''))
        practice_count = sum(1 for h in self.history if '实施' in h.get('topic', '') or '重构' in h.get('topic', ''))
        
        if practice_count > 0 and theory_count > 0:
            ratio = practice_count / (theory_count + practice_count)
            if ratio > 0.4:
                return 'implementation_focused'  # 实践导向
            else:
                return 'theory_focused'  # 理论导向
        return 'unknown'
    
    def detect_focus_topic(self) -> str:
        """检测当前焦点话题"""
        # 统计话题频率
        topic_counts = {}
        for h in self.history:
            topic = h.get('topic', '')
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        if topic_counts:
            return max(topic_counts, key=topic_counts.get)
        return 'unknown'
    
    def detect_session_duration(self) -> int:
        """检测会话时长（分钟）"""
        if not self.history:
            return 0
        
        # 简单估算：每个话题约 10-15 分钟
        return len(self.history) * 12
    
    def get_patterns(self) -> Dict[str, Any]:
        """获取所有识别的模式"""
        return {
            'learning_style': self.detect_learning_style(),
            'execution_style': self.detect_execution_style(),
            'focus_topic': self.detect_focus_topic(),
            'session_duration': self.detect_session_duration(),
            'topic_count': len(self.history)
        }


class IntentPredictor:
    """意图预测器"""
    
    def __init__(self, patterns: Dict[str, Any]):
        self.patterns = patterns
    
    def predict(self) -> List[Dict[str, Any]]:
        """生成意图预测"""
        predictions = []
        
        # 预测 1：实践导向 → 需要下一步指导
        if self.patterns['execution_style'] == 'implementation_focused':
            predictions.append({
                'type': 'next_step_guidance',
                'confidence': 0.85,
                'reason': '主人是实践导向，完成一个任务后通常需要下一步指导',
                'suggestion_type': 'guidance'
            })
        
        # 预测 2：深度学习 → 需要详细信息
        if self.patterns['learning_style'] == 'deep_dive':
            predictions.append({
                'type': 'detailed_explanation',
                'confidence': 0.80,
                'reason': '主人偏好深度学习，需要详细的技术细节',
                'suggestion_type': 'detail'
            })
        
        # 预测 3：会话时长 >2 小时 → 可能需要休息
        if self.patterns['session_duration'] > 120:
            predictions.append({
                'type': 'rest_reminder',
                'confidence': 0.75,
                'reason': f'主人已学习{self.patterns["session_duration"]}分钟，可能需要休息',
                'suggestion_type': 'rest'
            })
        
        # 预测 4：多话题学习 → 可能需要总结
        if self.patterns['topic_count'] > 5:
            predictions.append({
                'type': 'summary_request',
                'confidence': 0.70,
                'reason': '主人学习了多个话题，可能需要总结回顾',
                'suggestion_type': 'summary'
            })
        
        # 预测 5：焦点话题明确 → 可能需要深入资源
        if self.patterns['focus_topic'] != 'unknown':
            predictions.append({
                'type': 'resource_recommendation',
                'confidence': 0.65,
                'reason': f'主人聚焦于"{self.patterns["focus_topic"]}"，可能需要相关资源',
                'suggestion_type': 'resource',
                'topic': self.patterns['focus_topic']
            })
        
        return predictions


class SuggestionGenerator:
    """建议生成器"""
    
    def __init__(self, predictions: List[Dict], patterns: Dict):
        self.predictions = predictions
        self.patterns = patterns
    
    def generate(self) -> List[Dict[str, Any]]:
        """生成主动建议"""
        suggestions = []
        
        for pred in self.predictions:
            if pred['type'] == 'next_step_guidance':
                suggestions.append({
                    'emoji': '🎯',
                    'priority': 'high',
                    'text': f'主人！囡囡已准备好下一步实施指导～\n'
                           f'Phase 1 还剩意图预测引擎本身，需要继续吗？',
                    'actions': ['继续', '查看计划', '暂停']
                })
            
            elif pred['type'] == 'detailed_explanation':
                suggestions.append({
                    'emoji': '📚',
                    'priority': 'medium',
                    'text': f'囡囡准备了详细的技术文档和实现细节，\n'
                           f'主人需要深入了解哪个部分？',
                    'actions': ['RAG 集成', '向量化原理', '成本优化']
                })
            
            elif pred['type'] == 'rest_reminder':
                suggestions.append({
                    'emoji': '☕',
                    'priority': 'high',
                    'text': f'主人已专注学习{self.patterns["session_duration"]}分钟啦～\n'
                           f'囡囡建议休息一下，或者用轻松的方式总结今日所学？',
                    'actions': ['休息', '总结', '继续']
                })
            
            elif pred['type'] == 'summary_request':
                suggestions.append({
                    'emoji': '📊',
                    'priority': 'medium',
                    'text': f'主人今天学习了{self.patterns["topic_count"]}个话题，\n'
                           f'囡囡整理了学习路径和成果总结，需要查看吗？',
                    'actions': ['查看总结', '跳过']
                })
            
            elif pred['type'] == 'resource_recommendation':
                topic = pred.get('topic', '当前话题')
                suggestions.append({
                    'emoji': '💡',
                    'priority': 'low',
                    'text': f'囡囡发现了一些关于"{topic}"的优质资源，\n'
                           f'需要推荐吗？',
                    'actions': ['查看', '稍后']
                })
        
        # 按优先级排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return suggestions


def parse_topic_history() -> List[Dict]:
    """解析话题历史记录"""
    # 简化：从话题热度 JSON 读取
    if not TOPIC_HEAT_FILE.exists():
        print("⚠️  话题热度文件不存在")
        return []
    
    with open(TOPIC_HEAT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换为历史记录格式
    history = []
    topics = data.get('topics', {})
    for topic, info in topics.items():
        history.append({
            'topic': topic,
            'count': info.get('count', 1),
            'last_mentioned': info.get('last_mentioned', ''),
            'trend': info.get('trend', 'stable')
        })
    
    return history


def main():
    """主函数"""
    # 1. 解析话题历史
    print("📥 读取话题历史...")
    history = parse_topic_history()
    
    if not history:
        print("⚠️  无话题历史数据，使用模拟数据")
        history = [
            {'topic': '记忆系统重构', 'depth': 'deep'},
            {'topic': 'memU 学习', 'depth': 'deep'},
            {'topic': 'ruflo 学习', 'depth': 'medium'},
            {'topic': 'RAG 检索', 'depth': 'deep'},
            {'topic': '版本控制', 'depth': 'medium'},
            {'topic': '心跳记忆同步', 'depth': 'medium'},
        ]
    
    print(f"✅ 读取 {len(history)} 个话题")
    
    # 2. 识别模式
    print("🔍 识别模式...")
    recognizer = PatternRecognizer(history)
    patterns = recognizer.get_patterns()
    
    print(f"   学习风格：{patterns['learning_style']}")
    print(f"   执行风格：{patterns['execution_style']}")
    print(f"   焦点话题：{patterns['focus_topic']}")
    print(f"   会话时长：~{patterns['session_duration']}分钟")
    print()
    
    # 3. 预测意图
    print("🎯 预测意图...")
    predictor = IntentPredictor(patterns)
    predictions = predictor.predict()
    
    print(f"✅ 生成 {len(predictions)} 个预测")
    for pred in predictions:
        print(f"   - {pred['type']} (置信度：{pred['confidence']:.2f})")
    print()
    
    # 4. 生成建议
    print("💡 生成建议...")
    generator = SuggestionGenerator(predictions, patterns)
    suggestions = generator.generate()
    
    print(f"✅ 生成 {len(suggestions)} 个建议")
    for sug in suggestions:
        print(f"   {sug['emoji']} [{sug['priority']}] {sug['text'][:50]}...")
    print()
    
    # 5. 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'patterns': patterns,
        'predictions': predictions,
        'suggestions': suggestions
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"📄 结果已保存到：{OUTPUT_FILE}")
    print()
    
    # 6. 输出最佳建议
    if suggestions:
        print("=" * 50)
        print("🎁 最佳建议:")
        best = suggestions[0]
        print(f"{best['emoji']} {best['text']}")
        print(f"可操作：{', '.join(best['actions'])}")
        print("=" * 50)
    
    return output


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
