# API Security Scanner

> API 层安全测试工具集 — 覆盖 OWASP API Security Top 10 (2023)

## 定位

| 维度 | 本 Skill | semgrep-security |
|------|----------|------------------|
| 测试层 | **运行时 API 层** — 发送真实请求，检测行为 | **代码层 SAST** — 扫描源码找漏洞模式 |
| 目标 | 已部署/可访问的 API 端点 | 源代码仓库 |
| 方法 | 主动探测、模糊测试、权限绕过尝试 | 静态模式匹配 |
| 漏洞类型 | 配置错误、逻辑缺陷、认证绕过 | 代码中的不安全写法 |

**两者互补**：semgrep 找代码里的隐患，本 Skill 验证运行时实际风险。

## 适用场景

- 对已部署的 REST/GraphQL API 进行安全扫描
- CI/CD 中集成 API 安全门禁
- 渗透测试前的信息收集与自动化检测
- 安全审计中的 API 行为验证

## 依赖工具

```bash
# 核心
pip install httpx requests

# 推荐（可选）
pip install jwt          # JWT 解析
pip install gql[all]     # GraphQL 测试
brew install nuclei      # 漏洞模板扫描
brew install ffuf        # 路径/参数模糊测试
brew install curl        # HTTP 请求
brew install jq          # JSON 处理
```

## 快速开始

```bash
# 1. 扫描单个 API（基础认证测试 + 安全头检查）
python3 skills/api-security/scripts/api_scan.py \
  --base-url https://api.example.com \
  --token "Bearer eyJ..." \
  --endpoints /users /orders /admin/stats

# 2. OWASP Top 10 全量扫描
python3 skills/api-security/scripts/owasp_full_scan.py \
  --base-url https://api.example.com \
  --config skills/api-security/config.yaml

# 3. 单项快速检测
# BOLA
python3 skills/api-security/scripts/bola_test.py --url https://api.example.com/users/123 --victim-token "Bearer ..."

# 安全头检查
python3 skills/api-security/scripts/security_headers.py --url https://api.example.com

# 速率限制验证
python3 skills/api-security/scripts/rate_limit_test.py --url https://api.example.com/login --threads 50
```

## 扫描维度（OWASP API Security Top 10 2023）

### API1: 对象级授权失效 (BOLA / Broken Object Level Authorization)

**原理**：攻击者修改请求中的对象 ID（如 `/users/{id}`），访问不属于自己的资源。

**检测方法**：
- 用用户 A 的 token 访问用户 B 的资源，检查是否返回 200
- 遍历 ID 模式：数字递增、UUID 枚举、猜测常见 ID

```bash
# 使用 bola_test.py
python3 skills/api-security/scripts/bola_test.py \
  --url https://api.example.com/api/v1/orders \
  --token-a "Bearer userA_token" \
  --token-b "Bearer userB_token" \
  --id-range 1-100 \
  --id-field order_id
```

### API2: 认证机制失效 (Broken Authentication)

**检测项**：
- 弱密码策略 / 缺少 MFA
- Token 过期时间过长（>24h）
- 密码重置流程缺陷
- 凭据填充攻击防护
- JWT 签名验证缺失（`alg: none`）

```bash
# JWT 弱签名检测
python3 skills/api-security/scripts/auth_test.py \
  --url https://api.example.com/api/v1/me \
  --token "Bearer eyJ..." \
  --check-jwt-none \
  --check-token-expiry \
  --check-brute-force
```

### API3: 对象属性级授权失效 (Broken Object Property Level Authorization)

**检测项**：
- Mass Assignment：PUT/PATCH 时是否能修改只读字段（role、is_admin、balance）
- 过度数据暴露：GET 响应中是否包含不应暴露的字段

```bash
# 过度数据暴露检测
python3 skills/api-security/scripts/data_exposure.py \
  --url https://api.example.com/api/v1/users/123 \
  --token "Bearer ..." \
  --sensitive-fields password,ssn,credit_card,secret_key,api_key \
  --check-response-size
```

### API4: 不受限制的资源消耗 (Unrestricted Resource Consumption)

**检测项**：
- API 是否有速率限制
- 速率限制绕过（X-Forwarded-For、不同 endpoint 共享计数）
- 文件上传大小限制
- 分页参数无上限

```bash
python3 skills/api-security/scripts/rate_limit_test.py \
  --url https://api.example.com/api/v1/search \
  --method POST \
  --body '{"q":"test"}' \
  --threads 100 \
  --duration 30 \
  --check-bypass-headers
```

### API5: 功能级授权失效 (Broken Function Level Authorization)

**检测项**：
- 普通用户能否访问管理员接口
- HTTP 方法绕过（GET 代替 DELETE）
- 隐藏的管理端点

```bash
# 垂直越权检测
python3 skills/api-security/scripts/idor_vertical.py \
  --base-url https://api.example.com \
  --user-token "Bearer normal_user_token" \
  --endpoints-file skills/api-security/data/admin_endpoints.txt \
  --check-method-swap
```

### API6: 对敏感业务流的不受限制访问 (Unrestricted Access to Sensitive Business Flows)

**检测项**：
- 自动化滥用（抢购、刷单、批量注册）
- 缺少业务逻辑验证
- 缺少人机验证

### API7: 服务端请求伪造 (SSRF)

**检测项**：
- API 参数中是否可注入内部 URL
- 云元数据端点访问（169.254.169.254）
- 内网端口扫描

```bash
python3 skills/api-security/scripts/ssrf_test.py \
  --url https://api.example.com/api/v1/webhook \
  --param callback_url \
  --payloads skills/api-security/data/ssrf_payloads.txt \
  --canary-url https://your-collaborator.example.com/unique-id
```

### API8: 安全配置错误 (Security Misconfiguration)

**检测项**：
- 安全响应头缺失
- CORS 配置过宽
- 详细错误信息泄露
- 默认凭据
- 不必要的 HTTP 方法开启

```bash
python3 skills/api-security/scripts/security_headers.py \
  --url https://api.example.com \
  --check-cors \
  --check-methods \
  --check-error-leak
```

### API9: 不当的资产管理管理 (Improper Inventory Management)

**检测项**：
- 旧版本 API 未下线
- 未文档化的端点
- Shadow API 发现

### API10: 不安全的 API 消费 (Unsafe Consumption of APIs)

**检测项**：
- 下游 API 响应未验证
- 未校验 SSL 证书
- 缺少超时设置
- 未过滤第三方 API 返回数据

```bash
python3 skills/api-security/scripts/api_consumer_audit.py \
  --url https://api.example.com/api/v1/proxy \
  --param target_url \
  --check-ssl-verify \
  --check-timeout \
  --check-response-sanitization
```

## 扫描脚本清单

| 脚本 | 用途 | 对应 OWASP |
|------|------|------------|
| `scripts/api_scan.py` | 通用 API 扫描入口 | 全部 |
| `scripts/owasp_full_scan.py` | OWASP Top 10 全量扫描 | 全部 |
| `scripts/bola_test.py` | 对象级授权测试 | API1 |
| `scripts/auth_test.py` | 认证机制测试 | API2 |
| `scripts/data_exposure.py` | 数据过度暴露检测 | API3 |
| `scripts/rate_limit_test.py` | 速率限制验证 | API4 |
| `scripts/idor_vertical.py` | 垂直越权检测 | API5 |
| `scripts/ssrf_test.py` | SSRF 漏洞测试 | API7 |
| `scripts/security_headers.py` | 安全头/CORS 检查 | API8 |
| `scripts/api_consumer_audit.py` | API 消费安全审计 | API10 |
| `scripts/graphql_security.py` | GraphQL 专项测试 | 全部 |

## 配置文件

```yaml
# config.yaml
target:
  base_url: "https://api.example.com"
  auth:
    type: "bearer"
    token: "${API_TOKEN}"

scan:
  timeout: 10
  max_concurrent: 10
  rate_limit_pause: 1

owasp:
  api1_bola:
    enabled: true
    endpoints:
      - path: "/api/v1/users/{id}"
        method: GET
        id_field: id
      - path: "/api/v1/orders/{id}"
        method: GET
        id_field: order_id
    id_range: "1-1000"

  api2_auth:
    enabled: true
    check_jwt_none: true
    check_token_expiry: true
    check_brute_force: true
    login_endpoint: "/api/v1/auth/login"

  api3_data_exposure:
    enabled: true
    sensitive_patterns:
      - "password"
      - "secret"
      - "token"
      - "credit_card"
      - "ssn"
      - "private_key"

  api4_rate_limit:
    enabled: true
    threads: 50
    duration_seconds: 30

  api5_vertical:
    enabled: true
    user_token: "${USER_TOKEN}"
    admin_endpoints_file: "data/admin_endpoints.txt"

  api7_ssrf:
    enabled: true
    collaborator_url: "https://collaborator.example.com"
    internal_targets:
      - "http://127.0.0.1"
      - "http://169.254.169.254"
      - "http://10.0.0.1"

  api8_security_headers:
    enabled: true
    required_headers:
      - "Strict-Transport-Security"
      - "X-Content-Type-Options"
      - "X-Frame-Options"
      - "Content-Security-Policy"
      - "X-XSS-Protection"

  api10_consumer:
    enabled: true
    check_ssl_verify: true
    check_timeout: true

output:
  format: "json"
  file: "reports/api_security_report.json"
  verbose: true
```

## 输出格式

扫描结果输出为 JSON 报告，结构如下：

```json
{
  "scan_time": "2026-03-31T20:00:00+08:00",
  "target": "https://api.example.com",
  "summary": {
    "total_checks": 42,
    "passed": 35,
    "failed": 5,
    "warnings": 2,
    "risk_level": "MEDIUM"
  },
  "findings": [
    {
      "id": "API1-001",
      "owasp_category": "API1 - Broken Object Level Authorization",
      "severity": "HIGH",
      "endpoint": "/api/v1/users/{id}",
      "description": "User A can access User B's profile via ID enumeration",
      "evidence": "GET /api/v1/users/456 with User A token returned 200",
      "recommendation": "Implement object-level authorization checks in the resource handler"
    }
  ]
}
```

## 在 OpenClaw 中使用

当主人要求进行 API 安全测试时：

1. **信息收集**：先确认目标 API 的 base_url、认证方式、已知端点
2. **选择模式**：全量扫描（`owasp_full_scan.py`）或单项检测
3. **执行扫描**：运行脚本，收集结果
4. **分析报告**：解读 findings，按严重性排序
5. **提供建议**：针对每个 finding 给出修复方案

### 常用对话触发词

- "帮我扫一下这个 API 的安全"
- "做个 API 安全测试"
- "检查 API 有没有 BOLA 漏洞"
- "验证一下 API 的认证是否安全"
- "测试 API 的速率限制"

## 注意事项

⚠️ **仅对有授权的目标进行扫描** — 未经授权的扫描可能违法

⚠️ **生产环境慎用** — 速率限制测试可能触发 WAF/封禁

⚠️ **SSRF 测试需要协作服务器** — 建议使用 Burp Collaborator 或自建 canary 服务

⚠️ **Token 管理** — 扫描用的 token 应为测试账号，扫描后立即轮换
