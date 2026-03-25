#!/usr/bin/env python3
"""
囡囡质量评估器
基于 hello-agents Ch12 性能评估理论

用法：
    from nannan_evaluator import NannanEvaluator
    evaluator = NannanEvaluator()
    evaluator.evaluate(query, response, start_time, end_time)
    print(evaluator.get_report())
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

class NannanEvaluator:
    """囡囡质量评估器 - 5 维度 KPI"""
    
    # 目标指标
    TARGETS = {
        'task_completion_rate': 0.90,  # 任务完成率 >90%
        'response_time': 2.0,  # 响应时间 <2s
        'memory_accuracy': 0.85,  # 记忆准确率 >85%
        'prediction_accuracy': 0.70,  # 预测准确率 >70%
        'cost_savings': 0.60,  # 成本节省 >60%
    }
    
    def __init__(self, history_file: str = None):
        self.metrics = {
            'task_completion_rate': 0.0,
            'response_time': 0.0,
            'memory_accuracy': 0.0,
            'prediction_accuracy': 0.0,
            'cost_savings': 0.0,
        }
        self.history = []
        self.history_file = Path(history_file) if history_file else None
        self.load_history()
    
    def evaluate(self, query: str, response: str, start_time: datetime, 
                 end_time: datetime, memory_used: bool = False, 
                 prediction_correct: bool = False) -> Dict:
        """
        单次评估
        
        Args:
            query: 主人问题
            response: 囡囡回复
            start_time: 开始时间
            end_time: 结束时间
            memory_used: 是否使用了记忆检索
            prediction_correct: 意图预测是否正确
        """
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response[:200],  # 只存前 200 字符
            'response_time': (end_time - start_time).total_seconds(),
            'task_completed': self._check_task_completion(response),
            'memory_used': memory_used,
            'prediction_correct': prediction_correct,
        }
        
        self.history.append(evaluation)
        self.update_metrics()
        self.save_history()
        
        return evaluation
    
    def _check_task_completion(self, response: str) -> bool:
        """检查任务是否完成"""
        # 简化实现：检查回复是否包含有效内容
        if len(response) < 10:
            return False
        if '不知道' in response or '无法' in response:
            return False
        return True
    
    def update_metrics(self, window: int = 100):
        """
        更新指标（最近 window 次）
        
        Args:
            window: 评估窗口大小
        """
        recent = self.history[-window:]
        if not recent:
            return
        
        # 任务完成率
        completed = sum(1 for h in recent if h['task_completed'])
        self.metrics['task_completion_rate'] = completed / len(recent)
        
        # 平均响应时间
        self.metrics['response_time'] = sum(h['response_time'] for h in recent) / len(recent)
        
        # 记忆准确率（使用了记忆的占比）
        memory_used = sum(1 for h in recent if h['memory_used'])
        self.metrics['memory_accuracy'] = memory_used / len(recent)
        
        # 意图预测准确率
        prediction_correct = sum(1 for h in recent if h['prediction_correct'])
        self.metrics['prediction_accuracy'] = prediction_correct / len(recent)
        
        # 成本节省（估算：RAG 检索占比）
        rag_used = sum(1 for h in recent if h['memory_used'])
        self.metrics['cost_savings'] = rag_used / len(recent)
    
    def get_report(self) -> str:
        """生成评估报告"""
        report = f"""
📊 囡囡质量评估报告
━━━━━━━━━━━━━━━━━━━━
"""
        # 各项指标
        indicators = []
        for key, value in self.metrics.items():
            target = self.TARGETS.get(key, 0)
            status = '✅' if value >= target else '⚠️'
            
            # 格式化
            if key == 'response_time':
                value_str = f"{value:.2f}s"
                target_str = f"<{target}s"
            else:
                value_str = f"{value:.1%}"
                target_str = f">{target:.0%}"
            
            # 指标名称
            names = {
                'task_completion_rate': '任务完成率',
                'response_time': '响应时间',
                'memory_accuracy': '记忆准确率',
                'prediction_accuracy': '预测准确率',
                'cost_savings': '成本节省',
            }
            name = names.get(key, key)
            
            indicators.append(f"{status} {name}: {value_str} (目标：{target_str})")
        
        report += '\n'.join(indicators)
        report += f"""

━━━━━━━━━━━━━━━━━━━━
评估次数：{len(self.history)}
最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
"""
        return report
    
    def save_history(self):
        """保存历史"""
        if self.history_file:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """加载历史"""
        if self.history_file and self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
            self.update_metrics()
    
    def get_trend(self, days: int = 7) -> Dict[str, str]:
        """获取趋势分析"""
        if len(self.history) < 10:
            return {'trend': 'insufficient_data'}
        
        # 比较前后两半
        half = len(self.history) // 2
        first_half = self.history[:half]
        second_half = self.history[half:]
        
        # 计算趋势
        trends = {}
        for key in self.metrics.keys():
            first_avg = sum(h.get(key.replace('_rate', '').replace('_accuracy', '').replace('_savings', '') 
                                  .replace('task_completion', 'task_completed')
                                  .replace('response', 'response_time')
                                  .replace('memory', 'memory_used')
                                  .replace('prediction', 'prediction_correct'), 0) 
                          for h in first_half) / len(first_half)
            second_avg = sum(h.get(key.replace('_rate', '').replace('_accuracy', '').replace('_savings', '')
                                   .replace('task_completion', 'task_completed')
                                   .replace('response', 'response_time')
                                   .replace('memory', 'memory_used')
                                   .replace('prediction', 'prediction_correct'), 0) 
                           for h in second_half) / len(second_half)
            
            if second_avg > first_avg:
                trends[key] = '📈 上升'
            elif second_avg < first_avg:
                trends[key] = '📉 下降'
            else:
                trends[key] = '➡️ 稳定'
        
        return trends


# 测试
if __name__ == '__main__':
    evaluator = NannanEvaluator()
    
    # 模拟评估数据
    import random
    for i in range(50):
        start = datetime.now()
        end = start + timedelta(seconds=random.uniform(0.5, 3.0))
        
        evaluator.evaluate(
            query=f"测试问题{i}",
            response="这是测试回复" * 10,
            start_time=start,
            end_time=end,
            memory_used=random.random() > 0.3,
            prediction_correct=random.random() > 0.4
        )
    
    # 生成报告
    print(evaluator.get_report())
    
    # 趋势分析
    print("\n📈 趋势分析:")
    trends = evaluator.get_trend()
    for key, trend in trends.items():
        print(f"  {key}: {trend}")
