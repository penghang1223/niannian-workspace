# Cleanup Report

This cleanup is intentionally conservative. The repository contains many memory, knowledge, and agent-history documents that may be important product data, so this pass removes only files that are clearly unsafe or generated.

## Removed From Git

- Windows-invalid paths at the repository root. These were malformed generated files whose names started with `:`.
- `memory/dev-session-2026-03-24-14:00.md`, because `:` prevents checkout on Windows. If the content is needed later, recover it from Git history and recommit it as `memory/dev-session-2026-03-24-14-00.md`.
- `dashboard-v4/client/dist/`, because it is a Vite build output.
- `dashboard-v4/server/data/dashboard.db*`, because SQLite databases and WAL/SHM files are runtime state.
- `opc-platform/frontend/dist/` and `openclaw-statusline/dist/`, because they are generated build outputs.
- `memory/evolution/gep_prompt_*`, because these are generated prompt-cycle outputs already covered by `.gitignore`.
- `.cache/model-catalog.json`, because it is local model metadata cache.
- Early group-chat and Feishu experiment scripts at the repository root, because they depended on missing modules and were no longer runnable:
  - `group_chat_handler.js`
  - `rate_limit_manager.js`
  - `feishu_group_bot_scheduler.js`
  - `feishu_multi_role_middleware.js`
  - `test_group_chat.js`
  - `debug_streaming.py`
- Runtime usage/config files tied only to the removed rate-limit experiment:
  - `config/rate_limits.json`
  - `config/usage_stats.json`
- Obsolete temporary notes and test-case index:
  - `docs/archive/tmp-novel-doc-request.md`
  - `agents/qa_engineer/test-cases/README.md`
- Duplicate or misleading testing skill directories:
  - `test-runner`, after merging its useful framework command quick reference into `testing-patterns/`.
  - `test-patterns`, because it duplicated the broader `testing-patterns/` guidance.
  - `test-generator`, because its metadata described test generation but its implementation was a generic logging CLI; keep `sovereign-test-generator/` for actual test-generation guidance.
- Gitlink entries without `.gitmodules`:
  - `lobster-manager`
  - `skills/github-actions-workflows`
  - `skills/microsoft-api-guidelines`

## Keep For Now

- `memory/**`, `knowledge-base/**`, and root agent documentation stay in place for now. They should be reorganized later, not deleted blindly.
- old dashboard files under `dashboard/` stay until `dashboard-v4` is confirmed as the only active UI.
- remaining skill directories stay until each skill has an owner, manifest status, and usage signal.
- historical QA reports stay as records even if they mention removed experiments.

## Next Cleanup Candidates

- Confirm whether old dashboard files under `dashboard/` are superseded by `dashboard-v4/`.
- Continue auditing specialized testing directories (`test-master`, `test-specialist`, `test-sentinel`, E2E/API QA skills) before any further merge.
- Move live state into `workspace/`.
- Convert copied third-party references into submodules or documented external links.
- Add CI checks for Windows-safe paths and generated artifact drift.
