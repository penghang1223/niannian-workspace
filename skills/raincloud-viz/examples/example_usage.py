#!/usr/bin/env python3
"""
Raincloud Plot 使用示例

本文件展示如何使用 raincloud_plot 模块创建各种雨云图。
运行此文件将生成多个示例图表。

参考：Allen et al. (2019) "Raincloud plots: a multi-platform tool for robust data visualization"
"""

import numpy as np
from pathlib import Path

# 导入本地模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from raincloud_plot import RaincloudPlot, create_demo_data


def example_basic():
    """示例 1：基础用法 - 两组对比"""
    print("\n📊 示例 1：基础用法 - 两组对比")
    
    np.random.seed(42)
    control = np.random.normal(5, 1.0, 80)
    treatment = np.random.normal(6.5, 1.2, 80)
    
    plot = RaincloudPlot(
        data=[control, treatment],
        group_names=['Control', 'Treatment'],
        title='A/B 测试对比',
        backend='plotly'
    )
    
    output = Path(__file__).parent / 'example_basic.html'
    plot.save(str(output))
    print(f"   ✓ 已保存：{output}")


def example_multigroup():
    """示例 2：多组对比（4 组）"""
    print("\n📊 示例 2：多组对比（4 组）")
    
    np.random.seed(123)
    groups = [
        np.random.normal(5, 1.0, 60),   # 组 A
        np.random.normal(6, 1.2, 60),   # 组 B
        np.random.normal(5.5, 1.5, 60), # 组 C
        np.random.normal(7, 0.8, 60)    # 组 D
    ]
    names = ['Condition A', 'Condition B', 'Condition C', 'Condition D']
    
    plot = RaincloudPlot(
        data=groups,
        group_names=names,
        title='四组实验条件对比',
        backend='plotly',
        colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    )
    
    output = Path(__file__).parent / 'example_multigroup.html'
    plot.save(str(output))
    print(f"   ✓ 已保存：{output}")


def example_distribution_types():
    """示例 3：不同分布类型对比"""
    print("\n📊 示例 3：不同分布类型对比")
    
    np.random.seed(456)
    
    # 正态分布
    normal = np.random.normal(5, 1.0, 100)
    
    # 偏态分布（对数正态）
    skewed = np.random.lognormal(1.5, 0.5, 100)
    
    # 双峰分布
    bimodal = np.concatenate([
        np.random.normal(3, 0.5, 50),
        np.random.normal(7, 0.5, 50)
    ])
    
    # 均匀分布
    uniform = np.random.uniform(2, 8, 100)
    
    plot = RaincloudPlot(
        data=[normal, skewed, bimodal, uniform],
        group_names=['正态分布', '偏态分布', '双峰分布', '均匀分布'],
        title='不同分布类型对比',
        backend='plotly',
        title='分布类型对比：展示 Raincloud Plot 揭示数据特征的能力'
    )
    
    output = Path(__file__).parent / 'example_distributions.html'
    plot.save(str(output))
    print(f"   ✓ 已保存：{output}")


def example_seaborn():
    """示例 4：Seaborn 后端（静态图）"""
    print("\n📊 示例 4：Seaborn 后端（静态图）")
    
    data, names = create_demo_data()
    
    plot = RaincloudPlot(
        data=data,
        group_names=names,
        title='Seaborn 后端示例',
        backend='seaborn',
        figsize=(12, 7)
    )
    
    output = Path(__file__).parent / 'example_seaborn.png'
    plot.save(str(output))
    print(f"   ✓ 已保存：{output}")


def example_customization():
    """示例 5：自定义选项"""
    print("\n📊 示例 5：自定义选项（只显示部分组件）")
    
    np.random.seed(789)
    group_a = np.random.normal(5, 1.0, 50)
    group_b = np.random.normal(6, 1.2, 50)
    
    # 只显示小提琴 + 散点（无箱线图）
    plot1 = RaincloudPlot(
        data=[group_a, group_b],
        group_names=['A', 'B'],
        title='无箱线图',
        backend='plotly',
        show_boxplot=False
    )
    output1 = Path(__file__).parent / 'example_no_box.html'
    plot1.save(str(output1))
    print(f"   ✓ 已保存：{output1}")
    
    # 只显示散点（无小提琴和箱线图）
    plot2 = RaincloudPlot(
        data=[group_a, group_b],
        group_names=['A', 'B'],
        title='仅散点',
        backend='plotly',
        show_violin=False,
        show_boxplot=False
    )
    output2 = Path(__file__).parent / 'example_points_only.html'
    plot2.save(str(output2))
    print(f"   ✓ 已保存：{output2}")


def example_from_csv():
    """示例 6：从 CSV 文件读取数据"""
    print("\n📊 示例 6：从 CSV 文件读取数据")
    
    try:
        import pandas as pd
        
        csv_path = Path(__file__).parent / 'demo_data.csv'
        if not csv_path.exists():
            print(f"   ⚠️  CSV 文件不存在：{csv_path}")
            return
        
        df = pd.read_csv(csv_path)
        
        # 按组分割数据
        groups = df.groupby('group')
        data = [group['value'].values for _, group in groups]
        names = list(groups.groups.keys())
        
        plot = RaincloudPlot(
            data=data,
            group_names=names,
            title='从 CSV 读取数据',
            backend='plotly'
        )
        
        output = Path(__file__).parent / 'example_from_csv.html'
        plot.save(str(output))
        print(f"   ✓ 已保存：{output}")
        
    except ImportError:
        print("   ⚠️  需要 pandas：pip install pandas")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("🌧️  Raincloud Plot 示例集")
    print("=" * 60)
    
    examples = [
        example_basic,
        example_multigroup,
        example_distribution_types,
        example_seaborn,
        example_customization,
        example_from_csv
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"   ❌ 错误：{e}")
    
    print("\n" + "=" * 60)
    print("✅ 所有示例已完成！")
    print("=" * 60)
    print("\n生成的文件：")
    print("  - example_basic.html (两组对比)")
    print("  - example_multigroup.html (四组对比)")
    print("  - example_distributions.html (分布类型对比)")
    print("  - example_seaborn.png (Seaborn 静态图)")
    print("  - example_no_box.html (无箱线图)")
    print("  - example_points_only.html (仅散点)")
    print("  - example_from_csv.html (CSV 数据)")
    print("\n💡 提示：用浏览器打开 .html 文件查看交互式图表")


if __name__ == '__main__':
    main()
