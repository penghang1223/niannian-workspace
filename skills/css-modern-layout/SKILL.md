# CSS Modern Layout — Container Queries + Anchor Positioning

Two native CSS capabilities that **eliminate JavaScript hack** in responsive UIs and overlay positioning.

## 1. CSS Container Queries — 组件级响应式

### Problem

传统 Media Queries 基于 **视口宽度**，但一个 Card 组件放到侧边栏和放到主区域时，应该有不同的布局——这跟视口无关，跟**父容器**有关。

### Solution

```css
/* Step 1: 声明容器（父元素） */
.card-wrapper {
  container-type: inline-size;   /* 跟踪宽度 */
  container-name: card;           /* 可选：命名 */
}

/* Step 2: 基于容器条件写样式 */
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1rem;
  }
}

@container card (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
  .card__image {
    width: 100%;
    aspect-ratio: 16/9;
  }
}
```

### 关键语法

| 属性 | 值 | 说明 |
|------|-----|------|
| `container-type` | `inline-size` \| `size` \| `normal` | 要追踪的维度 |
| `container-name` | `<custom-ident>` | 一个或多个名字（空格分隔） |
| `container` | `name / type` | 简写 |

`@container` 规则可用的查询条件：`min-width`、`max-width`、`min-height`、`max-height`、`orientation`、`aspect-ratio`。

### 实战：Dashboard 自适应

```html
<aside class="sidebar">
  <div class="widget-wrapper">        <!-- 容器 -->
    <div class="weather-widget">...</div>
  </div>
</aside>

<main class="content">
  <div class="widget-wrapper">        <!-- 同一个组件，不同容器宽度 -->
    <div class="weather-widget">...</div>
  </div>
</main>
```

```css
.widget-wrapper {
  container-type: inline-size;
}

/* 容器 < 300px → 紧凑模式 */
@container (max-width: 299px) {
  .weather-widget {
    font-size: 0.875rem;
    padding: 0.5rem;
  }
  .weather-widget__forecast {
    display: none;            /* 隐藏次要信息 */
  }
}

/* 容器 ≥ 300px → 完整模式 */
@container (min-width: 300px) {
  .weather-widget {
    font-size: 1rem;
    padding: 1rem;
  }
  .weather-widget__forecast {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
  }
}
```

### Container Style Queries（实验性）

```css
/* 查询容器的自定义属性 */
@container style(--theme: dark) {
  .card { background: #1a1a2e; color: #eee; }
}
```

> ⚠️ 截至 2025，Chrome 111+ 支持 `style()` 查询，Firefox/Safari 尚未跟进。

### 浏览器支持

| 浏览器 | 支持版本 |
|--------|---------|
| Chrome | 105+ |
| Firefox | 110+ |
| Safari | 16+ |
| Edge | 105+ |

**Fallback 策略**：用 `@supports (container-type: inline-size)` 包裹：

```css
@supports (container-type: inline-size) {
  .card-wrapper { container-type: inline-size; }
  @container (min-width: 400px) { /* ... */ }
}
/* 不支持时，组件保持默认 flex 布局 */
```

---

## 2. CSS Anchor Positioning — 纯 CSS 定位 Tooltip/Popover

### Problem

传统 tooltip 需要 JavaScript 调用 `getBoundingClientRect()` 计算位置，处理滚动、resize、边界溢出……非常脆弱。

### Solution

CSS Anchor Positioning API 让你用**声明式**方式将一个元素锚定到另一个元素。

```html
<button class="anchor" popovertarget="tip">Hover me</button>
<div id="tip" class="tooltip" popover>
  This is a tooltip
</div>
```

```css
.anchor {
  anchor-name: --my-anchor;     /* 给锚点命名 */
}

.tooltip {
  position: fixed;
  position-anchor: --my-anchor; /* 引用锚点 */

  /* 水平居中对齐锚点 */
  left: anchor(center);
  translate: -50%;

  /* 放在锚点上方 */
  bottom: anchor(top);
  margin-bottom: 8px;
}
```

### 核心语法

#### 锚点声明

```css
.anchor-element {
  anchor-name: --name;  /* <dashed-ident>，可声明多个 */
}
```

#### 目标定位

```css
.positioned-element {
  position-anchor: --name;           /* 绑定锚点 */
  position: fixed;                   /* 或 absolute */

  /* anchor() 函数 — 获取锚点边缘 */
  top:    anchor(bottom);            /* 锚点底部 → 目标顶部 */
  left:   anchor(center);            /* 锚点水平居中 */
  right:  anchor(end);               /* 逻辑属性 */
}
```

#### `anchor()` 函数详解

```css
/* 语法: anchor(<anchor-name>? <anchor-side>, <fallback>) */
top:  anchor(--btn bottom, 0px);
left: anchor(center, 50%);

/* anchor-side 可选值 */
/* top | bottom | left | right | center | start | end | self-start | self-end */
```

#### `anchor-size()` 函数

```css
/* 引用锚点的尺寸 */
.tooltip {
  width: anchor-size(width);           /* 等宽 */
  min-width: anchor-size(--btn width);
  padding: calc(anchor-size(height) * 0.2);
}
```

### 实战：Tooltip（无 JS！）

```css
button {
  anchor-name: --tooltip-target;
}

.tooltip {
  position: fixed;
  position-anchor: --tooltip-target;

  /* 锚定在按钮上方居中 */
  bottom: anchor(--tooltip-target top);
  left: anchor(--tooltip-target center);
  translate: -50% -8px;

  /* 边界溢出自动翻转 */
  position-try-fallbacks: flip-block;  /* 上方放不下 → 翻到下方 */
}
```

### 实战：Dropdown Menu

```css
.menu-trigger {
  anchor-name: --menu-anchor;
}

.dropdown-menu {
  position: fixed;
  position-anchor: --menu-anchor;
  top: anchor(--menu-anchor bottom);
  left: anchor(--menu-anchor left);
  width: anchor-size(--menu-anchor width);  /* 跟触发器等宽 */

  /* 多个回退位置 */
  position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
}
```

### `position-try-fallbacks` — 智能翻转

```css
.tooltip {
  position-try-fallbacks:
    flip-block,           /* 上↔下翻转 */
    flip-inline,          /* 左↔右翻转 */
    flip-block flip-inline; /* 同时翻转 */

  /* 或自定义回退（更精细的控制） */
  position-try-options:
    --try-top,
    --try-bottom,
    --try-right;

  @position-try --try-top {
    bottom: anchor(top);
    left: anchor(center);
    translate: -50% 0;
  }
  @position-try --try-bottom {
    top: anchor(bottom);
    left: anchor(center);
    translate: -50% 0;
  }
}
```

### 浏览器支持

| 浏览器 | 支持版本 |
|--------|---------|
| Chrome | 125+ |
| Firefox | 131+ |
| Safari | 技术预览版（部分） |
| Edge | 125+ |

**检测方式**：

```css
@supports (anchor-name: --test) {
  /* 浏览器支持锚点定位 */
}

@supports not (anchor-name: --test) {
  /* 回退：JS getBoundingClientRect */
}
```

---

## 3. 两者结合 — 组件自适应 + 定位

```css
/* 一个响应式 Popover 组件 */
.popover-wrapper {
  container-type: inline-size;
  anchor-name: --popover-anchor;
}

.popover {
  position: fixed;
  position-anchor: --popover-anchor;
  top: anchor(--popover-anchor bottom);
  left: anchor(--popover-anchor center);
  translate: -50% 8px;

  position-try-fallbacks: flip-block, flip-inline;
}

/* 小容器中 popover 变成全宽 sheet */
@container (max-width: 300px) {
  .popover {
    position: fixed;
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    translate: none;
    border-radius: 12px 12px 0 0;
  }
}
```

---

## Quick Reference

| 特性 | Container Queries | Anchor Positioning |
|------|-------------------|--------------------|
| 解决问题 | 组件响应式布局 | 元素间相对定位 |
| 替代方案 | Media Queries + JS resize | getBoundingClientRect() |
| 核心关键字 | `container-type`, `@container` | `anchor-name`, `position-anchor`, `anchor()` |
| 推荐搭配 | Subgrid, CSS Layers | Popover API, Scroll-driven Animations |

---

## Further Reading

- [MDN: CSS Container Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_queries)
- [MDN: CSS Anchor Positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning)
- [web.dev: Anchor Positioning Guide](https://web.dev/blog/anchor-positioning-api)
- [Caniuse: Container Queries](https://caniuse.com/css-container-queries)
- [Caniuse: Anchor Positioning](https://caniuse.com/mdn-css_types_anchor)
