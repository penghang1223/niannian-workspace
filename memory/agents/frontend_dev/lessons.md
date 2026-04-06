## [2026-04-03] 学习闭环
### 学了什么
- 领域：现代CSS技术-:has()选择器
- 来源：https://webkit.org/blog/13096/css-has-pseudo-class/
- 核心知识点：使用:has()选择器实现父元素选择、兄弟元素选择、基于子元素状态的条件样式，以及结合伪类进行表单状态样式控制

### 有用吗？
- 价值评级：🔴
- 理由：:has()选择器是CSS的重大突破，实现了长期以来期望的父选择器功能，允许基于子元素状态来样式化父元素，无需JavaScript

### 用在哪？
- 具体场景：表单状态样式控制、卡片布局根据内容调整、主题切换、条件样式应用、以及其他需要基于子元素状态来样式化父元素的场景
- 预期改善：减少对JavaScript的依赖，实现更优雅的条件样式，提升用户体验和开发效率

### 实际效果
- （下次心跳时回填：用了没？效果如何？）
- 改善量化：待回填

---

## [2026-04-04] 学习闭环

### 学了什么
- 领域：CSS `@scope` 样式作用域隔离
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@scope
- 核心知识点：
  - `@scope (.root) to (.limit) { ... }` 定义样式作用域边界
  - 内联用法：`<style>@scope { ... }</style>` 自动绑定到父元素
  - Donut Scope 模式：样式到 limit 选择器处停止，不影响嵌套组件
  - 基于 DOM 接近度的特异性：更近的作用域优先于 source order
  - 替代 BEM/CSS Modules 的纯 CSS 样式隔离方案
  - 浏览器支持：Chrome 118+、Safari 17.4+、Firefox 123+

### 有用吗？
- 价值评级：🟡
- 理由：比 BEM/CSS Modules 更优雅的纯 CSS 样式隔离，Donut Scope 模式解决父组件样式泄漏子组件的经典问题。但在 Tailwind 项目中价值有限（原子化 CSS 天然隔离）。在组件库/设计系统项目中价值更高。

### 用在哪？
- 具体场景：组件样式隔离、第三方库样式集成、嵌套组件边界控制
- 预期改善：消除命名冲突，减少 specificity 战争，样式代码更清晰

### 实际效果
- （待回填）

---

## [2026-04-04] 学习闭环

### 学了什么
- 领域：CSS `@layer` 级联层管理
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer
- 核心知识点：
  - `@layer name1, name2, name3;` 声明层顺序
  - `@layer name { rules }` 定义层内容
  - 层顺序决定优先级：后声明的层覆盖前面的层
  - 未分层样式 > 层内样式（正常声明）
  - `!important` 优先级反转：层内 !important > 层外 !important
  - 嵌套层：`@layer framework.layout { }`
  - 浏览器支持：Chrome 99+、Safari 15.4+、Firefox 97+

### 有用吗？
- 价值评级：🟡
- 理由：解决 CSS specificity 战争的标准方案。对于 nannan-dashboard 集成第三方组件库（如 Ant Design）时非常有用：把第三方样式放 `@layer third-party`，自定义放 `@layer custom`，确保自定义永远覆盖，无需 `!important`。

### 用在哪？
- 具体场景：第三方组件库样式覆盖、设计系统基础样式管理、多团队协作样式优先级控制
- 预期改善：消除 `!important` 滥用，样式优先级可预测，减少样式冲突

### 实际效果
- （待回填）

---

## [2026-04-04] 学习闭环

### 学了什么
- 领域：CSS `accent-color` + `color-scheme`（原生表单控件主题适配）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/accent-color
- 核心知识点：
  - `accent-color: <color>` 设置 checkbox/radio/range/progress 的主题色
  - `color-scheme: light | dark | light dark` 声明支持的主题模式
  - 原生控件自动适配，无需自定义样式
  - `accent-color: auto` 跟随系统主题色
  - 浏览器支持：Chrome 93+、Safari 15.4+、Firefox 92+

### 有用吗？
- 价值评级：🟡
- 理由：一行 CSS 实现原生表单控件主题化，无需自定义 checkbox/radio 样式。配合 `color-scheme` 自动适配深色模式。nannan-dashboard 的表单组件可大幅简化。

### 用在哪？
- 具体场景：表单控件主题化、深色模式适配、原生 UI 一致性
- 预期改善：减少自定义表单样式代码，提升可访问性，深色模式自动适配

### 实际效果
- （待回填）

---

## [2026-04-04] 学习闭环

### 学了什么
- 领域：CSS `@layer` 级联层管理
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer
- 核心知识点：
  - `@layer name { rules }` 声明层，`@layer name1, name2, name3` 定义层顺序
  - 层顺序决定优先级：后声明的层覆盖先声明的层（normal 声明）
  - `!important` 优先级反转：层内 important > 层外 important
  - 层外声明 > 层内声明（normal），层内 important > 层外 important
  - 嵌套层：`@layer framework { @layer layout { } }`，用 `framework.layout` 引用
  - 第三方库集成：把第三方样式放 `@layer third-party`，自定义放 `@layer custom`，确保自定义永远覆盖
  - 浏览器支持：Chrome 99+、Safari 15.4+、Firefox 97+

### 有用吗？
- 价值评级：🟡
- 理由：解决 CSS specificity 战争的终极方案。对于 nannan-dashboard 这种集成第三方组件库的项目，用 `@layer` 可以确保自定义样式永远覆盖第三方样式，无需 `!important` 或高特异性选择器。

### 用在哪？
- 具体场景：第三方组件库样式覆盖、设计系统基础样式管理、多团队协作样式优先级控制
- 预期改善：消除 `!important`，减少特异性竞争，样式代码更清晰可维护

### 实际效果
- （待回填）

---

## [2026-04-04] 学习闭环

### 学了什么
- 领域：CSS `@layer` 级联层管理
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer
- 核心知识点：
  - `@layer name` 声明层，`@layer name { rules }` 定义层内容
  - 层顺序决定优先级：后声明的层覆盖前面的层（normal 声明）
  - `!important` 在层内优先级反转
  - 未分层的样式永远优先于层内样式
  - 嵌套层：`@layer framework { @layer layout { } }`，用 `framework.layout` 引用
  - 与 `@scope` 配合：`@layer` 控制全局优先级，`@scope` 控制局部隔离
  - 浏览器支持：Chrome 99+、Safari 15.4+、Firefox 97+

### 有用吗？
- 价值评级：🟡
- 理由：解决 CSS specificity 战争的终极方案。对于大型项目、第三方库集成、设计系统非常有用。但在 Tailwind 项目中价值有限（原子化 CSS 已解决优先级问题）。

### 用在哪？
- 具体场景：第三方库样式覆盖、设计系统主题层、组件库优先级管理
- 预期改善：消除 `!important` 滥用，样式优先级可预测，维护成本降低

### 实际效果
- （待回填）
---

## [2026-04-05] 学习闭环

### 学了什么
- 领域：CSS `light-dark()` 函数（自动主题色切换）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/light-dark
- 核心知识点：
  - `color: light-dark(#000, #fff)` — 浅色模式用黑色，深色模式用白色
  - 自动检测系统/浏览器主题偏好，无需 `@media (prefers-color-scheme)`
  - 可配合 `color-scheme: light dark` 声明支持的主题
  - 与 `accent-color` 配合实现完整原生主题适配
  - 浏览器支持：Chrome 119+、Safari 17.4+、Firefox 123+（2024 年 5 月起）

### 有用吗？
- 价值评级：🔴
- 理由：一行 CSS 替代整个 `@media (prefers-color-scheme)` 媒体查询块。nannan-dashboard 的深色模式切换可大幅简化，无需 JS 监听主题变化。

### 用在哪？
- 具体场景：主题色切换、深色模式适配、自动对比度调整
- 预期改善：减少主题切换代码量 80%+，无需 JS 监听，自动适配系统偏好

### 实际效果
- （待回填）

---

## [2026-04-05] 学习闭环

### 学了什么
- 领域：CSS `field-sizing: content`（自动适配内容的表单控件）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/field-sizing
- 核心知识点：
  - `field-sizing: content` — textarea/input 自动根据内容高度调整
  - 替代 JS 实现的 auto-growing textarea
  - 达到最大尺寸后自动出现滚动条
  - 适用元素：`<textarea>`, `<input type="text/email/password/search/url/tel">`
  - 浏览器支持：Chrome 123+、Safari 17.4+、Firefox 128+

### 有用吗？
- 价值评级：🔴
- 理由：一行 CSS 替代整个 JS auto-resize textarea 方案。nannan-dashboard 的表单输入体验可大幅简化，无需监听 input 事件手动调整高度。

### 用在哪？
- 具体场景：多行文本输入框、评论框、备注字段
- 预期改善：减少 JS 代码，提升用户体验（无闪烁），更好的无障碍支持

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS Subgrid（嵌套网格继承）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Subgrid
- 核心知识点：
  - `grid-template-columns: subgrid` — 子网格继承父网格轨道
  - `grid-template-rows: subgrid` — 子网格继承父网格行轨道
  - 解决嵌套网格对齐问题：卡片内容跨卡片对齐
  - Gap 默认继承，可单独覆盖
  - 支持 line names 继承
  - 浏览器支持：Chrome 117+、Safari 16+、Firefox 70+

### 有用吗？
- 价值评级：🟡
- 理由：解决卡片布局中内容对齐的经典问题。以前要用 JS 测量或固定高度，现在纯 CSS 实现跨卡片对齐。nannan-dashboard 的卡片列表可用。

### 用在哪？
- 具体场景：卡片列表（标题/内容/按钮跨卡片对齐）、表单网格、复杂布局
- 预期改善：消除 JS 测量代码，布局更稳健，响应式更简单

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：Intersection Observer API（滚动视口检测）
- 来源：https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API
- 核心知识点：
  - `new IntersectionObserver(callback, options)` 异步检测元素可见性
  - `threshold: [0, 0.5, 1]` 设置触发阈值（0=进入视口，1=完全可见）
  - `rootMargin: '0px 0px -100px 0px'` 提前/延迟触发
  - 替代 scroll event + getBoundingClientRect 的性能方案
  - 在主线程外运行，避免 jank
  - 应用场景：懒加载图片、无限滚动、广告可见性统计、滚动触发动画
  - 浏览器支持：Chrome 51+、Safari 12.1+、Firefox 55+

### 有用吗？
- 价值评级：🟡
- 理由：滚动交互的标准方案。nannan-dashboard 的图片懒加载、卡片进入视口动画都能用。但已有 CSS Scroll-Driven Animations 可替代部分场景（纯 CSS 更优）。

### 用在哪？
- 具体场景：图片懒加载、滚动触发动画、无限滚动列表
- 预期改善：减少 scroll event 监听，提升滚动性能

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS Nesting（原生嵌套语法）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Nesting/Using
- 核心知识点：
  - `.parent { .child { } }` — 原生嵌套，无需 Sass/Less
  - `&` 选择器：`.parent { &.active { } }` = `.parent.active`
  - 组合选择器：`.parent { & > .child { } }` = `.parent > .child`
  - 伪类嵌套：`.btn { &:hover { } }` = `.btn:hover`
  - 媒体查询嵌套：`.card { @media (min-width: 768px) { } }`
  - 浏览器支持：Chrome 112+、Safari 17.2+、Firefox 117+

### 有用吗？
- 价值评级：🟡
- 理由：消除对 Sass/Less 嵌套语法的依赖，但功能相对基础（无 mixin/函数）。对于 nannan-dashboard 使用 Tailwind 的场景价值有限，但在传统 CSS 项目中可提升代码可读性。

### 用在哪？
- 具体场景：组件样式编写、传统 CSS 项目、减少预处理器依赖
- 预期改善：减少构建步骤，CSS 代码更直观，嵌套层级清晰

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS Subgrid（嵌套网格继承）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Subgrid
- 核心知识点：
  - `grid-template-columns: subgrid` — 子网格继承父网格的列轨道
  - `grid-template-rows: subgrid` — 子网格继承父网格的行轨道
  - 解决嵌套网格对齐问题：无需手动同步轨道尺寸
  - 间隙（gap）默认继承，可单独覆盖
  - 支持传递行/列线名称（line names）
  - 浏览器支持：Chrome 117+、Safari 16+、Firefox 89+

### 有用吗？
- 价值评级：🟡
- 理由：解决 Grid 布局的遗留痛点 — 嵌套网格无法对齐父网格轨道。对于复杂卡片布局、表单网格、Dashboard 组件非常有用。但在简单布局场景中价值有限。

### 用在哪？
- 具体场景：Dashboard 卡片网格、表单字段对齐、复杂组件布局
- 预期改善：消除手动同步轨道尺寸的代码，布局更简洁，对齐更精准

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS `will-change` 性能优化提示
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/will-change
- 核心知识点：
  - `will-change: transform, opacity` 提示浏览器提前优化
  - 浏览器会创建独立合成层（compositor layer）
  - ⚠️ 警告：仅作为最后手段，不要用于"预防性"优化
  - 不要对太多元素使用（占用大量内存）
  - 动画完成后移除 `will-change`（用 JS 或 animationend 事件）
  - Baseline: 2020 年 1 月起广泛支持

### 有用吗？
- 价值评级：🟡
- 理由：动画性能优化的重要工具，但滥用会导致内存问题。在 css-animation-toolkit skill 中已覆盖最佳实践。nannan-dashboard 的复杂动画场景（如页面过渡、滚动动画）可受益。

### 用在哪？
- 具体场景：复杂 CSS 动画、滚动驱动动画、页面过渡效果
- 预期改善：动画帧率提升，减少 jank

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS `@property`（类型化自定义属性）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@property
- 核心知识点：
  - `@property --name { syntax: "<type>"; inherits: bool; initial-value: val; }` 注册类型化 CSS 变量
  - syntax 类型：`<color>`, `<length>`, `<percentage>`, `<angle>`, `<time>`, `<number>`, `*`(任意)
  - **核心突破**：没有 @property 时，`transition: --bg-color 0.3s` 不生效（值跳变）；注册后可平滑过渡！
  - 可继承控制：`inherits: true/false`
  - 初值设定：`initial-value: <value>`
  - 浏览器支持：Chrome 85+、Safari 15.4+、Firefox 120+

### 有用吗？
- 价值评级：🔴
- 理由：解锁 CSS 变量动画！以前要实现渐变动画要用 JS 或复杂 hack，现在纯 CSS 实现。nannan-dashboard 的主题色过渡、按钮悬停渐变都能用。

### 用在哪？
- 具体场景：渐变背景动画、主题色平滑过渡、旋转动画、自定义缓动
- 预期改善：减少 JS 动画依赖，性能更好，代码更简洁

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS `field-sizing: content`（自动适配内容的表单控件）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/field-sizing
- 核心知识点：
  - `field-sizing: content` — 表单控件（input/textarea）自动根据内容调整高度
  - 替代 JS 的 textarea 自动增高方案
  - 达到最大尺寸后自动滚动
  - 适用元素：input[email/number/password/search/tel/text/url]、textarea
  - 浏览器支持：Chrome 123+、Safari 17.4+、Firefox 128+

### 有用吗？
- 价值评级：🔴
- 理由：一行 CSS 替代整套 JS 自动增高逻辑。nannan-dashboard 的表单输入体验可大幅提升，无需监听 input 事件手动调整高度。

### 用在哪？
- 具体场景：多行文本输入、评论框、备注字段
- 预期改善：减少 JS 代码，提升性能，用户体验更流畅

### 实际效果
- （待回填）

---

## [2026-04-06] 学习闭环

### 学了什么
- 领域：CSS `interpolate-size: allow-keywords`（动画 intrinsic size）
- 来源：https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/interpolate-size
- 核心知识点：
  - `interpolate-size: allow-keywords` — 允许动画 `height: 0` → `height: auto`
  - 解决 CSS 最古老的痛点：无法过渡到 intrinsic size
  - 可动画值：`fit-content`, `max-content`, `min-content`, `auto`
  - 实验性特性，需检查浏览器支持
  - 浏览器支持：Chrome 131+（实验性）

### 有用吗？
- 价值评级：🔴
- 理由：解决手风琴/展开动画的终极方案！以前要用 `max-height` hack 或 JS 测量，现在纯 CSS 实现平滑展开/收起。

### 用在哪？
- 具体场景：手风琴菜单、展开/收起卡片、下拉面板
- 预期改善：消除 max-height hack，动画更精确，代码更简洁

### 实际效果
- （待回填）
