# Workspace Inbox

Agent-to-coordinator messages live here.

## Structure

- `pending/`: messages waiting for coordinator review
- `processing/`: messages currently being handled
- `done/`: completed messages kept for short-term traceability

Each message is a JSON file. See `docs/architecture/agent-comm-v2-design.md` for the historical message contract.

## Flow

1. Agent finishes work and writes `pending/{task_id}.json`.
2. Coordinator heartbeat moves it to `processing/`.
3. Coordinator handles it and moves it to `done/`.
4. Old completed messages can be archived into `docs/archive/`.
