# 测试自动化项目模板

> 用 Claude Code 在 VS Code 中自动生成和管理测试用例

## 核心思路

**一个 MD 文件（TESTING.md）= 整个测试项目的索引**

每次打开项目，Claude 会自动读取 `TESTING.md`，知道：
- ✅ 哪些测试已写
- 🔴 哪些测试还没写
- 📝 测试规范是什么
- 🔧 怎么运行测试

## 项目结构

```
├── TESTING.md              ← 测试索引（最重要！）
├── CLAUDE.md               ← Claude 项目配置（自动加载）
├── src/                    ← 源代码
├── __tests__/              ← 测试文件
├── __mocks__/              ← Mock 数据
├── jest.config.js          ← Jest 配置
├── tsconfig.json           ← TypeScript 配置
└── package.json            ← 项目配置
```

## 快速开始

### 1. 复制模板
```bash
cp -r ~/.openclaw/workspace/templates/test-automation-project ./my-test-project
cd my-test-project
npm install
```

### 2. 修改 TESTING.md
编辑 `TESTING.md`，把项目信息改成你的：
- 修改项目名、测试框架、语言
- 列出你的模块和当前进度
- 定义当前任务

### 3. 在 VS Code 中打开
```bash
code .
```

### 4. 对 Claude 说
```
帮我写 TESTING.md 中 "🔴 P0 - 高优先级" 的任务。
写完后运行 npm test 验证，然后更新 TESTING.md 的进度。
```

## 工作流

```
1. 打开 VS Code → Claude 自动读 CLAUDE.md + TESTING.md
2. 告诉 Claude 写哪个模块的测试
3. Claude 写测试 → 运行验证 → 更新 TESTING.md
4. 检查进度，继续下一个模块
```

## 为什么用这种方式？

1. **持久化** — MD 文件不会丢，Git 可追踪
2. **Claude 自动读** — CLAUDE.md 保证每次对话都加载
3. **人类可读** — 不只是给 AI 看的，测试工程师也能直接编辑
4. **渐进式** — 写完一个模块，打个勾，继续下一个
5. **团队协作** — 所有人都能看到进度和任务

## Prompt 示例

```
读取 TESTING.md，完成 "商品 API 测试补充" 任务。
写完运行 npm test 验证通过，然后更新 TESTING.md 进度。
```

```
运行 npm run test:coverage，根据结果补充覆盖率低于 80% 的测试。
完成后更新 TESTING.md 中的覆盖率数据。
```

```
为 payment.ts 写测试，覆盖正常支付、支付超时、余额不足、退款场景。
Mock 数据库，写完后运行测试验证。
```
