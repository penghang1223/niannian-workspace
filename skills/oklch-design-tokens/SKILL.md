# OKLCH Design Tokens Skill

> 基于 OKLCH 色彩空间的现代设计系统配色工具，提供 Token 架构、派生色板、主题切换和动画支持。

## 触发条件

用户提到：`设计系统`、`design tokens`、`OKLCH`、`配色方案`、`色板生成`、`主题切换`、`light-dark`、`color-mix`、`CSS 变量`、`设计配色`

---

## 1. OKLCH 核心 Token 定义

OKLCH 三通道：**L**(明度 0-1)、**C**(色度 0-0.4)、**H**(色相 0-360)。

```css
/* === 核心色相 Token === */
:root {
  /* 主色相角度 */
  --hue-primary: 250;      /* 紫蓝 */
  --hue-secondary: 340;    /* 玫红 */
  --hue-accent: 160;       /* 翠绿 */
  --hue-neutral: 250;      /* 中性色（低色度时偏灰紫） */

  /* 基础色板 — 仅定义 L/C，H 从 Token 继承 */
  --color-primary-50:  oklch(0.97 0.01 var(--hue-primary));
  --color-primary-100: oklch(0.93 0.03 var(--hue-primary));
  --color-primary-200: oklch(0.87 0.06 var(--hue-primary));
  --color-primary-300: oklch(0.78 0.10 var(--hue-primary));
  --color-primary-400: oklch(0.68 0.14 var(--hue-primary));
  --color-primary-500: oklch(0.58 0.18 var(--hue-primary));
  --color-primary-600: oklch(0.50 0.18 var(--hue-primary));
  --color-primary-700: oklch(0.42 0.16 var(--hue-primary));
  --color-primary-800: oklch(0.35 0.12 var(--hue-primary));
  --color-primary-900: oklch(0.28 0.08 var(--hue-primary));
  --color-primary-950: oklch(0.20 0.04 var(--hue-primary));

  /* 语义 Token（映射到基础色板） */
  --color-bg:        oklch(0.99 0 0);
  --color-bg-subtle: oklch(0.96 0.005 var(--hue-neutral));
  --color-surface:   oklch(0.94 0.008 var(--hue-neutral));
  --color-border:    oklch(0.88 0.01 var(--hue-neutral));
  --color-text:      oklch(0.20 0.02 var(--hue-neutral));
  --color-text-muted: oklch(0.50 0.02 var(--hue-neutral));
  --color-primary:   var(--color-primary-500);
  --color-primary-hover: var(--color-primary-400);
  --color-primary-active: var(--color-primary-600);
}
```

### Token 架构分层

```
┌─────────────────────────────────────┐
│  语义层 (Semantic)                   │  --color-bg, --color-primary-hover
├─────────────────────────────────────┤
│  组件层 (Component)                  │  --btn-bg, --card-border
├─────────────────────────────────────┤
│  基础层 (Primitive)                  │  --color-primary-500, --color-red-300
├─────────────────────────────────────┤
│  核心层 (Core / Channel Token)       │  --hue-primary, --chroma-max
└─────────────────────────────────────┘
```

**设计原则**：语义层引用基础层，基础层引用核心层。修改 `--hue-primary` 即可全局换色。

---

## 2. color-mix() 派生色板

用 `color-mix()` 动态派生，避免硬编码每个色阶。

```css
/* 半透明 / hover / disabled 状态自动派生 */
:root {
  --color-primary-alpha-10: color-mix(in oklch, var(--color-primary) 10%, transparent);
  --color-primary-alpha-20: color-mix(in oklch, var(--color-primary) 20%, transparent);
  --color-primary-alpha-50: color-mix(in oklch, var(--color-primary) 50%, transparent);

  /* 混合白色 = tint，混合黑色 = shade */
  --color-primary-tint:  color-mix(in oklch, var(--color-primary) 30%, white);
  --color-primary-shade: color-mix(in oklch, var(--color-primary) 30%, black);

  /* Hover 态：主色混入 15% 白 */
  --btn-hover-bg: color-mix(in oklch, var(--color-primary) 85%, white 15%);
  /* Active 态：主色混入 15% 黑 */
  --btn-active-bg: color-mix(in oklch, var(--color-primary) 85%, black 15%);

  /* Disabled 态 */
  --btn-disabled-bg: color-mix(in oklch, var(--color-primary) 40%, var(--color-bg) 60%);
  --btn-disabled-text: color-mix(in oklch, var(--color-text) 30%, var(--color-bg) 70%);
}
```

### 动态生成色阶函数（Less/Sass/PostCSS）

```less
// Less 示例 — 用 OKLCH 生成 10 级色阶
.generate-palette(@name, @hue, @chroma: 0.16) {
  each(range(9), {
    @lightness: 0.97 - (@value - 1) * 0.085;
    @c: if((@value < 3) or (@value > 7), @chroma * 0.5, @chroma);
    --color-@{name}-@{value * 100}: oklch(@lightness @c @hue);
  });
}

:root {
  .generate-palette(primary, 250);
  .generate-palette(secondary, 340, 0.14);
  .generate-palette(accent, 160, 0.12);
}
```

---

## 3. @property 注册 — 解锁渐变颜色动画

用 `@property` 注册自定义属性为 `<color>` 类型，浏览器即可对颜色做平滑插值。

```css
/* 注册核心颜色为可动画类型 */
@property --color-primary {
  syntax: '<color>';
  inherits: true;
  initial-value: oklch(0.58 0.18 250);
}

@property --color-bg {
  syntax: '<color>';
  inherits: true;
  initial-value: oklch(0.99 0 0);
}

@property --color-text {
  syntax: '<color>';
  inherits: true;
  initial-value: oklch(0.20 0.02 250);
}

@property --gradient-start {
  syntax: '<color>';
  inherits: false;
  initial-value: oklch(0.58 0.18 250);
}

@property --gradient-end {
  syntax: '<color>';
  inherits: false;
  initial-value: oklch(0.78 0.10 340);
}
```

### 渐变动画示例

```css
/* 主题切换动画 — 颜色平滑过渡 */
html {
  transition: --color-primary 0.4s ease, --color-bg 0.4s ease, --color-text 0.4s ease;
}

/* 渐变色流动动画 */
.hero-gradient {
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  animation: gradient-shift 6s ease-in-out infinite alternate;
}

@keyframes gradient-shift {
  0%   { --gradient-start: oklch(0.58 0.18 250); --gradient-end: oklch(0.78 0.10 340); }
  50%  { --gradient-start: oklch(0.65 0.16 160); --gradient-end: oklch(0.70 0.14 250); }
  100% { --gradient-start: oklch(0.60 0.20 340); --gradient-end: oklch(0.80 0.12 50); }
}

/* 按钮 hover 颜色过渡 */
.btn-primary {
  background: var(--color-primary);
  transition: background 0.25s ease;
}
.btn-primary:hover {
  background: var(--color-primary-hover); /* 自动平滑过渡 */
}
```

---

## 4. light-dark() 自动主题切换

CSS 原生 `light-dark()` 函数，配合 `color-scheme` 一行搞定双主题。

```css
:root {
  color-scheme: light dark;

  /* 语义 Token 自动切换 */
  --color-bg:         light-dark(oklch(0.99 0 0),           oklch(0.15 0.01 250));
  --color-bg-subtle:  light-dark(oklch(0.96 0.005 250),    oklch(0.19 0.015 250));
  --color-surface:    light-dark(oklch(0.94 0.008 250),    oklch(0.22 0.02 250));
  --color-border:     light-dark(oklch(0.88 0.01 250),     oklch(0.30 0.02 250));
  --color-text:       light-dark(oklch(0.20 0.02 250),     oklch(0.93 0.01 250));
  --color-text-muted: light-dark(oklch(0.50 0.02 250),     oklch(0.65 0.015 250));

  /* 主色在暗色模式提亮 */
  --color-primary:        light-dark(oklch(0.58 0.18 250), oklch(0.72 0.16 250));
  --color-primary-hover:  light-dark(oklch(0.68 0.14 250), oklch(0.78 0.14 250));

  /* 覆层透明度也自动切换 */
  --overlay-bg: light-dark(oklch(0 0 0 / 0.5), oklch(0 0 0 / 0.7));
}
```

### JS 手动切换（兼容旧浏览器）

```js
// 切换主题
function setTheme(mode) {
  // mode: 'light' | 'dark' | 'system'
  if (mode === 'system') {
    document.documentElement.style.colorScheme = 'light dark';
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.style.colorScheme = mode;
    document.documentElement.dataset.theme = mode;
  }
  localStorage.setItem('theme', mode);
}

// 初始化
const saved = localStorage.getItem('theme') || 'system';
setTheme(saved);
```

### @property + light-dark 联动动画

```css
@property --color-bg {
  syntax: '<color>';
  inherits: true;
  initial-value: oklch(0.99 0 0);
}

:root {
  color-scheme: light dark;
  --color-bg: light-dark(oklch(0.99 0 0), oklch(0.15 0.01 250));
  transition: --color-bg 0.5s ease; /* 主题切换时背景色平滑过渡 */
}
```

---

## 5. accent-color 原生表单控件主题适配

`accent-color` 让浏览器原生控件（checkbox/radio/range/progress）自动使用主题色。

```css
:root {
  /* 单值：所有控件统一主题色 */
  accent-color: var(--color-primary);

  /* 也支持细粒度控制 */
  accent-color: light-dark(oklch(0.58 0.18 250), oklch(0.72 0.16 250));
}

/* 更精细：按控件类型覆盖 */
input[type="checkbox"] { accent-color: oklch(0.65 0.20 160); }  /* 绿色确认 */
input[type="radio"]    { accent-color: var(--color-primary); }
input[type="range"]    { accent-color: oklch(0.70 0.14 340); }   /* 玫红滑块 */
progress               { accent-color: var(--color-primary); }
```

---

## 6. 完整 Token 模板（开箱即用）

```css
/* ========================================
   Design Token System — OKLCH Edition
   ======================================== */

@property --color-primary {
  syntax: '<color>'; inherits: true;
  initial-value: oklch(0.58 0.18 250);
}
@property --color-bg {
  syntax: '<color>'; inherits: true;
  initial-value: oklch(0.99 0 0);
}
@property --color-text {
  syntax: '<color>'; inherits: true;
  initial-value: oklch(0.20 0.02 250);
}
@property --color-surface {
  syntax: '<color>'; inherits: true;
  initial-value: oklch(0.94 0.008 250);
}

:root {
  color-scheme: light dark;
  accent-color: var(--color-primary);
  transition: --color-primary 0.4s ease, --color-bg 0.4s ease,
              --color-text 0.4s ease, --color-surface 0.4s ease;

  /* ── 核心通道 ── */
  --hue-primary: 250;
  --hue-secondary: 340;
  --hue-accent: 160;
  --hue-neutral: 250;

  /* ── 语义层 ── */
  --color-bg:         light-dark(oklch(0.99 0 0),           oklch(0.15 0.01 250));
  --color-bg-subtle:  light-dark(oklch(0.96 0.005 250),    oklch(0.19 0.015 250));
  --color-surface:    light-dark(oklch(0.94 0.008 250),    oklch(0.22 0.02 250));
  --color-border:     light-dark(oklch(0.88 0.01 250),     oklch(0.30 0.02 250));
  --color-text:       light-dark(oklch(0.20 0.02 250),     oklch(0.93 0.01 250));
  --color-text-muted: light-dark(oklch(0.50 0.02 250),     oklch(0.65 0.015 250));
  --color-primary:        light-dark(oklch(0.58 0.18 250), oklch(0.72 0.16 250));
  --color-primary-hover:  light-dark(oklch(0.68 0.14 250), oklch(0.78 0.14 250));
  --color-primary-active: light-dark(oklch(0.50 0.18 250), oklch(0.65 0.16 250));
  --color-danger:  light-dark(oklch(0.55 0.20 25),  oklch(0.70 0.16 25));
  --color-success: light-dark(oklch(0.60 0.18 155), oklch(0.72 0.14 155));
  --color-warning: light-dark(oklch(0.75 0.16 80),  oklch(0.80 0.14 80));

  /* ── 派生层 (color-mix) ── */
  --color-primary-alpha-10: color-mix(in oklch, var(--color-primary) 10%, transparent);
  --color-primary-alpha-20: color-mix(in oklch, var(--color-primary) 20%, transparent);
  --color-primary-tint:    color-mix(in oklch, var(--color-primary) 30%, white);
  --color-primary-shade:   color-mix(in oklch, var(--color-primary) 30%, black);
  --overlay-bg: light-dark(oklch(0 0 0 / 0.5), oklch(0 0 0 / 0.7));
}
```

---

## 7. 浏览器兼容性备注

| 特性 | Chrome | Firefox | Safari |
|------|--------|---------|--------|
| `oklch()` | 111+ | 113+ | 15.4+ |
| `color-mix()` | 111+ | 113+ | 16.2+ |
| `light-dark()` | 123+ | 120+ | 17.5+ |
| `@property` | 85+ | 128+ | 15.4+ |
| `accent-color` | 93+ | 92+ | 15.4+ |
| `color-scheme` | 81+ | 96+ | 13+ |

**降级策略**：对不支持 `light-dark()` 的浏览器，提供 `@media (prefers-color-scheme: dark)` 回退：

```css
@supports not (color: light-dark(red, blue)) {
  :root {
    --color-bg: oklch(0.99 0 0);
    --color-text: oklch(0.20 0.02 250);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --color-bg: oklch(0.15 0.01 250);
      --color-text: oklch(0.93 0.01 250);
    }
  }
}
```

---

## 使用流程

1. **确定品牌色相**：选定 `--hue-primary` 等核心 H 值
2. **搭建基础层**：用 OKLCH 写出 50-950 色阶
3. **定义语义层**：映射 bg/surface/text/border/primary
4. **注册 @property**：解锁颜色动画能力
5. **套 light-dark()**：一行搞定明暗主题
6. **设置 accent-color**：原生控件自动适配
7. **用 color-mix 派生**：hover/active/disabled 自动生成
