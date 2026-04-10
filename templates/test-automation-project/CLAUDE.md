# CLAUDE.md

> 本文件在每次 Claude Code 对话开始时自动读取。

---

## 项目概述
这是一个测试自动化项目，用 Claude 自动生成和维护测试用例。

## 测试规范
**详见 `TESTING.md`** — 包含测试进度、任务列表、命名规范、覆盖率目标。

## 关键规则
1. **先读 TESTING.md** — 了解当前进度和下一步做什么
2. **写完测试后运行** — `npm test` 验证通过
3. **更新 TESTING.md** — 完成后更新进度表和变更记录
4. **遵循命名规范** — 用例名用中文：`应该 [预期行为] 当 [条件] 时`

## 运行命令
```bash
npm test                    # 运行所有测试
npm test -- -t "关键词"      # 运行特定用例
npm run test:coverage       # 覆盖率报告
npm run test:watch          # 监听模式
```

## 技术栈
- **框架**: Jest + TypeScript
- **API 测试**: supertest
- **Mock**: jest.mock() + __mocks__/ 目录

## 目录结构
```
src/           → 源代码
__tests__/     → 测试文件
__mocks__/     → Mock 数据
TESTING.md     → 测试计划索引
```
