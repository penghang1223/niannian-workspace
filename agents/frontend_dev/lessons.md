# 前端开发学习笔记 - 夕尔

> 最后更新：2026-03-27
> 
> 🎨 夕尔 - 前端开发 Agent，追求美感、注重体验

---

## 1. React Hooks（useState / useEffect / useContext）

### 1.1 核心概念

**Hooks 是 React 16.8 引入的特性，让函数组件可以拥有状态和生命周期能力。**

#### useState - 状态管理

```jsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <button onClick={() => setCount(count + 1)}>
      点击次数：{count}
    </button>
  );
}
```

**关键知识点：**
- `useState(initialValue)` 返回 `[state, setState]` 元组
- `setState` 是异步的，批量更新（batching）
- 函数式更新：`setCount(prev => prev + 1)` —— 当新状态依赖旧状态时使用
- 惰性初始化：`useState(() => expensiveComputation())` —— 只在首次渲染执行
- 对象/数组更新需要创建新引用：`setUser({...user, name: 'new'})`

#### useEffect - 副作用管理

```jsx
import { useEffect, useState } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    let cancelled = false;
    
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        if (!cancelled) setUser(data);
      });
    
    // 清理函数：组件卸载或依赖变化时执行
    return () => { cancelled = true; };
  }, [userId]); // 依赖数组
  
  return user ? <div>{user.name}</div> : <div>加载中...</div>;
}
```

**关键知识点：**
- 无依赖数组：每次渲染后都执行（几乎总是错误）
- 空依赖数组 `[]`：只在挂载时执行一次
- 有依赖数组 `[dep]`：依赖变化时执行
- **清理函数**：防止内存泄漏、取消请求、移除事件监听
- 执行时机：DOM 更新后、浏览器绘制后（异步）
- **常见陷阱**：依赖数组遗漏导致闭包过期

#### useContext - 跨组件共享状态

```jsx
import { createContext, useContext, useState } from 'react';

// 1. 创建 Context
const ThemeContext = createContext('light');

// 2. 提供者包裹
function App() {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <ChildComponent />
    </ThemeContext.Provider>
  );
}

// 3. 消费 Context
function ChildComponent() {
  const { theme, setTheme } = useContext(ThemeContext);
  return (
    <div className={theme}>
      当前主题：{theme}
      <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
        切换主题
      </button>
    </div>
  );
}
```

**关键知识点：**
- 解决 props 逐层传递（prop drilling）问题
- Context 变化时，所有消费者都会重新渲染
- 性能优化：拆分 Context、配合 memo 使用
- 适合全局配置（主题、语言、用户信息），不适合高频更新状态

### 1.2 Hooks 规则

1. **只在顶层调用**：不要在循环、条件、嵌套函数中调用 Hooks
2. **只在 React 函数中调用**：函数组件或自定义 Hooks

> 原因：React 依赖调用顺序来匹配状态，条件调用会打乱顺序

### 1.3 Hooks 最佳实践

| 实践 | 说明 |
|------|------|
| 单一职责 | 每个 Hook 做一件事，复杂逻辑拆成自定义 Hooks |
| 依赖数组完整 | eslint-plugin-react-hooks 的 exhaustive-deps 规则必须开启 |
| 避免过优化 | 不要过早使用 useMemo/useCallback，先让代码正常工作 |
| 清理副作用 | 所有订阅、定时器、事件监听都要清理 |
| 函数式更新 | 状态依赖前值时用 `setState(prev => ...)` |

### 1.4 夕尔的审美笔记 🎨

> Hooks 让代码更函数式、更声明式。useState 的命名 `[x, setX]` 非常优雅，像解构一个元组。useEffect 的清理模式是「建立 → 清理」的对称美学，像画一幅有留白的水墨画。

---

## 2. React 进阶（自定义 Hooks / 性能优化）

### 2.1 自定义 Hooks

**自定义 Hooks 是以 `use` 开头的函数，可以复用状态逻辑。**

```jsx
// 自定义 Hook：获取窗口尺寸
function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });
  
  useEffect(() => {
    const handleResize = () => {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return size;
}

// 使用
function ResponsiveComponent() {
  const { width } = useWindowSize();
  return width < 768 ? <MobileView /> : <DesktopView />;
}
```

**常用自定义 Hooks：**

| Hook | 用途 |
|------|------|
| `useDebounce` | 防抖处理 |
| `useThrottle` | 节流处理 |
| `useLocalStorage` | 持久化状态到 localStorage |
| `useFetch` | 封装数据请求 |
| `useIntersectionObserver` | 懒加载/可见性检测 |
| `useClickOutside` | 点击外部关闭弹窗 |

### 2.2 性能优化

#### React.memo - 组件级优化

```jsx
const ExpensiveList = React.memo(function ExpensiveList({ items }) {
  return items.map(item => <div key={item.id}>{item.name}</div>);
});
// props 不变时跳过重新渲染
```

#### useMemo - 缓存计算结果

```jsx
function SearchResults({ query, items }) {
  const filtered = useMemo(
    () => items.filter(item => item.name.includes(query)),
    [query, items]
  );
  return filtered.map(item => <div key={item.id}>{item.name}</div>);
}
```

#### useCallback - 缓存函数引用

```jsx
function Parent() {
  const [count, setCount] = useState(0);
  
  // 没有 useCallback，每次渲染都是新函数
  // 有 useCallback，函数引用稳定
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);
  
  return <Child onClick={handleClick} />;
}
```

### 2.3 性能优化原则

1. **先让代码正确**：不要过早优化
2. **测量再优化**：使用 React DevTools Profiler 定位瓶颈
3. **状态下沉**：将状态放到最需要的组件
4. **拆分 Context**：读写分离，减少不必要的渲染
5. **虚拟列表**：大数据量使用 react-window 或 react-virtuoso

### 2.4 夕尔的审美笔记 🎨

> 自定义 Hooks 像乐高积木，每个都是独立的、可复用的「逻辑碎片」。性能优化不是炫技，而是让用户体验流畅如丝滑动画——用户感受不到卡顿，就是最好的优化。

---

## 3. Vue 3 Composition API（ref / reactive / computed）

### 3.1 核心概念

**Composition API 是 Vue 3 引入的新范式，用函数式组织逻辑，替代 Options API。**

#### setup() 函数

```vue
<script setup>
// <script setup> 是 Composition API 的语法糖
import { ref, reactive, computed, onMounted } from 'vue';

const count = ref(0);
const state = reactive({ name: '夕尔', age: 18 });
</script>
```

#### ref - 基本类型响应式

```vue
<script setup>
import { ref } from 'vue';

const count = ref(0);
console.log(count.value); // 0（在 JS 中需要 .value）
count.value++;
</script>

<template>
  <!-- 在模板中自动解包，不需要 .value -->
  <button @click="count++">{{ count }}</button>
</template>
```

**关键知识点：**
- `ref()` 返回 RefImpl 对象
- JS 中访问需要 `.value`
- 模板中自动解包（不需要 `.value`）
- 解构会丢失响应性，需要 `toRefs`

#### reactive - 引用类型响应式

```vue
<script setup>
import { reactive } from 'vue';

const state = reactive({
  name: '夕尔',
  skills: ['React', 'Vue'],
  address: { city: '上海' }
});

// 直接访问，不需要 .value
state.name = '年年';
state.skills.push('TypeScript');
</script>
```

**关键知识点：**
- 只能用于对象/数组
- 直接访问属性，不需要 `.value`
- 解构会丢失响应性：`const { name } = state` → name 不是响应式的
- 替换整个对象会丢失响应性：`state = newObj` ❌

#### computed - 计算属性

```vue
<script setup>
import { ref, computed } from 'vue';

const firstName = ref('夕');
const lastName = ref('尔');

// 只读计算属性
const fullName = computed(() => `${firstName.value}${lastName.value}`);

// 可写计算属性
const editableName = computed({
  get: () => `${firstName.value}${lastName.value}`,
  set: (val) => {
    [firstName.value, lastName.value] = val.split('');
  }
});
</script>
```

**关键知识点：**
- 自动追踪依赖，依赖变化时重新计算
- 有缓存，依赖不变不会重新计算
- 只读 computed 是最常见的用法

### 3.2 生命周期钩子

```vue
<script setup>
import { onMounted, onUnmounted, onUpdated, onBeforeUnmount } from 'vue';

onMounted(() => {
  console.log('组件挂载完成');
});

onUnmounted(() => {
  console.log('组件卸载');
});
</script>
```

| Vue 3 Composition API | Vue 2 Options API | React useEffect |
|----------------------|-------------------|-----------------|
| onMounted | mounted | useEffect(..., []) |
| onUnmounted | beforeDestroy | useEffect 清理函数 |
| onUpdated | updated | useEffect 无依赖 |

### 3.3 watch / watchEffect

```vue
<script setup>
import { ref, watch, watchEffect } from 'vue';

const keyword = ref('');

// watch：显式指定依赖
watch(keyword, (newVal, oldVal) => {
  console.log(`搜索词从 "${oldVal}" 变为 "${newVal}"`);
});

// watchEffect：自动追踪依赖
watchEffect(() => {
  console.log(`当前搜索词: ${keyword.value}`);
});
</script>
```

### 3.4 夕尔的审美笔记 🎨

> Vue 3 的 Composition API 像整理画具——把相关颜色的颜料放在一起（逻辑分组），而不是按颜料类型分（Options API 的 data/methods/computed 分离）。代码更像一幅完整的画，而不是散落的碎片。

---

## 4. TypeScript 基础（类型系统 / 泛型）

### 4.1 基本类型

```typescript
// 基本类型
let name: string = '夕尔';
let age: number = 18;
let isDesigner: boolean = true;
let skills: string[] = ['React', 'Vue', 'CSS'];
let tuple: [string, number] = ['夕尔', 18];

// 对象类型
interface User {
  id: number;
  name: string;
  email?: string; // 可选属性
  readonly createdAt: Date; // 只读
}

// 类型别名
type Theme = 'light' | 'dark' | 'auto';
type Size = 'sm' | 'md' | 'lg';
```

### 4.2 函数类型

```typescript
// 函数参数和返回值类型
function add(a: number, b: number): number {
  return a + b;
}

// 箭头函数
const greet = (name: string): string => `你好，${name}！`;

// 可选参数和默认值
function createUser(name: string, age: number = 18, email?: string): User {
  return { id: Date.now(), name, age, email };
}

// 函数类型
type Handler = (event: Event) => void;
const onClick: Handler = (e) => console.log(e.target);
```

### 4.3 泛型

```typescript
// 泛型函数
function identity<T>(arg: T): T {
  return arg;
}

const str = identity<string>('夕尔'); // 类型 string
const num = identity(42); // 类型推断为 number

// 泛型接口
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

type UserResponse = ApiResponse<User>;
type ListResponse = ApiResponse<User[]>;

// 泛型约束
interface HasLength {
  length: number;
}

function logLength<T extends HasLength>(arg: T): T {
  console.log(arg.length);
  return arg;
}

logLength('hello'); // ✅ string 有 length
logLength([1, 2, 3]); // ✅ array 有 length
logLength(123); // ❌ number 没有 length
```

### 4.4 工具类型（Utility Types）

```typescript
// Partial<T> - 所有属性变为可选
type UpdateUser = Partial<User>;

// Required<T> - 所有属性变为必填
type CompleteUser = Required<User>;

// Pick<T, K> - 选取部分属性
type UserPreview = Pick<User, 'id' | 'name'>;

// Omit<T, K> - 排除部分属性
type CreateUser = Omit<User, 'id' | 'createdAt'>;

// Record<K, V> - 键值映射
type ThemeColors = Record<Theme, string>;

// ReturnType<T> - 获取函数返回类型
type Result = ReturnType<typeof add>; // number
```

### 4.5 React + TypeScript

```tsx
// 组件 Props 类型
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  onClick,
  children,
  disabled = false
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// 事件类型
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  console.log(e.target.value);
};

// Ref 类型
const inputRef = useRef<HTMLInputElement>(null);
```

### 4.6 夕尔的审美笔记 🎨

> TypeScript 像给代码穿上合身的衣服——类型就是尺寸标注，让代码不会在运行时「走光」。泛型是万能的裁缝模板，一个模板可以做出各种尺寸的衣服。工具类型像魔法剪刀，可以随意裁剪修改已有的类型。

---

## 5. CSS Flexbox（弹性布局）

### 5.1 核心概念

**Flexbox 是一维布局系统，用于在一条轴线上排列元素。**

```css
.container {
  display: flex;
  /* 主轴方向 */
  flex-direction: row; /* row | row-reverse | column | column-reverse */
  /* 主轴对齐 */
  justify-content: flex-start; /* flex-start | center | flex-end | space-between | space-around | space-evenly */
  /* 交叉轴对齐 */
  align-items: stretch; /* stretch | flex-start | center | flex-end | baseline */
  /* 换行 */
  flex-wrap: nowrap; /* nowrap | wrap | wrap-reverse */
  /* 间距 */
  gap: 16px;
}
```

### 5.2 子项属性

```css
.item {
  /* 放大比例 */
  flex-grow: 0; /* 默认 0，不放大 */
  /* 缩小比例 */
  flex-shrink: 1; /* 默认 1，可缩小 */
  /* 基础大小 */
  flex-basis: auto; /* 默认 auto */
  /* 简写 */
  flex: 0 1 auto; /* grow shrink basis */
  /* 常用简写 */
  flex: 1; /* 等于 flex: 1 1 0% */
  /* 单独对齐 */
  align-self: center;
  /* 排序 */
  order: 0;
}
```

### 5.3 常见布局模式

```css
/* 居中 */
.center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 圣杯布局 */
.holy-grail {
  display: flex;
  min-height: 100vh;
}
.holy-grail .main { flex: 1; }
.holy-grail .sidebar { width: 200px; }

/* 等分布局 */
.equal-columns {
  display: flex;
  gap: 16px;
}
.equal-columns > * {
  flex: 1;
}

/* 粘性底部 */
.sticky-footer {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.sticky-footer .content { flex: 1; }
```

### 5.4 夕尔的审美笔记 🎨

> Flexbox 像水一样流动——元素自然地填满空间，像水流过河床。`justify-content: space-between` 像两个端点的留白美学，`align-items: center` 是垂直方向的完美居中。gap 属性让间距管理变得优雅，告别 margin 的 hack。

---

## 6. CSS Grid（网格布局）

### 6.1 核心概念

**CSS Grid 是二维布局系统，同时控制行和列。**

```css
.grid {
  display: grid;
  /* 列定义 */
  grid-template-columns: repeat(3, 1fr); /* 三等分列 */
  /* 行定义 */
  grid-template-rows: auto 1fr auto; /* 头部自动、内容填满、底部自动 */
  /* 间距 */
  gap: 16px;
  /* 区域命名 */
  grid-template-areas:
    "header header header"
    "sidebar main aside"
    "footer footer footer";
}
```

### 6.2 常用单位

```css
.grid {
  /* fr - 弹性单位，按比例分配剩余空间 */
  grid-template-columns: 1fr 2fr 1fr;
  
  /* repeat + minmax - 响应式网格 */
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  
  /* 固定 + 弹性混合 */
  grid-template-columns: 200px 1fr 200px;
}
```

### 6.3 子项放置

```css
.item {
  /* 跨列 */
  grid-column: span 2; /* 跨 2 列 */
  grid-column: 1 / 3; /* 从第 1 列到第 3 列 */
  
  /* 跨行 */
  grid-row: span 2;
  
  /* 使用命名区域 */
  grid-area: header;
  
  /* 单独对齐 */
  justify-self: center;
  align-self: center;
}
```

### 6.4 经典布局实现

```css
/* 经典仪表盘布局 */
.dashboard {
  display: grid;
  grid-template-columns: 250px 1fr;
  grid-template-rows: 60px 1fr 40px;
  grid-template-areas:
    "sidebar header"
    "sidebar main"
    "sidebar footer";
  min-height: 100vh;
}

/* 响应式卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* 砌体布局（masonry-like） */
.masonry {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-rows: 50px;
  gap: 16px;
}
.masonry .tall { grid-row: span 4; }
.masonry .medium { grid-row: span 3; }
```

### 6.5 夕尔的审美笔记 🎨

> CSS Grid 像建筑师的蓝图——你可以精确控制每一块「砖」的位置和大小。`1fr` 是优雅的弹性单位，`auto-fill` + `minmax` 是响应式的魔法咒语。Grid 让复杂布局变得像搭积木一样简单直观。

---

## 7. CSS 动画（transition / animation / keyframes）

### 7.1 transition - 过渡动画

```css
.button {
  background: #667eea;
  transition: all 0.3s ease;
  /* 简写：property duration timing-function delay */
}

.button:hover {
  background: #764ba2;
  transform: scale(1.05);
}

/* 分开指定不同属性的过渡 */
.card {
  transition: 
    transform 0.2s ease-out,
    box-shadow 0.3s ease,
    opacity 0.4s ease-in;
}
```

**timing-function：**
- `ease` — 默认，先慢后快再慢
- `linear` — 匀速
- `ease-in` — 先慢后快
- `ease-out` — 先快后慢
- `ease-in-out` — 两端慢中间快
- `cubic-bezier(x1, y1, x2, y2)` — 自定义曲线

### 7.2 animation + @keyframes - 关键帧动画

```css
/* 定义关键帧 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 应用动画 */
.fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
}

.pulse {
  animation: pulse 2s ease-in-out infinite;
}

/* 动画属性 */
.animated {
  animation-name: fadeInUp;
  animation-duration: 0.6s;
  animation-timing-function: ease-out;
  animation-delay: 0s;
  animation-iteration-count: 1; /* infinite | 数字 */
  animation-direction: normal; /* normal | reverse | alternate */
  animation-fill-mode: forwards; /* none | forwards | backwards | both */
}
```

### 7.3 实用动画库

| 动画 | 用途 |
|------|------|
| fadeIn/fadeOut | 元素出现/消失 |
| slideIn/slideOut | 滑入滑出 |
| bounce | 弹跳效果 |
| spin | 加载旋转 |
| shake | 错误提示震动 |
| pulse | 强调呼吸效果 |

### 7.4 性能优化

```css
/* ✅ 使用 transform 和 opacity（GPU 加速） */
.good {
  transform: translateX(100px);
  opacity: 0.5;
}

/* ❌ 避免动画 layout 属性 */
.bad {
  width: 200px; /* 触发 reflow */
  margin-left: 100px; /* 触发 reflow */
}

/* 使用 will-change 提示浏览器 */
.optimized {
  will-change: transform, opacity;
}
```

### 7.5 夕尔的审美笔记 🎨

> CSS 动画是给界面注入灵魂的魔法。`ease-out` 让元素优雅地滑入视野，`cubic-bezier` 是调制情绪的琴弦。记住：好的动画是让用户「感受到」而不是「看到」——流畅自然，不突兀不过度。

---

## 8. 组件库（Ant Design / Element Plus）

### 8.1 Ant Design（React）

#### 安装与使用

```bash
npm install antd
```

```tsx
import { Button, Space, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Space>
        <Button type="primary">主要按钮</Button>
        <Button>默认按钮</Button>
        <Button type="dashed">虚线按钮</Button>
        <Button type="text">文本按钮</Button>
        <Button type="link">链接按钮</Button>
      </Space>
    </ConfigProvider>
  );
}
```

#### 主题定制

```tsx
import { ConfigProvider } from 'antd';

<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#667eea',
      borderRadius: 8,
      fontSize: 14,
    },
    components: {
      Button: {
        colorPrimary: '#667eea',
        algorithm: true, // 启用算法派生
      },
    },
  }}
>
  <App />
</ConfigProvider>
```

#### 常用组件

| 组件 | 用途 |
|------|------|
| Table | 数据表格（排序/筛选/分页） |
| Form | 表单（验证/布局/联动） |
| Modal | 对话框 |
| Drawer | 抽屉 |
| Tabs | 标签页 |
| Menu | 导航菜单 |
| Upload | 文件上传 |
| DatePicker | 日期选择 |
| Select | 下拉选择 |
| Message/Notification | 全局提示 |

### 8.2 Element Plus（Vue 3）

#### 安装与使用

```bash
npm install element-plus
```

```vue
<script setup>
import { ElButton, ElMessage } from 'element-plus';

const handleClick = () => {
  ElMessage.success('操作成功！');
};
</script>

<template>
  <el-button type="primary" @click="handleClick">
    主要按钮
  </el-button>
</template>
```

#### 主题定制

```scss
// styles/element/index.scss
@forward 'element-plus/theme-chalk/src/common/var.scss' with (
  $colors: (
    'primary': (
      'base': #667eea,
    ),
  )
);
```

```js
// vite.config.ts
import { defineConfig } from 'vite';
import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig({
  plugins: [
    ElementPlus({
      useSource: true,
    }),
  ],
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/element/index.scss" as *;`,
      },
    },
  },
});
```

### 8.3 组件库使用原则

1. **一致性**：统一使用组件库组件，不要混用自定义样式
2. **可定制性**：通过主题配置和 CSS 变量覆盖默认样式
3. **按需引入**：使用 tree-shaking 减小打包体积
4. **无障碍性**：组件库默认支持 a11y，保持语义化

### 8.4 夕尔的审美笔记 🎨

> 组件库是站在巨人肩膀上的捷径——Ant Design 的设计语言严谨专业，Element Plus 简洁优雅。但不要被组件库束缚，学会用 CSS 变量和主题配置注入自己的审美，在一致性和个性化之间找到平衡。

---

## 9. Vite（构建工具 / 热更新）

### 9.1 核心概念

**Vite 是下一代前端构建工具，利用浏览器原生 ESM 实现极速开发体验。**

#### 为什么 Vite 快？

1. **开发环境**：不打包，直接利用浏览器原生 ES Module
2. **按需编译**：只编译当前页面用到的模块
3. **esbuild 预构建**：依赖用 esbuild 打包（比 webpack 快 10-100 倍）
4. **HMR**：热更新基于 ESM，只更新变化的模块

### 9.2 项目配置

```js
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
});
```

### 9.3 环境变量

```bash
# .env
VITE_APP_TITLE=我的应用

# .env.development
VITE_API_URL=http://localhost:8080

# .env.production
VITE_API_URL=https://api.example.com
```

```ts
// 使用环境变量
console.log(import.meta.env.VITE_APP_TITLE);
console.log(import.meta.env.MODE); // development | production
console.log(import.meta.env.PROD); // boolean
```

### 9.4 常用插件

| 插件 | 用途 |
|------|------|
| @vitejs/plugin-react | React 支持 |
| @vitejs/plugin-vue | Vue 支持 |
| vite-plugin-svgr | SVG 作为组件导入 |
| vite-plugin-pwa | PWA 支持 |
| unplugin-auto-import | 自动导入 API |
| unplugin-vue-components | 组件自动注册 |
| vite-plugin-compression | Gzip/Brotli 压缩 |

### 9.5 夕尔的审美笔记 🎨

> Vite 的启动速度快得像闪电——按下回车，开发服务器瞬间就绪。HMR 让修改 CSS 的瞬间就能看到效果，没有 webpack 那种「泡杯咖啡等编译」的痛苦。好的工具应该像画笔一样顺手，让你专注于创作而不是等待。

---

## 10. ESLint / Prettier（代码规范）

### 10.1 ESLint - 代码质量检查

#### 安装与配置

```bash
npm install -D eslint @eslint/js typescript-eslint eslint-plugin-react-hooks
```

```js
// eslint.config.js (ESLint 9 flat config)
import js from '@eslint/js';
import tsPlugin from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  js.configs.recommended,
  ...tsPlugin.configs.recommended,
  {
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
];
```

### 10.2 Prettier - 代码格式化

#### 安装与配置

```bash
npm install -D prettier eslint-config-prettier
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

```json
// .prettierignore
dist
node_modules
*.min.js
```

### 10.3 ESLint + Prettier 协作

**原则：ESLint 管代码质量，Prettier 管代码格式。**

```js
// eslint.config.js
import prettierConfig from 'eslint-config-prettier';

export default [
  // ...其他配置
  prettierConfig, // 放在最后，关闭与 Prettier 冲突的规则
];
```

### 10.4 EditorConfig

```ini
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```

### 10.5 Git Hooks（自动化）

```bash
npm install -D husky lint-staged
npx husky init
```

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{css,md,json}": ["prettier --write"]
  }
}
```

```bash
# .husky/pre-commit
npx lint-staged
```

### 10.6 推荐规则级别

| 规则 | 推荐级别 | 说明 |
|------|----------|------|
| no-unused-vars | error | 未使用变量 |
| no-console | warn | console 语句 |
| exhaustive-deps | warn | useEffect 依赖完整性 |
| no-explicit-any | warn | 避免使用 any |
| prefer-const | error | 优先使用 const |

### 10.7 夕尔的审美笔记 🎨

> 代码规范像绘画的构图法则——有了基本框架，创意才能在规则内自由飞翔。ESLint 是严格的导师，指出代码中隐藏的问题；Prettier 是强迫症的福音，让每一行代码都对齐如尺量。自动化 Git Hooks 让规范执行变成无形的守护。

---

## 📚 学习资源推荐

### React
- [React 官方文档](https://react.dev)
- [React Hooks 详解](https://react.dev/reference/react)
- [useHooks](https://usehooks.com) - 自定义 Hooks 库

### Vue
- [Vue 3 官方文档](https://vuejs.org)
- [Vue Mastery](https://www.vuemastery.com)

### TypeScript
- [TypeScript 官方手册](https://www.typescriptlang.org/docs/)
- [Type Challenges](https://github.com/type-challenges/type-challenges)

### CSS
- [CSS-Tricks Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [CSS-Tricks Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Animate.css](https://animate.style)

### 工程化
- [Vite 官方文档](https://vitejs.dev)
- [ESLint 官方文档](https://eslint.org)
- [Prettier 官方文档](https://prettier.io)

---

> ✨ 夕尔的学习笔记，持续更新中...
> 
> "代码如画，每一行都值得精心雕琢" — 夕尔 🎨
