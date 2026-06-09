# Workspace

Live coordination state for Niannian Workspace.

The repository root used to contain `inbox/`, `outbox/`, and `tasks/`. They now live under this directory so root stays focused on stable entrypoints and source areas.

## Structure

- `inbox/`: agent-to-coordinator messages
- `outbox/`: coordinator-to-agent instructions
- `tasks/`: task state and workflow templates

Historical architecture docs may still mention the old root paths. Treat those as `workspace/inbox/`, `workspace/outbox/`, and `workspace/tasks/` unless a document explicitly says it is describing the pre-migration layout.
