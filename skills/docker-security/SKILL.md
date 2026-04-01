# Docker Security — 容器安全审计技能

> **Skill**: docker-security
> **用途**: Docker 容器全生命周期安全审计，覆盖 Dockerfile 静态分析、运行时加固、镜像漏洞扫描、供应链安全
> **触发条件**: 用户提到"容器安全"、"Docker安全"、"Dockerfile审计"、"镜像扫描"、"容器加固"、"Trivy"、"供应链安全"、"Cosign"

## ⚠️ 边界声明

**本 Skill 职责**: 容器层安全（Dockerfile、镜像、运行时配置、供应链）

**不涉及**: 源代码层 SAST 扫描 → 请使用 `semgrep-security` Skill

| 维度 | docker-security（本 Skill） | semgrep-security |
|------|---------------------------|-----------------|
| 扫描对象 | Dockerfile / 容器镜像 / 运行时参数 | 源代码文件 |
| 工具 | Trivy / Hadolint / Cosign | Semgrep |
| 阶段 | 构建 → 部署 → 运行 | 编码阶段 |
| 典型问题 | 过权容器、root用户、已知CVE | SQL注入、XSS、硬编码密钥 |

---

## 1. Dockerfile 安全审计

### 1.1 审计规则清单

| # | 规则 | 严重级 | 说明 |
|---|------|--------|------|
| D01 | 使用 multi-stage 构建 | HIGH | 减小攻击面，编译工具不进最终镜像 |
| D02 | 基础镜像用 distroless/Alpine | HIGH | 比 Ubuntu/Debian 少 90%+ 包 |
| D03 | 非 root 用户运行 | CRITICAL | `USER nonroot:nonroot` |
| D04 | 不使用 `latest` 标签 | HIGH | 锁定版本，如 `node:20.11-alpine3.19` |
| D05 | 不安装 `sudo`/`curl`/`wget` | MEDIUM | 减少容器内攻击工具 |
| D06 | 每个 RUN 后清理包管理器缓存 | LOW | `rm -rf /var/lib/apt/lists/*` |
| D07 | 不暴露不必要的端口 | MEDIUM | 仅暴露服务端口 |
| D08 | 使用 `COPY` 替代 `ADD` | LOW | `ADD` 有自动解压和远程 URL 行为 |
| D09 | 设置 `HEALTHCHECK` | MEDIUM | 运行时健康检测 |
| D10 | 敏感信息不写入镜像 | CRITICAL | 用 `--secret` 或 BuildKit mounts |

### 1.2 Multi-Stage Dockerfile 模板

```dockerfile
# ============ Stage 1: Build ============
FROM node:20.11-alpine3.19 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# ============ Stage 2: Production ============
FROM gcr.io/distroless/nodejs20-debian12:nonroot
# ✅ distroless + nonroot 用户
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["dist/index.js"]
```

### 1.3 Hadolint 审计脚本

```bash
#!/usr/bin/env bash
# dockerfile-audit.sh — Dockerfile 静态安全审计
set -euo pipefail

DOCKERFILE="${1:-Dockerfile}"
SEVERITY="${2:-error,warning}"  # error, warning, info, style

echo "🔍 Auditing: $DOCKERFILE"

# 安装: brew install hadolint (macOS) / docker pull hadolint/hadolint
if command -v hadolint &>/dev/null; then
    hadolint --format json --failure-threshold warning "$DOCKERFILE" | \
        jq -r '.[] | "[\(.level)] \(.code): \(.message) (line \(.line))"'
else
    # Docker 方式运行
    docker run --rm -i hadolint/hadolint < "$DOCKERFILE"
fi

# 额外自定义检查
echo ""
echo "🔎 Custom checks:"

# 检查 non-root USER
if ! grep -qE '^USER\s+(?!root)' "$DOCKERFILE"; then
    echo "  ❌ CRITICAL: Missing non-root USER directive"
else
    echo "  ✅ Non-root USER found"
fi

# 检查 latest 标签
if grep -qE '^FROM\s+\S+:latest' "$DOCKERFILE"; then
    echo "  ❌ HIGH: Using :latest tag — pin to specific version"
else
    echo "  ✅ No :latest tags"
fi

# 检查 ADD vs COPY
if grep -qE '^ADD\s+' "$DOCKERFILE"; then
    echo "  ⚠️  MEDIUM: ADD used — prefer COPY unless you need auto-extract"
fi

# 检查多阶段构建
stage_count=$(grep -cE '^FROM\s+' "$DOCKERFILE" || true)
if (( stage_count < 2 )); then
    echo "  ⚠️  MEDIUM: Single-stage build ($stage_count FROM) — consider multi-stage"
else
    echo "  ✅ Multi-stage build ($stage_count stages)"
fi

# 检查 HEALTHCHECK
if ! grep -qE '^HEALTHCHECK' "$DOCKERFILE"; then
    echo "  ⚠️  LOW: No HEALTHCHECK directive"
fi

echo ""
echo "✅ Audit complete for $DOCKERFILE"
```

---

## 2. 运行时安全加固

### 2.1 最安全运行参数模板

```bash
#!/usr/bin/env bash
# docker-run-secure.sh — 最安全容器启动模板
set -euo pipefail

IMAGE="$1"
shift

docker run -d \
    --name secure-app \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --tmpfs /var/run:rw,noexec,nosuid,size=16m \
    --cap-drop=ALL \
    --cap-add=NET_BIND_SERVICE \
    --security-opt=no-new-privileges:true \
    --security-opt=seccomp=unconfined \
    --pids-limit=256 \
    --memory=512m \
    --cpus=1.0 \
    --user=1000:1000 \
    --network=app-net \
    --restart=no \
    --log-driver=json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    --health-cmd="curl -f http://localhost:3000/health || exit 1" \
    --health-interval=30s \
    --health-timeout=5s \
    --health-retries=3 \
    "$@" "$IMAGE"
```

### 2.2 运行时参数速查表

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| `--read-only` | 根文件系统只读 | ✅ 始终开启 |
| `--cap-drop=ALL` | 丢弃所有 Linux capabilities | ✅ 始终开启 |
| `--cap-add=NET_BIND_SERVICE` | 按需添加（绑定 <1024 端口） | 仅需要时 |
| `--no-new-privileges` | 禁止提权 | ✅ 始终开启 |
| `--pids-limit` | 防止 fork bomb | 256-1024 |
| `--memory` | 内存上限 | 按需 |
| `--cpus` | CPU 限制 | 按需 |
| `--user` | 非 root UID | 1000:1000 |
| `--tmpfs /tmp` | 临时文件系统 + noexec | 64m |
| `--network` | 自定义网络隔离 | 不用默认 bridge |

### 2.3 Docker Compose 安全模板

```yaml
# docker-compose.secure.yml
services:
  app:
    image: myapp:v1.2.3@sha256:abc123...  # ✅ digest pinning
    read_only: true
    user: "1000:1000"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M
    pids_limit: 256
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - app-net

networks:
  app-net:
    driver: bridge
    internal: false  # 设为 true 则完全隔离外网
```

---

## 3. Trivy 镜像漏洞扫描

### 3.1 安装 Trivy

```bash
# macOS
brew install trivy

# Docker (无需安装)
alias trivy='docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy'

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

### 3.2 审计脚本

```bash
#!/usr/bin/env bash
# trivy-audit.sh — 镜像漏洞 + 配置扫描
set -euo pipefail

IMAGE="${1:?Usage: $0 <image>[:tag]}"
SEVERITY="${2:-CRITICAL,HIGH}"
EXIT_CODE="${3:-1}"  # 1=发现漏洞则失败, 0=仅报告

echo "🔍 Scanning image: $IMAGE"
echo "   Severity filter: $SEVERITY"
echo ""

# 1. 漏洞扫描
echo "=== Vulnerability Scan ==="
trivy image \
    --severity "$SEVERITY" \
    --format table \
    --exit-code "$EXIT_CODE" \
    --ignore-unfixed \
    --scanners vuln \
    "$IMAGE"

# 2. 敏感信息泄露扫描
echo ""
echo "=== Secrets Scan ==="
trivy image \
    --scanners secret \
    --format table \
    --exit-code 0 \
    "$IMAGE"

# 3. 镜像配置审计
echo ""
echo "=== Misconfiguration Scan ==="
trivy image \
    --scanners misconfig \
    --format table \
    --exit-code 0 \
    "$IMAGE"

# 4. 生成 SBOM (Software Bill of Materials)
echo ""
echo "=== Generating SBOM ==="
trivy image --format spdx-json --output sbom.json "$IMAGE"
echo "✅ SBOM saved to sbom.json"

echo ""
echo "✅ Full audit complete for $IMAGE"
```

### 3.3 Trivy CI 集成

#### GitHub Actions

```yaml
# .github/workflows/container-security.yml
name: Container Security Scan

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - 'docker-compose*.yml'
      - '.github/workflows/container-security.yml'
  pull_request:
    branches: [main]

jobs:
  trivy-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH
          exit-code: 1
          ignore-unfixed: true

      - name: Upload Trivy scan results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif

      - name: Trivy SBOM generation
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: spdx-json
          output: sbom.spdx.json

      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
container-scan:
  stage: test
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  variables:
    GIT_STRATEGY: fetch
  script:
    - trivy image
        --exit-code 1
        --severity CRITICAL,HIGH
        --ignore-unfixed
        --format table
        $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  allow_failure: false
```

---

## 4. 供应链安全

### 4.1 Digest Pinning（摘要固定）

**问题**: 镜像标签可被覆盖（tag mutability），`node:20` 可能指向不同镜像。
**解决**: 使用 digest 锁定镜像内容。

```bash
# 获取镜像 digest
docker inspect --format='{{index .RepoDigests 0}}' node:20-alpine
# → node:20-alpine@sha256:abc123def456...

# 在 Dockerfile 中使用
# ❌ 不安全
FROM node:20-alpine

# ✅ 安全 — digest 锁定
FROM node:20-alpine@sha256:abc123def456789...
```

**批量获取 digest 脚本**:

```bash
#!/usr/bin/env bash
# pin-digests.sh — 批量获取并固定镜像 digest
set -euo pipefail

DOCKERFILE="${1:-Dockerfile}"

echo "📌 Pinning digests in: $DOCKERFILE"
echo ""

# 提取所有 FROM 镜像（跳过 AS alias）
grep -E '^FROM\s+' "$DOCKERFILE" | \
    grep -v 'AS\s' | \
    awk '{print $2}' | \
while read -r image; do
    # 跳过已有 digest 的
    if [[ "$image" == *@sha256:* ]]; then
        echo "  ✅ Already pinned: $image"
        continue
    fi
    
    digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null | cut -d@ -f2)
    if [[ -n "$digest" ]]; then
        echo "  📌 $image → $image@$digest"
    else
        echo "  ⚠️  Cannot resolve: $image"
    fi
done
```

### 4.2 Cosign 镜像签名验证

**用途**: 验证镜像来源可信，防止供应链攻击（类似 SLSA Level 3）。

```bash
# 安装 cosign
brew install cosign  # macOS
# 或
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# ============ 签名镜像（发布者）============
# 用 cosign 生成密钥对（首次）
cosign generate-key-pair

# 签名镜像
cosign sign --key cosign.key myregistry/myapp:v1.2.3

# 签名 + 附带 SBOM attestation
cosign attest --key cosign.key \
    --predicate sbom.spdx.json \
    --type spdxjson \
    myregistry/myapp:v1.2.3

# ============ 验证镜像（消费者/CI）============
# 验证签名
cosign verify --key cosign.pub myregistry/myapp:v1.2.3

# 验证 + 获取 SBOM attestation
cosign verify-attestation --key cosign.pub \
    --type spdxjson \
    myregistry/myapp:v1.2.3
```

### 4.3 CI 供应链验证流水线

```bash
#!/usr/bin/env bash
# supply-chain-verify.sh — CI 中的供应链安全验证
set -euo pipefail

IMAGE="${1:?Usage: $0 <image>}"
COSIGN_PUB_KEY="${2:-cosign.pub}"

echo "🔗 Supply chain verification for: $IMAGE"
echo ""

# 1. Digest 验证 — 检查是否使用了 digest pinning
echo "=== Digest Pinning Check ==="
if [[ "$IMAGE" == *@sha256:* ]]; then
    echo "  ✅ Image uses digest pinning"
else
    echo "  ⚠️  Image uses mutable tag — prefer digest pinning"
fi

# 2. Cosign 签名验证
echo ""
echo "=== Cosign Signature Verification ==="
if [[ -f "$COSIGN_PUB_KEY" ]]; then
    if cosign verify --key "$COSIGN_PUB_KEY" "$IMAGE" 2>/dev/null; then
        echo "  ✅ Signature verified"
    else
        echo "  ❌ Signature verification FAILED"
        exit 1
    fi
else
    echo "  ⚠️  No cosign public key found at $COSIGN_PUB_KEY"
fi

# 3. SBOM Attestation 验证
echo ""
echo "=== SBOM Attestation Check ==="
if cosign verify-attestation --key "$COSIGN_PUB_KEY" --type spdxjson "$IMAGE" 2>/dev/null; then
    echo "  ✅ SBOM attestation present and verified"
else
    echo "  ⚠️  No verified SBOM attestation found"
fi

# 4. Trivy 快速扫描
echo ""
echo "=== Vulnerability Scan ==="
trivy image --severity CRITICAL --exit-code 1 --ignore-unfixed "$IMAGE"

echo ""
echo "✅ Supply chain verification complete"
```

---

## 5. 完整审计 Pipeline（一键执行）

```bash
#!/usr/bin/env bash
# docker-security-full-audit.sh — 全链路容器安全审计
set -euo pipefail

IMAGE="${1:?Usage: $0 <image>}"
DOCKERFILE="${2:-Dockerfile}"

echo "╔══════════════════════════════════════╗"
echo "║  Docker Security Full Audit          ║"
echo "╚══════════════════════════════════════╝"
echo ""

REPORT_DIR="security-reports-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

# Phase 1: Dockerfile 静态分析
echo "📋 Phase 1: Dockerfile Audit"
docker run --rm -i hadolint/hadolint < "$DOCKERFILE" > "$REPORT_DIR/hadolint.txt" 2>&1 || true
echo "   → $REPORT_DIR/hadolint.txt"

# Phase 2: 镜像漏洞扫描
echo ""
echo "🔍 Phase 2: Vulnerability Scan"
trivy image --severity CRITICAL,HIGH --format json --output "$REPORT_DIR/trivy-vuln.json" "$IMAGE"
echo "   → $REPORT_DIR/trivy-vuln.json"

# Phase 3: 敏感信息扫描
echo ""
echo "🔑 Phase 3: Secrets Scan"
trivy image --scanners secret --format json --output "$REPORT_DIR/trivy-secrets.json" "$IMAGE"
echo "   → $REPORT_DIR/trivy-secrets.json"

# Phase 4: 镜像配置审计
echo ""
echo "⚙️  Phase 4: Misconfiguration Scan"
trivy image --scanners misconfig --format json --output "$REPORT_DIR/trivy-misconfig.json" "$IMAGE"
echo "   → $REPORT_DIR/trivy-misconfig.json"

# Phase 5: SBOM 生成
echo ""
echo "📦 Phase 5: SBOM Generation"
trivy image --format spdx-json --output "$REPORT_DIR/sbom.spdx.json" "$IMAGE"
echo "   → $REPORT_DIR/sbom.spdx.json"

# Phase 6: 供应链验证
echo ""
echo "🔗 Phase 6: Supply Chain Check"
bash "$(dirname "$0")/supply-chain-verify.sh" "$IMAGE" > "$REPORT_DIR/supply-chain.txt" 2>&1 || true
echo "   → $REPORT_DIR/supply-chain.txt"

# 汇总
echo ""
echo "════════════════════════════════════════"
echo "📊 Reports saved to: $REPORT_DIR/"
ls -la "$REPORT_DIR/"
echo ""
echo "✅ Full audit complete!"
```

---

## 6. 快速决策指南

```
用户说什么 → 做什么

"帮我审计 Dockerfile"
  → 运行 dockerfile-audit.sh（Phase 1 Hadolint + 自定义规则）

"扫描镜像漏洞"
  → 运行 trivy-audit.sh（Phase 2-5 Trivy）

"检查容器运行时安全"
  → 审查 docker run / docker-compose 参数，对照 §2 参数模板

"供应链安全"
  → 检查 digest pinning + Cosign 签名，运行 supply-chain-verify.sh

"完整安全审计"
  → 运行 docker-security-full-audit.sh（全 6 个阶段）

"加到 CI 里"
  → 复制 §3.3 的 GitHub Actions / GitLab CI 配置
```

---

## 7. 常用命令速查

```bash
# 检查容器以 root 运行
docker inspect --format='{{.Config.User}}' <container>

# 检查容器 capabilities
docker inspect --format='{{.HostConfig.CapAdd}}' <container>

# 检查安全选项
docker inspect --format='{{.HostConfig.SecurityOpt}}' <container>

# 检查只读根文件系统
docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' <container>

# 列出所有运行中容器的安全配置
docker ps -q | xargs -I{} docker inspect --format='{{.Name}} user={{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}} caps={{.HostConfig.CapDrop}}' {}

# 批量检查是否有容器以 root 运行
docker ps -q | xargs -I{} docker inspect --format='{{.Name}}: {{.Config.User}}' {} | grep -v '1000\|nonroot\|nobody' || echo "All containers use non-root users ✅"
```
