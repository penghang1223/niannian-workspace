# 🧪 测试用例库

**维护者:** 鉴微 (QA Engineer) 🛡️  
**最后更新:** 2026-03-26  
**版本:** v1.0

---

## 📁 测试文件结构

```
workspace/
├── test_*.js              # 集成测试文件
├── agents/qa_engineer/
│   └── test-reports/      # 测试报告
├── memory/
│   └── test_*.py          # Python 测试脚本
└── config/
    └── test_config.json   # 测试配置 (待创建)
```

---

## ✅ 现有测试用例

### 1. 群聊处理器测试 (`test_group_chat.js`)

**测试文件:** `/workspace/test_group_chat.js`  
**测试类型:** 集成测试  
**最后执行:** 2026-03-26 17:00

| 用例 ID | 测试场景 | 预期结果 | 状态 |
|---------|----------|----------|------|
| TC-GC-001 | 私聊消息处理 | 成功生成 Prompt，groupChat=false | ✅ |
| TC-GC-002 | 群聊消息（未@） | 忽略消息，ignored=true | ✅ |
| TC-GC-003 | 群聊消息（已@） | 需要群聊授权或管理员权限 | ⚠️ |
| TC-GC-004 | 群聊授权（管理员） | 授权成功，success=true | ⚠️ |
| TC-GC-005 | 群聊授权（普通用户） | 授权失败，提示非管理员 | ✅ |
| TC-GC-006 | 查看授权群聊 | 返回授权群聊列表 | ✅ |
| TC-GC-007 | 禁用群聊（管理员） | 禁用成功，success=true | ⚠️ |
| TC-GC-008 | 禁用群聊（普通用户） | 禁用失败，提示非管理员 | ✅ |

**备注:** ⚠️ 需要管理员测试用户才能完整测试

---

### 2. Python 测试脚本 (`memory/` 目录)

| 文件 | 测试内容 | 状态 |
|------|----------|------|
| `test_web_tools.py` | Web 工具测试 | 待执行 |
| `test_rag.py` | RAG 功能测试 | 待执行 |

---

## 📋 待补充测试用例

### 权限管理器测试
- [ ] TC-PM-001: 管理员角色识别
- [ ] TC-PM-002: 普通用户角色识别
- [ ] TC-PM-003: 权限检查（管理员）
- [ ] TC-PM-004: 权限检查（普通用户）
- [ ] TC-PM-005: 获取管理员列表

### 速率限制器测试
- [ ] TC-RL-001: 每分钟限制检查
- [ ] TC-RL-002: 每小时限制检查
- [ ] TC-RL-003: 每日限制检查
- [ ] TC-RL-004: 限制重置
- [ ] TC-RL-005: 自定义用户限制

### 隐私过滤器测试
- [ ] TC-PF-001: 敏感词过滤（群聊）
- [ ] TC-PF-002: 敏感词过滤（私聊）
- [ ] TC-PF-003: 隐私问题识别
- [ ] TC-PF-004: 群聊安全回复生成
- [ ] TC-PF-005: USER.md 敏感数据加载

### 多角色引擎测试
- [ ] TC-MR-001: 会话初始化
- [ ] TC-MR-002: 系统 Prompt 生成
- [ ] TC-MR-003: 用户消息注入
- [ ] TC-MR-004: 记忆保存
- [ ] TC-MR-005: 记忆加载

### 集成测试
- [ ] TC-INT-001: 完整消息处理流程
- [ ] TC-INT-002: 群聊隐私保护流程
- [ ] TC-INT-003: 速率限制触发流程
- [ ] TC-INT-004: 错误处理流程

---

## 🔧 测试配置

### 测试用户数据
```json
{
  "test_users": {
    "admin": {
      "open_id": "ou_admin_test_001",
      "role": "admin"
    },
    "beta_user": {
      "open_id": "ou_beta_test_001",
      "role": "beta_user"
    },
    "normal_user": {
      "open_id": "ou_a0406c4f0dd910da73bb748272663b95",
      "role": "user"
    }
  }
}
```

### 测试群聊数据
```json
{
  "test_groups": {
    "authorized_group": {
      "chat_id": "gc_test_authorized_001",
      "status": "active"
    },
    "disabled_group": {
      "chat_id": "gc_test_disabled_001",
      "status": "disabled"
    },
    "unauthorized_group": {
      "chat_id": "gc_test_unauthorized_001",
      "status": "pending"
    }
  }
}
```

---

## 📊 测试覆盖率统计

| 模块 | 文件数 | 测试用例数 | 覆盖率 |
|------|--------|------------|--------|
| 群聊处理器 | 1 | 8 | 60% |
| 权限管理器 | 1 | 0 | 0% |
| 速率限制器 | 1 | 0 | 0% |
| 隐私过滤器 | 1 | 0 | 0% |
| 多角色引擎 | 1 | 0 | 0% |
| **总计** | **5** | **8** | **12%** |

**目标覆盖率:** 80%  
**当前状态:** ⚠️ 需要补充测试

---

## 📝 测试执行记录

### 2026-03-26 17:00
- **执行者:** 鉴微 (QA Engineer)
- **测试类型:** 每日质量验证
- **测试结果:** 6/8 通过 (75%)
- **发现 Bug:** 3 个（已全部修复）
- **测试报告:** `agents/qa_engineer/test-reports/2026-03-26-quality-report.md`

---

## 🔗 相关文档

- [测试报告目录](./test-reports/)
- [质量验证流程](./workflow.md)
- [Bug 管理流程](./bug-tracking.md)

---

**维护说明:**
- 每次代码变更后应更新相关测试用例
- 每日 17:00 自动执行质量验证
- 测试覆盖率低于 80% 时需补充测试
