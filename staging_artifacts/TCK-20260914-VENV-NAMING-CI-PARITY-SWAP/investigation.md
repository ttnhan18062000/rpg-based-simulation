---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
phase: open
date: 2026-09-15
tags: [ai, process-improvement]
---

# Investigation — TCK-20260914-VENV-NAMING-CI-PARITY-SWAP

## Confirmed baseline

```
$ .venv/bin/python3 --version      -> Python 3.12.3
$ .venv313/bin/python3 --version   -> Python 3.13.14
$ grep python-version .github/workflows/test.yml   -> "3.13" (every job)
$ .venv/bin/python3 -c "import torch"      -> OK
$ .venv313/bin/python3 -c "import torch"   -> ModuleNotFoundError
```

Matches the ticket's own claim exactly: `.venv` (3.12) is the default-named env, holds the
knowledge-search stack, and does not match CI. `.venv313` (3.13) matches CI but is not the
default-named env any tool reaches for.

## Hazard #1 (already named in the ticket's own Scope, re-confirmed): `tools/start_search_mcp.sh`

```bash
for py in \
    "/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3" \
    "$REPO_ROOT/.venv/bin/python3" \
    "/home/vboxuser/Work/venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] && exec "$py" "$SCRIPT_DIR/search_mcp.py" "$@"
done
```

First candidate is an *absolute*, hardcoded path to the current `.venv`. After a naive rename
(`.venv` → `.venv-knowledge`, `.venv313` → `.venv`), this candidate still exists — it now IS the
3.13 env, which lacks `torch`/`sentence-transformers` (confirmed above). This is **not** the silent
fallthrough-to-bare-python3 failure the ticket's Request Summary describes for the general
"unnamed reference" case — `exec` still succeeds against an executable interpreter, so the script
does not fall through to later candidates. Instead `search_mcp.py` would start under the wrong
interpreter and fail at its own `import torch` (or whatever dependency it needs first) — a louder
failure than silence, but still a real breakage requiring this line's absolute path updated to
point at the new knowledge-stack env name.

## Hazard #2 — NOT named in the ticket's own Scope, found by grep per AC #3 ("don't assume")

`Makefile`'s `knowledge-index`, `knowledge-index-update`, and `eval-search` targets all resolve
their interpreter via `$(PYTHON3)` or an inline copy of the same discovery loop:

```make
PYTHON3 := $(shell for py in .venv/bin/python3 /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done)
...
knowledge-index: ...
	$(PYTHON3) tools/knowledge_search.py build
knowledge-index-update: ...
	$(PYTHON3) tools/knowledge_search.py build --incremental
...
eval-search: ...
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do command -v "$$py" >/dev/null 2>&1 && echo "$$py" && break; done) tools/eval_search.py
```

`$(PYTHON3)`'s FIRST candidate is the relative `.venv/bin/python3` — after rename this resolves to
the new 3.13 env, which `tools/knowledge_search.py build` (and `eval_search.py`) need `torch`/
`sentence-transformers` from and will not have. **`make knowledge-index`, `make knowledge-index-
update`, and `make eval-search` would all break post-rename** unless they resolve their interpreter
independently of the general-purpose `$(PYTHON3)`.

Every OTHER `$(PYTHON3)`/`$(PYTHON)`-using Makefile target (serve, docs-registry, sim, tests, etc. —
grepped, ~15 call sites) is engine/API/tooling code that *should* run under whichever env `.venv`
resolves to post-rename (that becomes correct, not broken, since it becomes the CI-matching 3.13
env) — those need no change. Only the three knowledge-stack-specific targets above are at risk.

## Hazard #3 — checked, confirmed NOT a hazard

- `tools/codebase_health_baseline.py:77` — `.venv`/`venv` appear only in a generic directory-name
  exclusion list for a codebase scanner (skip these dirs when walking). Directory-name-agnostic to
  which env is which; unaffected by a rename.
- `tools/agent_codex_posttool_adapter/command.py:10` — `root / ".venv" / "bin" / "python3"`,
  relative, used to render a hook command string for `hook_entry.py` (general tooling, not
  knowledge-search). Resolves correctly to whichever env sits at `.venv` post-rename — this becomes
  *more* correct after the swap (CI-matching env), not broken.
- `tools/perf/live_map_ws_payload_measure.py:66` — a `.venv/bin/python3 ...` example invocation
  inside a docstring/comment, not a runtime path resolution. No functional impact either way, but
  worth a mention in the doc pass since it now illustrates the (still-correct) generic-env usage.
- `.mcp.json` — references `tools/start_search_mcp.sh` by relative path only, no venv name baked in
  directly (confirmed, matches the ticket's own Related Code Areas note).
- The ~50+ hits in `tickets/done/*.md` are historical prose recording what command a past ticket's
  implementer actually ran at the time — correctly untouched; rewriting history in closed tickets is
  out of scope and would misrepresent what was actually run.

## `docs/guidelines/agent_working_environment.md` — exact prose needing the swap

Read the current file in full. The venv table (lines 33-35), the "Run tests as..." sentence
(line 37), the "must be preserved" paragraph (line 48, which also cites
`tools/start_search_mcp.sh`'s hardcoded path — needs updating to match whatever the new absolute
path becomes), and the `uv venv .venv313 ...` first-time-setup recipe (lines 68-70, which should
become `uv venv .venv-knowledge ...` or whatever the renamed knowledge env is called, since a fresh
machine following this doc after the swap should build the knowledge env under its NEW name, not
recreate a stray `.venv313`).

## `search_docs` verification plan (AC #2 — "verified by a real query, not by the MCP server merely
## starting")

Before and after the rename, run an actual `mcp__knowledge-search__search_docs` call (already used
throughout this ticket's own investigation) and confirm it returns real, non-empty results — not
just that the MCP server process starts without crashing. A server that starts but silently returns
zero results (e.g. an empty/stale index) would pass a weaker "does it start" check while still
being broken for the AC's actual purpose.

## Sequencing hazard (the ticket's own Assumptions, re-confirmed as still live)

`.venv` is shared across every session and worktree on this machine — confirmed via this session's
own repeated experience this batch (multiple concurrent sessions in `.claude/worktrees/*` all
resolving to the one absolute shared venv path). A rename mid-task for any concurrent session
running `.venv/bin/python3` breaks that session's next command with no warning. This is not a
question this investigation can answer on its own — it requires knowing whether other sessions are
active right now, which only the user (or a live `ListAgents` check immediately before executing)
can answer with confidence. See plan.md for the recommended sequencing and why this ticket's own
implementation stops short of executing the actual `mv` commands.
