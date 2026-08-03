---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX
phase: done
date: 2026-08-03
tags: [agent-monitoring, bug]
---

# TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX

## Title
Add `agent-monitoring-index` to the Makefile's `.PHONY` list to fix silent permanent no-op

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The `agent-monitoring-index` Makefile target (Makefile line 281) is not declared in the `.PHONY`
list (Makefile line 1). `tools/agent-monitoring/build_index.py`'s `DEFAULT_DB_PATH = Path(
"agent-monitoring-index/monitoring.db")` creates a real, gitignored directory named exactly
`agent-monitoring-index/` at the repo root (`.gitignore` line 267; confirmed present on disk with
a 30MB `monitoring.db` inside, last modified Jul 29). Because the Makefile target shares that exact
name, is not phony, and has no prerequisites, `make` treats it as a file target that already exists
and is therefore always up-to-date. Once the directory has been created once, every subsequent
`make agent-monitoring-index` becomes a silent, permanent no-op that never re-runs
`build_index.py`, even when the underlying `agent-monitoring/*.jsonl` source data has changed.

Confirmed live and reproduced directly in this repo's current working tree:
`make --dry-run agent-monitoring-index` returns `make: 'agent-monitoring-index' is up to date.`
instead of showing the recipe.

Surfaced by `tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`
failing during an unrelated ticket's Test gate (TCK-20260803-RETRO-TOOL-SAFETY-AUDIT). That ticket
does not itself fix the Makefile — this ticket is the dedicated fix.

## Scope
- Add `agent-monitoring-index` to the Makefile's `.PHONY` line (Makefile line 1), matching the
  existing convention already used for every other target in that list (e.g. `docs-build`,
  `knowledge-index`, `agent-monitoring-retro`, `agent-monitoring-validate`, `agent-monitoring-query`,
  `agent-monitoring-epic-staleness`) — none of which correspond to real output paths either.
- Update `docs/parity_ledger/infrastructure.yaml` entry `INFRA-285`'s `v2_evidence` to flag that its
  "no `agent-monitoring-*` target is in `.PHONY`" precedent claim is now partially superseded by this
  fix (required by the Authoritative Mechanics Rule's parity-ledger-in-same-session-as-behavior-change
  requirement, since this ticket's own Related Docs section already cited INFRA-285 as the entry this
  change would make stale).

## Out of Scope
- Changing `tools/agent-monitoring/build_index.py`'s `DEFAULT_DB_PATH` or any other behavior of
  `build_index.py`.
- Changing any other Makefile target, including the four sibling `agent-monitoring-*` targets
  (`agent-monitoring-retro`, `agent-monitoring-validate`, `agent-monitoring-query`,
  `agent-monitoring-epic-staleness`, `agent-monitoring-weight-check`) — none of them collide with a
  real filesystem path the way `agent-monitoring-index` does (see Related Docs / parity note below),
  so they are not affected by this bug and are not touched here.
- Re-running the index build itself (deleting or regenerating the existing
  `agent-monitoring-index/monitoring.db`) — this ticket only fixes the Makefile's up-to-date
  detection; the next real `make agent-monitoring-index` invocation (run by whoever needs a fresh
  index) will do that naturally once the fix lands.
- Any change to `.gitignore` — the gitignored directory name is correct and expected; the bug is
  purely the Makefile/filesystem name collision plus the missing `.PHONY` declaration.

## Acceptance Criteria
- [ ] `agent-monitoring-index` appears in the Makefile's `.PHONY` list (Makefile line 1).
- [ ] `make --dry-run agent-monitoring-index` shows the recipe (the `build_index.py` invocation)
      instead of `make: 'agent-monitoring-index' is up to date.`, even though the local
      `agent-monitoring-index/` directory already exists on disk.
- [ ] `tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`
      passes.
- [ ] The other three `TestMakeTarget` tests in the same file
      (`test_makefile_has_agent_monitoring_index_target`,
      `test_makefile_agent_monitoring_index_calls_build_index`,
      `test_agent_monitoring_index_not_in_test_ci_all_targets`) and
      `TestGitignore::test_db_path_in_gitignore` still pass unmodified (regression guard — this
      fix should not touch their assertions).

## Related Tickets
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (in `tickets/inprogress/`) — the ticket whose Test-gate run
  surfaced this failing test; it does not fix the Makefile itself, this ticket is the dedicated fix.
- TCK-20260713-MONITORING-SQLITE-INDEX (in `tickets/done/`) — originally built the
  `agent-monitoring-index` target and `build_index.py`'s `DEFAULT_DB_PATH`; this ticket does not
  change that design, only the `.PHONY` declaration.
- TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE (in `tickets/done/`) — added the sibling
  `agent-monitoring-weight-check` target and its parity ledger entry (INFRA-285) explicitly notes
  that target was *not* added to `.PHONY`, citing a "confirmed-via-grep precedent that no other
  `agent-monitoring-*` target is listed there either." That precedent is real but does not apply
  here: `agent-monitoring-weight-check` has no colliding filesystem path, so its non-phony status is
  harmless (a minor style inconsistency, not a functional bug). `agent-monitoring-index` is the one
  target whose name collides with a real, gitignored, once-created directory
  (`agent-monitoring-index/`), which is what turns the missing `.PHONY` entry into an actual silent
  no-op. See Assumptions / Open Questions.

## Related Docs
- `docs/guides/agent_monitoring.md` ("Makefile Targets" section documents
  `make agent-monitoring-index` as the way to rebuild the derived SQLite index)
- `docs/parity_ledger/infrastructure.yaml`, entry `INFRA-285` (v2_evidence text explicitly records
  the "no `agent-monitoring-*` target is in `.PHONY`" precedent this ticket partially departs from,
  for the reason above)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/` (investigation.md, plan.md,
  test_plan.md) — original design of `build_index.py` and the `agent-monitoring-index` target.

## Related Code Areas
- `Makefile` (line 1 `.PHONY` list; line 281 `agent-monitoring-index` target)
- `tools/agent-monitoring/build_index.py` (line 45 `DEFAULT_DB_PATH` — read for context only, not
  modified)
- `.gitignore` (line 267 `agent-monitoring-index/` entry — read for context only, not modified)
- `tests/tools/test_build_index.py` (`TestMakeTarget` class, lines 317-348)

## Assumptions / Open Questions
- Assumes the fix is exactly the one-line `.PHONY` addition and nothing else — confirmed by
  reproducing the bug directly (`make --dry-run agent-monitoring-index` currently returns
  `'agent-monitoring-index' is up to date.` against this repo's real, already-created
  `agent-monitoring-index/` directory) and by the target's own recipe having zero prerequisites, so
  declaring it phony is sufficient to force `make` to always re-run it. If this assumption is wrong
  (e.g. if `make` still short-circuits after the fix for some other reason), the acceptance criteria
  dry-run check will catch it before this ticket can close.
- `layer: observability` was chosen over `testing` because the defect is in the build/refresh
  mechanism for agent-monitoring tooling itself (matches the `layer` used by the target's originating
  ticket, TCK-20260713-MONITORING-SQLITE-INDEX, and its sibling TCK-20260716-AGENTOPS-BUILD-SERVE),
  even though the bug was discovered via a test failure. If a future reviewer disagrees, `testing` is
  the next-best fit.
- INFRA-285's "no `agent-monitoring-*` target in `.PHONY`" note could be read as an intentional
  repo-wide convention rather than an accidental gap. This ticket's position (see Related Tickets) is
  that INFRA-285 only established that omission is *harmless* for targets with no colliding
  filesystem path, not that it is *desirable* — `agent-monitoring-index` is a distinct, worse case
  because the collision makes the omission a real functional bug, confirmed by direct reproduction
  above. If Investigate/Verify disagrees with this reading, that is a scope-level disagreement worth
  surfacing before this hotfix closes, not a silent judgment call.

## Implementation Notes
Added `agent-monitoring-index` to the end of the `.PHONY` list on Makefile line 1, matching the
existing space-separated convention used for every other target in that list. No other line in the
Makefile was touched, and `tools/agent-monitoring/build_index.py` was not modified, per the
ticket's Out of Scope. Verified the fix directly: `make --dry-run agent-monitoring-index` now
prints the recipe (`.venv/bin/python3 tools/agent-monitoring/build_index.py`) instead of
`make: 'agent-monitoring-index' is up to date.`, even with the real `agent-monitoring-index/`
directory already present on disk — confirming the `.PHONY` declaration is what fixed the
false up-to-date short-circuit.

Also updated `docs/parity_ledger/infrastructure.yaml` entry `INFRA-285`: appended a dated
clarification to its `v2_evidence` noting its "no other `agent-monitoring-*` target is in `.PHONY`"
precedent claim is now partially superseded (`agent-monitoring-index` is in `.PHONY` as of this
ticket; `agent-monitoring-weight-check` itself is unaffected and remains non-phony, since it has no
colliding filesystem path). `status`/`priority`/`test_path`/`divergence_note` were left unchanged —
INFRA-285's core claims about `compute_weight_sensitivity_report`/CLI behavior are untouched.

## Test Summary
Ran `tests/tools/test_build_index.py` in full (17 tests, all passed), including the previously
failing `TestMakeTarget::test_makefile_dry_run_agent_monitoring_index` and the three regression-guard
tests named in Acceptance Criteria (`test_makefile_has_agent_monitoring_index_target`,
`test_makefile_agent_monitoring_index_calls_build_index`,
`test_agent_monitoring_index_not_in_test_ci_all_targets`) plus `TestGitignore::test_db_path_in_gitignore`.
No test files were modified.

## Files Changed
- `Makefile` (line 1: added `agent-monitoring-index` to `.PHONY` list)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-285` `v2_evidence`: appended a dated clarification
  noting its "no `agent-monitoring-*` target is in `.PHONY`" precedent claim is now partially
  superseded by this fix)

## Completion Summary
Fixed the silent permanent no-op in `make agent-monitoring-index` by adding the target to the
Makefile's `.PHONY` list. The target's name collided with the real, gitignored
`agent-monitoring-index/` directory created by `build_index.py`'s `DEFAULT_DB_PATH`, so without the
`.PHONY` declaration `make` treated it as an up-to-date file target once that directory existed.
Single-line Makefile fix, no other Makefile targets or source files touched, plus a corresponding
`docs/parity_ledger/infrastructure.yaml` (`INFRA-285`) `v2_evidence` update to keep that entry's
now-superseded precedent claim accurate. All acceptance criteria verified: `.PHONY` list updated,
dry-run now shows the recipe, the previously failing test passes, and all sibling regression-guard
tests remain green.
