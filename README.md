# Niannian Workspace

Niannian Workspace is a personal multi-agent workspace. It combines agent profiles, task orchestration, memory, skills, knowledge assets, and a local dashboard for monitoring work.

## What Is In This Repo

- `agents/`: agent roles, lessons, capability notes, and task dispatch experiments.
- `dashboard-v4/`: current dashboard implementation with React, Vite, Fastify, WebSocket, and SQLite.
- `lib/`: shared TypeScript utilities for dispatching, schemas, recovery, memory indexing, and integrations.
- `skills/`: local skill catalog and experimental skill implementations.
- `memory/`: dated memory, per-agent memory, and evolution logs.
- `knowledge-base/`: raw notes, curated knowledge, and generated reports.
- `docs/`: architecture, product, operations, workspace notes, and archive.

## Architecture Redesign

The current repository grew organically and mixes runtime state, documentation, application code, skills, and generated artifacts. The proposed target structure is documented here:

- [Architecture Redesign](docs/architecture/architecture-redesign.md)
- [Documentation Index](docs/README.md)
- [Repository Map](docs/repository-map.md)
- [Workspace Boundaries](docs/architecture/workspace-boundaries.md)
- [Cleanup Report](docs/operations/cleanup-report.md)

Target direction:

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

## Dashboard v4

Dashboard v4 now combines seeded task/agent data with a live workspace inventory from `/api/workspace/summary`. The inventory scans the repository for agent profiles, skill manifests, memory files, knowledge files, queue state, docs, and dashboard app status.

Backend:

```bash
cd dashboard-v4/server
npm install
npm run seed
npm run dev
```

Frontend:

```bash
cd dashboard-v4/client
npm install
npm run dev
```

Default API port: `3456`.

Note: `dashboard-v4/server` uses `better-sqlite3`. On Windows with very new Node versions, install may require Visual Studio C++ Build Tools or an LTS Node version with a matching prebuilt binary.

## Current Cleanup Policy

This repository contains valuable personal and agent history, so cleanup is conservative:

- generated dashboard builds are ignored
- runtime SQLite files are ignored
- malformed Windows-invalid paths were removed from Git
- undocumented gitlink entries without `.gitmodules` were removed
- memory, knowledge, and agent documents are kept until they can be classified safely

## Recommended Next Steps

1. Create `packages/contracts` and move shared API/event types there.
2. Split `dashboard-v4/server/src/routes.ts` into routes, services, repositories, and event modules.
3. Move dashboard client/server into `apps/dashboard` and `services/api`.
4. Move live state into `workspace/`.
5. Add CI checks for Windows-safe paths and generated artifacts.

## Screenshots

<img width="1280" height="959" alt="image" src="https://github.com/user-attachments/assets/9406355f-6652-4034-8b25-62900d90e969" />
<img width="1208" height="905" alt="image" src="https://github.com/user-attachments/assets/2c879c08-a2fa-4a54-aefd-79ae64678393" />
<img width="1208" height="895" alt="image" src="https://github.com/user-attachments/assets/1c23b40a-897c-4dea-b9fc-35c1a7aeb4f9" />
<img width="1216" height="795" alt="image" src="https://github.com/user-attachments/assets/03714d5a-cdca-45cd-9683-e4eb6b2b9196" />
