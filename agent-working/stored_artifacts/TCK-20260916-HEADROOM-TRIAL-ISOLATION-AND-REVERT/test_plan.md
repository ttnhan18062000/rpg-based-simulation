# Test Plan — TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT (second pass)

No pytest suite applies — this ticket touches machine/environment state (a venv, `.mcp.json`,
`~/.claude.json`) and repo config, not engine/API/test-suite code. Verification is entirely
real-execution evidence.

| Case | Verification |
|---|---|
| Base package only, no extras | `pip show headroom-ai` after install: no `fastapi`/`uvicorn`/`onnxruntime`/`transformers` in the dependency tree |
| `requirements.txt` untouched | `sha256sum requirements.txt` identical before install, after install, and after revert |
| `.venv313` untouched | `pip show headroom-ai` returns "not found" in `.venv313` throughout |
| MCP server registered and connects from inside this repo | `claude mcp list` run from inside `doc-tag-enforcement`: `headroom: ... ✔ Connected` |
| Worktree-safe (not just main-checkout-safe) | This worktree has no `.venv` of its own (`ls` confirms); the launcher still resolved via its absolute-path fallback |
| Not active outside this repository | `claude mcp list` run from a directory with no `.mcp.json`: only the pre-existing global `claude.ai Claude Docs` server listed, no `headroom` |
| `~/.claude.json` structurally unmodified | Parsed directly before and after: `mcpServers` absent at top level and in every one of its 5 `projects` entries, both times |
| State lands in the configured directory, not `~/.headroom` | `paths.ensure_workspace_dir()`/`ensure_config_dir()` created real directories at the isolated path; a real file (`update_check.json`) landed inside; `ls ~/.headroom` returned "No such file" before, during, and after |
| Revert executed, not just documented | Two git commits with exactly symmetric diffs: `967f1efa4` (47 insertions) then `55a55e7cf` (47 deletions), same 4 files |
| Revert didn't collaterally break the shared venv | `search_mcp.py` (pre-existing, unrelated tool in the same `.venv`) still imports cleanly after uninstalling `headroom-ai` and its 5 transitive-only dependencies |
| Nothing enabled | `headroom doctor` reports "not reachable at http://127.0.0.1:8787" throughout (proxy never started); `headroom learn`/`wrap`/`mcp install` never invoked |

Executed, in order: user-run `pip install`; `pip show` (3x, at install/pre-revert/post-revert
checkpoints); `sha256sum requirements.txt` (3x); `claude mcp list` (inside repo, outside repo, and
again after revert); direct `headroom.paths` calls under the isolated env var; `git log --stat` on
the two paired commits; `pip uninstall` for the package and its 5 dependencies; a final import
smoke-test of `search_mcp.py`.
