# Workspace Tasks

This directory stores live task and workflow state for the local multi-agent workspace.

Use `templates/workflow.example.json` as the graph-shaped task format for new multi-agent work. It separates:

- nodes: units of work owned by agents
- edges: dependency, review, and handoff relationships
- approval_gates: checkpoints that require human or coordinator review

This format keeps simple task boards possible while making future durable workflow execution easier.
