# Workspace Outbox

Coordinator-to-agent instructions live here.

## Structure

- `pending/`: instructions waiting for agent pickup
- `done/`: instructions that have been dispatched or completed

Each instruction is a JSON file. It uses the same basic message shape as the inbox, with `from` normally set to `main`.
