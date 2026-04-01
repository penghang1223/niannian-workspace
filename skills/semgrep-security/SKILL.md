# Semgrep Security — OWASP Top 10:2025 静态分析技能

> **Skill**: semgrep-security
> **用途**: 使用 Semgrep SAST 进行代码安全扫描，对标 OWASP Top 10:2025
> **触发条件**: 用户提到"安全扫描"、"SAST"、"Semgrep"、"代码审计"、"安全检查"

---

## 📋 OWASP Top 10:2025 完整列表与变化

### 2025 版本总览

| 编号 | 类别名称 | 变化说明 |
|------|---------|---------|
| A01 | Broken Access Control | 🔄 保持 #1，SSRF 合并入此类 |
| A02 | Security Misconfiguration | ⬆️ 从 #5 升至 #2 |
| **A03** | **Software Supply Chain Failures** | 🆕 **新增**（扩展自 A06:2021） |
| A04 | Cryptographic Failures | ⬇️ 从 #2 降至 #4 |
| A05 | Injection | ⬇️ 从 #3 降至 #5 |
| A06 | Insecure Design | ⬇️ 从 #4 降至 #6 |
| A07 | Authentication Failures | 🔄 维持 #7，更名（去掉"Identification"）|
| A08 | Software or Data Integrity Failures | 🔄 维持 #8 |
| A09 | Security Logging & Alerting Failures | 🔄 维持 #9，更名（强调 Alerting）|
| **A10** | **Mishandling of Exceptional Conditions** | 🆕 **新增**（24个CWE）|

### 🆕 A03:2025 — Software Supply Chain Failures（供应链安全）

**背景**: 社区调查中 50% 受访者将其排在 #1。从 A06:2021（使用有漏洞组件）扩展为全面的供应链安全问题。

**覆盖范围**:
- 有漏洞/过时/未维护的第三方依赖
- CI/CD 管道安全弱于被构建的系统
- 依赖链（传递依赖）未跟踪
- 组件来源不可信、无签名验证
- 缺少职责分离（一人写代码并直接上线）

**关键 CWE**: CWE-477（废弃函数）、CWE-1104（未维护组件）、CWE-1329（不可更新依赖）、CWE-1395（依赖有漏洞第三方组件）

**Semgrep 检测能力**: ✅ 通过 `p/security-audit` 规则集检测已知漏洞模式；配合 `semgrep scan --config p/owasp-top-ten` 可覆盖

### 🆕 A10:2025 — Mishandling of Exceptional Conditions（异常处理）

**背景**: 全新类别，包含 24 个 CWE，从"代码质量"拆分出来，更精确聚焦异常处理。

**覆盖范围**:
- 错误信息泄露敏感数据（CWE-209）
- 缺少参数处理（CWE-234）
- 权限不足处理不当（CWE-274）
- 空指针解引用（CWE-476）
- Fail Open（CWE-636）— 应关闭时反而开放
- 不一致的异常处理导致系统进入不可预测状态

**防御措施**:
- 在异常发生处就地捕获处理，不要仅靠全局兜底
- 关键事务失败时回滚（Fail Closed）
- 统一错误处理 + 速率限制 + 输入验证
- 全局异常处理器作为最后防线

**Semgrep 检测能力**: ✅ 可检测空指针解引用、未处理异常、敏感信息泄露等模式

---

## 🔧 Semgrep 安装

### 快速安装

```bash
# macOS (推荐)
brew install semgrep

# pip (通用)
pip install semgrep

# Docker
docker pull semgrep/semgrep

# 验证安装
semgrep --version
```

### 首次使用

```bash
# 登录（可选，用于 Semgrep App 集成）
semgrep login

# 快速测试 - 扫描当前目录
semgrep scan --config auto
```

---

## 🔍 Semgrep 基本使用

### 常用命令

```bash
# 使用官方 OWASP Top 10 规则集扫描
semgrep scan --config p/owasp-top-ten ./src

# 使用安全审计规则集
semgrep scan --config p/security-audit ./src

# 使用 CI 安全规则（含 Supply Chain）
semgrep scan --config p/ci ./src

# 组合多个规则集
semgrep scan --config p/owasp-top-ten --config p/security-audit ./src

# 仅扫描特定语言
semgrep scan --config p/owasp-top-ten --lang python ./src

# 排除目录
semgrep scan --config p/owasp-top-ten --exclude tests --exclude vendor ./src

# 输出 SARIF 格式（供 GitHub/GitLab 集成）
semgrep scan --config p/owasp-top-ten --sarif -o results.sarif ./src

# 输出 JSON 格式
semgrep scan --config p/owasp-top-ten --json -o results.json ./src

# 只看 ERROR 级别
semgrep scan --config p/owasp-top-ten --severity ERROR ./src

# 修复自动修复建议（dry-run）
semgrep scan --config p/owasp-top-ten --autofix --dryrun ./src
```

### 自定义规则示例

```yaml
# .semgrep/supply-chain-check.yml
rules:
  - id: unpinned-dependency
    patterns:
      - pattern: |
          import $X
    message: "考虑锁定依赖版本以避免供应链攻击 (OWASP A03:2025)"
    languages: [python]
    severity: WARNING

  - id: missing-error-handling
    patterns:
      - pattern: |
          try:
              ...
          except:
              pass
    message: "空 except 块可能导致异常被静默吞掉 (OWASP A10:2025 CWE-636)"
    languages: [python]
    severity: ERROR

  - id: error-message-info-leak
    patterns:
      - pattern: |
          raise Exception(...)
    message: "错误消息可能泄露内部信息 (OWASP A10:2025 CWE-209)"
    languages: [python]
    severity: WARNING
```

使用自定义规则:
```bash
semgrep scan --config .semgrep/ --config p/owasp-top-ten ./src
```

---

## 🚀 CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/semgrep.yml
name: Semgrep SAST
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # 每周一 UTC 06:00

jobs:
  semgrep:
    name: Semgrep Scan
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v4

      - name: Run Semgrep
        run: |
          semgrep ci \
            --config p/owasp-top-ten \
            --config p/security-audit \
            --sarif -o semgrep-results.sarif \
            --json -o semgrep-results.json
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep-results.sarif
```

### GitLab CI

```yaml
# .gitlab-ci.yml
semgrep-sast:
  stage: test
  image: semgrep/semgrep
  script:
    - semgrep ci
        --config p/owasp-top-ten
        --gitlab-sast -o gl-sast-report.json
  artifacts:
    reports:
      sast: gl-sast-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### 本地 Git Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: 'v1.56.0'
    hooks:
      - id: semgrep
        args: ['--config', 'p/owasp-top-ten', '--error']
```

### Makefile 集成

```makefile
.PHONY: security-scan
security-scan:
	semgrep scan --config p/owasp-top-ten --config p/security-audit \
		--severity ERROR --json -o security-report.json ./src
	@echo "扫描完成，报告: security-report.json"

.PHONY: security-scan-ci
security-scan-ci:
	semgrep ci --config p/owasp-top-ten --sarif -o semgrep.sarif
```

---

## 📊 扫描结果解读

### 输出结构（JSON）

```json
{
  "results": [
    {
      "check_id": "python.lang.security.audit.formatted-sql-query",
      "path": "src/app.py",
      "start": { "line": 42, "col": 5 },
      "end": { "line": 42, "col": 55 },
      "extra": {
        "severity": "ERROR",
        "message": "Detected string concatenation in SQL query...",
        "metadata": {
          "owasp": ["A05:2025 - Injection"],
          "cwe": ["CWE-89: SQL Injection"],
          "confidence": "HIGH",
          "references": ["https://owasp.org/Top10/2025/A05_2025-Injection/"]
        },
        "lines": "cursor.execute(\"SELECT * FROM users WHERE id=\" + user_id)"
      }
    }
  ],
  "errors": [],
  "paths": { "scanned": ["src/app.py"] }
}
```

### 关键字段

| 字段 | 含义 |
|------|------|
| `check_id` | 规则 ID，格式: `语言.模块.规则名` |
| `severity` | `ERROR`（必须修复）、`WARNING`（建议修复）、`INFO`（参考） |
| `metadata.owasp` | 对应的 OWASP Top 10 类别 |
| `metadata.cwe` | CWE 编号 |
| `metadata.confidence` | `HIGH` / `MEDIUM` / `LOW` |
| `path` + `start` | 问题文件路径和行号 |

### 结果分级处理策略

```
ERROR + HIGH confidence  → 🚨 必须修复，阻断合并
WARNING + HIGH confidence → ⚠️  建议修复，记录跟踪
LOW confidence           → ℹ️  人工审核确认
已知误报                  → 用 # nosem 注释或 .semgrepignore 忽略
```

### 忽略误报

```python
# 单行忽略
result = dangerous_function()  # nosem: python.lang.security.xxx

# 文件级忽略 → 在 .semgrepignore 中添加
# vendor/
# tests/fixtures/
```

### SARIF 结果查看

```bash
# 安装 SARIF CLI 工具
npm install -g @microsoft/sarif-multitool

# 查看摘要
sarif summary results.sarif

# VS Code: 安装 "SARIF Viewer" 扩展直接查看
```

---

## 🎯 按 OWASP 类别扫描映射

| OWASP 2025 类别 | Semgrep 规则集 | 关键检测项 |
|-----------------|---------------|-----------|
| A01 Broken Access Control | `p/access-control` | 授权缺失、IDOR、路径遍历 |
| A02 Security Misconfiguration | `p/security-audit` | 默认凭证、调试模式、CORS |
| A03 Supply Chain Failures | `p/dependency-check` + SCA | 过时依赖、未锁定版本 |
| A04 Cryptographic Failures | `p/crypto` | 弱算法、硬编码密钥 |
| A05 Injection | `p/owasp-top-ten` | SQL注入、XSS、命令注入 |
| A06 Insecure Design | `p/security-audit` | 业务逻辑缺陷 |
| A07 Authentication Failures | `p/authentication` | 弱密码策略、会话管理 |
| A08 Integrity Failures | `p/security-audit` | 不安全反序列化、CI/CD |
| A09 Logging Failures | `p/security-audit` | 日志遗漏、无告警 |
| A10 Exception Mishandling | `p/security-audit` | 空catch、信息泄露、fail-open |

---

## 💡 最佳实践

1. **分阶段集成**: 先用 `p/owasp-top-ten` 基础扫描，再逐步增加规则集
2. **CI 中只阻断 ERROR**: `--severity ERROR` 避免 WARNING 阻断开发
3. **定期全量扫描**: cron job 使用完整规则集做深度扫描
4. **结合 SCA**: Semgrep SAST + 依赖扫描工具（如 `npm audit`、`pip-audit`）组合使用
5. **持续更新规则**: `semgrep --version` 确认版本，定期更新
6. **团队培训**: 让开发者理解 OWASP 2025 新增的 A03（供应链）和 A10（异常处理）

---

## 🔗 参考链接

- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- Semgrep 官方文档: https://semgrep.dev/docs/
- Semgrep Registry: https://semgrep.dev/r
- CWE 数据库: https://cwe.mitre.org/
