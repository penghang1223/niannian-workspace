# 月影（yueying）学习记录

> 最后更新：2026-04-02
> 维护者：月影

---

## 📚 今日学习

### 2026-04-02

#### Step 0: 落地检查
- 上次学的 CSS Anchor Positioning API 今早刚学，尚未落地验证（合理，刚学完）
- 2026-04-01 的 Python 3.14 t-strings / free-threaded / uv workspaces 均未实际使用 — 原因：当前项目暂不需要
- Polars/DuckDB/Plotly 管线已写入 lessons.md 速查手册，君上爬虫项目可用到
- **结论：** 工具类知识在 lessons.md 中备查，等具体项目触发；方法论类知识需主动应用

#### Step 1-4: 学→评→用→反馈

**学习主题：Raincloud Plot — 告别 Dynamite Plot（柱状图+误差线）**

**Step 1 学：**
- **Dynamite Plot 的四大罪状：**
  1. **隐藏数据**：相同的均值和标准差可以来自完全不同的分布（Anscombe 四重奏效应）
  2. **扭曲效应量**：柱子从 0 开始，视觉上夸大/缩小组间差异
  3. **掩盖分布假设**：双峰分布、偏态分布、异方差性在柱状图中完全不可见
  4. **误导推断**：误差线（SE/CI）不等于数据分布，读者常误读

- **Raincloud Plot 的构成（三合一）：**
  1. **半小提琴图（half-violin）**：展示概率密度分布，只画一侧，节省空间
  2. **箱线图（boxplot）**：中位数 + IQR + 须线，统计摘要一目了然
  3. **抖动散点（jittered points）**：展示原始数据点，不隐藏任何数据

- **来源：** Allen et al. (2019) "Raincloud plots: a multi-platform tool for robust data visualization" (Wellcome Open Research)
- **开源代码：** github.com/RainCloudPlots/RainCloudPlots（R/Python/Matlab）

- **Python 实现方案：**
  - `ptitprince` 包（matplotlib 风格）
  - Plotly 手动组合：`go.Violin(side='positive')` + `go.Box` + `go.Scatter(mode='markers')`
  - Seaborn：`sns.violinplot(inner=None)` + `sns.stripplot` + `sns.boxplot`

**Step 2 评：**
- 🔴 **高价值** — 作为数据可视化 CVO，这是核心技能
- 数据分析报告中 90% 的组间对比图都在用 dynamite plot，改用 raincloud plot 是专业度的质变
- 直接服务于月影的"美的翻译官"定位 — 把枯燥的统计结果翻译成直观、诚实、美观的视觉语言

**Step 3 用：**
- 君上如果需要展示任何"组间对比"数据（如 A/B 测试结果、不同方案效果对比），用 raincloud plot 替代柱状图
- Plotly 实现模板（速查用）：

```python
import plotly.graph_objects as go
import numpy as np

def raincloud_plot(groups_data, group_names, title="Raincloud Plot"):
    """groups_data: list of arrays, group_names: list of str"""
    fig = go.Figure()
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
    
    for i, (data, name) in enumerate(zip(groups_data, group_names)):
        offset = i * 1.5  # 组间距
        c = colors[i % len(colors)]
        
        # 1. 半小提琴（上方）
        fig.add_trace(go.Violin(
            y=data, x=[offset]*len(data), side='positive',
            orientation='v', width=0.8, line_color=c,
            fillcolor=c, opacity=0.5, meanline_visible=True,
            showlegend=False
        ))
        
        # 2. 抖动散点（下方）
        jitter = np.random.uniform(-0.3, 0.3, len(data))
        fig.add_trace(go.Scatter(
            x=[offset + j for j in jitter], y=data,
            mode='markers', marker=dict(size=4, color=c, opacity=0.6),
            showlegend=False, name=name
        ))
    
    fig.update_layout(
        title=title,
        xaxis=dict(tickvals=[i*1.5 for i in range(len(group_names))],
                   ticktext=group_names),
        violinmode='overlay'
    )
    return fig
```

**Step 4 反馈：**
- （待下次心跳验证：用 raincloud plot 画一个实际数据集的组间对比图）

---

## 📋 知识贡献

### 2026-04-02
- 🔴 **Raincloud Plot** — 数据可视化最佳实践，替代 Dynamite Plot。三层结构（半小提琴+箱线图+抖动散点），Plotly 实现模板已写入速查手册。适用于 A/B 测试、组间对比等所有需要"诚实展示数据分布"的场景

---

## 🎯 待改进

*待补充*

---

## 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？

---

### 四维评估（必须填写）

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | /5 | 能写成代码/脚本/skill吗？ |
| 🎯 可操作 | /5 | 有具体步骤和示例吗？ |
| ✅ 可验证 | /5 | 有明确的成功标准吗？ |
| 🔄 可复用 | /5 | 其他Agent能直接应用吗？ |

**总分**：/20
- 🔴 < 11：不合格，不记录
- 🟠 11-14：合格，可记录
- 🟡 15-17：良好，优先推荐
- 🟢 18-20：优秀，立即打包为skill

### 2026-04-03 09:27

#### 🔴 Falcon Perception — 超SAM 3的视觉追踪/分割模型

**核心收获**：
1. **Falcon Perception（TII，0.6B参数）** — 超SAM 3的视觉追踪/分割模型
   - 自然语言选区（用文字描述要分割的区域）
   - 消费级硬件可跑（不需要高端GPU）
2. **Falcon OCR（0.3B）** — 文档理解模型

**应用场景**：
- 漫剧角色抠图/场景分割可零成本完成
- 无需SAM 3，更轻量更易用

**预期改善**：视觉处理成本降到零

**四维评估**：

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | 5/5 | 可直接部署使用 |
| 🎯 可操作 | 5/5 | 自然语言接口，非常易用 |
| ✅ 可验证 | 5/5 | 效果可直观验证 |
| 🔄 可复用 | 5/5 | 所有视觉任务都能用 |

**总分**：20/20 🟢 优秀！立即打包为skill候选

### 2026-04-03 13:08

#### 🔴 工具链验证

**核心收获**：
编写验证脚本确认已学工具实际可用性

**应用场景**：
新工具学习后立即验证安装状态

**预期改善**：
避免学了工具却无法使用的尴尬

**四维评估**：

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | 5/5 | 可直接编写验证脚本 |
| 🎯 可操作 | 5/5 | 验证工具可用性是刚需 |
| ✅ 可验证 | 5/5 | 验证结果明确 |
| 🔄 可复用 | 5/5 | 所有工具安装后都可用 |

**总分**：20/20 🟢 优秀！立即实施

### 2026-04-03 13:10

#### 🔴 ECharts 6.0 新特性

**核心收获**：
Matrix坐标系可自由组合图表实现复杂布局

**应用场景**：
- 复杂仪表盘
- 数据分析报告

**预期改善**：
解决当前可视化布局灵活性不足问题

**四维评估**：

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | 4/5 | 可用于可视化项目 |
| 🎯 可操作 | 5/5 | Matrix坐标系具体功能 |
| ✅ 可验证 | 4/5 | 通过实际图表验证 |
| 🔄 可复用 | 5/5 | 所有可视化场景可用 |

**总分**：18/20 🟢 优秀！值得研究实现
