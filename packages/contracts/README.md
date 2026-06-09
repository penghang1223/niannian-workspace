# @niannian/contracts

Shared contracts for Niannian Workspace.

This package is intentionally small. It gives the dashboard, API server, future worker, and agent runtime the same vocabulary for:

- agent manifests
- workflow/task graphs
- runtime events
- memory references
- permission scopes

The contracts are framework-neutral so the workspace can later integrate ideas from CrewAI, LangGraph, Mastra, or other runtimes without rewriting the project model.

## Files

- `src/index.ts`: TypeScript source of truth for contracts.
- `schemas/agent-manifest.schema.json`: JSON Schema for agent registry entries.
- `schemas/workflow.schema.json`: JSON Schema for graph-shaped workflows.

## Design Rules

1. Contracts must not import dashboard, database, or runtime code.
2. Runtime events are append-only facts.
3. Agent manifests describe identity and capability, not execution state.
4. Workflows describe intended task structure; events describe what actually happened.
