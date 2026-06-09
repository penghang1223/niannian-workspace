# Agent Registry

This directory is the canonical declarative registry for Niannian agents.

Existing `agents/<agent_id>/` directories remain useful as playbooks, reports, lessons, and history. The registry adds a machine-readable layer for dashboard, API, worker, and future orchestration code.

## Files

- `agents.json`: active agent manifests.

## Rules

1. Every active agent should have one manifest entry.
2. `id` must match the workspace directory name when a directory exists under `agents/<id>/`.
3. `playbook_paths` should point to existing docs or directories.
4. Permissions describe allowed capability classes, not secrets.
5. Runtime status belongs in events or state, not in long-term manifest files unless it is only a default.
