# Dashboard v4.0 技术架构方案

> 太一 (Taiyi) · 首席架构师 · 2026-03-27

---

## 1. 技术栈选型

### 总览

| 层级 | 技术 | 理由 |
|------|------|------|
| **前端** | React 18 + Vite + TypeScript | 团队已用过 Vite(v3)，React 生态成熟、组件库丰富 |
| **UI 框架** | Ant Design 5 + Ant Design Charts | 开箱即用的管理面板组件 + 图表，暗色主题内置 |
| **后端** | Node.js 22 + Fastify | 比 Express 快 2-3x，原生 TypeScript 支持，轻量 |
| **数据库** | SQLite (better-sqlite3) | 零配置、单文件、ARM64 原生支持，13 Agent 规模绰绰有余 |
| **实时通信** | WebSocket (ws) | 双向通信，Agent 状态变更即时推送 |
| **状态采集** | OpenClaw CLI + 文件系统监听 | 读取 STATE.yaml、memory/*.md、sessions 状态 |
| **构建工具** | Vite 6 | HMR 快速开发，生产构建优化 |
| **包管理** | pnpm | 磁盘效率高，monorepo-ready |

### 为什么不选...

- **Next.js**: 过重，Dashboard 不需要 SSR，SPA 足够
- **PostgreSQL**: 13 个 Agent 的数据量用 SQLite 绑绑有余，零运维
- **Redis**: 不需要分布式缓存，单机部署
- **SSE**: WebSocket 更灵活，支持双向通信（未来可下发指令）

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器 (SPA)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Agent 看板 │ │ 任务看板  │ │ 数据可视化│ │ 系统设置  │  │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬─────┘  │
│        └────────────┼────────────┼────────────┘         │
│                     │   React    │                       │
│              ┌──────┴────────────┴──────┐                │
│              │   WebSocket + REST API   │                │
│              └──────────┬───────────────┘                │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP/WS (localhost:3456)
┌─────────────────────────┼───────────────────────────────┐
│              Dashboard Server (Fastify)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Agent    │ │  Task    │ │ Metrics  │ │ WebSocket │  │
│  │ Monitor  │ │ Manager  │ │ Collector│ │ Hub       │  │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬─────┘  │
│        │            │            │             │         │
│  ┌─────┴────────────┴────────────┴─────────────┴─────┐  │
│  │              Data Layer (SQLite)                   │  │
│  │  agents.db  ·  tasks.db  ·  metrics.db            │  │
│  └───────────────────────┬───────────────────────────┘  │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│           OpenClaw Runtime Environment                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │STATE.yaml│ │memory/  │ │sessions │ │ Agent        │  │
│  │ 文件监听 │ │*.md 监听│ │状态轮询 │ │ workspaces   │  │
│  └─────────┘ └─────────┘ └─────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 数据流向

1. **状态采集**: 定时读取 STATE.yaml + 监听文件变更 → 解析 Agent 状态
2. **实时推送**: Server 通过 WebSocket 广播状态变更 → 前端即时更新
3. **任务管理**: 前端操作 → REST API → 更新 STATE.yaml + SQLite
4. **指标聚合**: 按小时/天聚合 Agent 活跃度、任务完成率、响应时间

---

## 3. API 设计

### 3.1 Agent 管理

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/agents` | 获取所有 Agent 列表及状态 |
| GET | `/api/agents/:id` | 获取单个 Agent 详情 |
| GET | `/api/agents/:id/tasks` | 获取 Agent 的任务列表 |
| GET | `/api/agents/:id/metrics` | 获取 Agent 性能指标 |
| PATCH | `/api/agents/:id/status` | 更新 Agent 状态 (active/idle/busy/error) |

### 3.2 任务管理

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/tasks` | 获取任务列表 (支持 filter/sort/pagination) |
| POST | `/api/tasks` | 创建新任务 |
| GET | `/api/tasks/:id` | 获取任务详情 |
| PATCH | `/api/tasks/:id` | 更新任务 (状态/负责人/优先级) |
| DELETE | `/api/tasks/:id` | 删除任务 |
| GET | `/api/tasks/stats` | 任务统计 (完成率/按状态分布) |

### 3.3 指标与监控

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/metrics/overview` | 仪表盘概览数据 |
| GET | `/api/metrics/agents` | Agent 活跃度时序数据 |
| GET | `/api/metrics/tasks` | 任务趋势数据 |
| GET | `/api/metrics/system` | 系统资源 (CPU/内存/磁盘) |

### 3.4 系统

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 获取 Dashboard 配置 |
| PATCH | `/api/config` | 更新配置 |

### 3.5 WebSocket 事件

```typescript
// Server → Client 推送
interface WSEvents {
  'agent:status-change': { agentId: string; status: string; timestamp: string };
  'agent:heartbeat':     { agentId: string; lastSeen: string };
  'task:created':        { task: Task };
  'task:updated':        { task: Task; changes: Partial<Task> };
  'task:deleted':        { taskId: string };
  'metrics:update':      { type: string; data: MetricData };
  'system:alert':        { level: 'info' | 'warn' | 'error'; message: string };
}

// Client → Server 请求
interface WSCommands {
  'subscribe:agents':    { agentIds?: string[] };
  'subscribe:tasks':     { filters?: TaskFilter };
  'unsubscribe':         { channel: string };
}
```

---

## 4. 数据模型

### 4.1 Agent

```sql
CREATE TABLE agents (
  id            TEXT PRIMARY KEY,           -- 'main', 'dev_engineer', etc.
  name          TEXT NOT NULL,              -- '年年', '玄机'
  role          TEXT NOT NULL,              -- '团队领导/协调员'
  model         TEXT DEFAULT 'default',     -- 使用的模型
  workspace     TEXT,                       -- workspace 路径
  status        TEXT DEFAULT 'idle',        -- active | idle | busy | offline | error
  last_heartbeat TEXT,                      -- ISO 8601 时间戳
  current_task  TEXT,                       -- 当前执行的任务 ID
  capabilities  TEXT DEFAULT '[]',          -- JSON: 能力标签
  metrics_json  TEXT DEFAULT '{}',          -- JSON: 性能指标缓存
  created_at    TEXT DEFAULT (datetime('now')),
  updated_at    TEXT DEFAULT (datetime('now'))
);
```

### 4.2 Task

```sql
CREATE TABLE tasks (
  id            TEXT PRIMARY KEY,           -- 'TASK-001'
  title         TEXT NOT NULL,
  description   TEXT,
  status        TEXT DEFAULT 'todo',        -- todo | in_progress | done | blocked | cancelled
  priority      TEXT DEFAULT 'P2',          -- P0 | P1 | P2 | P3
  owner         TEXT,                       -- Agent ID
  assignees     TEXT DEFAULT '[]',          -- JSON: 关联 Agent ID 列表
  tags          TEXT DEFAULT '[]',          -- JSON: 标签
  parent_id     TEXT,                       -- 父任务 ID
  wave          INTEGER DEFAULT 0,          -- 执行波次
  dependencies  TEXT DEFAULT '[]',          -- JSON: 依赖任务 ID 列表
  output_path   TEXT,                       -- 产出文件路径
  notes         TEXT,
  started_at    TEXT,
  completed_at  TEXT,
  due_at        TEXT,
  created_at    TEXT DEFAULT (datetime('now')),
  updated_at    TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (owner) REFERENCES agents(id)
);
```

### 4.3 Metric (时序指标)

```sql
CREATE TABLE metrics (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id      TEXT NOT NULL,
  metric_type   TEXT NOT NULL,              -- 'cpu' | 'memory' | 'response_time' | 'task_count'
  value         REAL NOT NULL,
  unit          TEXT,                       -- 'ms', '%', 'count'
  recorded_at   TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_metrics_agent_time ON metrics(agent_id, recorded_at);
CREATE INDEX idx_metrics_type_time ON metrics(metric_type, recorded_at);
```

### 4.4 Event (审计日志)

```sql
CREATE TABLE events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type    TEXT NOT NULL,              -- 'agent.status_change', 'task.created', etc.
  entity_type   TEXT,                       -- 'agent' | 'task' | 'system'
  entity_id     TEXT,
  payload       TEXT DEFAULT '{}',          -- JSON: 事件详情
  source        TEXT,                       -- 'state_yaml' | 'api' | 'heartbeat'
  created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_events_type_time ON events(event_type, created_at);
```

---

## 5. 项目结构

```
dashboard-v4/
├── package.json              # workspace root
├── pnpm-workspace.yaml
│
├── server/                   # 后端
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts          # Fastify 入口
│   │   ├── plugins/          # Fastify 插件 (cors, websocket, etc.)
│   │   ├── routes/
│   │   │   ├── agents.ts
│   │   │   ├── tasks.ts
│   │   │   ├── metrics.ts
│   │   │   └── health.ts
│   │   ├── services/
│   │   │   ├── agent-monitor.ts    # Agent 状态采集
│   │   │   ├── task-manager.ts     # 任务 CRUD
│   │   │   ├── metrics-collector.ts # 指标采集
│   │   │   ├── state-reader.ts     # STATE.yaml 解析
│   │   │   └── ws-hub.ts           # WebSocket 管理
│   │   ├── db/
│   │   │   ├── connection.ts       # SQLite 连接
│   │   │   ├── migrations.ts       # 表初始化
│   │   │   └── repositories/       # 数据访问层
│   │   └── types/
│   │       └── index.ts
│   └── data/                 # SQLite 数据文件 (gitignored)
│       └── dashboard.db
│
├── client/                   # 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/              # API 客户端 (axios/fetch 封装)
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   ├── useAgents.ts
│       │   └── useTasks.ts
│       ├── stores/           # Zustand 状态管理
│       │   ├── agentStore.ts
│       │   └── taskStore.ts
│       ├── pages/
│       │   ├── Dashboard.tsx       # 概览页
│       │   ├── Agents.tsx          # Agent 看板
│       │   ├── Tasks.tsx           # 任务看板
│       │   ├── Metrics.tsx         # 数据可视化
│       │   └── Settings.tsx
│       ├── components/
│       │   ├── AgentCard.tsx
│       │   ├── TaskKanban.tsx
│       │   ├── MetricChart.tsx
│       │   ├── StatusDot.tsx
│       │   └── layout/
│       └── styles/
│           └── theme.ts            # Ant Design 暗色主题定制
│
└── docs/
    └── dashboard-v4-architecture.md  # 本文件
```

---

## 6. 部署方案

### 开发环境

```bash
# 终端 1: 后端 (热重载)
cd server && pnpm dev          # tsx watch → localhost:3456

# 终端 2: 前端 (HMR)
cd client && pnpm dev          # Vite → localhost:5180, proxy → 3456
```

### 生产部署 (单机)

```bash
# 1. 构建
pnpm build                     # 前端 → client/dist, 后端 → server/dist

# 2. 启动
cd server && node dist/index.js   # 静态文件托管 + API + WS, 端口 3456

# 3. (可选) 用 pm2 守护
pm2 start "node dist/index.js" --name dashboard-v4
pm2 save
```

### 数据备份

- SQLite 文件: `server/data/dashboard.db`
- 定期备份到: `workspace/backups/dashboard-YYYY-MM-DD.db`
- STATE.yaml 是数据源之一，本身就是版本控制的

---

## 7. 性能与安全考量

### 性能

| 策略 | 说明 |
|------|------|
| **SQLite WAL 模式** | 读写并发不阻塞 |
| **WebSocket 心跳** | 30s 心跳，断线自动重连 |
| **前端虚拟滚动** | Agent 列表/任务列表超过 50 条时启用 |
| **指标降采样** | 超过 7 天的指标按小时聚合，超 30 天按天聚合 |
| **增量同步** | 状态变更只推送 diff，不传全量数据 |
| **静态资源缓存** | Vite 构建产物带 hash，Nginx/CDN 长缓存 |

### 安全

| 策略 | 说明 |
|------|------|
| **本地绑定** | 默认监听 127.0.0.1，不暴露外网 |
| **API Key 鉴权** | 简单 Bearer Token，防止未授权访问 |
| **CORS 白名单** | 仅允许 localhost 前端域名 |
| **输入校验** | Zod schema 校验所有 API 输入 |
| **SQL 注入防护** | better-sqlite3 参数化查询 |
| **敏感数据脱敏** | 日志中不输出 API Key、文件路径中的用户信息 |

### 监控自身

Dashboard 自监控：
- 健康检查端点 `/api/health`
- WebSocket 连接数监控
- SQLite 文件大小告警 (>100MB)
- 内存使用告警 (>512MB)

---

## 8. 开发环境搭建

### 前置条件

- macOS ARM64 (Apple Silicon)
- Node.js >= 22
- pnpm >= 9 (`corepack enable` 或 `npm i -g pnpm`)

### 步骤

```bash
# 1. 创建项目
mkdir -p ~/dashboard-v4 && cd ~/dashboard-v4

# 2. 初始化 workspace
pnpm init
cat > pnpm-workspace.yaml << 'EOF'
packages:
  - 'server'
  - 'client'
EOF

# 3. 初始化后端
mkdir -p server/src/{routes,services,db/repositories,plugins,types} server/data
cd server
pnpm init
pnpm add fastify @fastify/cors @fastify/websocket better-sqlite3 zod
pnpm add -D typescript tsx @types/better-sqlite3 @types/node
cd ..

# 4. 初始化前端
mkdir -p client/src/{api,hooks,stores,pages,components/layout,styles} client/public
cd client
pnpm init
pnpm add react react-dom antd @ant-design/charts zustand axios
pnpm add -D vite @vitejs/plugin-react typescript @types/react @types/react-dom
cd ..

# 5. 启动开发
# 终端 1
cd server && pnpm dev

# 终端 2
cd client && pnpm dev
```

### 关键配置文件

**server/tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

**client/vite.config.ts**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    proxy: {
      '/api': 'http://127.0.0.1:3456',
      '/ws': { target: 'ws://127.0.0.1:3456', ws: true }
    }
  }
})
```

---

## 9. 开发里程碑

| 阶段 | 内容 | 预估工时 |
|------|------|---------|
| **M1: 骨架** | 后端 Fastify + SQLite + 前端 React + 路由 + 暗色主题 | 1 天 |
| **M2: Agent 看板** | 状态采集 + Agent 卡片 + 实时更新 | 1 天 |
| **M3: 任务看板** | CRUD + 看板视图 + 拖拽排序 | 1 天 |
| **M4: 数据可视化** | 指标采集 + 图表 + 趋势分析 | 1 天 |
| **M5: 打磨** | 错误处理、加载状态、响应式适配、文档 | 0.5 天 |

**总计: ~4.5 天** (可由前端+后端并行，实际 2-3 天)

---

## 10. 与 v3 的对比升级

| 维度 | v3 | v4 |
|------|-----|-----|
| 前端 | 原生 HTML/JS | React + TypeScript + Ant Design |
| 后端 | 原生 http.server | Fastify (高性能 + 插件化) |
| 数据 | 内存 / STATE.yaml 直读 | SQLite 持久化 + STATE.yaml 双写 |
| 实现 | 无 | WebSocket 双向通信 |
| 任务管理 | 只读展示 | 完整 CRUD + 看板拖拽 |
| 图表 | 无 | Ant Design Charts |
| 测试 | 无 | Vitest + 单元测试 |
| 类型安全 | 无 | 全栈 TypeScript |

---

*方案由太一设计，如有疑问请在团队内讨论。轻量优先，能跑就行。* 🏗️
