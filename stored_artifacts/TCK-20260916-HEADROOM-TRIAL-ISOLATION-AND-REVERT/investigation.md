# Investigation — TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT

This ticket ran in two passes. The first (2026-09-20, earlier) hit a genuine sandbox-level network
block on `files.pythonhosted.org` and answered what it could from real upstream source instead of
installing anything — see `docs/plans/agent_infrastructure/headroom_context_compression_trial.md`'s
"Epic-level gate" section for that pass's full findings (`ccr_store.db`/`HEADROOM_CCR_BACKEND`
confirmed real, MCP/proxy CCR-store sharing confirmed, `HEADROOM_STATELESS` and `headroom wrap`'s
`~/.claude.json`/Serena side effect surfaced as new findings).

This document covers the second pass, after the user approved installing Headroom directly, with a
rescoped design: repository-scoped `.mcp.json` activation (not the originally-proposed bespoke
env-var isolation alone), install into `.venv` (never `.venv313`/`requirements.txt`), and
`headroom wrap`/`headroom mcp install` both explicitly forbidden.

## 1. The user's own shell is not behind the sandbox's network block

Confirmed by asking the user to run `.venv/bin/python3 -m pip install headroom-ai` themselves via
`!` — it succeeded on the first attempt, establishing that the `files.pythonhosted.org` block is
specific to this Claude Code sandbox, not universal.

## 2. Independently verified every technical claim the peer relayed before acting on it

- `.mcp.json` already registers `knowledge-search` and `github` the same way (`bash <script>`) —
  read directly.
- `requirements.txt`'s own header states agent tooling belongs in `requirements-knowledge.txt` —
  read directly.
- `tools/start_search_mcp.sh`'s absolute-shared-path-first pattern, and its own comment explaining
  why a relative `$REPO_ROOT/.venv` lookup fails in a worktree — read directly.
- `.venv` = Python 3.12.3, `.venv313` = Python 3.13.14 — checked directly.
- `~/.claude.json` = 78228 bytes with a real `mcpServers` key — checked directly.
- This worktree (`doc-tag-enforcement`) has no `.venv` of its own — confirmed via `ls`, which is
  exactly the worktree trap the launcher needs to handle.

## 3. New finding beyond what the peer's brief covered: `headroom mcp install`

The real installed CLI's own `--help` surfaced a second command with the identical hazard shape as
the already-forbidden `headroom wrap`: `headroom mcp install` "Install[s] the Headroom MCP server
into every detected coding agent... Claude Code today; Cursor / Codex / Continue / others added in
subsequent releases." This would write to user-scope config exactly like `wrap` does — never
invoked. The repo-scoped `.mcp.json` entry was hand-edited directly instead, which achieves the
identical practical outcome (a working, repo-scoped registration) without going through Headroom's
own installer at all.

## 4. Demonstrating each acceptance criterion with real, observed evidence

- **Repo scoping**: `claude mcp list` (Claude Code's own CLI inspection command) run from inside
  this repo shows `headroom: ... ✔ Connected`; run from a directory with no `.mcp.json` shows only
  the pre-existing global `claude.ai Claude Docs` server. This is Claude Code's own tooling
  reporting the real, current MCP configuration — not inferred from where `.mcp.json` happens to
  live.
- **Worktree safety**: this worktree has no `.venv` of its own (confirmed above), so the launcher
  working at all is itself proof the absolute-path-first resolution is doing real work, not
  incidental.
- **State isolation**: `HEADROOM_WORKSPACE_DIR` set to an isolated path; Headroom's own
  `ensure_workspace_dir()`/`ensure_config_dir()` created real directories there; a real file
  (`update_check.json`, an incidental auto-update-check cache) landed inside it; `~/.headroom`
  never existed at any point, confirmed by `ls` before/during/after.
- **`~/.claude.json` unmodified**: the raw byte hash is *not* the right check — it changes
  continuously from ordinary multi-session Claude Code activity unrelated to this work (confirmed:
  the changed top-level keys are session/usage metadata, e.g. `numStartups`,
  `cachedUsageUtilization`, never MCP-related). The real check, done both before and after: parse
  the file directly and confirm `mcpServers` is absent at the top level and absent from every one
  of its 5 `projects` entries.
- **Revert executed, not just documented**: two paired git commits (`967f1efa4` setup,
  `55a55e7cf` revert) with exactly symmetric diffs (47 insertions, then 47 deletions across the
  same 4 files) — the strongest available evidence that the repo returned to a clean tree.
  Filesystem-level: the isolated state directory removed; `headroom-ai` and its 5 dependencies
  pulled in solely for it (`ast-grep-cli`, `litellm`, `opentelemetry-api`, `tiktoken`, `tomlkit`)
  uninstalled from `.venv`; `search_mcp.py` (the pre-existing, unrelated tool sharing the same
  venv) still imports cleanly afterward, confirming the cleanup didn't collaterally break anything.
- **Nothing enabled**: `headroom proxy` was never started (`headroom doctor`'s own health check
  reported "not reachable" throughout); no session's `ANTHROPIC_BASE_URL` pointed at Headroom;
  `headroom learn`/`wrap`/`mcp install` were never invoked.
