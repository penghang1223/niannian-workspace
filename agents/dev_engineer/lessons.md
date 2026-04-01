# 玄机 (dev_engineer) — 经验记录

## 2026-03-30 | TypeScript 编译性能优化

**来源**: TypeScript 官方 Wiki
**价值评级**: 🟡 中等（通用知识，适用于所有 TS 项目）
**学习反馈**: 学→评→用→反馈 闭环完成

### 核心收获
1. **interface extends > type intersection**: `interface B extends A` 比 `type B = A & ...` 编译更快，因为类型关系可缓存
2. **显式返回类型**: 公共 API 导出函数加显式返回类型注解，减少编译器推断开销
3. 预期改善：大型项目 tsc 编译提速 10-30%

### 实际应用场景
- ✅ 公共 API 模块：所有导出函数加返回类型注解
- ✅ 类型组合：用 `interface extends` 替代 `A & B & C` 嵌套交叉类型
- 📋 适用范围：Dashboard v4、OpenClaw 插件、Agent 通信模块

### 待验证
- [ ] 在 Dashboard v4 中实测编译速度差异
- [ ] 统计当前代码库中 type intersection 的使用量
