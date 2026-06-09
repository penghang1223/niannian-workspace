# Cleanup Report

This cleanup is intentionally conservative. The repository contains many memory, knowledge, and agent-history documents that may be important product data, so this pass removes only files that are clearly unsafe or generated.

## Removed From Git

- Windows-invalid paths at the repository root. These were malformed generated files whose names started with `:`.
- `memory/dev-session-2026-03-24-14:00.md`, because `:` prevents checkout on Windows. If the content is needed later, recover it from Git history and recommit it as `memory/dev-session-2026-03-24-14-00.md`.
- `dashboard-v4/client/dist/`, because it is a Vite build output.
- `dashboard-v4/server/data/dashboard.db*`, because SQLite databases and WAL/SHM files are runtime state.
- `opc-platform/frontend/dist/` and `openclaw-statusline/dist/`, because they are generated build outputs.
- `memory/evolution/gep_prompt_*`, because these are generated prompt-cycle outputs already covered by `.gitignore`.
- Gitlink entries without `.gitmodules`:
  - `lobster-manager`
  - `skills/github-actions-workflows`
  - `skills/microsoft-api-guidelines`

## Keep For Now

- `memory/**`, `knowledge-base/**`, and root agent documentation stay in place for now. They should be reorganized later, not deleted blindly.
- old dashboard files under `dashboard/` stay until `dashboard-v4` is confirmed as the only active UI.
- skill directories stay until each skill has an owner, manifest status, and usage signal.

## Next Cleanup Candidates

- Move root documentation into `docs/` by topic.
- Archive older architecture drafts after `docs/architecture/architecture-redesign.md` is accepted.
- Move live state into `workspace/`.
- Convert copied third-party references into submodules or documented external links.
- Add CI checks for Windows-safe paths and generated artifact drift.
