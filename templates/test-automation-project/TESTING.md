# 测试计划 & 索引

> 本文件是 Claude 的测试工作指南。每次打开项目时 Claude 必须读取此文件。
> 
> 项目：[项目名称]  
> 测试框架：Jest + supertest  
> 语言：TypeScript  
> 最后更新：2026-04-09

---

## 📋 项目测试概览

### 测试目录结构
```
├── TESTING.md                    ← 本文件（测试索引）
├── src/                          ← 源代码
│   ├── auth/
│   ├── api/
│   └── utils/
├── __tests__/                    ← 测试文件
│   ├── auth.test.ts              ← ✅ 已完成
│   ├── api/
│   │   ├── users.test.ts         ← ✅ 已完成
│   │   └── products.test.ts      ← 🔄 进行中
│   └── utils/
│       └── helpers.test.ts       ← ⏳ 待开始
└── __mocks__/                    ← Mock 数据
    ├── database.ts
    └── external-api.ts
```

### 当前进度

| 模块 | 文件 | 测试数 | 覆盖率 | 状态 |
|------|------|--------|--------|------|
| 认证模块 | auth.ts | 12 | 92% | ✅ 完成 |
| 用户 API | api/users.ts | 8 | 85% | ✅ 完成 |
| 商品 API | api/products.ts | 3 | 45% | 🔄 进行中 |
| 工具函数 | utils/helpers.ts | 0 | 0% | ⏳ 待开始 |
| 支付模块 | services/payment.ts | 0 | 0% | ⏳ 待开始 |

---

## 🎯 当前任务（Claude 优先处理这些）

### 🔴 P0 - 高优先级

#### 1. 商品 API 测试补充
- **文件**: `api/products.ts`
- **已覆盖**: GET /products, GET /products/:id
- **缺少的**:
  - [ ] POST /products 创建商品（正常 + 缺少必填字段 + 重复 SKU）
  - [ ] PUT /products/:id 更新商品
  - [ ] DELETE /products/:id 删除商品
  - [ ] 分页参数测试（page, limit）
  - [ ] 排序参数测试（sort, order）

#### 2. 工具函数测试
- **文件**: `utils/helpers.ts`
- **函数列表**:
  - [ ] `formatCurrency(amount, currency)` — 金额格式化
  - [ ] `validateEmail(email)` — 邮箱验证
  - [ ] `generateSlug(title)` — URL 友好的 slug
  - [ ] `parseDate(dateStr)` — 日期解析（含错误处理）

### 🟡 P1 - 中优先级

#### 3. 支付模块测试
- **文件**: `services/payment.ts`
- **场景**:
  - [ ] 正常支付
  - [ ] 支付超时
  - [ ] 余额不足
  - [ ] 退款流程
  - [ ] 并发支付（防重复）

---

## 📝 测试规范（Claude 必须遵守）

### 文件命名
- 测试文件：`xxx.test.ts`（与源文件同名 + .test）
- 放在 `__tests__/` 目录下，与 `src/` 平级

### 测试结构
```typescript
describe('模块名称', () => {
  describe('函数/接口名称', () => {
    it('应该 [预期行为] 当 [条件] 时', () => {
      // given
      const input = ...
      
      // when
      const result = targetFunction(input)
      
      // then
      expect(result).toEqual(...)
    })
  })
})
```

### 用例命名规范
```
✅ 应该返回用户列表当请求 GET /users 时
✅ 应该返回401当未提供 token 时
✅ 应该抛出错误当邮箱格式无效时
❌ 测试用户列表
❌ test 1
```

### 必须覆盖的测试类型
1. **正向用例** — 正常输入，预期成功
2. **边界值** — 最大值、最小值、空值、null、undefined
3. **异常用例** — 错误输入、权限不足、资源不存在
4. **业务规则** — 特殊业务逻辑（如"同一用户每天只能退款一次"）

### Mock 规则
- 外部 API 调用必须 mock（放在 `__mocks__/`）
- 数据库操作使用内存数据库或 mock
- 时间相关函数使用 `jest.useFakeTimers()`

---

## 🔧 运行命令

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- __tests__/api/users.test.ts

# 运行特定测试用例（模糊匹配）
npm test -- -t "应该返回用户列表"

# 生成覆盖率报告
npm run test:coverage

# 监听模式（开发时用）
npm run test:watch
```

---

## ⚠️ 已知问题 & 跳过项

| 用例 | 原因 | 计划修复 |
|------|------|---------|
| 支付网关超时测试 | 需要真实网关，暂用 mock | Phase 3 接测试环境 |
| 并发测试 | Jest 默认串行执行 | 升级 Jest 配置 |

---

## 📊 覆盖率目标

| 类型 | 目标 | 当前 |
|------|------|------|
| 行覆盖率 | ≥ 80% | 62% |
| 分支覆盖率 | ≥ 70% | 45% |
| 函数覆盖率 | ≥ 85% | 70% |

---

## 📝 变更记录

| 日期 | 操作 | 详情 |
|------|------|------|
| 2026-04-09 | 初始化 | 创建测试计划，定义规范 |
| 2026-04-09 | 完成认证模块 | 12 条用例，覆盖率 92% |
| 2026-04-09 | 完成用户 API | 8 条用例，覆盖率 85% |

---

> 💡 Claude：每次完成测试后，请更新本文件中的进度表和变更记录。
