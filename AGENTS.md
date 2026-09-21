# AGENTS.md

## Cursor Cloud specific instructions

### Repository type

Mira-project is a **documentation / knowledge-continuity repository**, not a software
application. All tracked files are Markdown (`*.md`) plus one Cursor rule (`.cursor/rules/mira-workflow.mdc`)
and `.gitignore`. There is **no application code, no package manager, no dependencies,
and no build / test / lint / run tooling**. Do not invent any.

- Source of truth: `PROJECT_MEMORY.md` (current Mira state), `docs/lineage.md` (lineage),
  and Git history (past states + rationale). See `README.md`.
- The `.gitignore` lists `__pycache__/` and `node_modules/` defensively; there is currently
  no Python or Node code in the repo.

### There is nothing to install / build / test / lint / run

- **No dependency install step is needed.** The only required tool is `git` (already present).
- There are **no** lint, test, build, or dev-server commands. If asked to "run the app",
  the equivalent is the Git-based continuity workflow: read `PROJECT_MEMORY.md`, make a
  minimal Markdown edit, and commit/push it on a branch/PR.
- Python 3 and Node are available in the base image but are unused by this repo.

### Working conventions (from `.cursor/rules/mira-workflow.mdc`)

- Respond in Japanese unless the user specifies English.
- Keep changes minimal; do not add new directories, taxonomies, or log systems without a
  clear, stated use case. Do not refactor beyond the request.
- Prefer branches + PRs so diffs and rationale are reviewable before reaching `main`.
- Never commit secrets (`.env`, API keys, passwords, confidential info) — the repo is public.
