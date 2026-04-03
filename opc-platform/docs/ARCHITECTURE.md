# OPC Platform - 完整技术架构文档

> **项目名称**: OPC Platform (中国区 OPC 创业平台)  
> **版本**: v1.0.0  
> **最后更新**: 2026-04-04  
> **状态**: ✅ 本地测试环境运行中

---

## 📋 目录

1. [项目概述](#-项目概述)
2. [技术栈](#-技术栈)
3. [系统架构](#-系统架构)
4. [目录结构](#-目录结构)
5. [核心模块](#-核心模块)
6. [数据流](#-数据流)
7. [部署架构](#-部署架构)
8. [API 接口](#-api-接口)
9. [开发指南](#-开发指南)

---

## 🎯 项目概述

### 产品定位
OPC Platform 是一个面向中国创业者市场的**情报展示平台**，通过可视化方式展示创业者的分布、融资情况和行业动态。

### 核心功能
- 🌍 **3D 地球可视化**: 使用 globe.gl 展示创业者地理分布
- 📊 **数据仪表盘**: 实时统计 MRR、融资轮次、行业分布
- 📍 **区域筛选**: 按省份、城市、行业赛道筛选
- 🔔 **实时更新**: WebSocket 推送新注册和投融资事件
- 👤 **用户系统**: JWT 认证的创业者注册和管理

### 目标用户
- 创业者 (Entrepreneurs)
- 投资人 (Investors)
- 行业分析师 (Analysts)
- 政府/园区管理者 (Government/Park Managers)

---

## 🛠️ 技术栈

### 前端 (Frontend)

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 18.2.0 | UI 框架 |
| **Vite** | 5.0.8 | 构建工具 |
| **globe.gl** | 2.27.2 | 3D 地球可视化 |
| **Zustand** | 4.4.7 | 状态管理 |
| **Socket.IO Client** | 4.6.1 | WebSocket 通信 |
| **TailwindCSS** | 3.4.0 | CSS 框架 |
| **PostCSS** | 8.4.32 | CSS 处理 |

### 后端 (Backend)

| 技术 | 版本 | 用途 |
|------|------|------|
| **Node.js** | 18.x / 25.x | 运行时 |
| **Express** | 4.18.2 | Web 框架 |
| **Socket.IO** | 4.6.1 | WebSocket 服务 |
| **PostgreSQL** | 15 (PostGIS) | 主数据库 |
| **Redis** | 7 | 缓存/会话 |
| **Joi** | 17.9.2 | 数据验证 |
| **JWT** | 9.0.0 | 认证令牌 |
| **Bcrypt** | 5.1.0 | 密码加密 |
| **Winston** | 3.8.2 | 日志 |

### 基础设施 (Infrastructure)

| 技术 | 用途 |
|------|------|
| **Docker** | 容器化部署 |
| **Docker Compose** | 多容器编排 |
| **PostGIS** | 地理空间数据支持 |
| **Nginx** | 反向代理 (生产环境) |

---

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Frontend (React + Vite)                 │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │   Globe     │  │  Dashboard  │  │   Auth      │  │    │
│  │  │  Component  │  │  Components │  │   System    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │         │                │                │          │    │
│  │         └────────────────┼────────────────┘          │    │
│  │                          │                           │    │
│  │              ┌───────────▼───────────┐              │    │
│  │              │   Zustand Store       │              │    │
│  │              │   (State Management)  │              │    │
│  │              └───────────┬───────────┘              │    │
│  └──────────────────────────┼──────────────────────────┘    │
└─────────────────────────────┼────────────────────────────────┘
                              │ HTTP / WebSocket
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                   Backend (Express + Node.js)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Layer                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Routes  │  │  Routes  │  │  Routes  │          │   │
│  │  │  /api/   │  │  /api/   │  │  /api/   │          │   │
│  │  │  entre-  │  │  invest- │  │  auth/   │          │   │
│  │  │  preneurs│  │  ments   │  │  login   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │       │              │              │                │   │
│  │       └──────────────┼──────────────┘                │   │
│  │                      │                               │   │
│  │  ┌───────────────────▼───────────────────┐          │   │
│  │  │          Controllers Layer            │          │   │
│  │  └───────────────────┬───────────────────┘          │   │
│  │                      │                               │   │
│  │  ┌───────────────────▼───────────────────┐          │   │
│  │  │           Services Layer              │          │   │
│  │  │  (Business Logic + Validation)        │          │   │
│  │  └───────────────────┬───────────────────┘          │   │
│  │                      │                               │   │
│  │  ┌───────────────────▼───────────────────┐          │   │
│  │  │            Models Layer               │          │   │
│  │  │  (Data Access + ORM-like)             │          │   │
│  │  └───────────────────┬───────────────────┘          │   │
│  └──────────────────────┼──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼───────────────────┐             │
│  │          WebSocket (Socket.IO)            │             │
│  │  - real-time updates                      │             │
│  │  - new registrations                      │             │
│  │  - investment events                      │             │
│  └───────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  PostgreSQL   │   │     Redis     │   │   File System │
│  + PostGIS    │   │   (Cache)     │   │   (Logs)      │
│  (Primary DB) │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 分层架构

| 层级 | 职责 | 文件位置 |
|------|------|----------|
| **表现层** | React 组件、UI 渲染 | `frontend/src/components/` |
| **状态层** | Zustand Store、数据标准化 | `frontend/src/store/`, `services/` |
| **通信层** | API 调用、WebSocket | `frontend/src/services/` |
| **路由层** | HTTP 路由、中间件 | `backend/src/routes/`, `middleware/` |
| **控制层** | 请求处理、响应格式化 | `backend/src/controllers/` |
| **服务层** | 业务逻辑、验证 | `backend/src/services/`, `validators/` |
| **数据层** | 数据库操作、模型 | `backend/src/models/`, `database.js` |

---

## 📁 目录结构

### 项目根目录

```
opc-platform/
├── backend/                    # 后端服务
│   ├── src/
│   │   ├── app.js             # 主应用入口
│   │   ├── database.js        # 数据库连接
│   │   ├── controllers/       # 控制器层
│   │   ├── models/            # 数据模型
│   │   ├── routes/            # 路由定义
│   │   ├── services/          # 业务服务
│   │   ├── middleware/        # 中间件 (auth, validation)
│   │   ├── validators/        # 数据验证器
│   │   └── utils/             # 工具函数
│   ├── scripts/               # 数据库脚本
│   ├── tests/                 # 单元测试
│   ├── .env                   # 环境变量
│   ├── .env.example           # 环境变量示例
│   ├── Dockerfile             # Docker 镜像
│   ├── package.json           # 依赖配置
│   └── node_modules/          # Node 依赖
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── App.jsx            # 根组件
│   │   ├── main.jsx           # 入口文件
│   │   ├── index.css          # 全局样式
│   │   ├── components/        # React 组件
│   │   │   ├── Common/        # 通用组件
│   │   │   ├── Dashboard/     # 仪表盘组件
│   │   │   ├── Entrepreneur/  # 创业者组件
│   │   │   └── Globe/         # 3D 地球组件
│   │   ├── services/          # API 和 WebSocket 服务
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── store/             # Zustand 状态管理
│   │   └── utils/             # 工具函数
│   ├── public/                # 静态资源
│   ├── dist/                  # 构建输出
│   ├── index.html             # HTML 模板
│   ├── vite.config.js         # Vite 配置
│   ├── package.json           # 依赖配置
│   └── node_modules/          # Node 依赖
│
├── docker/                     # Docker 配置
│   ├── docker-compose.yml     # 容器编排
│   └── init.sql               # 数据库初始化脚本
│
├── design/                     # 设计文档
│   ├── DESIGN_SYSTEM.md       # 设计系统
│   ├── COLOR_PALETTE.md       # 配色方案
│   ├── COMPONENT_SPECS.md     # 组件规格
│   └── LAYOUT_DESIGNS.md      # 布局设计
│
└── docs/                       # 项目文档
    ├── OPC_PROJECT_PLAN.md    # 项目计划
    └── OPC_3D_GLOBE_PROPOSAL.md # 3D 地球方案
```

---

## 🔧 核心模块

### 1. 后端核心模块

#### app.js - 主应用入口
**职责**: 
- Express 应用初始化
- 中间件配置 (CORS, Helmet, Rate Limiting)
- 路由注册
- WebSocket 初始化
- 数据库连接

**关键代码**:
```javascript
// 中间件配置
app.use(helmet())
app.use(cors({ origin: FRONTEND_URL, credentials: true }))
app.use(rateLimit({ windowMs: 15*60*1000, max: 100 }))

// WebSocket 事件
io.on('connection', async (socket) => {
  const entrepreneurs = await Entrepreneur.findAll()
  socket.emit('initial_data', {
    entrepreneurs: sortByCreatedAtDesc(entrepreneurs),
    stats: deriveStats(entrepreneurs)
  })
})
```

#### models/entrepreneur.js - 创业者模型
**职责**: 数据库 CRUD 操作

**方法**:
| 方法 | 描述 | 参数 |
|------|------|------|
| `create(data)` | 创建创业者 | `{name, city, province, track, lat, lng, mrr}` |
| `findById(id)` | 按 ID 查询 | `UUID` |
| `findAll(filters)` | 查询列表 | `{search, track, limit, offset}` |
| `count(filters)` | 统计数量 | `{search, track}` |
| `update(id, data)` | 更新信息 | `UUID, {name, city, ...}` |
| `delete(id)` | 删除记录 | `UUID` |
| `getStats()` | 获取统计数据 | - |

#### middleware/auth.js - 认证中间件
**职责**: JWT Token 验证

```javascript
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization']
  const token = authHeader && authHeader.split(' ')[1]
  
  if (!token) return res.status(401).json({ error: '未提供认证令牌' })
  
  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: '无效的令牌' })
    req.user = user
    next()
  })
}
```

### 2. 前端核心模块

#### App.jsx - 根组件
**职责**: 
- 应用初始化
- WebSocket 连接管理
- 全局状态同步
- 路由管理

**状态流**:
```
WebSocket → initial_data → Zustand Store → Components
     ↓
new_registration → broadcast → Store Update → UI Re-render
```

#### services/api.js - API 服务层
**职责**: 
- HTTP 请求封装
- 数据标准化
- 错误处理

**核心函数**:
```javascript
// 标准化创业者数据
function normalizeEntrepreneur(item, index) {
  return {
    id: item.id || `${name}-${city}-${index}`,
    name: item.name || `创业者 ${index + 1}`,
    city: item.city || '未知城市',
    track: item.track || '未分类',
    // ... 其他字段
  }
}

// API 调用
export async function fetchEntrepreneurs(filters) {
  const response = await fetch(joinPath('/api/entrepreneurs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters)
  })
  return normalizeResponse(await response.json())
}
```

#### services/websocket.js - WebSocket 服务
**职责**: 
- Socket.IO 连接管理
- 实时事件订阅
- 数据同步

```javascript
import { io } from 'socket.io-client'

const socket = io('http://localhost:3001', {
  transports: ['websocket', 'polling']
})

// 订阅事件
socket.on('initial_data', (data) => {
  useStore.getState().setEntrepreneurs(data.entrepreneurs)
  useStore.getState().setStats(data.stats)
})

socket.on('new_registration', (data) => {
  useStore.getState().addEntrepreneur(data)
})
```

#### components/Globe/ - 3D 地球组件
**技术**: globe.gl

**功能**:
- 地理坐标可视化
- 弧线和标签显示
- 交互 (旋转、缩放、点击)
- 按赛道筛选

```javascript
<Globe
  globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
  pointsData={entrepreneurs}
  pointLat="latitude"
  pointLng="longitude"
  pointColor={() => getTrackColor(track)}
  pointsMerge={true}
  onPointClick={(point) => showDetail(point)}
/>
```

---

## 🔄 数据流

### 1. 数据获取流程

```
用户打开页面
    ↓
App.jsx 初始化
    ↓
WebSocket 连接 (Socket.IO)
    ↓
backend: io.on('connection')
    ↓
Entrepreneur.findAll() → PostgreSQL
    ↓
{ entrepreneurs: [...], stats: {...} }
    ↓
socket.emit('initial_data')
    ↓
frontend: socket.on('initial_data')
    ↓
Zustand Store 更新
    ↓
React Components 重新渲染
    ↓
Globe + Dashboard 显示数据
```

### 2. 实时更新流程

```
新用户注册
    ↓
POST /api/entrepreneurs
    ↓
Entrepreneur.create()
    ↓
broadcastNewRegistration(data)
    ↓
io.to('registrations').emit('new_registration')
    ↓
所有订阅的客户端收到事件
    ↓
Store 添加新数据
    ↓
UI 自动更新 (Globe + 列表)
```

### 3. 认证流程

```
用户登录
    ↓
POST /api/auth/login
    ↓
验证用户名密码 (bcrypt.compare)
    ↓
生成 JWT Token (jwt.sign)
    ↓
返回 { token, user }
    ↓
前端存储 Token (localStorage)
    ↓
后续请求携带 Authorization: Bearer <token>
    ↓
authenticateToken 中间件验证
    ↓
req.user 包含用户信息
```

---

## 🚀 部署架构

### 本地开发环境

```
┌─────────────────────────────────────┐
│         Developer Machine           │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Frontend (localhost:4173) │   │
│  │   npm run preview           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Backend (localhost:3001)  │   │
│  │   node src/app.js           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Docker Containers         │   │
│  │   ├─ PostgreSQL :5432       │   │
│  │   └─ Redis :6379            │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 生产环境 (建议)

```
┌──────────────────────────────────────────────────────────┐
│                    Cloud Load Balancer                    │
│                    (阿里云 SLB)                           │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Nginx 1    │ │   Nginx 2    │ │   Nginx 3    │
│  (Reverse    │ │  (Reverse    │ │  (Reverse    │
│   Proxy)     │ │   Proxy)     │ │   Proxy)     │
└───────┬──────┘ └───────┬──────┘ └───────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Backend 1   │ │  Backend 2   │ │  Backend 3   │
│  (Node.js)   │ │  (Node.js)   │ │  (Node.js)   │
└───────┬──────┘ └───────┬──────┘ └───────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  RDS PGSQL   │ │  Redis 版    │ │    OSS      │
│  (主从)      │ │  (集群)      │ │  (静态资源)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 推荐云服务 (中国区)

| 组件 | 服务 | 规格建议 |
|------|------|----------|
| **计算** | 阿里云 ECS | 2 核 4G × 3 (自动伸缩) |
| **数据库** | 阿里云 RDS PostgreSQL | 2 核 8G 高可用版 |
| **缓存** | 阿里云 Redis 版 | 2G 集群版 |
| **存储** | 阿里云 OSS | 标准存储 (前端静态资源) |
| **CDN** | 阿里云 CDN | 加速静态资源 |
| **负载均衡** | 阿里云 SLB | 按量付费 |

---

## 📡 API 接口

### 认证相关

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/auth/login` | 用户登录 | ❌ |
| POST | `/api/auth/register` | 用户注册 | ❌ |
| GET | `/api/auth/me` | 获取当前用户 | ✅ |

### 创业者相关

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/entrepreneurs` | 获取列表 | ❌ |
| POST | `/api/entrepreneurs` | 创建创业者 | ✅ |
| GET | `/api/entrepreneurs/:id` | 获取详情 | ❌ |
| PUT | `/api/entrepreneurs/:id` | 更新信息 | ✅ |
| DELETE | `/api/entrepreneurs/:id` | 删除记录 | ✅ (Admin) |
| GET | `/api/entrepreneurs/protected` | 受保护列表 | ✅ |

### 投融资相关

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/investments` | 获取列表 | ❌ |
| POST | `/api/investments` | 创建事件 | ✅ |

### 统计相关

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/stats` | 获取统计数据 | ❌ |
| GET | `/api/health` | 健康检查 | ❌ |

### 请求示例

```bash
# 获取创业者列表
curl -X POST http://localhost:3001/api/entrepreneurs \
  -H "Content-Type: application/json" \
  -d '{"track":"AI","limit":10,"offset":0}'

# 创建创业者 (需要认证)
curl -X POST http://localhost:3001/api/entrepreneurs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试用户",
    "track": "AI",
    "province": "广东省",
    "city": "深圳市",
    "lat": 22.5431,
    "lng": 114.0579,
    "mrr": 50000
  }'
```

---

## 📖 开发指南

### 环境准备

```bash
# 1. 安装依赖
cd backend && npm install
cd ../frontend && npm install

# 2. 启动数据库和 Redis
cd docker && docker-compose up -d postgres redis

# 3. 配置环境变量
cd backend && cp .env.example .env
# 编辑 .env 文件

# 4. 初始化数据库
npm run db:init
```

### 启动开发服务器

```bash
# 终端 1: 后端
cd backend
npm run dev

# 终端 2: 前端
cd frontend
npm run dev
```

### 构建生产版本

```bash
# 前端构建
cd frontend
npm run build

# 输出到 dist/ 目录
# 部署到 Nginx 或 CDN
```

### Docker 部署

```bash
# 一键启动所有服务
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 🔒 安全考虑

### 已实现
- ✅ JWT Token 认证
- ✅ 密码 bcrypt 加密
- ✅ CORS 限制
- ✅ Rate Limiting (防刷)
- ✅ Helmet (HTTP 安全头)
- ✅ SQL 参数化查询 (防注入)

### 待实现 (生产环境)
- [ ] HTTPS 强制
- [ ] API Key 管理
- [ ] 敏感数据加密存储
- [ ] 审计日志
- [ ] 数据备份策略
- [ ] 监控告警系统

---

## 📊 性能优化

### 前端
- ✅ Vite 构建 (HMR + Tree Shaking)
- ✅ 代码分割 (动态 import)
- ✅ TailwindCSS Purge (移除未使用样式)
- ⏳ 图片懒加载
- ⏳ 虚拟列表 (大数据量)

### 后端
- ✅ PostgreSQL 连接池
- ✅ Redis 缓存 (待实现)
- ✅ 数据库索引 (地理空间 + 常用查询字段)
- ⏳ 查询结果缓存
- ⏳ API 响应压缩

### 数据库
- ✅ GIST 索引 (地理空间查询)
- ✅ B-Tree 索引 (track, city, created_at)
- ⏳ 分区表 (数据量大时)
- ⏳ 读写分离

---

## 🧪 测试策略

### 后端测试
```bash
cd backend
npm test
```

**测试覆盖**:
- 模型层 (CRUD 操作)
- 服务层 (业务逻辑)
- API 接口 (集成测试)

### 前端测试
```bash
cd frontend
npm test
```

**测试覆盖**:
- 组件单元测试
- Hook 测试
- E2E 测试 (待实现)

---

## 📈 监控与日志

### 日志系统
- **Winston** 统一日志格式
- **日志级别**: error, warn, info, debug
- **输出**: 控制台 + 文件 (生产环境)

### 监控指标 (待实现)
- API 响应时间
- 数据库查询性能
- WebSocket 连接数
- 内存/CPU 使用率
- 错误率统计

---

## 🚧 待办事项

### 功能完善
- [ ] 用户个人资料页面
- [ ] 高级搜索筛选
- [ ] 数据导出功能
- [ ] 移动端适配优化
- [ ] 多语言支持

### 技术债务
- [ ] 完善单元测试 (目标: 80% 覆盖率)
- [ ] API 文档 (Swagger/OpenAPI)
- [ ] CI/CD 流水线
- [ ] 性能基准测试
- [ ] 安全审计

---

## 📞 联系方式

**项目地址**: `/Users/narain/.openclaw/workspace/opc-platform`  
**当前状态**: ✅ 本地测试环境运行正常  
**前端**: http://localhost:4173  
**后端**: http://localhost:3001  

---

**文档版本**: v1.0  
**最后更新**: 2026-04-04  
**维护者**: 年年 🎀
