# Workspace Boundaries

This document defines the target ownership model for the Niannian workspace.

## Boundary Rules

1. Source code belongs in `apps/`, `services/`, `packages/`, `skills/`, or `scripts/`.
2. Live mutable state belongs in `workspace/`.
3. Reusable knowledge belongs in `knowledge/`.
4. Product and architecture documents belong in `docs/`.
5. Agent manifests and playbooks belong in `agents/`.
6. Generated artifacts should be clearly marked and either ignored or stored under `knowledge/reports` or `workspace/outbox`.

## Current To Target Mapping

| Current path | Target path | Notes |
| --- | --- | --- |
| `dashboard-v4/client` | `apps/dashboard` | Keep React + Vite. Reorganize by feature. |
| `dashboard-v4/server` | `services/api` | Split routes, services, repositories, events. |
| `lib/api-schema-validator.ts` | `packages/contracts` | Expand into shared schemas and generated TS types. |
| `lib/batch-dispatcher.ts` | `packages/agent-core` | Keep pure. Inject runtime-specific spawn adapter. |
| `lib/error-recovery.ts` | `packages/resilience` | Shared retry, timeout, fallback, circuit breaker. |
| `lib/memory-indexer.ts` | `packages/memory-core` | Own memory extraction and indexing. |
| `lib/feishu-hub.ts` | `packages/integrations/feishu` | External service adapter. |
| `agents/*/LEARNING_PLAN.md` | `agents/playbooks/*` | Role-specific guides. |
| `agents/*/capability.json` | `agents/registry/*.yaml` plus database mirror | Manifest is source of truth. DB stores runtime state. |
| `memory/*` | `workspace/memory/*` | Live personal and agent memory. |
| `SHARED_KNOWLEDGE.md` | `knowledge/library/shared-knowledge.md` | Curated reusable knowledge. |
| `knowledge-base/library` | `knowledge/library` | Curated material. |
| `knowledge-base/raw` | `knowledge/raw` | Imported material. |
| `knowledge-base/output` | `knowledge/reports` | Generated outputs. |
| `inbox`, `tasks`, `outbox` | `workspace/inbox`, `workspace/tasks`, `workspace/outbox` | Operational state. |
| root setup docs | `docs/setup/*` | Keep root clean. |
| one-off root scripts | `scripts/maintenance` or `packages/integrations` | Classify before moving. |

## Root Directory Policy

The root should only contain:

- workspace config: `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`
- repository docs: `README.md`, `CONTRIBUTING.md`, `LICENSE`
- project config: `.gitignore`, `.editorconfig`, `.github`
- top-level folders from the target shape

Everything else should move behind an owning boundary.

## Package Dependency Direction

Allowed dependency direction:

```text
apps/* -> services API clients -> packages/contracts
services/* -> packages/*
packages/agent-core -> packages/contracts + packages/resilience
packages/memory-core -> packages/contracts
packages/datastore -> packages/contracts
packages/integrations -> packages/contracts + packages/resilience
skills/runtime -> packages/contracts + packages/resilience
```

Disallowed:

- `packages/*` importing from `apps/*`
- `packages/*` importing from `services/*`
- route handlers importing SQL directly after the repository split
- dashboard UI reading files from `workspace/*` directly

## Testing Ownership

| Area | Test type |
| --- | --- |
| `packages/contracts` | schema compatibility and type generation tests |
| `packages/agent-core` | graph, scheduling, capability matching, retry boundaries |
| `packages/datastore` | repository tests against temp SQLite DB |
| `services/api` | route integration tests with test DB |
| `services/worker` | job tests with fixture workspace |
| `apps/dashboard` | component tests and Playwright smoke tests |
| `skills/runtime` | manifest validation and sandbox wrapper tests |

## Migration Guardrails

- Move code in small slices and keep compatibility shims while migrating imports.
- Preserve behavior before improving behavior.
- Keep UI redesign separate from service boundary refactors.
- Before deleting any root document, classify it as `docs`, `knowledge`, `workspace`, or `archive`.
- Add a Windows path validation check before the next push.
