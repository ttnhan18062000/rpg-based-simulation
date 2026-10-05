---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE
phase: done
date: 2026-10-05
tags: []
---

# TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE

## Title
Every in-place `docs/REGISTRY.yaml` regeneration indexes untracked files, so the documented close flow commits a registry CI rejects

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Routed by `rpg-feature-planning` (2026-10-05), reported by `rpg-implementer`; two lanes hit it the same day.

Mechanism (verified against `origin/main`): `tools/agent-monitoring/record_hand_orchestrated_closure.py:483` calls
`generate_registry(Path(".").resolve(), Path("docs/REGISTRY.yaml").resolve())`, and `tools/generate_registry.py` walks
the filesystem (`glob` / `rglob` over `docs/`, `done/`, `inprogress/`, `todos/`), not the tracked tree. On a branch that
carries a deliberately untracked file under an indexed path (another lane's ticket kept on disk, a planner's draft in
`todos/`), the regenerated registry lists a file that is not committed.
`tests/tools/test_generate_registry.py::test_check_flag_detects_no_drift_against_real_registry` then fails in CI, where
the file does not exist, so local and CI disagree.

This is worse than an omitted step: CLAUDE.md tells every lane the closure tool regenerates the registry for them, so the
documented flow produces the drift. The same in-place regeneration also runs in `implement-ticket.js` Finalize (same
function), the post-merge hook and `make docs-registry`; `rpg-implementer-2`'s handover records the same trap for those.

Workaround both lanes used, in the meantime: export the tracked tree (`git archive HEAD` or a detached
`git worktree add`), run `generate_registry.py --root <export>`, copy the result back, verify with `--check`
("In sync: 3178 entries").

## Scope
Make every automated regeneration index the tracked tree, or refuse loudly when it cannot:

- Preferred: regenerate from a clean export of `HEAD` plus the closing ticket's staged changes (the registry must still
  carry the ticket's new `done/` entry, which may not be committed yet at close time; decide and test the ordering), shared
  by the closure tool, Finalize and `make docs-registry`.
- Alternative: detect untracked `*.md` under indexed paths (`git ls-files --others --exclude-standard`) and fail with a
  message naming them and the clean-export recipe.
- Decide the post-merge hook's behaviour on the same rule.

## Out of Scope
- Changing what the registry indexes.
- The stale `todos/` copy gap (`TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS`), though both
  touch the close sequence and may share a PR.

## Acceptance Criteria
- With an untracked ticket file present under `agent-working/tickets/todos/`, a hand-orchestrated close produces a
  registry that passes `generate_registry.py --check` in a clean checkout, or the tool stops and names the file.
- The closing ticket's own `done/` entry is still in the regenerated registry.
- A test pins the untracked-file case for each entry point changed.
- CLAUDE.md and `docs/guides/delivery_process.md` describe the real behaviour (any CLAUDE.md edit needs the owner's
  literal-diff confirmation).

## Related Tickets
- `TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS`
- `TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES` (added the closure tool's regeneration)
- `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`

## Related Docs
- `CLAUDE.md` (After Work)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE/`

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/generate_registry.py`
- `.claude/workflows/implement-ticket.js` (Finalize)
- the post-merge git hook and the `docs-registry` Makefile target
- `tests/tools/test_generate_registry.py`

## Assumptions / Open Questions
- Clean export versus refuse-and-warn is the implementer's call; the export fixes it silently, the refusal surfaces it.
- Side note from the same close, not in scope: the test-plan advisory warned about a missing `## Proof Plan` section;
  reported as possibly noisier than intended.

## Implementation Notes
Chose tracked-tree indexing over clean export or refuse-and-warn: one change at the shared function covers all entry points, silently and correctly.

## Test Summary
`tests/tools/test_close_sequence_repairs.py` (registry cases: 10 tests), `tests/tools/test_generate_registry.py`, `tests/tools/test_done_checker_static.py`; full `tests/tools tests/docs`: 4206 passed, 55 skipped, 2 xfailed.

## Files Changed
`tools/generate_registry.py`, `tools/agent-monitoring/record_hand_orchestrated_closure.py`, `tools/gate_checks/done_checker_static.py`, `tools/hooks/registry_post_merge_regen.sh` (comment), `tests/tools/test_close_sequence_repairs.py`, `docs/guides/delivery_process.md`, `docs/REGISTRY.yaml` (regenerated). CLAUDE.md is unchanged.

## Completion Summary
Every regeneration entry point (`generate_registry.py`, `make docs-registry`, the post-merge hook, the closure tool, Finalize) now indexes only files git tracks or has staged, so an untracked draft never reaches a committed registry; the closing ticket and its stored artifacts are passed as `include` so its own `done/` entry is still present. Verified: `generate_registry.py --check` is in sync with untracked drafts on disk. A non-git root is indexed as before. A bare `make docs-registry` needs the closing ticket `git add`ed first (documented). CLAUDE.md is not edited: its "regenerated automatically" statement is now true.
