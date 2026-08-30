---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX
phase: done
date: 2026-08-26
tags: [mcp, setup]
---

# TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX

## Title
`make knowledge-index` / `make knowledge-index-update` fail with "Permission denied" from any git
worktree — reinvent an older, broken python3-discovery block instead of reusing `$(PYTHON3)`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`make knowledge-index` (Makefile:331-335) and `make knowledge-index-update` (Makefile:337-340) each
still use their own inline `$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3
python3; do [ -x "$$py" ] && echo "$$py" && break; done)` python3-discovery block. From any git
worktree (which gets no `.venv/` of its own), the loop finds no executable candidate, so the
`$(shell ...)` call expands to an empty string — collapsing the recipe to running
`tools/knowledge_search.py build[--incremental]` directly as a shell command. That file has no `+x`
bit, so the command fails with "Permission denied". Live-reproduced twice this session during two
separate ticket Finalize runs from a worktree.

The top-level `PYTHON3` variable (Makefile:35) already solves this correctly — it adds an
absolute-path fallback (`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`) that
works regardless of which worktree the command runs from, and `dev`/`dev-backend`/`serve`/
`serve-only` already consume it via `$(PYTHON3)`. `knowledge-index`/`knowledge-index-update` predate
that fix and were never migrated onto it.

## Scope
- `Makefile:331-335` (`knowledge-index` target): replace the inline `$(shell for py in ... done)`
  block with `$(PYTHON3)`, matching the `dev`/`serve` pattern exactly.
- `Makefile:337-340` (`knowledge-index-update` target): same replacement.
- Confirm (or add) `tests/tools/test_dashboard_makefile_targets.py`-style static/pinned coverage of
  both targets' recipe text so a future edit can't silently reintroduce the inline discovery block.
- Live-verify from a worktree (not the main checkout): run both `make knowledge-index` and
  `make knowledge-index-update` and confirm each resolves a real, pydantic-capable python3 and
  executes `tools/knowledge_search.py` instead of failing with "Permission denied" or silently
  no-op'ing on an empty `$(shell ...)` expansion.

## Out of Scope
- `eval-search` (Makefile:367-368): has the identical inline discovery pattern and the same missing
  absolute-path candidate, but was not named in this request's scope. Left as a known, separately
  fixable instance of the same bug class — do not fold it into this ticket's diff.
- Any change to `tools/knowledge_search.py` itself, its build/incremental-build logic, or its
  `+x` bit — the fix is purely in how the Makefile invokes it, not the script.
- Any change to the top-level `PYTHON3` variable definition (Makefile:35) itself — it is already
  correct; this ticket only makes two more targets consume it.
- Broader repo-wide sweep of every remaining bare-`python3`/inline-discovery Makefile target beyond
  the two named here — out of scope per the same reasoning
  `TCK-20260825-LIVE-VERIFICATION-TOOLING` used to explicitly limit its own scope to 4 targets.
- Any documentation rewrite of `docs/guidelines/agent_working_environment.md` — its existing
  `make knowledge-index`/`make knowledge-index-update` usage guidance is already accurate; this
  ticket only makes that guidance actually work from a worktree, no doc content needs to change.

## Acceptance Criteria
- [x] `Makefile:331-335`'s `knowledge-index` recipe uses `$(PYTHON3)`, no inline
      `$(shell for py in ... done)` block remains in that target.
- [x] `Makefile:337-340`'s `knowledge-index-update` recipe uses `$(PYTHON3)`, no inline
      `$(shell for py in ... done)` block remains in that target.
- [x] From a git worktree directory (not the main checkout), `make knowledge-index-update` runs
      `tools/knowledge_search.py build --incremental` via a real resolved python3 interpreter and
      does not fail with "Permission denied" or a bare empty-command shell error.
- [x] From a git worktree directory, `make knowledge-index` runs
      `tools/knowledge_search.py build` via a real resolved python3 interpreter, same success
      condition.
- [x] A static/pinned test (new or extended) guards both targets' recipe text so a future edit
      can't silently reintroduce the old inline discovery block or lose `$(PYTHON3)` usage.
- [x] Existing `tests/tools/test_dashboard_makefile_targets.py` suite (and any other Makefile-text
      static guard it overlaps with) still passes unchanged for every other pinned target.

## Related Tickets
- `TCK-20260825-LIVE-VERIFICATION-TOOLING` (done) — the ticket that introduced the top-level
  `PYTHON3` variable (Makefile:35) and migrated `dev`/`dev-backend`/`serve`/`serve-only` onto it.
  Its own Out of Scope explicitly named the gap this ticket closes: "Broader Makefile `python3`
  cleanup -- dozens of other targets still use bare `python3`; only the 4 `serve`-invoking targets
  this ticket's own tooling actually exercises were touched." This is a deliberate, documented prior
  scope boundary, not an oversight — not a conflict, just the ticket this one follows up on.
- `TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN` (done) — landed in the same commit as the
  `PYTHON3` variable; unrelated engine bug, no scope overlap.
- `TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC` (done) — earlier Makefile/`dev`-target doc hotfix,
  unrelated target, no scope overlap.

## Related Docs
- `docs/guidelines/agent_working_environment.md` — documents `make knowledge-index` /
  `make knowledge-index-update` usage and the git post-commit hook that auto-runs the incremental
  target; no content change needed, its guidance becomes actually true for worktrees once this
  fix lands.

## Related Stored Artifacts
None found covering this specific gap (hotfix tier — no staging artifacts required for this
ticket either).

## Related Code Areas
- `Makefile` (lines 33-35 `PYTHON3` variable definition, 331-340 the two broken targets, 367-368
  `eval-search` — same bug pattern, explicitly out of scope above)
- `tools/knowledge_search.py` (invoked by both targets, read-only reference — not modified)
- `tests/tools/test_dashboard_makefile_targets.py` (existing pinned-recipe-snapshot pattern to
  extend/mirror for the new coverage)

## Assumptions / Open Questions
- `layer: ai` was chosen because this fix is agent-orchestration/dev-tooling (the Makefile plumbing
  behind `search_docs`/Knowledge Gateway MCP index freshness), matching the layer used by the large
  cluster of prior KGMCP-related tickets, rather than `testing` (no test-infrastructure subsystem
  change) or `misc`.
- Assumes the fix is a pure mechanical substitution (`$(shell for py in ...)` → `$(PYTHON3)`) with
  no behavior change beyond "now actually resolves a python3 from a worktree" — if `$(PYTHON3)`'s
  candidate list is ever found to omit some environment `knowledge-index`/`knowledge-index-update`
  specifically needs (unlikely; `SSL_CERT_FILE`/`SSL_CERT_DIR` env exports on both targets are
  unrelated to interpreter discovery and untouched by this fix), that would invalidate this scope.

## Implementation Notes
Replaced the inline `$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3
python3; do [ -x "$$py" ] && echo "$$py" && break; done)` discovery block in both
`knowledge-index` (Makefile:331-335) and `knowledge-index-update` (Makefile:337-340) with the
existing top-level `$(PYTHON3)` variable (Makefile:35), matching the pattern already used by
`dev`/`dev-backend`/`serve`/`serve-only`. Pure mechanical substitution — no other line in either
recipe changed (echo text, `SSL_CERT_FILE`/`SSL_CERT_DIR` exports, and the trailing
`tools/knowledge_search.py build[--incremental]` invocation are untouched).

Added `test_knowledge_index_targets_use_python3_variable` to
`tests/tools/test_dashboard_makefile_targets.py`, following that file's existing
`_makefile_text`/`_extract_recipe` helper pattern: asserts both targets' recipes contain
`$(PYTHON3)` and contain neither `for py in` nor `$(shell` — guarding against a future edit
silently reintroducing the inline discovery block.

## Test Summary
Ran `tests/tools/test_dashboard_makefile_targets.py` with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest` (this worktree has no
local `.venv/`, so the absolute-path fallback interpreter was used directly): 4 passed, including
the new pinned-recipe guard and the pre-existing `test_existing_targets_unmodified` (confirms no
other pinned target's recipe was touched).

Live-verified from this worktree directory (which genuinely has no `.venv/` of its own — the
exact failure condition the ticket describes):
- `make -n knowledge-index-update` and `make -n knowledge-index` (dry-run) both print
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` as the resolved interpreter
  (the `PYTHON3` absolute-path fallback), not an empty string.
- `make knowledge-index-update` (full live run, not dry-run) executed
  `tools/knowledge_search.py build --incremental` via that real interpreter: it imported
  `pydantic`/`sentence_transformers`/`transformers` successfully and proceeded to attempt a
  HuggingFace model download, failing only with `OSError: We couldn't connect to
  'https://huggingface.co'` (network-blocked in this sandbox) — not "Permission denied" and not
  an empty-command shell error. This is the exact class of unrelated failure the ticket
  anticipates as acceptable evidence that python3 discovery itself now works.

## Files Changed
- `Makefile` — `knowledge-index` and `knowledge-index-update` targets now use `$(PYTHON3)`
- `tests/tools/test_dashboard_makefile_targets.py` — added
  `test_knowledge_index_targets_use_python3_variable`

## Completion Summary
Fixed `make knowledge-index` and `make knowledge-index-update`, which previously reinvented a
broken inline python3-discovery `$(shell for py in ... done)` block that resolved to an empty
string from any git worktree (no local `.venv/`), collapsing the recipe into directly executing
`tools/knowledge_search.py` as a shell command and failing with "Permission denied". Both targets
now consume the existing, already-correct top-level `$(PYTHON3)` variable (Makefile:35), matching
`dev`/`dev-backend`/`serve`/`serve-only`. Added a static pinned-recipe test guarding against
regression, and live-verified from this worktree that both targets now resolve a real
`.venv/bin/python3` and execute the underlying script successfully (up to an unrelated
network-blocked HuggingFace download).
