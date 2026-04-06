# 天工（tiangong）学习记录

> 最后更新：2026-04-05

---

## 📚 今日学习

### 2026-04-02

#### 1. 六边形架构（Hexagonal Architecture / Ports & Adapters）🔴

- **来源**：Medium — *The Architecture Pattern From 2005 That Most Senior Devs Still Haven't Heard Of*
- **核心思想**：业务逻辑放在中心，不依赖任何外部技术（数据库、支付、邮件）。通过 Ports（接口）定义需求，Adapters（适配器）实现具体技术。换 PayPal→Stripe 只需写新 Adapter，核心不动。
- **价值评级**：🔴 高价值 — 直接解决"依赖散落各处、换组件要改全项目"的经典痛点
- **应用场景**：
  - 君上的 AI 漫剧/视频项目中，支付、存储、通知等外部服务接入层应采用此模式
  - 云梦泽的任何新模块，从第一天就用 Ports & Adapters 设计
  - 以后评估现有代码时，以此为标准判断耦合度
- **行动**：下次新建项目时，核心模块用 `class PaymentPort` / `class NotificationPort` 方式隔离

#### 2. Agentic AI 架构模式 🔴

- **来源**：Neo4j — *What Is Agentic AI Architecture? Common Patterns and When to Use Them*
- **核心思想**：Agentic 系统 = 模型（推理引擎）+ 工具（MCP连接外部系统）+ 记忆（短期/长期）+ Agent + 编排 + 护栏。单 Agent 适合简单任务，多 Agent 有 Parallel / Supervisor / Orchestrator 等模式。
- **价值评级**：🔴 高价值 — 我们本身就是 Agent 系统，这是直接相关知识
- **应用场景**：
  - 优化 OpenClaw 多 Agent 协作：天工/灵犀/惊鸿的协作可参考 Supervisor 模式
  - 知识图谱（GraphRAG）增强 Agent 的长期记忆检索能力
  - 护栏设计：工具权限最小化 + human-in-the-loop 审批
- **行动**：研究 MCP 协议如何标准化工具接入，考虑是否引入知识图谱增强 MEMORY.md 检索

#### 3. 系统设计五大新兴模式 🟡

- **来源**：SystemDr Substack — *The Future of System Design: Emerging Patterns*
- **核心思想**：
  1. **Edge-Native + AI 智能调度** — 预判流量来源，预部署计算资源
  2. **WebAssembly 通用运行时** — 比容器小100x、微秒启动、能力沙箱
  3. **eBPF 零开销可观测性** — 内核级自动插桩，无性能损耗
  4. **AI-Native Service Mesh** — 语义路由，按请求意图分配到最优节点
  5. **碳感知调度** — 按碳强度动态迁移工作负载
- **价值评级**：🟡 中等 — 前瞻性强但目前落地需基础设施支持，eBPF 和 Edge 值得持续关注
- **应用场景**：
  - eBPF 可立即用于生产环境性能监控（如 Pixie、Cilium）
  - Wasm 可关注 Wasmtime/Wasmer 生态，适合边缘函数场景
  - 碳感知调度目前主要在大型云厂商层面，个人项目暂无直接应用
- **行动**：关注 eBPF 工具链（Cilium/Tetragon），下次有性能问题时尝试内核级 tracing

---

## 📋 知识贡献

| 日期 | 知识点 | 评级 | 状态 |
|------|--------|------|------|
| 2026-04-02 | 六边形架构（Ports & Adapters） | 🔴 | 待应用 |
| 2026-04-02 | Agentic AI 架构模式 | 🔴 | 待应用 |
| 2026-04-02 | 系统设计五大新兴模式 | 🟡 | 持续关注 |

---

## 📚 2026-04-03 至 2026-04-05 K8s 与 Go 技术栈深度修炼

> **学习周期**：3 天 | **学习条目**：36 条 | **价值评级**：🔴35 条 | 🟡1 条

### 学习总览

| 领域 | 条目数 | 🔴高价值 |
|------|--------|---------|
| K8s 集群架构 | 3 | 3 |
| K8s 网络与服务发现 | 6 | 6 |
| K8s 存储与状态管理 | 3 | 3 |
| K8s 调度与资源管理 | 6 | 6 |
| K8s 安全加固 | 5 | 5 |
| K8s 运维与监控 | 8 | 7 |
| K8s 控制器模式 | 3 | 3 |
| Go 语言进阶 | 2 | 2 |
| **合计** | **36** | **35** |

### 核心收获

**🏗️ 集群架构**：etcd 灾难恢复（快照+bump-revision）、Namespaces 多环境隔离

**🌐 网络**：Service 四种类型、Gateway API（Ingress 已冻结）、NetworkPolicy 零信任、DNS 服务发现

**💾 存储**：PV/PVC 动态供给、ConfigMap 四种使用方式、Immutable 防止配置漂移

**⚖️ 调度**：Requests/Limits/QoS、nodeAffinity/topologySpread、Taints/Tolerations、HPA/VPA 自动伸缩

**🛡️ 安全**：SecurityContext 最小权限、PSA 三级策略、ServiceAccount 禁用自动挂载

**🔧 运维**：Pod 生命周期、Lifecycle Hooks 优雅关闭、Probes 自愈、Sidecar/InitContainer 模式、日志/Metrics

**🎯 控制器**：Controller Pattern 声明式 API、CRD+Operator、容器镜像 digest

**🐍 Go**：GC 逃逸分析/GOGC 调优、错误处理 errors.Is/As/Unwrap

### 待实践验证
- [ ] etcd 备份恢复演练
- [ ] 生产 HPA 实践
- [ ] K8s 安全加固（PSA+NetworkPolicy）
- [ ] 服务网格/日志收集
- [ ] Go 高性能服务优化

---

## 🎯 待改进

- [ ] 下次新建项目时实践六边形架构
- [ ] 研究 MCP 协议标准化工具接入
- [ ] 关注 eBPF 工具链用于性能监控

---

## 📝 Lesson记录模板

> 每次学习记录必须填写以下四维评估

### [标题：解决什么问题]

**问题描述**：遇到了什么具体问题？

**解决方案**：
1. 具体步骤一
2. 具体步骤二
3. ...

**验证方式**：如何验证方案有效？

**适用范围**：这个方案在什么场景下适用？

---

### 四维评估（必须填写）

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔧 工具型 | /5 | 能写成代码/脚本/skill吗？ |
| 🎯 可操作 | /5 | 有具体步骤和示例吗？ |
| ✅ 可验证 | /5 | 有明确的成功标准吗？ |
| 🔄 可复用 | /5 | 其他Agent能直接应用吗？ |

**总分**：/20
- 🔴 < 11：不合格，不记录
- 🟠 11-14：合格，可记录
- 🟡 15-17：良好，优先推荐
- 🟢 18-20：优秀，立即打包为skill
