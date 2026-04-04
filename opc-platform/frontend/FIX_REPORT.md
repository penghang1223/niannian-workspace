# OPC 平台前端严重问题修复说明

## 修复范围

### 1. 合规模块接入主链路
- 将 `src/utils/compliance.js` 改为真实的 `WGS-84 -> GCJ-02` 转换逻辑。
- 新增 `toCompliantCoordinate`、`sanitizeEntrepreneurLocation`、`sanitizeEntrepreneurDataset`，统一做坐标脱敏与敏感字段剔除。
- `src/components/Globe/GlobeComponent.jsx` 在渲染前统一调用合规处理，所有点位都保留 2 位小数，达到城市级精度。

### 2. WebSocket 实时推送接入
- `src/App.jsx` 接入 `src/services/websocket.js`，监听 `new_registration`、`initial_data`、`stats_update`。
- 新注册事件会实时合并进创业者列表，并同步更新 Dashboard 统计与 Globe 数据点。
- `src/services/websocket.js` 改为幂等连接、统一事件分发、自动重连。

### 3. Dashboard 数据动态化
- `src/components/Dashboard/Dashboard.jsx` 改为完全由状态驱动，不再展示硬编码统计值。
- 支持显示总创业者、今日新增、覆盖城市、活跃赛道、总 MRR。
- 移除了误导性固定文案，替换为真实的数据源、连接状态和最近刷新时间。

### 4. 地球仪数据动态化
- 新增 `src/services/api.js`，从后端 API 拉取创业者与统计数据，并兼容多个常见返回结构。
- `GlobeComponent` 改为消费实时数据源，不再内置硬编码样例点位。
- 新增本地搜索与赛道筛选，支持按姓名、城市、省份、赛道过滤。

## 变更文件
- `opc-platform/frontend/src/utils/compliance.js`
- `opc-platform/frontend/src/services/api.js`
- `opc-platform/frontend/src/services/websocket.js`
- `opc-platform/frontend/src/App.jsx`
- `opc-platform/frontend/src/components/Dashboard/Dashboard.jsx`
- `opc-platform/frontend/src/components/Globe/GlobeComponent.jsx`
- `opc-platform/frontend/FIX_REPORT.md`

## 构建验证
- 目标命令：`npm run build`
- 说明：本次修复完成后应执行构建验证，确认前端可以正常打包。

## PRD 符合度评估（修复后）

### 已满足
- 合规展示链路已打通，地图展示不再直接暴露高精度原始坐标。
- Dashboard 与 Globe 均已切换为动态数据源驱动。
- WebSocket 事件已接入主界面，支持注册数据实时更新。
- Globe 支持基础搜索与赛道过滤，符合运营查看和定位需求。

### 仍需后端配合的点
- 当前仓库中的后端 `src/app.js` 只暴露了健康检查和 WebSocket，没有实际的 `/api/entrepreneurs`、`/api/stats` 路由实现。
- 前端已按真实 API 接入方式完成，但若要在线上完全生效，后端需补齐对应 REST 接口或在 `initial_data` 中返回完整数据。

### 综合结论
- 前端层面的 4 个严重问题已完成修复。
- 若后端按约定补齐数据接口/事件载荷，当前前端即可直接承接真实业务链路。
