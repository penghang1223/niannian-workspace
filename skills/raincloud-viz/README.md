# Raincloud Plot 可视化工具

> **诚实展示数据分布，告别 Dynamite Plot 时代**

## 📖 目录

1. [安装说明](#安装说明)
2. [快速开始](#快速开始)
3. [API 参考](#api-参考)
4. [Raincloud vs Dynamite](#raincloud-plot-vs-dynamite-plot)
5. [示例画廊](#示例画廊)
6. [参考文献](#参考文献)

---

## 安装说明

### 依赖安装

```bash
# 基础依赖（必需）
pip install numpy pandas plotly seaborn matplotlib

# 可选：Jupyter 支持
pip install jupyter notebook
```

### 验证安装

```bash
python3 -c "import plotly, seaborn, matplotlib; print('✅ 所有依赖已安装')"
```

---

## 快速开始

### 方式一：CLI 命令行

```bash
# 运行内置示例
python3 scripts/raincloud_plot.py --demo

# 自定义数据（分号分隔组，冒号分隔组名和数据）
python3 scripts/raincloud_plot.py \
  --data "Control:1.2,1.5,1.8,2.1,2.3;Treatment:2.5,2.8,3.1,3.4,3.7" \
  --backend plotly \
  --output comparison.html

# 从 CSV 文件读取
python3 scripts/raincloud_plot.py \
  --csv examples/demo_data.csv \
  --value-column score \
  --group-column group \
  --backend seaborn \
  --output seaborn_output.png
```

### 方式二：Python API

```python
from raincloud_plot import RaincloudPlot
import numpy as np

# 准备数据
np.random.seed(42)
group_a = np.random.normal(5, 1.5, 100)
group_b = np.random.normal(7, 1.2, 100)
group_c = np.random.normal(6, 2.0, 100)

# 创建图表
plot = RaincloudPlot(
    data=[group_a, group_b, group_c],
    group_names=['A', 'B', 'C'],
    title='组间对比分析',
    backend='plotly'  # 或 'seaborn' / 'matplotlib'
)

# 显示/保存
plot.show()  # 交互式显示
plot.save('output.html')  # 保存文件
```

### 方式三：Jupyter Notebook

```python
from raincloud_plot import RaincloudPlot
import numpy as np

# 生成示例数据
data = [np.random.normal(loc, 1.5, 50) for loc in [4, 5, 6, 7]]
groups = ['Group A', 'Group B', 'Group C', 'Group D']

# 创建并显示
plot = RaincloudPlot(data, groups, title='Jupyter 示例')
plot.show()
```

---

## API 参考

### RaincloudPlot 类

```python
class RaincloudPlot:
    """
    Raincloud Plot 可视化工具类
    
    参数:
        data (list): 数据列表，每个元素是一个数组（组数据）
        group_names (list): 组名列表
        title (str): 图表标题，默认 "Raincloud Plot"
        backend (str): 后端引擎，可选 'plotly' | 'seaborn' | 'matplotlib'
        colors (list): 颜色列表，默认使用内置配色
        show_boxplot (bool): 是否显示箱线图，默认 True
        show_violin (bool): 是否显示小提琴图，默认 True
        show_points (bool): 是否显示散点，默认 True
        point_alpha (float): 散点透明度，默认 0.6
        violin_alpha (float): 小提琴图透明度，默认 0.5
        jitter_width (float): 散点抖动宽度，默认 0.3
        figsize (tuple): 图表大小 (宽，高)，默认 (10, 6)
        
    方法:
        show() -> None: 显示图表
        save(path: str) -> None: 保存图表到文件
        get_figure(): 返回底层图表对象
    """
```

### CLI 参数

```bash
python3 raincloud_plot.py [选项]

选项:
  --demo                  运行内置示例
  --data TEXT             自定义数据（格式："组名 1: 数据 1,数据 2;组名 2: 数据 3,数据 4"）
  --csv PATH              CSV 文件路径
  --value-column TEXT     CSV 中数值列名
  --group-column TEXT     CSV 中分组列名
  --backend TEXT          后端引擎：plotly|seaborn|matplotlib（默认：plotly）
  --output PATH           输出文件路径
  --title TEXT            图表标题
  --figsize TEXT          图表大小：宽 x 高（默认：10x6）
  --no-boxplot           不显示箱线图
  --no-violin            不显示小提琴图
  --no-points            不显示散点
  --help                 显示帮助信息
```

---

## Raincloud Plot vs Dynamite Plot

### 什么是 Dynamite Plot？

Dynamite Plot（柱状图 + 误差线）是传统统计图表的常见形式：
- 柱子高度 = 均值
- 误差线 = 标准差/标准误/置信区间

### Dynamite Plot 的四大罪状

#### 1️⃣ 隐藏数据分布

**问题：** 完全不同的分布可以有相同的均值和标准差

```
分布 A: [1, 5, 5, 5, 9]  → 均值=5, 标准差≈2.8
分布 B: [4, 5, 5, 5, 6]  → 均值=5, 标准差≈0.7
分布 C: [1, 2, 5, 8, 9]  → 均值=5, 标准差≈3.3
```

在 Dynamite Plot 中，这三组数据看起来可能完全一样！

#### 2️⃣ 扭曲效应量

**问题：** 柱子从 0 开始，视觉夸大/缩小组间差异

- 如果数据范围是 50-55，柱子从 0 开始 → 差异看起来很小
- 如果 Y 轴截断从 45 开始 → 差异看起来很大

**Raincloud 方案：** 只显示数据实际分布范围，不强制从 0 开始

#### 3️⃣ 掩盖分布假设

**问题：** 以下分布特征在柱状图中完全不可见：

- 🔴 **双峰分布** — 可能存在两个亚群体
- 🔴 **偏态分布** — 均值可能不是最佳中心度量
- 🔴 **异方差性** — 不同组的方差不同
- 🔴 **异常值** — 极端值被隐藏

#### 4️⃣ 误导统计推断

**问题：** 读者常误读误差线

- 误差线 = SE（标准误）？CI（置信区间）？SD（标准差）？
- 重叠的误差线 ≠ 无显著差异
- 不重叠的误差线 ≠ 有显著差异

### Raincloud Plot 的优势

| 特性 | Dynamite Plot | Raincloud Plot |
|------|---------------|----------------|
| 展示原始数据 | ❌ 隐藏 | ✅ 全部散点 |
| 展示分布形状 | ❌ 无法 | ✅ 小提琴图 |
| 展示统计摘要 | ⚠️ 仅均值 | ✅ 中位数+IQR+须线 |
| 识别异常值 | ❌ 困难 | ✅ 直观可见 |
| 识别双峰/偏态 | ❌ 不可能 | ✅ 清晰可见 |
| 视觉诚实度 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### 对比图说明

```
┌─────────────────────────────────────────────────────────────┐
│                    Dynamite Plot                            │
│                                                             │
│     ┌───┐     ┌───┐                                         │
│     │   │     │   │     ← 柱子高度=均值                     │
│     │   │     │   │                                         │
│     │   │     │   │     ← 误差线=SD/SE/CI                   │
│     └───┘     └───┘                                         │
│     Group A   Group B                                       │
│                                                             │
│  ❌ 看不到数据点分布                                         │
│  ❌ 看不到是否有双峰                                         │
│  ❌ 看不到异常值                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Raincloud Plot                           │
│                                                             │
│      ╭───╮       ╭───╮      ← 半小提琴=概率密度             │
│     ╱     ╲     ╱     ╲                                     │
│    │ ┌───┐ │   │ ┌───┐ │    ← 箱线图=中位数+IQR            │
│    ● ● ● ● ●   ● ● ● ● ●    ← 散点=原始数据点               │
│    Group A     Group B                                      │
│                                                             │
│  ✅ 清晰看到分布形状                                         │
│  ✅ 每个数据点都可见                                         │
│  ✅ 统计摘要一目了然                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 示例画廊

### 示例 1：A/B 测试对比

```python
import numpy as np
from raincloud_plot import RaincloudPlot

# 模拟 A/B 测试数据
np.random.seed(42)
control = np.random.lognormal(1.5, 0.5, 200)  # 对照组（偏态分布）
treatment = np.random.lognormal(1.7, 0.4, 200)  # 实验组

plot = RaincloudPlot(
    data=[control, treatment],
    group_names=['Control', 'Treatment'],
    title='A/B 测试：用户停留时长对比',
    backend='plotly'
)
plot.save('ab_test.html')
```

### 示例 2：多组对比（4 组）

```python
# 四组实验条件
groups = [
    np.random.normal(5, 1.0, 80),
    np.random.normal(6, 1.2, 80),
    np.random.normal(5.5, 1.5, 80),
    np.random.normal(7, 0.8, 80)
]
names = ['Condition A', 'Condition B', 'Condition C', 'Condition D']

plot = RaincloudPlot(groups, names, title='四组实验条件对比')
plot.show()
```

### 示例 3：从 CSV 读取数据

```python
import pandas as pd

# 读取 CSV
df = pd.read_csv('experiment_data.csv')
# 假设列：'group' (分组), 'score' (分数)

# 按组分割数据
groups = [group['score'].values for name, group in df.groupby('group')]
names = list(df['group'].unique())

plot = RaincloudPlot(groups, names, backend='seaborn')
plot.save('experiment_results.png')
```

---

## 参考文献

1. **Allen, M., Poggiali, D., Whitaker, K., Marshall, T. R., & Kievit, R. A. (2019).** 
   Raincloud plots: a multi-platform tool for robust data visualization. 
   *Wellcome Open Research*, 4:63. 
   **DOI:** [10.12688/wellcomeopenres.15191.1](https://doi.org/10.12688/wellcomeopenres.15191.1)

2. **Weissgerber, T. L., et al. (2015).**
   Beyond Bar and Line Graphs: Time for a New Data Presentation Paradigm.
   *PLoS Biology*, 13(4): e1002128.
   **DOI:** [10.1371/journal.pbio.1002128](https://doi.org/10.1371/journal.pbio.1002128)

3. **GitHub Repository:** 
   [RainCloudPlots/RainCloudPlots](https://github.com/RainCloudPlots/RainCloudPlots)

---

## 常见问题

### Q: 为什么叫 "Raincloud"？
A: 因为图表形状像一朵雨云 — 上方的小提琴图像云层，下方的散点像雨滴。

### Q: 应该选择哪种后端？
- **Plotly:** 交互式图表，适合网页展示、Jupyter Notebook
- **Seaborn:** 静态高清图，适合论文、报告
- **Matplotlib:** 完全自定义，适合高级用户

### Q: 数据量多大时适用？
- 每组 10-500 个点效果最佳
- >500 点时可降低散点透明度或采样

### Q: 能否自定义颜色？
可以！传入 `colors` 参数：
```python
plot = RaincloudPlot(data, names, colors=['#FF6B6B', '#4ECDC4', '#45B7D1'])
```

---

**🎨 让数据说话，诚实展示每一个数据点！**
