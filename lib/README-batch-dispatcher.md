# BatchDispatcher - 批量 Agent 调度框架

> 🛠️ 由玄机 (Karl) 设计实现，解决 Agent 串行调度效率问题。

## 问题背景

每次 `sessions_spawn` 一个 Agent 约需 1-5 分钟。当需要调度多个 Agent 且存在依赖关系时，串行执行会显著拖慢整体速度。**BatchDispatcher** 通过波次（Wave）机制实现并行调度，将总耗时从 **Σ(所有任务)** 降低到 **Σ(最慢波次)**。

## 核心概念

```
传统串行:  TaskA(3min) → TaskB(2min) → TaskC(4min) = 9min
波次并行:  Wave0[TaskA(3min), TaskD(1min)] → Wave1[TaskB(2min), TaskC(4min)] = 7min
```

- **Task（任务）**: 单个 Agent 调度单元，包含标签、Agent ID、任务内容
- **Wave（波次）**: 可并行执行的任务集合
- **依赖关系**: 任务间依赖自动推断波次划分

## 快速开始

### 基础用法

```typescript
import { BatchDispatcher } from './lib/batch-dispatcher';

const dispatcher = new BatchDispatcher({
  // 注入实际的 spawn 函数（OpenClaw sessions_spawn）
  spawnFn: async ({ agentId, task }) => {
    const session = await sessions_spawn({ agentId, task });
    return { result: session };
  },
  defaultTimeout: 300_000, // 5 分钟
});

// 添加任务
dispatcher
  .addTask('需求分析', 'product_manager', '请分析用户登录需求并输出 PRD')
  .addTask('技术调研', 'dev_engineer', '调研 OAuth2.0 实现方案')
  .addTask('API 设计', 'dev_engineer', '设计登录接口', { dependsOn: ['需求分析', '技术调研'] });

// 执行
const results = await dispatcher.execute();
console.log(results);
```

### 使用 addWave 添加并行波次

```typescript
dispatcher
  .addWave([
    { label: '前端', agentId: 'frontend_dev', task: '设计登录页面' },
    { label: '后端', agentId: 'dev_engineer', task: '实现登录接口' },
    { label: '测试', agentId: 'qa_engineer', task: '编写登录测试用例' },
  ])
  .addWave([
    { label: '联调', agentId: 'dev_engineer', task: '前后端联调' },
  ]);
```

### quickDispatch 快捷方式

```typescript
import { quickDispatch } from './lib/batch-dispatcher';

const results = await quickDispatch([
  { label: 'pm', agentId: 'product_manager', task: '需求分析' },
  { label: 'dev', agentId: 'dev_engineer', task: '技术方案', options: { dependsOn: ['pm'] } },
  { label: 'test', agentId: 'qa_engineer', task: '测试计划', options: { dependsOn: ['dev'] } },
], { spawnFn: mySpawnFn });
```

## API 参考

### BatchDispatcher

#### 构造函数

```typescript
new BatchDispatcher(config?: DispatcherConfig)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `defaultTimeout` | `number` | `300000` | 全局默认超时（毫秒） |
| `defaultMaxRetries` | `number` | `0` | 全局默认最大重试次数 |
| `defaultRetryDelay` | `number` | `2000` | 全局默认重试间隔（毫秒） |
| `stopOnWaveFailure` | `boolean` | `false` | 波次失败时停止后续 |
| `spawnFn` | `SpawnFunction` | - | **必须注入**实际 spawn 函数 |

#### 方法

##### `addTask(label, agentId, task, options?)`

添加单个任务。

```typescript
dispatcher.addTask(
  '标签',           // string - 任务唯一标识
  'agent_id',       // string - 目标 Agent ID
  '任务内容',        // string - 发送给 Agent 的任务描述
  {                 // TaskOptions - 可选
    timeout: 60000,
    maxRetries: 2,
    retryDelay: 3000,
    dependsOn: ['其他任务标签'],
    metadata: { key: 'value' },
  }
);
```

##### `addWave(tasks[])`

添加一波并行任务。

```typescript
dispatcher.addWave([
  { label: 'A', agentId: 'agent1', task: 'task A' },
  { label: 'B', agentId: 'agent2', task: 'task B' },
]);
```

##### `execute(): Promise<WaveResult[]>`

按波次顺序执行。同波次内任务并行，波次间串行。

##### `onComplete(callback)`

所有波次完成后触发。

```typescript
dispatcher.onComplete((results) => {
  console.log('全部完成', results);
});
```

##### `onWaveComplete(callback, waveIndex?)`

波次完成时触发。指定 `waveIndex` 则只监听该波次。

```typescript
dispatcher.onWaveComplete((result, waveIndex) => {
  console.log(`波次 ${waveIndex} 完成`, result);
});
```

##### `onProgress(callback)`

进度变更时触发。

```typescript
dispatcher.onProgress((progress) => {
  console.log(`${progress.percentage}% (${progress.completed}/${progress.total})`);
});
```

##### `onTaskStatus(callback)`

任务状态变更时触发。

##### `getProgress(): DispatcherProgress`

获取当前进度快照。

##### `getTasks(): TaskDefinition[]`

获取所有任务定义。

##### `getTask(label): TaskDefinition | undefined`

获取指定任务。

##### `reset()`

清空所有任务和回调。

##### `removeTask(label)`

移除指定任务。

### 类型定义

```typescript
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'retrying';

interface TaskOptions {
  timeout?: number;       // 超时时间（毫秒）
  maxRetries?: number;    // 最大重试次数
  retryDelay?: number;    // 重试间隔（毫秒）
  dependsOn?: string[];   // 依赖的任务标签
  metadata?: Record<string, unknown>;
}

interface TaskResult {
  label: string;
  status: TaskStatus;
  result?: unknown;
  error?: Error;
  duration: number;
  retryCount: number;
}

interface WaveResult {
  waveIndex: number;
  tasks: TaskResult[];
  duration: number;
  success: boolean;
}

interface DispatcherProgress {
  total: number;
  completed: number;
  failed: number;
  running: number;
  currentWave: number;
  totalWaves: number;
  percentage: number;
}
```

## 典型场景

### 场景 1: 需求 → 设计 → 开发 → 测试

```typescript
const results = await quickDispatch([
  { label: 'prd', agentId: 'product_manager', task: '撰写用户管理模块 PRD' },
  { label: 'api', agentId: 'dev_engineer', task: '设计 REST API', options: { dependsOn: ['prd'] } },
  { label: 'ui', agentId: 'frontend_dev', task: '设计 UI 原型', options: { dependsOn: ['prd'] } },
  { label: 'backend', agentId: 'dev_engineer', task: '实现后端接口', options: { dependsOn: ['api'] } },
  { label: 'frontend', agentId: 'frontend_dev', task: '实现前端页面', options: { dependsOn: ['ui', 'api'] } },
  { label: 'test', agentId: 'qa_engineer', task: '执行测试', options: { dependsOn: ['backend', 'frontend'] } },
], { spawnFn: mySpawnFn });
```

波次划分:
```
Wave 0: [prd]
Wave 1: [api, ui]        ← 并行
Wave 2: [backend, frontend] ← 并行
Wave 3: [test]
```

### 场景 2: 批量数据处理

```typescript
const dispatcher = new BatchDispatcher({ spawnFn: mySpawnFn });

// 每 10 个任务一波
for (let i = 0; i < 100; i += 10) {
  const batch = Array.from({ length: 10 }, (_, j) => ({
    label: `batch-${i + j}`,
    agentId: 'data_processor',
    task: `处理数据分片 ${i + j}`,
  }));
  dispatcher.addWave(batch);
}

dispatcher.onProgress(p => console.log(`${p.percentage}%`));
await dispatcher.execute();
```

### 场景 3: 带超时和重试的容错调度

```typescript
const dispatcher = new BatchDispatcher({
  spawnFn: mySpawnFn,
  defaultTimeout: 120_000,    // 2 分钟超时
  defaultMaxRetries: 2,       // 最多重试 2 次
  defaultRetryDelay: 5_000,   // 重试间隔 5 秒
  stopOnWaveFailure: true,    // 波次失败停止
});

dispatcher
  .addTask('critical', 'agent', '关键任务', { maxRetries: 5 }) // 该任务重试 5 次
  .addTask('normal', 'agent', '普通任务');
```

## 运行测试

```bash
# Node.js 内置 test runner
node --test lib/batch-dispatcher.test.ts

# 或用 tsx
npx tsx --test lib/batch-dispatcher.test.ts
```

## 设计决策

| 决策 | 理由 |
|------|------|
| 波次机制而非纯并行 | 支持依赖关系，避免手动管理执行顺序 |
| 回调而非事件发射器 | 简单场景不需要事件系统，回调更直接 |
| 注入 spawnFn | 解耦测试，生产环境注入真实 `sessions_spawn` |
| 依赖自动推断波次 | 用户只需声明依赖，框架自动优化并行度 |
| 默认不重试 | 明确需求，避免隐藏的重试风暴 |

## 注意事项

- ⚠️ `spawnFn` 必须在构造函数中注入，否则使用的是无意义的默认实现
- ⚠️ 依赖关系中引用不存在的任务标签会被忽略（静默跳过）
- ⚠️ 循环依赖会将涉及的任务全部放入最后一个波次
- ⚠️ 执行中（`execute()` 进行时）不能调用 `addTask` / `addWave` / `reset`

---

**版本**: 1.0.0  
**作者**: 玄机 (Karl) 🛠️  
**创建日期**: 2026-03-27
