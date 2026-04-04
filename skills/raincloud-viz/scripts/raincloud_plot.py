#!/usr/bin/env python3
"""
Raincloud Plot — 数据分布可视化工具

替代传统 Dynamite Plot（柱状图 + 误差线），诚实展示数据分布。
三合一结构：半小提琴图 + 箱线图 + 抖动散点

参考：Allen et al. (2019) "Raincloud plots: a multi-platform tool for robust data visualization"
Wellcome Open Research, 4:63. DOI: 10.12688/wellcomeopenres.15191.1

作者：年年 AI 助理 - 月影（数据可视化 CVO）
版本：1.0.0
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np

# 可选依赖导入
try:
    import plotly.graph_objects as go
    from plotly.offline import plot as plotly_plot
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class RaincloudPlot:
    """
    Raincloud Plot 可视化工具类
    
    提供三种后端引擎（Plotly/Seaborn/Matplotlib）实现雨云图，
    用于诚实、全面地展示数据分布特征。
    
    Attributes:
        data (list): 数据列表，每个元素是一个数组
        group_names (list): 组名列表
        title (str): 图表标题
        backend (str): 后端引擎 ('plotly' | 'seaborn' | 'matplotlib')
        colors (list): 颜色列表
        show_boxplot (bool): 是否显示箱线图
        show_violin (bool): 是否显示小提琴图
        show_points (bool): 是否显示散点
        
    Example:
        >>> import numpy as np
        >>> data = [np.random.normal(5, 1, 100), np.random.normal(7, 1.5, 100)]
        >>> names = ['Group A', 'Group B']
        >>> plot = RaincloudPlot(data, names, title='对比分析')
        >>> plot.show()
        >>> plot.save('output.html')
    """
    
    def __init__(
        self,
        data: List[np.ndarray],
        group_names: List[str],
        title: str = "Raincloud Plot",
        backend: str = "plotly",
        colors: Optional[List[str]] = None,
        show_boxplot: bool = True,
        show_violin: bool = True,
        show_points: bool = True,
        point_alpha: float = 0.6,
        violin_alpha: float = 0.5,
        jitter_width: float = 0.3,
        figsize: Tuple[int, int] = (10, 6)
    ):
        """
        初始化 Raincloud Plot
        
        Args:
            data: 数据列表，每个元素是一个数组（组数据）
            group_names: 组名列表
            title: 图表标题，默认 "Raincloud Plot"
            backend: 后端引擎，可选 'plotly' | 'seaborn' | 'matplotlib'
            colors: 颜色列表，默认使用内置配色
            show_boxplot: 是否显示箱线图，默认 True
            show_violin: 是否显示小提琴图，默认 True
            show_points: 是否显示散点，默认 True
            point_alpha: 散点透明度，默认 0.6
            violin_alpha: 小提琴图透明度，默认 0.5
            jitter_width: 散点抖动宽度，默认 0.3
            figsize: 图表大小 (宽，高)，默认 (10, 6)
            
        Raises:
            ValueError: 当 data 和 group_names 长度不一致时
            ImportError: 当指定的后端依赖未安装时
        """
        if len(data) != len(group_names):
            raise ValueError(
                f"data 长度 ({len(data)}) 必须等于 group_names 长度 ({len(group_names)})"
            )
        
        self.data = data
        self.group_names = group_names
        self.title = title
        self.backend = backend.lower()
        self.figsize = figsize
        
        # 可视化选项
        self.show_boxplot = show_boxplot
        self.show_violin = show_violin
        self.show_points = show_points
        self.point_alpha = point_alpha
        self.violin_alpha = violin_alpha
        self.jitter_width = jitter_width
        
        # 默认配色（Plotly 默认色板）
        self.colors = colors or [
            '#636EFA', '#EF553B', '#00CC96', '#AB63FA',
            '#FFA15A', '#19D3F3', '#FF6692', '#B6E880'
        ]
        
        # 验证后端依赖
        self._validate_backend()
        
        # 图表对象
        self._fig = None
    
    def _validate_backend(self) -> None:
        """验证后端依赖是否已安装"""
        if self.backend == 'plotly' and not PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly 未安装。请运行：pip install plotly"
            )
        elif self.backend in ['seaborn', 'matplotlib'] and not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Seaborn/Matplotlib 未安装。请运行：pip install seaborn matplotlib"
            )
        elif self.backend not in ['plotly', 'seaborn', 'matplotlib']:
            raise ValueError(
                f"不支持的后端：{self.backend}。可选：plotly, seaborn, matplotlib"
            )
    
    def _create_plotly(self) -> go.Figure:
        """
        创建 Plotly 后端图表
        
        Returns:
            plotly.graph_objects.Figure: Plotly 图表对象
        """
        fig = go.Figure()
        
        for i, (group_data, group_name) in enumerate(zip(self.data, self.group_names)):
            offset = i * 2.0  # 组间距
            color = self.colors[i % len(self.colors)]
            
            # 1. 半小提琴图（上方，只画右侧）
            if self.show_violin:
                fig.add_trace(go.Violin(
                    y=group_data,
                    x=[offset] * len(group_data),
                    side='positive',  # 只画右侧
                    orientation='v',
                    width=1.2,
                    line_color=color,
                    fillcolor=color,
                    opacity=self.violin_alpha,
                    meanline_visible=True,
                    showlegend=False,
                    name=group_name,
                    box_visible=False,
                    points=False
                ))
            
            # 2. 箱线图（中间）
            if self.show_boxplot:
                fig.add_trace(go.Box(
                    y=group_data,
                    x=[offset] * len(group_data),
                    orientation='v',
                    line_color=color,
                    showlegend=False,
                    name=group_name,
                    boxpoints=False,  # 不显示异常点（散点图会显示）
                    opacity=0.8
                ))
            
            # 3. 抖动散点（下方）
            if self.show_points:
                jitter = np.random.uniform(
                    -self.jitter_width, 
                    self.jitter_width, 
                    len(group_data)
                )
                fig.add_trace(go.Scatter(
                    x=[offset + j for j in jitter],
                    y=group_data,
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=color,
                        opacity=self.point_alpha,
                        line=dict(width=0.5, color='white')
                    ),
                    showlegend=False,
                    name=group_name
                ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=self.title,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis=dict(
                tickvals=[i * 2.0 for i in range(len(self.group_names))],
                ticktext=self.group_names,
                title="组别",
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="数值",
                gridcolor='lightgray'
            ),
            violinmode='overlay',
            showlegend=False,
            plot_bgcolor='white',
            height=self.figsize[1] * 80,
            width=self.figsize[0] * 80
        )
        
        return fig
    
    def _create_seaborn(self) -> plt.Figure:
        """
        创建 Seaborn 后端图表
        
        Returns:
            matplotlib.figure.Figure: Matplotlib 图表对象
        """
        # 准备长格式数据
        import pandas as pd
        
        long_data = []
        for group_name, group_values in zip(self.group_names, self.data):
            for value in group_values:
                long_data.append({
                    'group': group_name,
                    'value': value
                })
        
        df = pd.DataFrame(long_data)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 绘制雨云图（使用 Raincloud 风格）
        # 1. 小提琴图
        if self.show_violin:
            sns.violinplot(
                data=df,
                x='group',
                y='value',
                ax=ax,
                inner=None,  # 不显示内部统计
                alpha=self.violin_alpha,
                palette=self.colors[:len(self.group_names)],
                linewidth=1.5
            )
        
        # 2. 箱线图（窄箱）
        if self.show_boxplot:
            sns.boxplot(
                data=df,
                x='group',
                y='value',
                ax=ax,
                width=0.15,  # 窄箱
                showfliers=False,  # 不显示异常点
                boxprops={'alpha': 0.8, 'zorder': 3},
                whiskerprops={'zorder': 3},
                medianprops={'color': 'white', 'linewidth': 2, 'zorder': 4}
            )
        
        # 3. 散点图（带抖动）
        if self.show_points:
            sns.stripplot(
                data=df,
                x='group',
                y='value',
                ax=ax,
                size=5,
                alpha=self.point_alpha,
                palette=self.colors[:len(self.group_names)],
                edgecolor='white',
                linewidth=0.5,
                jitter=self.jitter_width
            )
        
        ax.set_title(self.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('组别', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        
        return fig
    
    def _create_matplotlib(self) -> plt.Figure:
        """
        创建纯 Matplotlib 后端图表（不依赖 Seaborn）
        
        Returns:
            matplotlib.figure.Figure: Matplotlib 图表对象
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        for i, (group_data, group_name) in enumerate(zip(self.data, self.group_names)):
            offset = i * 2.0
            color = self.colors[i % len(self.colors)]
            
            # 1. 小提琴图（使用核密度估计）
            if self.show_violin:
                from scipy.stats import gaussian_kde
                
                # 计算核密度估计
                kde = gaussian_kde(group_data)
                y_range = np.linspace(min(group_data), max(group_data), 100)
                density = kde(y_range)
                
                # 只画右侧（归一化到组位置）
                violin_width = density / max(density) * 0.8
                ax.fill_betweenx(
                    y_range,
                    offset,
                    offset + violin_width,
                    color=color,
                    alpha=self.violin_alpha
                )
            
            # 2. 箱线图
            if self.show_boxplot:
                box_props = dict(
                    boxes=dict(color=color, linewidth=2),
                    whiskers=dict(color=color, linewidth=2),
                    medians=dict(color='white', linewidth=2),
                    caps=dict(color=color, linewidth=2)
                )
                ax.boxplot(
                    group_data,
                    positions=[offset],
                    widths=0.6,
                    patch_artist=True,
                    boxprops=dict(facecolor=color, alpha=0.3),
                    showfliers=False
                )
            
            # 3. 散点图
            if self.show_points:
                jitter = np.random.uniform(
                    -self.jitter_width,
                    self.jitter_width,
                    len(group_data)
                )
                ax.scatter(
                    offset + jitter,
                    group_data,
                    s=30,
                    c=color,
                    alpha=self.point_alpha,
                    edgecolors='white',
                    linewidths=0.5
                )
        
        # 设置
        ax.set_xticks([i * 2.0 for i in range(len(self.group_names))])
        ax.set_xticklabels(self.group_names)
        ax.set_title(self.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('组别', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        
        return fig
    
    def show(self) -> None:
        """
        显示图表
        
        根据后端不同：
        - Plotly: 在浏览器中打开交互式图表
        - Seaborn/Matplotlib: 显示静态图表窗口
        """
        if self.backend == 'plotly':
            self._fig = self._create_plotly()
            self._fig.show()
        elif self.backend == 'seaborn':
            self._fig = self._create_seaborn()
            plt.show()
        elif self.backend == 'matplotlib':
            self._fig = self._create_matplotlib()
            plt.show()
    
    def save(self, path: str) -> None:
        """
        保存图表到文件
        
        Args:
            path: 输出文件路径（根据扩展名自动选择格式）
                  - .html: Plotly 交互式图表
                  - .png/.jpg/.pdf: 静态图片（Matplotlib）
                  
        Example:
            >>> plot.save('output.html')  # Plotly 交互式
            >>> plot.save('output.png')   # PNG 图片
            >>> plot.save('output.pdf')   # PDF 矢量图
        """
        path = Path(path)
        
        if self.backend == 'plotly':
            self._fig = self._create_plotly()
            if path.suffix.lower() == '.html':
                plotly_plot(self._fig, filename=str(path), auto_open=False)
            else:
                # 转换为静态图片需要 kaleido
                try:
                    self._fig.write_image(str(path))
                except ImportError:
                    raise ImportError(
                        "保存为图片需要安装 kaleido: pip install kaleido"
                    )
        else:
            # Seaborn/Matplotlib
            self._fig = self._create_seaborn() if self.backend == 'seaborn' else self._create_matplotlib()
            self._fig.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close(self._fig)
    
    def get_figure(self):
        """
        获取底层图表对象
        
        Returns:
            Figure 对象（Plotly Figure 或 Matplotlib Figure）
        """
        if self._fig is None:
            if self.backend == 'plotly':
                self._fig = self._create_plotly()
            elif self.backend == 'seaborn':
                self._fig = self._create_seaborn()
            else:
                self._fig = self._create_matplotlib()
        return self._fig


def create_demo_data() -> Tuple[List[np.ndarray], List[str]]:
    """
    创建示例数据
    
    Returns:
        tuple: (数据列表，组名列表)
    """
    np.random.seed(42)
    
    # 模拟四组实验数据（不同分布）
    group_a = np.random.normal(5, 1.0, 100)  # 正态分布
    group_b = np.random.normal(6.5, 1.2, 100)  # 均值更高
    group_c = np.random.lognormal(1.5, 0.5, 100)  # 偏态分布
    group_d = np.concatenate([  # 双峰分布
        np.random.normal(4, 0.5, 50),
        np.random.normal(7, 0.5, 50)
    ])
    
    data = [group_a, group_b, group_c, group_d]
    names = ['正态分布', '高均值', '偏态分布', '双峰分布']
    
    return data, names


def parse_data_string(data_str: str) -> Tuple[List[np.ndarray], List[str]]:
    """
    解析命令行数据字符串
    
    Args:
        data_str: 格式 "组名 1: 数据 1,数据 2;组名 2: 数据 3,数据 4"
        
    Returns:
        tuple: (数据列表，组名列表)
        
    Example:
        >>> parse_data_string("A:1,2,3;B:4,5,6")
        ([array([1, 2, 3]), array([4, 5, 6])], ['A', 'B'])
    """
    groups = data_str.split(';')
    data = []
    names = []
    
    for group in groups:
        if ':' not in group:
            raise ValueError(f"无效的数据格式：{group}（缺少冒号分隔符）")
        
        name, values_str = group.split(':', 1)
        values = [float(v.strip()) for v in values_str.split(',')]
        
        names.append(name.strip())
        data.append(np.array(values))
    
    return data, names


def main():
    """CLI 主函数"""
    parser = argparse.ArgumentParser(
        description='Raincloud Plot - 数据分布可视化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --demo                              # 运行内置示例
  %(prog)s --data "A:1,2,3;B:4,5,6"           # 自定义数据
  %(prog)s --csv data.csv --value score       # 从 CSV 读取
  %(prog)s --demo --backend seaborn           # 使用 Seaborn 后端
        """
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行内置示例'
    )
    
    parser.add_argument(
        '--data',
        type=str,
        help='自定义数据，格式："组名 1: 数据 1,数据 2;组名 2: 数据 3,数据 4"'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        help='CSV 文件路径'
    )
    
    parser.add_argument(
        '--value-column',
        type=str,
        default='value',
        help='CSV 中数值列名（默认：value）'
    )
    
    parser.add_argument(
        '--group-column',
        type=str,
        default='group',
        help='CSV 中分组列名（默认：group）'
    )
    
    parser.add_argument(
        '--backend',
        type=str,
        choices=['plotly', 'seaborn', 'matplotlib'],
        default='plotly',
        help='后端引擎（默认：plotly）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default='Raincloud Plot',
        help='图表标题（默认：Raincloud Plot）'
    )
    
    parser.add_argument(
        '--figsize',
        type=str,
        default='10x6',
        help='图表大小：宽 x 高（默认：10x6）'
    )
    
    parser.add_argument(
        '--no-boxplot',
        action='store_true',
        help='不显示箱线图'
    )
    
    parser.add_argument(
        '--no-violin',
        action='store_true',
        help='不显示小提琴图'
    )
    
    parser.add_argument(
        '--no-points',
        action='store_true',
        help='不显示散点'
    )
    
    args = parser.parse_args()
    
    # 解析 figsize
    try:
        width, height = map(int, args.figsize.split('x'))
        figsize = (width, height)
    except ValueError:
        print("错误：figsize 格式应为 '宽 x 高'，例如 '10x6'")
        sys.exit(1)
    
    # 加载数据
    if args.demo:
        print("✓ 使用内置示例数据")
        data, names = create_demo_data()
    elif args.data:
        print("✓ 解析自定义数据")
        try:
            data, names = parse_data_string(args.data)
        except ValueError as e:
            print(f"错误：{e}")
            sys.exit(1)
    elif args.csv:
        print(f"✓ 从 CSV 读取：{args.csv}")
        try:
            import pandas as pd
            df = pd.read_csv(args.csv)
            
            # 按组分割数据
            groups = df.groupby(args.group_column)
            data = [group[args.value_column].values for _, group in groups]
            names = list(groups.groups.keys())
            
            if not data:
                print(f"错误：CSV 中没有找到分组列 '{args.group_column}'")
                sys.exit(1)
        except ImportError:
            print("错误：读取 CSV 需要 pandas：pip install pandas")
            sys.exit(1)
        except FileNotFoundError:
            print(f"错误：CSV 文件不存在：{args.csv}")
            sys.exit(1)
    else:
        print("错误：请指定 --demo、--data 或 --csv")
        parser.print_help()
        sys.exit(1)
    
    # 创建图表
    print(f"✓ 创建 Raincloud Plot（后端：{args.backend}）")
    
    try:
        plot = RaincloudPlot(
            data=data,
            group_names=names,
            title=args.title,
            backend=args.backend,
            figsize=figsize,
            show_boxplot=not args.no_boxplot,
            show_violin=not args.no_violin,
            show_points=not args.no_points
        )
    except ImportError as e:
        print(f"错误：{e}")
        sys.exit(1)
    
    # 输出
    if args.output:
        print(f"✓ 保存到：{args.output}")
        try:
            plot.save(args.output)
            print(f"✅ 完成！图表已保存到 {args.output}")
        except Exception as e:
            print(f"错误：保存失败 - {e}")
            sys.exit(1)
    else:
        print("✓ 显示图表（关闭窗口退出）")
        plot.show()


if __name__ == '__main__':
    main()
