# GitHub Agent Project Benchmark

> Created: 2026-06-09
> Purpose: capture reusable architecture ideas from mature open source agent projects and map them to Niannian Workspace.

## Benchmarked Projects

| Project | Useful Pattern | What To Adopt Here | What To Avoid |
| --- | --- | --- | --- |
| [Microsoft AutoGen](https://github.com/microsoft/autogen) | Layered agent APIs, multi-agent orchestration, agent tools, studio/bench concepts. | Keep a split between low-level event/runtime contracts and higher-level agent playbooks. Add benchmark/eval hooks early. | AutoGen itself is in maintenance mode, so do not build new architecture around it directly. |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Clear project shape with declarative `agents.yaml` and `tasks.yaml` plus runtime code. | Move agent identity and task definitions into a declarative registry that can be validated before execution. | Do not duplicate all agent prompts in executable code and config at the same time. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Long-running stateful workflows, durable execution, human-in-the-loop checkpoints, memory. | Model Niannian tasks as workflow graphs with explicit nodes, edges, checkpoints, and approval gates. | Do not hide workflow state inside ad hoc markdown notes only. |
| [Mastra](https://github.com/mastra-ai/mastra) | TypeScript-first agents, model routing, graph workflows, storage-backed resume. | Prefer TypeScript contracts/packages for the dashboard/API/worker path. Keep model routing separate from agent identity. | Do not introduce a full framework dependency before local contracts are stable. |
| [Langfuse](https://github.com/langfuse/langfuse) | LLM observability, metrics, evals, prompt management, datasets, OpenTelemetry integration. | Add normalized event contracts for agent runs, tool calls, memory writes, task transitions, and human approvals. | Do not treat dashboard metrics as only SQLite seed data; they need traceable runtime events. |

## Architecture Decisions

1. **Use declarative manifests for agents and tasks.**
   Agent role, goal, tools, memory scope, model policy, permissions, and output expectations should live in a registry file before runtime code imports them.

2. **Add contracts before moving code.**
   A small `packages/contracts` package gives dashboard, API, worker, and future runtime code a shared vocabulary without forcing a big monorepo migration first.

3. **Treat task execution as a graph.**
   Even when tasks run sequentially, store them as nodes and edges. This supports pause/resume, retries, approvals, and parallel waves later.

4. **Separate observability from business data.**
   `tasks` tables describe work. Events describe what happened while doing the work. The dashboard should eventually read both.

5. **Keep memory as a first-class domain.**
   Short-term working memory, long-term curated memory, and shared knowledge need separate contracts so they can be indexed and compacted without losing provenance.

## Immediate Changes In This Repo

- Add `packages/contracts` with shared TypeScript contracts and JSON schemas.
- Add `agents/registry/agents.json` as the first canonical declarative agent registry.
- Add `tasks/templates/workflow.example.json` as a graph-shaped task/workflow example.
- Keep existing `agents/<id>/` folders as playbooks and historical artifacts.
- Keep existing Dashboard APIs, but prepare them to consume the registry and event contracts later.

## Next Implementation Steps

1. Teach `dashboard-v4/server/src/workspace.ts` to read `agents/registry/agents.json` instead of only counting directories.
2. Split `dashboard-v4/server/src/routes.ts` into route, service, repository, and event modules.
3. Add a lightweight event append API based on `AgentRuntimeEvent`.
4. Add validation scripts for `agents/registry/*.json` and `tasks/templates/*.json`.
5. Add dashboard views for workflow graph state and recent runtime events.
