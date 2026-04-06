# 💻 天工技术栈 - K8s 与 Go 深度修炼

> **所属 Agent**：天工（tiangong）- 云梦泽首席架构师  
> **学习周期**：2026-04-03 至 2026-04-05  
> **定位**：Kubernetes 云原生架构 + Go 高性能开发  
> **文档位置**：`agents/tiangong/k8s-go-study-2026-04.md`

---

## 📊 学习总览

| 领域 | 学习条目数 | 🔴高价值 | 🟡一般有用 |
|------|-----------|---------|-----------|
| K8s 集群架构 | 3 | 3 | 0 |
| K8s 网络与服务发现 | 6 | 6 | 0 |
| K8s 存储与状态管理 | 3 | 3 | 0 |
| K8s 调度与资源管理 | 6 | 6 | 0 |
| K8s 安全加固 | 5 | 5 | 0 |
| K8s 运维与监控 | 8 | 7 | 1 |
| K8s 控制器模式 | 3 | 3 | 0 |
| Go 语言进阶 | 2 | 2 | 0 |
| **合计** | **36** | **35** | **1** |

---

## 🏗️ 一、K8s 集群架构

### 1.1 集群组件全景 🔴
**来源**：https://kubernetes.io/docs/concepts/overview/components/

**核心收获**：
- 控制平面五大组件：kube-apiserver（唯一入口）、etcd（真理来源）、kube-scheduler、kube-controller-manager、cloud-controller-manager
- 节点三大组件：kubelet（节点代理）、kube-proxy（网络规则）、Container Runtime
- 关键设计原则：apiserver 是唯一入口，etcd 存储一切，声明式 API

**应用场景**：
- 故障排查：Pod Pending→scheduler；Pod 不启动→kubelet；API 超时→apiserver
- 高可用部署：控制平面多副本 + etcd 集群 + 负载均衡

---

### 1.2 etcd 灾难恢复 🔴
**来源**：https://etcd.io/docs/v3.5/op-guide/recovery/

**核心收获**：
- N 节点集群容忍 (N-1)/2 永久故障（5 节点容忍 2 节点）
- 在线快照：`etcdctl snapshot save snapshot.db`
- 恢复流程：`etcdutl snapshot restore` + `--bump-revision 1000000000 --mark-compacted`

**应用场景**：
- 定期备份：每天 `etcdctl snapshot save` 到远程存储
- 灾难恢复：revision bump 防止 controller 缓存不一致

---

### 1.3 Namespaces 资源隔离 🔴
**来源**：https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/

**核心收获**：
- 初始 Namespace：default、kube-system、kube-public、kube-node-lease
- DNS 解析：`<service>.<namespace>.svc.cluster.local`
- Cluster-scoped 资源：Node、PersistentVolume、StorageClass、Namespace 自身、ClusterRole

---

## 🌐 二、K8s 网络与服务发现

### 2.1 Service 服务抽象 🔴
**来源**：https://kubernetes.io/docs/concepts/services-networking/service/

**核心收获**：
- 四种 Service 类型：ClusterIP、NodePort、LoadBalancer、ExternalName
- Headless Service：`spec.clusterIP: None`，DNS 直接解析到 Pod IP 集合
- EndpointSlice：替代 Endpoints，支持大规模集群

---

### 2.2 Ingress 七层路由 🔴
**来源**：https://kubernetes.io/docs/concepts/services-networking/ingress/

**核心收获**：
- Ingress 定义：管理 HTTP/HTTPS 访问，提供负载均衡、SSL 终止
- PathType：Prefix、Exact、ImplementationSpecific
- ⚠️ 已冻结：官方推荐使用 **Gateway API**

---

### 2.3 Gateway API 下一代流量入口 🔴
**来源**：https://gateway-api.sigs.k8s.io/concepts/api-overview/

**核心收获**：
- 三种角色：Infrastructure Provider、Cluster Operator、Application Developer
- 核心资源：GatewayClass、Gateway、Routes（HTTPRoute/TLSRoute/GRPCRoute）
- 与 Ingress 对比：分层模型、多协议支持、角色分离

---

### 2.4 DNS 服务发现 🔴
**来源**：https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/

**核心收获**：
- Service DNS 格式：`my-svc.my-namespace.svc.cluster-domain.example`
- Headless Service：解析到所有匹配 Pod IP 集合
- Pod DNS Policy：Default、ClusterFirst（默认）、ClusterFirstWithHostNet、None

---

### 2.5 NetworkPolicy 网络防火墙 🔴
**来源**：https://kubernetes.io/docs/concepts/services-networking/network-policies/

**核心收获**：
- 两种隔离类型：Ingress（入站）、Egress（出站）
- 前提条件：需要 CNI 插件支持（Calico/Cilium/Weave）
- 规则叠加：多条 Policy 应用于同一 Pod 时，允许的连接是并集

---

### 2.6 Labels and Selectors 🔴
**来源**：https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

**核心收获**：
- Label vs Annotation：Label 用于标识和选择，Annotation 存储元数据
- 两种选择器：Equality-based（=,==,!=）、Set-based（in,notin,exists）
- 常用 Label 约定：`app.kubernetes.io/name`、`app.kubernetes.io/instance`

---

## 💾 三、K8s 存储与状态管理

### 3.1 PersistentVolume 持久化存储 🔴
**来源**：https://kubernetes.io/docs/concepts/storage/persistent-volumes/

**核心收获**：
- PV/PVC 分离设计：PV 是集群存储资源，PVC 是存储请求
- 三种供给模式：Static、Dynamic、Empty
- 访问模式：RWO、ROX、RWX
- 回收策略：Retain、Delete、Recycle（已废弃）

---

### 3.2 Volumes 容器存储 🔴
**来源**：https://kubernetes.io/docs/concepts/storage/volumes/

**核心收获**：
- emptyDir：临时空目录，Pod 删除时销毁
- configMap/secret：挂载为文件/目录
- projected：合并多个源到同一目录
- downwardAPI：将 Pod 元数据暴露为文件

---

### 3.3 ConfigMap 配置管理 🔴
**来源**：https://kubernetes.io/docs/concepts/configuration/configmap/

**核心收获**：
- 四种使用方式：环境变量、命令行参数、Volume 挂载、API 读取
- Immutable ConfigMap：`immutable: true` 防止意外修改
- 更新行为：Volume 挂载自动同步（默认 1 分钟）

---

## ⚖️ 四、K8s 调度与资源管理

### 4.1 容器资源管理 Requests/Limits/QoS 🔴
**来源**：https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

**核心收获**：
- Requests vs Limits：Request 用于调度，Limit 用于限制
- CPU 限制机制：cgroups CPU throttling
- 内存限制机制：cgroups OOM kill
- QoS 等级：Guaranteed、Burstable、BestEffort

---

### 4.2 kube-scheduler 调度机制 🔴
**来源**：https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/

**核心收获**：
- 两步调度算法：Filtering → Scoring
- Filtering：PodFitsResources、NodeSelector/Affinity、Taint/Toleration
- Scoring：NodeResourcesFit、ImageLocality、InterPodAffinity

---

### 4.3 节点调度约束 🔴
**来源**：https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/

**核心收获**：
- 四种方式：nodeSelector、nodeAffinity、podAffinity/antiAffinity、topologySpreadConstraints
- nodeAffinity 两种类型：required（硬约束）、preferred（软约束）
- topologySpreadConstraints：maxSkew、whenUnsatisfiable

---

### 4.4 Taints and Tolerations 🔴
**来源**：https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

**核心收获**：
- 三种 Effect：NoSchedule、PreferNoSchedule、NoExecute
- 多污点过滤模型：剩余污点生效
- 内置污点：not-ready、unreachable、disk-pressure

---

### 4.5 HPA 水平自动伸缩 🔴
**来源**：https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/

**核心收获**：
- 工作原理：基于 resource request 计算利用率，每 15 秒同步
- 三种指标类型：Resource、Custom、External Metrics
- 伸缩行为控制：scaleDownStabilizationSeconds（默认 300 秒）

---

### 4.6 VPA 垂直自动伸缩 🟡
**来源**：https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/README.md

**核心收获**：
- 三种更新模式：Off、Initial、Auto
- 三大组件：Recommender、Updater、Admission Controller
- 与 HPA 互斥：同一资源不能同时用 HPA 和 VPA

---

## 🛡️ 五、K8s 安全加固

### 5.1 Security Context 安全上下文 🔴
**来源**：https://kubernetes.io/docs/tasks/configure-pod-container/security-context/

**核心收获**：
- 用户/组设置：runAsUser、runAsGroup、fsGroup
- 特权控制：allowPrivilegeEscalation（推荐 false）、readOnlyRootFilesystem
- Linux Capabilities：`drop: ["ALL"]` + 按需添加

---

### 5.2 Pod Security Admission (PSA) 🔴
**来源**：https://kubernetes.io/docs/concepts/security/pod-security-admission/

**核心收获**：
- 三种执行模式：enforce、audit、warn
- 三种策略级别：privileged、baseline、restricted
- 命名空间标签配置：`pod-security.kubernetes.io/enforce: baseline`

---

### 5.3 PSP 到 PSA 迁移 🔴
**来源**：https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/

**核心收获**：
- PSP 移除时间线：1.21 弃用→1.25 移除
- PSA 与 PSP 关键差异：PSA 不 mutating、仅三级标准
- 迁移步骤：dry-run → audit → warn → enforce

---

### 5.4 ServiceAccount 身份认证 🔴
**来源**：https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/

**核心收获**：
- Token 自动挂载：`/var/run/secrets/kubernetes.io/serviceaccount/token`
- 禁用自动挂载：`automountServiceAccountToken: false`
- 最小权限原则：每个 SA 只授予必要权限

---

### 5.5 LimitRange 资源约束 🔴
**来源**：https://kubernetes.io/docs/concepts/policy/limit-range/

**核心收获**：
- 与 ResourceQuota 区别：ResourceQuota 控总额，LimitRange 控单体
- 约束类型：min/max、default、defaultRequest、maxLimitRequestRatio

---

## 🔧 六、K8s 运维与监控

### 6.1 Pod 生命周期 🔴
**来源**：https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/

**核心收获**：
- 五种 Pod Phase：Pending、Running、Succeeded、Failed、Unknown
- 容器状态：Waiting、Running、Terminated
- Pod 不"重新调度"：节点故障时由新 Pod（新 UID）替换

---

### 6.2 Container Lifecycle Hooks 🔴
**来源**：https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/

**核心收获**：
- 两种钩子：PostStart、PreStop
- 三种处理器：Exec、HTTP、Sleep
- 交付保证：At least once（需幂等）

---

### 6.3 Liveness/Readiness/Startup Probes 🔴
**来源**：https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

**核心收获**：
- Liveness：检测存活，失败则重启
- Readiness：检测就绪，失败则从 Service 移除
- Startup：检测启动，成功后才启用其他 probes

---

### 6.4 Sidecar Containers 🔴
**来源**：https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/

**核心收获**：
- 实现机制：`initContainers` + `restartPolicy: Always`
- 终止顺序：先停主容器，后停 sidecar
- 典型用例：日志收集、服务网格、监控代理

---

### 6.5 Init Containers 🔴
**来源**：https://kubernetes.io/docs/concepts/workloads/pods/init-containers/

**核心收获**：
- 执行顺序：按顺序执行，全部完成后才启动应用容器
- 典型用途：等待依赖、克隆配置、数据库迁移

---

### 6.6 日志架构 🔴
**来源**：https://kubernetes.io/docs/concepts/cluster-administration/logging/

**核心收获**：
- 日志设计原则：写 stdout/stderr
- kubectl logs：`--previous` 看崩溃前日志
- 日志轮转：containerLogMaxSize（默认 10Mi）、containerLogMaxFiles（默认 5）

---

### 6.7 Metrics Pipeline 🔴
**来源**：https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/

**核心收获**：
- 架构：cAdvisor→kubelet→metrics-server→Metrics API
- Metrics API 用途：HPA、VPA、`kubectl top`

---

### 6.8 kubectl 速查 🔴
**来源**：https://kubernetes.io/docs/reference/kubectl/quick-reference/

**核心收获**：
- 自动补全：Bash/Zsh/Fish
- JSONPath 查询：`kubectl get pod -o jsonpath='{.items[*].metadata.name}'`
- 调试命令：logs、describe、exec、debug、top

---

## 🎯 七、K8s 控制器模式

### 7.1 Controller Pattern 🔴
**来源**：https://kubernetes.io/docs/concepts/architecture/controller/

**核心收获**：
- 控制器定义：控制循环，使当前状态趋近期望状态
- 两种控制方式：通过 API server、直接控制外部系统
- 设计原则：简单控制器、职责分离、可组合性

---

### 7.2 Custom Resources (CRD) 🔴
**来源**：https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/

**核心收获**：
- Custom Resource + Custom Controller = Operator Pattern
- 何时使用 CRD：需要声明式 API、需要用 kubectl 读写
- 何时使用独立 API：非声明式、存储大量数据、高带宽访问

---

### 7.3 容器镜像管理 🔴
**来源**：https://kubernetes.io/docs/concepts/containers/images/

**核心收获**：
- 镜像命名：`[registry]/image-name[:tag][@digest]`
- Tag vs Digest：Tag 可变，Digest 不可变
- imagePullPolicy：IfNotPresent、Always、Never
- ⚠️ 避免使用 latest

---

## 🐍 八、Go 语言进阶

### 8.1 Go GC 原理与优化 🔴
**来源**：https://go.dev/doc/gc-guide

**核心收获**：
- 栈分配 vs 堆分配：逃逸分析决定
- GC 触发条件：堆内存达到阈值（GOGC 控制）
- GC 调优：GOGC=100（默认）、GOGC=50（更频繁）、GOGC=200（更少）
- 减少 GC 压力：减少堆分配、sync.Pool 复用、预分配 slice/map

---

### 8.2 Go 错误处理 🔴
**来源**：https://go.dev/blog/error-handling-and-go

**核心收获**：
- error 接口：`type error interface { Error() string }`
- 自定义错误类型：实现 error 接口 + 额外字段
- Go 1.13+：errors.Is()、errors.As()、errors.Unwrap()

---

## 📝 后续行动计划

### 待实践验证（🔴 高价值但未实践）
- [ ] **etcd 备份恢复演练**：定期快照 + 灾难恢复测试
- [ ] **生产 HPA 实践**：基于 CPU/QPS 自动伸缩
- [ ] **K8s 安全加固**：PSA Restricted + NetworkPolicy + SecurityContext
- [ ] **服务网格/日志收集**：Istio sidecar + Fluentd DaemonSet
- [ ] **Go 高性能服务**：GC 优化 + sync.Pool 对象复用

---

## 🔄 学习闭环状态

| 步骤 | 状态 | 说明 |
|------|------|------|
| 学 | ✅ 完成 | 36 条学习条目 |
| 评 | ✅ 完成 | 35 条🔴，1 条🟡 |
| 用 | ⏳ 待实践 | 大部分知识待生产环境验证 |
| 反馈 | ⏳ 待回填 | 下次心跳时回填实际效果 |

---

*文档创建时间：2026-04-05*  
*最后更新：2026-04-05*  
*维护者：天工（云梦泽首席架构师）*
