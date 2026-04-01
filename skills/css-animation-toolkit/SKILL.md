# CSS Animation Toolkit — 现代 CSS 动画全指南

> Scroll-Driven Animations · @starting-style · Scroll-State Queries · content-visibility 优化

## 🎯 使用场景

当用户需要：
1. 滚动驱动动画（元素随滚动进度变化）
2. 纯 CSS 进出场动画（无 JS 监听 scroll/intersection）
3. 吸附阴影（滚动时 sticky 元素动态阴影）
4. 渲染性能优化（大量内容的延迟渲染）

**去重说明**：本技能专注动画与视觉交互。布局系统（Container Size Queries、Anchor Positioning）见 `css-modern-layout` 技能。

---

## 1. Scroll-Driven Animations（滚动驱动动画）

### 核心概念

```css
/* 绑定动画到滚动时间线 */
animation-timeline: scroll();    /* 滚动容器的时间线 */
animation-timeline: view();      /* 元素进出视口的时间线 */
animation-range: entry 0% entry 100%;  /* 控制动画生效区间 */
```

### 模式 A：元素进入视口时渐显（view()）

```css
.fade-in-up {
  animation: fadeInUp linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(60px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

**实战：产品卡片滚动入场**

```html
<div class="product-grid">
  <article class="card fade-in-up">...</article>
  <article class="card fade-in-up">...</article>
  <!-- 每个卡片进入视口时自动淡入上移 -->
</div>
```

### 模式 B：进度指示器（scroll()）

```css
.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #ec4899);
  transform-origin: left;
  animation: growWidth linear;
  animation-timeline: scroll();
}

@keyframes growWidth {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}
```

### 模式 C：Parallax 视差效果

```css
.parallax-bg {
  animation: parallaxMove linear;
  animation-timeline: view();
  animation-range: entry 0% exit 100%;
}

@keyframes parallaxMove {
  from { transform: translateY(-30%); }
  to   { transform: translateY(30%); }
}
```

### animation-range 速查

| 关键字 | 含义 |
|--------|------|
| `entry 0% entry 100%` | 元素从完全不可见到完全进入视口 |
| `exit 0% exit 100%` | 元素从完全可见到完全离开视口 |
| `cover 0% cover 100%` | 元素从进入视口到完全离开 |
| `contain 0% contain 100%` | 元素完全在视口内的时间段 |

### 滚动驱动时间线（命名时间线）

```css
/* 滚动容器定义时间线 */
.scroll-container {
  scroll-timeline: --myTimeline y;
}

/* 后代元素引用时间线 */
.scroll-indicator {
  animation: rotate linear;
  animation-timeline: --myTimeline;
}
```

---

## 2. @starting-style + transition-behavior（纯 CSS 进出场）

### 核心概念

```css
/* 允许 display 变化的过渡 */
transition-behavior: allow-discrete;

/* 定义"出场起始状态"（被隐藏前的最终状态） */
@starting-style {
  .element {
    /* 元素刚从 display:none 变为可见时的状态 */
  }
}
```

### 模式 A：模态框弹出动画

```css
.modal-backdrop {
  display: none;
  opacity: 0;
  transition: opacity 0.3s ease, display 0.3s ease allow-discrete;

  &.open {
    display: grid;
    opacity: 1;
  }
}

@starting-style {
  .modal-backdrop.open {
    opacity: 0;
  }
}

.modal-panel {
  transform: scale(0.9) translateY(20px);
  transition: transform 0.3s ease, display 0.3s ease allow-discrete;

  /* 这里用 :popover-open 伪类更优雅 */
}

@starting-style {
  .modal-backdrop.open .modal-panel {
    transform: scale(0.8) translateY(40px);
  }
}
```

### 模式 B：Popover API + @starting-style（推荐）

```css
[popover] {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
  transition: opacity 0.25s, transform 0.25s, display 0.25s allow-discrete;
}

[popover]:popover-open {
  opacity: 1;
  transform: translateY(0) scale(1);
}

@starting-style {
  [popover]:popover-open {
    opacity: 0;
    transform: translateY(-10px) scale(0.95);
  }
}
```

```html
<button popovertarget="my-popover">打开菜单</button>
<div id="my-popover" popover>
  <a href="#">选项一</a>
  <a href="#">选项二</a>
</div>
```

### 模式 C：Toast 通知

```css
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: none;
  opacity: 0;
  translate: 0 1rem;
  transition: opacity 0.3s, translate 0.3s, display 0.3s allow-discrete;
}

.toast.show {
  display: flex;
  opacity: 1;
  translate: 0 0;
}

@starting-style {
  .toast.show {
    opacity: 0;
    translate: 0 1rem;
  }
}
```

### 进入 vs 退出动画对比

| 阶段 | 过渡方向 | @starting-style 起作用？ |
|------|---------|------------------------|
| 进入 | display:none → block | ✅ 用 @starting-style 定义初始状态 |
| 退出 | display:block → none | ✅ 用 transition 定义最终状态 |

---

## 3. Scroll-State Container Queries（吸附阴影 / Snap 高亮）

> ⚠️ 实验性 API，Chrome 125+ 支持部分功能，需 `#enable-experimental-web-platform-features`

### 模式 A：Sticky 元素吸附阴影

```css
.sticky-header {
  position: sticky;
  top: 0;
  container-type: scroll-state;
  container-name: header;
}

.sticky-header::after {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 8px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.15), transparent);
  opacity: 0;
  transition: opacity 0.2s;
}

@container scroll-state(scroll-state: stuck) {
  .sticky-header::after {
    opacity: 1;
  }
}
```

### 模式 B：Snap 容器高亮当前项

```css
.snap-container {
  scroll-snap-type: x mandatory;
  container-type: scroll-state;
}

.snap-item {
  scroll-snap-align: center;
  container-type: scroll-state;
}

@container scroll-state(snapped: inline) {
  .snap-item {
    scale: 1.05;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  }
}
```

### 降级方案（当前兼容）

```css
/* 用 IntersectionObserver + CSS 变量的渐进增强 */
.sticky-shadow {
  --stuck: 0;
  box-shadow: 0 calc(var(--stuck) * 4px) 12px rgba(0,0,0,calc(0.1 * var(--stuck)));
  transition: box-shadow 0.2s;
}
```

```js
const header = document.querySelector('.sticky-shadow');
const observer = new IntersectionObserver(
  ([e]) => header.style.setProperty('--stuck', e.intersectionRatio < 1 ? 1 : 0),
  { threshold: [1], rootMargin: '-1px 0px 0px 0px' }
);
observer.observe(header);
```

---

## 4. content-visibility 渲染优化

### 核心概念

```css
content-visibility: auto;       /* 浏览器按需跳过屏外内容渲染 */
contain-intrinsic-size: 0 500px; /* 占位高度（避免布局跳动） */
```

### 模式 A：长列表/文章优化

```css
/* 适用于：博客列表、无限滚动、FAQ 手风琴 */
.list-item {
  content-visibility: auto;
  contain-intrinsic-size: auto 200px; /* 预估高度 */
}

/* 关键帧动画配合内容可见性 */
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.list-item {
  content-visibility: auto;
  contain-intrinsic-size: auto 200px;
  animation: slideIn ease both;
  animation-timeline: view();
  animation-range: entry 0% entry 50%;
}
```

### 模式 B：画廊/网格优化

```css
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.gallery-item {
  content-visibility: auto;
  contain-intrinsic-size: 300px 250px;
  contain: content; /* 同时启用 layout + style + paint 隔离 */
}
```

### 性能收益

| 场景 | 无优化 | content-visibility: auto |
|------|--------|--------------------------|
| 1000 项列表首屏 | 渲染全部 | 仅渲染可见项 |
| 首次交互 (TTI) | 800ms+ | 200ms |
| 内存占用 | 高 | 显著降低 |

---

## 5. 综合实战：Landing Page 滚动体验

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<style>
  /* 📊 阅读进度条 */
  .progress-bar {
    position: fixed; top: 0; left: 0;
    height: 3px; z-index: 100;
    background: linear-gradient(90deg, #6366f1, #ec4899);
    transform-origin: left;
    animation: growWidth linear;
    animation-timeline: scroll();
  }

  /* 🧭 Sticky Header 吸附阴影 */
  .site-header {
    position: sticky; top: 0; z-index: 50;
    background: white;
    transition: box-shadow 0.3s;
  }
  .site-header.scrolled {
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  }

  /* 🎞️ 卡片滚动入场 */
  .feature-card {
    content-visibility: auto;
    contain-intrinsic-size: auto 400px;
    animation: fadeSlideUp linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 80%;
  }

  /* 🪟 弹窗动画 */
  .modal {
    display: none;
    opacity: 0;
    backdrop-filter: blur(4px);
    transition: opacity 0.3s, display 0.3s allow-discrete;
  }
  .modal.open {
    display: flex;
    opacity: 1;
  }
  @starting-style {
    .modal.open { opacity: 0; }
  }

  @keyframes growWidth {
    from { transform: scaleX(0); }
    to   { transform: scaleX(1); }
  }

  @keyframes fadeSlideUp {
    from {
      opacity: 0;
      translate: 0 40px;
    }
    to {
      opacity: 1;
      translate: 0 0;
    }
  }
</style>
</head>
<body>
  <div class="progress-bar"></div>
  <header class="site-header">...</header>
  <main>
    <section class="feature-card">...</section>
    <section class="feature-card">...</section>
    <section class="feature-card">...</section>
  </main>
  <dialog class="modal" id="demo-modal">...</dialog>
</body>
</html>
```

---

## 📋 速查表

| 特性 | 语法 | 支持度 | 用途 |
|------|------|--------|------|
| `animation-timeline: scroll()` | `<css-values>` | Chrome 115+ | 进度条、滚动值映射 |
| `animation-timeline: view()` | `<css-values>` | Chrome 115+ | 元素进入/离开视口动画 |
| `@starting-style` | CSS 块 | Chrome 117+ | 纯 CSS 进入动画 |
| `transition-behavior: allow-discrete` | CSS 值 | Chrome 117+ | display 属性过渡 |
| `content-visibility: auto` | CSS 值 | Chrome 85+ | 跳过屏外渲染 |
| `container-type: scroll-state` | CSS 值 | Chrome 125+ 实验 | 吸附阴影、snap 状态 |

---

## 🔗 相关技能

- `css-modern-layout` — Container Size Queries + Anchor Positioning（布局系统）
- `css-variables` — CSS 自定义属性与 @property
