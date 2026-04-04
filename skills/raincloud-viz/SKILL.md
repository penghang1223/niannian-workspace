---
name: raincloud-viz
description: Raincloud Plot 可视化工具 — 替代 Dynamite Plot（柱状图 + 误差线），诚实展示数据分布。三合一结构（半小提琴 + 箱线图 + 抖动散点），支持 Plotly/Seaborn/Matplotlib 三种后端。
---

# Raincloud Viz — 数据分布可视化技能

## 技能描述

**解决什么问题：**
传统 Dynamite Plot（柱状图 + 误差线）存在四大缺陷：
1. **隐藏数据分布** — 相同均值/标准差可能来自完全不同的分布
2. **扭曲效应量** — 柱子从 0 开始，视觉夸大/缩小组间差异
3. **掩盖分布假设** — 双峰/偏态/异方差性完全不可见
4. **误导统计推断** — 误差线（SE/CI）≠ 数据分布

**Raincloud Plot 方案：**
三合一可视化结构（Allen et al. 2019）：
- 🌧️ **半小提琴图** — 概率密度分布（只画一侧，节省空间）
- 📦 **箱线图** — 中位数 + IQR + 须线（统计摘要）
- 🔵 **抖动散点** — 原始数据点（不隐藏任何数据）

## 使用场景

| 场景 | 说明 | 示例 |
|------|------|------|
| A/B 测试对比 | 展示实验组/对照组数据分布 | 用户转化率、点击率 |
| 组间差异分析 | 多组数据对比 | 不同方案效果、不同人群特征 |
| 统计报告 | 学术论文、数据分析报告 | 替代传统柱状图 |
| 探索性数据分析 | 发现分布特征（双峰/偏态） | 数据质量检查 |

## 触发条件

用户提到以下关键词时触发：
- "raincloud plot" / "雨云图"
- "替代柱状图" / "替代 dynamite plot"
- "展示数据分布" / "分布可视化"
- "组间对比图" / "A/B 测试图"
- "小提琴图 + 散点" / "箱线图 + 散点"

## 四维评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | 5/5 | 完整 Python 脚本，CLI 可直接执行 |
| 🎯 可操作 | 5/5 | 三种后端可选，含示例数据 |
| ✅ 可验证 | 5/5 | 输出图像可直观验证 |
| 🔄 可复用 | 5/5 | 所有组间对比场景通用 |

**总分：20/20 🟢 优秀**

## 快速使用

```bash
# 1. 安装依赖
pip install plotly seaborn matplotlib numpy pandas

# 2. 运行示例
python3 skills/raincloud-viz/scripts/raincloud_plot.py --demo

# 3. 自定义数据
python3 skills/raincloud-viz/scripts/raincloud_plot.py \
  --data "group1:1,2,3,4,5;group2:2,3,4,5,6" \
  --backend plotly \
  --output raincloud.html
```

## 文件结构

```
skills/raincloud-viz/
├── SKILL.md              # 技能说明（本文件）
├── README.md             # 详细文档
├── scripts/
│   └── raincloud_plot.py # 主脚本（CLI 接口）
└── examples/
    ├── demo_data.csv     # 示例数据
    └── example_usage.py  # 使用示例
```

## 参考文献

- Allen, M., Poggiali, D., Whitaker, K., Marshall, T. R., & Kievit, R. A. (2019). **Raincloud plots: a multi-platform tool for robust data visualization**. *Wellcome Open Research*, 4:63. [DOI: 10.12688/wellcomeopenres.15191.1](https://doi.org/10.12688/wellcomeopenres.15191.1)
- GitHub: [RainCloudPlots/RainCloudPlots](https://github.com/RainCloudPlots/RainCloudPlots)
