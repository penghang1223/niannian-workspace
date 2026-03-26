# 太一 · 架构师学习笔记

> 持续学习记录 | 创建于 2026-03-27

---

## 1. 分布式系统 — CAP/BASE/一致性

### CAP 定理
- **提出者**：Eric Brewer (2000)，MIT 的 Gilbert & Lynch 于 2002 年证明
- **三大特性**：
  - **C (Consistency/线性一致性)**：写操作完成后，后续所有读必须返回最新值（Linearizability）
  - **A (Availability)**：每个非故障节点必须对请求返回响应
  - **P (Partition Tolerance)**：网络分区发生时系统仍能运行
- **核心权衡**：P 是分布式系统的常态（不可回避），当分区发生时只能在 C 和 A 之间二选一
- **不是简单"三选二"**：实际是"分区发生时，CP 还是 AP"的选择
- **PACELC 扩展**：无分区时 (Else)，还需在延迟(L)和一致性(C)之间权衡

### CP vs AP 架构选型
| 类型 | 代表组件 | 特点 | 适用场景 |
|------|---------|------|---------|
| CP | ZooKeeper、etcd、HBase | 牺牲可用性，保证强一致 | 分布式锁、配置管理、金融交易 |
| AP | Eureka、Cassandra | 牺牲一致性，保证高可用 | 微服务注册、社交动态、商品搜索 |
| CP+AP | Nacos | 可切换模式 | 灵活场景 |

### BASE 理论
- **来源**：eBay 架构师 Dan Pritchett (2008)，ACID 的替代方案
- **BA (Basically Available 基本可用)**：系统故障时允许损失部分非核心功能，保证核心可用
- **S (Soft State 软状态)**：允许系统中存在中间状态，不要求实时强一致
- **E (Eventually Consistent 最终一致性)**：经过一段时间后，所有副本数据趋于一致
- **本质**：CAP 中 AP 架构在工程实践中的指导原则

### 一致性级别（从强到弱）
1. **线性一致性 (Linearizability)**：最强，操作有全局时序，读到最新写入值
2. **顺序一致性 (Sequential Consistency)**：所有客户端看到相同操作顺序，但可能有延迟
3. **因果一致性 (Causal Consistency)**：有因果关系的操作保持顺序
4. **最终一致性 (Eventual Consistency)**：最终所有副本收敛，但时间不确定

### 关键实践认知
- 业务开发者不"实践" CAP，而是**选择**合适的 CP/AP 组件
- 必须理解底层组件的 CAP 属性，否则可能导致**级联雪崩**
- 防护措施：多层防护（本地缓存+熔断+降级）、合理超时重试、故障隔离
- ZooKeeper 读取区分：Sync 读取保证线性一致性，普通读取保证顺序一致性
- Eureka 自我保护机制：续约率 < 85% 时暂停剔除，宁保留"僵尸"也不误杀健康实例

---

## 2. 微服务架构 — 服务拆分/通信/治理

### 核心原则
- **单一职责 (SRP)**：每个服务只负责一个业务能力
- **自治性**：独立部署、独立数据库、独立技术栈
- **有界上下文 (Bounded Context)**：借鉴 DDD，按业务域划分

### 服务拆分策略
- **按业务领域拆分**：用户服务、订单服务、支付服务、库存服务
- **按数据拆分**：每个服务拥有自己的数据库（Database per Service）
- **拆分粒度**：过细导致分布式事务复杂，过粗失去微服务意义
- **拆分顺序**：先识别领域边界 → 定义 API 契约 → 数据拆分 → 逐步迁移

### 服务通信模式
| 模式 | 协议 | 特点 | 适用场景 |
|------|------|------|---------|
| 同步 RPC | gRPC/HTTP REST | 简单直接，强耦合 | 实时查询、简单调用 |
| 异步消息 | Kafka/RabbitMQ | 解耦、削峰、可靠 | 事件通知、异步处理 |
| 事件驱动 | Event Bus | 完全解耦、可审计 | 复杂业务流程 |

### 服务治理核心组件
- **服务注册与发现**：Nacos / Consul / Eureka / etcd
- **API 网关**：Kong / APISIX / Spring Cloud Gateway — 统一入口、路由、鉴权、限流
- **配置中心**：Nacos Config / Apollo / Spring Cloud Config
- **负载均衡**：客户端（Ribbon） vs 服务端（Nginx/ALB）
- **熔断降级**：Sentinel / Hystrix / Resilience4j

### 关键实践
- **API 版本管理**：URL 版本 (`/v1/`) 或 Header 版本
- **服务间认证**：JWT / OAuth2 / mTLS
- **数据一致性**：分布式事务（2PC/TCC/Saga）或最终一致性 + 补偿
- **链路追踪**：Jaeger / Zipkin / SkyWalking — 分布式 TraceID 贯穿全链路
- **可观测性三支柱**：Logging（ELK）+ Metrics（Prometheus）+ Tracing（Jaeger）

---

## 3. 高可用设计 — 容灾/降级/限流

### 高可用核心指标
- **SLA 等级**：99.9% (8.76h/年) → 99.99% (52.6min/年) → 99.999% (5.26min/年)
- **MTBF (Mean Time Between Failure)**：平均故障间隔
- **MTTR (Mean Time To Repair)**：平均修复时间
- **可用性 = MTBF / (MTBF + MTTR)**

### 容灾架构
- **同城双活**：同一城市两个数据中心，RPO≈0，RTO<分钟级
- **异地多活**：多地部署，分片路由，数据最终同步
- **两地三中心**：同城双中心 + 异地灾备中心
- **关键点**：数据同步策略（同步/异步）、流量调度（DNS/Anycast）、故障自动切换

### 限流算法
| 算法 | 原理 | 优缺点 |
|------|------|--------|
| 计数器 | 固定时间窗口内计数 | 简单但有突刺问题 |
| 滑动窗口 | 细分时间窗口，平滑计数 | 解决突刺，稍复杂 |
| 漏桶 (Leaky Bucket) | 固定速率流出 | 流量整形好，不支持突发 |
| 令牌桶 (Token Bucket) | 速率生成令牌，支持突发 | 最灵活，常用 |

### 降级策略
- **自动降级**：超时/异常率触发，返回兜底数据或缓存
- **人工降级**：开关控制，关闭非核心功能（如评论、推荐）
- **读降级**：返回缓存/默认值
- **写降级**：异步写入、消息队列缓冲
- **熔断模式**：Closed → Open → Half-Open 三态

### 容错机制
- **重试策略**：指数退避 + Jitter（避免惊群效应）
- **超时控制**：连接超时 + 读取超时 分别设置
- **舱壁隔离**：线程池/信号量隔离，故障不扩散
- **幂等设计**：请求唯一ID + 去重表/token 机制

---

## 4. 性能优化 — 缓存/CDN/数据库优化

### 缓存架构
- **本地缓存**：Caffeine / Guava Cache — 毫秒级，容量有限
- **分布式缓存**：Redis Cluster / Memcached — 跨节点共享
- **多级缓存**：L1 本地 → L2 Redis → L3 DB
- **缓存模式**：
  - Cache-Aside (旁路缓存)：最常用，应用管理读写
  - Read-Through / Write-Through：缓存代理自动同步
  - Write-Behind (Write-Back)：异步批量写 DB

### 缓存常见问题
| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 缓存穿透 | 查不存在的数据，每次打到 DB | 布隆过滤器 / 缓存空值 |
| 缓存击穿 | 热点 key 过期瞬间大量请求 | 互斥锁 / 永不过期+异步刷新 |
| 缓存雪崩 | 大量 key 同时过期 | 随机过期时间 / 多级缓存 |
| 数据一致性 | 缓存与 DB 不同步 | 延迟双删 / 订阅 binlog |

### CDN 优化
- **原理**：将静态资源缓存到边缘节点，就近访问
- **适用**：图片、JS/CSS、视频、下载文件
- **关键策略**：缓存过期策略、URL 带版本号刷新、预热

### 数据库优化
- **索引优化**：覆盖索引、联合索引最左匹配、避免 SELECT *
- **读写分离**：主库写 + 从库读，中间件(MyCat/ShardingSphere)路由
- **分库分表**：水平分片（按 user_id 取模）/ 垂直拆分（按业务）
- **SQL 优化**：EXPLAIN 分析、避免 N+1 查询、批量操作
- **连接池**：HikariCP（推荐）/ Druid — 控制最大连接数、超时

### 性能优化方法论
1. **先度量**：APM 监控、压测基线、火焰图分析
2. **找瓶颈**：CPU / IO / 网络 / 内存 哪个先到极限
3. **分层优化**：前端 → 网关 → 服务 → 缓存 → DB → OS
4. **渐进式**：每次优化一个点，对比前后数据

---

## 5. Docker 基础 — 容器化/镜像构建

### 核心概念
- **容器 vs 虚拟机**：容器共享 OS 内核，轻量秒级启动；VM 有完整 OS，隔离更强
- **镜像 (Image)**：只读模板，分层存储（Layer），基于 UnionFS
- **容器 (Container)**：镜像的运行实例，可读写层叠加
- **仓库 (Registry)**：Docker Hub / 阿里云 ACR / Harbor（私有）

### Dockerfile 最佳实践
```dockerfile
# 多阶段构建 - 减小镜像体积
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 关键指令
| 指令 | 作用 | 注意 |
|------|------|------|
| FROM | 基础镜像 | 用 alpine 版本减体积 |
| COPY vs ADD | 复制文件 | 优先 COPY，ADD 仅用于自动解压 |
| RUN | 执行命令 | 合并 RUN 减少层数 |
| CMD vs ENTRYPOINT | 启动命令 | CMD 可覆盖，ENTRYPOINT 固定 |
| HEALTHCHECK | 健康检查 | 编排工具依赖此判断 |
| .dockerignore | 排除文件 | 避免复制 node_modules/.git |

### 常用命令
```bash
docker build -t myapp:v1 .          # 构建镜像
docker run -d -p 8080:3000 myapp    # 运行容器
docker logs -f container_id         # 查看日志
docker exec -it container_id sh     # 进入容器
docker system prune -a              # 清理无用资源
docker compose up -d                # 启动编排
```

### 镜像优化要点
- 选择最小基础镜像（alpine / distroless / scratch）
- 多阶段构建分离构建和运行环境
- 合并 RUN 指令减少层数
- 利用构建缓存：不常变的指令放前面
- .dockerignore 排除无用文件

---

## 6. Docker Compose — 多容器编排

### 核心概念
- **服务 (Service)**：一个容器的定义和配置
- **网络 (Network)**：服务间通信的桥梁
- **卷 (Volume)**：数据持久化存储
- **项目 (Project)**：一组相关服务的集合

### docker-compose.yml 关键配置
```yaml
version: '3.8'
services:
  web:
    build: .
    ports: ["3000:3000"]
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      POSTGRES_PASSWORD: pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  redis:
    image: redis:7-alpine
    volumes: ["redisdata:/data"]

volumes:
  pgdata:
  redisdata:
```

### 常用命令
```bash
docker compose up -d          # 后台启动所有服务
docker compose down -v        # 停止并删除卷
docker compose logs -f web    # 查看指定服务日志
docker compose exec web sh    # 进入服务容器
docker compose build --no-cache  # 重新构建
docker compose ps             # 查看服务状态
```

### 服务依赖与启动顺序
- `depends_on` 控制启动顺序，但不等待"就绪"
- 配合 `condition: service_healthy` 实现真正的就绪等待
- 应用代码仍需处理连接重试（DB 可能未完全就绪）

### 网络模式
- 默认创建项目专属网络，服务名即 DNS 名
- `network_mode: host` 共享宿主机网络
- `networks` 自定义网络拓扑

### 数据管理
- **Named Volumes**：Docker 管理，持久化数据
- **Bind Mounts**：挂载宿主机目录，适合开发热更新
- **tmpfs**：内存中临时存储

---

## 7. Kubernetes 基础 — Pod/Service/Ingress

### 架构概览
- **Control Plane**：API Server、etcd（存储）、Scheduler、Controller Manager
- **Node**：kubelet（管理 Pod）、kube-proxy（网络代理）、Container Runtime
- **核心对象**：Pod → Deployment → Service → Ingress

### Pod — 最小调度单元
- 一个 Pod 包含 1+ 个容器，共享网络命名空间（localhost 互通）
- **生命周期**：Pending → Running → Succeeded/Failed → Unknown
- **Controller 类型**：
  - **Deployment**：无状态应用，管理 ReplicaSet，支持滚动更新和回滚
  - **StatefulSet**：有状态应用（DB、MQ），稳定网络标识和持久存储
  - **DaemonSet**：每个 Node 运行一个（日志采集、监控 agent）
  - **Job/CronJob**：一次性/定时任务

### Service — 服务发现与负载均衡
| 类型 | 用途 |
|------|------|
| ClusterIP（默认） | 集群内部访问 |
| NodePort | 通过 Node 端口暴露 |
| LoadBalancer | 云厂商 LB 自动创建 |
| ExternalName | DNS CNAME 映射 |

- 通过 Label Selector 关联 Pod
- kube-proxy 维护 iptables/IPVS 规则实现负载均衡

### Ingress — HTTP 层路由
- 统一入口，基于 Host/Path 路由到不同 Service
- 需要 Ingress Controller（Nginx / Traefik / APISIX）
- 支持 TLS 终止、限流、认证

### 关键配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
      - name: web
        image: myapp:v1
        ports: [{ containerPort: 3000 }]
        resources:
          requests: { cpu: "100m", memory: "128Mi" }
          limits: { cpu: "500m", memory: "512Mi" }
        livenessProbe:
          httpGet: { path: /health, port: 3000 }
          initialDelaySeconds: 10
        readinessProbe:
          httpGet: { path: /ready, port: 3000 }
```

### 常用 kubectl 命令
```bash
kubectl get pods -A                    # 查看所有命名空间的 Pod
kubectl describe pod <name>            # 查看 Pod 详情
kubectl logs -f <pod> -c <container>   # 查看容器日志
kubectl exec -it <pod> -- sh           # 进入容器
kubectl apply -f deployment.yaml       # 声明式部署
kubectl rollout status deploy/web-app  # 查看滚动更新状态
kubectl rollout undo deploy/web-app    # 回滚到上一版本
```

### ConfigMap 与 Secret
- **ConfigMap**：非敏感配置（环境变量、配置文件）
- **Secret**：敏感数据（密码、证书），Base64 编码（非加密）
- 挂载方式：环境变量 / Volume 挂载

---

## 8. 事件驱动 — Event Sourcing / CQRS

### Event Sourcing (事件溯源)
- **核心思想**：不存储当前状态，而是存储所有导致状态变化的事件序列
- **状态 = f(事件流)**：通过重放事件重建任意时刻的状态
- **优势**：
  - 完整审计日志（天然可追溯）
  - 可重建任意时间点的状态（Time Travel）
  - 天然支持事件驱动架构
  - 高写入性能（只追加，不更新）
- **挑战**：
  - 事件 schema 演化（版本兼容）
  - 快照机制（避免从头重放）
  - 事件删除/GDPR 合规（不可变性 vs 隐私权）
  - 查询复杂（无法直接查当前状态）

### CQRS (Command Query Responsibility Segregation)
- **核心思想**：读写分离 — Command（写）和 Query（读）使用不同的模型
- **写模型**：处理业务逻辑，产生事件，写入事件存储
- **读模型**：订阅事件，构建物化视图/投影（Projection），优化查询
- **适用场景**：
  - 读写比例差异大（读多写少或写多读少）
  - 读写操作需要不同的数据模型
  - 复杂查询需求
- **不适用**：简单 CRUD，过度设计会增加复杂度

### Event Sourcing + CQRS 组合模式
```
Client → Command Handler → Event Store → Event Bus → Projection → Read DB
                                          ↓
                                     Event Handler (触发后续业务)
```
- 写路径：Command → 验证 → 产生 Event → 存储 → 发布
- 读路径：Query → 读模型（预计算的物化视图）
- **最终一致性**：读模型异步更新，存在短暂延迟

### 关键实现要素
- **事件存储**：EventStoreDB / Apache Kafka / 自建（PostgreSQL + 事件表）
- **幂等处理**：消费者必须处理重复事件（基于 Event ID 去重）
- **事件版本**：Upcaster（旧事件转换为新格式）/ 多版本共存
- **快照策略**：每 N 个事件生成快照，加速状态重建
- **Saga 模式**：跨聚合/跨服务的长时间事务，通过事件协调

---

## 9. 领域驱动 — DDD / 聚合根

### DDD 核心理念
- **战略设计**：划分 Bounded Context（限界上下文），定义领域边界
- **战术设计**：在上下文内用聚合、实体、值对象建模
- **通用语言 (Ubiquitous Language)**：团队与业务专家共享的统一术语

### 战略设计 — 限界上下文
- 每个 Bounded Context 是一个独立的模型世界
- 上下文之间通过 **Context Map** 定义集成关系
- 常见关系：
  - **Shared Kernel**：共享部分模型
  - **Customer-Supplier**：上游提供，下游消费
  - **Anti-Corruption Layer (ACL)**：防腐层，翻译外部模型
  - **Open Host Service**：提供标准化 API

### 战术设计 — 核心构件
| 概念 | 说明 | 示例 |
|------|------|------|
| **Entity (实体)** | 有唯一标识，生命周期可变 | Order (orderId) |
| **Value Object (值对象)** | 无唯一标识，按值比较，不可变 | Money, Address, DateRange |
| **Aggregate (聚合)** | 一组关联实体/值对象的事务一致性边界 | Order + OrderItems |
| **Aggregate Root (聚合根)** | 聚合的入口，外部只能通过它访问内部 | Order 是聚合根 |
| **Domain Event (领域事件)** | 领域中发生的有意义的事情 | OrderPlaced, PaymentReceived |
| **Repository (仓储)** | 聚合的持久化抽象 | OrderRepository |
| **Domain Service (领域服务)** | 不属于任何实体的业务逻辑 | FraudCheckService |
| **Factory (工厂)** | 复杂对象创建逻辑 | OrderFactory |

### 聚合设计原则
1. **小聚合**：聚合越小越好，减少锁竞争和事务范围
2. **通过 ID 引用**：聚合之间只通过 ID 关联，不直接持有对象引用
3. **事务一致性边界**：一个事务只修改一个聚合
4. **最终一致性**：跨聚合操作通过事件驱动实现最终一致性
5. **聚合根负责不变量**：聚合内部的所有修改必须满足业务规则

### 分层架构
```
┌─────────────────────────┐
│   User Interface / API  │  ← 控制器、DTO
├─────────────────────────┤
│      Application        │  ← 用例编排、事务管理（不含业务逻辑）
├─────────────────────────┤
│        Domain           │  ← 实体、值对象、聚合、领域服务（核心）
├─────────────────────────┤
│    Infrastructure       │  ← 仓储实现、消息队列、外部服务
└─────────────────────────┘
```
- **依赖方向**：外层依赖内层，Domain 层不依赖任何外层
- **六边形架构 (Hexagonal)**：端口+适配器，Domain 在中心，通过接口与外界交互

### DDD 与微服务的关系
- 一个 Bounded Context 通常映射为一个微服务
- 聚合是微服务内的一致性边界
- 领域事件是微服务间通信的自然载体
- ACL（防腐层）用于集成遗留系统或第三方服务

### DDD 落地建议
1. 先做**事件风暴 (Event Storming)** 工作坊，与业务专家一起梳理领域
2. 识别核心域、支撑域、通用域，重点投入核心域
3. 不要一开始就全盘 DDD，从最复杂的业务域开始
4. 代码结构按领域组织（而非按技术层）：`order/`, `payment/`, `inventory/`
