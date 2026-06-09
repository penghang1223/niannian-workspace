# Repository Map

Niannian Workspace is currently a mixed workspace: agent runtime files, knowledge assets, experiments, skills, and dashboards live in one repository. This map defines the intended ownership boundaries so future cleanup has a stable direction.

## Current Top-Level Areas

| Path | Purpose | Keep In Git? |
| --- | --- | --- |
| `agents/` | Agent profiles, lessons, task reports, and role-specific notes. | Yes |
| `dashboard-v4/` | Current dashboard app: React client and Fastify server. | Yes, source only |
| `lib/` | Shared TypeScript contracts, validators, recovery, memory, and integration utilities. | Yes |
| `skills/` | Local skill catalog and experimental skill implementations. | Yes |
| `memory/` | Agent memory, long-term notes, state, and evolution traces. | Yes, curated state only |
| `knowledge-base/` | Raw notes, curated knowledge, and generated reports. | Yes, curated docs |
| `docs/` | Architecture, operations, product, workspace notes, and archive. | Yes |
| `scripts/` | Maintenance scripts and local automation helpers. | Yes |
| `inbox/`, `outbox/`, `tasks/` | Workspace coordination queues. | Yes if they are canonical; ignore transient payloads later |
| `reports/` | Generated or curated reports. | Case by case |

## Root Policy

The root directory should contain only:

- project entry docs: `README.md`, `AGENTS.md`
- runtime contract files read by name: `HEARTBEAT.md`, `TOOLS.md`, `WORKFLOW.md`, `MEMORY.md`, `SHARED_KNOWLEDGE.md`
- active planning/status files: `STATE.yaml`, `DECISIONS.md`, `GOALS.md`, `KANBAN.md`, `PROJECT_STATUS.md`
- package/config files used from the root
- source files only when an existing runtime imports them from the root

Everything else should move into `docs/`, `scripts/`, a feature directory, or an archive.

## Target Architecture

```text
apps/          dashboard and browser-facing applications
services/      API and background workers
packages/      shared contracts, datastore, agent core, memory core
agents/        agent manifests and playbooks
skills/        skill catalog and runtime
knowledge/     curated reusable knowledge
workspace/     live state, memory, inbox, outbox
docs/          architecture, setup, ADRs, product notes
scripts/       development and maintenance scripts
```

Do not move code to the target layout without first updating import paths and adding a small verification pass.
