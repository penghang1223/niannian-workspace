# Tasks - 任务状态跟踪

每个任务一个 JSON 文件，包含完整的任务生命周期信息。
与 inbox/ 配合使用，提供更详细的任务状态。
## Workflow Templates

Use `templates/workflow.example.json` as the graph-shaped task format for new multi-agent work. It separates:

- nodes: units of work owned by agents
- edges: dependency, review, and handoff relationships
- approval_gates: checkpoints that require human or coordinator review

This format keeps simple task boards possible while making future durable workflow execution easier.
