---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP
phase: done
date: 2026-09-21
tags: [ai, registry, process-improvement, workflows]
---

# TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP

## Title
An epic ticket closed via the CLAUDE.md folder-move rule (`tickets/done/{folder}/`) disappears
from `docs/REGISTRY.yaml`, and its `done_checker_static.py` finalize checks fail — a pre-existing
gap, deferred, not this batch's problem to fix

## Status
DONE — picked up and fixed 2026-09-22.

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found while closing `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (2026-09-21) via CLAUDE.md's
own written rule: "When all tickets in the folder are done, move the entire folder to
`tickets/done/{folder}/`." `tools/generate_registry.py` (its own docstring, lines 355-365) walks
`tickets/done/*.md` **flat only** — it never recurses into `tickets/done/{folder}/`, so an epic
ticket closed this way is invisible to the registry, even though it is genuinely closed and its own
file genuinely exists under `tickets/done/`. `tools/gate_checks/done_checker_static.py`'s finalize
conditions (`migration_complete`, `ticket_finalized`, `registry_entry_regenerated`) have the same
flat-path assumption and FAIL for the same reason — not because anything is actually wrong with the
closure, but because the checker looks for the ticket file at a flat `tickets/done/{id}.md` path
that a folder-closed epic never uses.

**Confirmed on two independent real closures, not a one-off:**
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (closed 2026-09-15, already accepted, living at
  `tickets/done/agent-monitoring-retro-anomalies/`) — 0 entries in `docs/REGISTRY.yaml`, same 3
  `done_checker_static.py --tier epic --part finalize` conditions FAIL when re-run against it today.
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (closed 2026-09-21, living at
  `tickets/done/headroom-context-compression-trial/`) — `grep -c` confirms 1 entry on `origin/main`
  (indexed while the ticket lived in `tickets/todos/`) dropping to 0 once moved into the folder on
  `tickets/done/`; same 3 finalize conditions FAIL identically.

Child tickets closed at the flat `tickets/done/` root (matching CLAUDE.md's own note that individual
children move out of the folder as they close, leaving only the epic + `SEQUENCE.md` behind) remain
correctly indexed — only the folder-nested epic ticket itself is affected.

## Scope
When picked up:
- Either make `generate_registry.py` recurse into one level of `tickets/done/{folder}/` (matching
  how it already must handle `tickets/todos/{folder}/` for open epics, if it does — verify first
  rather than assume), or give folder-closed epics a documented, deliberate registry-visibility
  workaround.
- Make `done_checker_static.py`'s finalize path lookups folder-aware for epic-tier tickets closed
  via the CLAUDE.md folder-move rule, so a legitimate folder closure doesn't read as 3 failed
  conditions.
- Decide whether the fix should be scoped to epic-tier tickets specifically, or any ticket that
  ends up in a `tickets/done/{folder}/` path for any reason.

## Out of Scope
- **Not implemented in this ticket.** Filed to record the gap with real evidence, not to fix it —
  per the user's own defer-minor-effect rule: this rides along unbuilt until someone picks it up
  deliberately, since it affects registry completeness/search convenience and a manual
  `done_checker_static.py` re-run's readability, not correctness of the actual closure or any
  blocking gate.
- Changing the CLAUDE.md folder-move rule itself, or how epics are closed. The rule is correct;
  the tooling around it hasn't caught up.
- Any change to `docs/REGISTRY.yaml`'s schema or `done_checker_static.py`'s non-finalize conditions.

## Acceptance Criteria
- [x] `generate_registry.py` includes an entry for a folder-closed epic ticket (or an equivalent,
      deliberately-chosen visibility mechanism is in place and documented).
      `collect_tickets()` now also walks `tickets/done/*/*.md` (one level deep, excluding
      `SEQUENCE.md`), confirmed present in the regenerated registry for both named precedents.
- [x] `done_checker_static.py --tier epic --part finalize`, run against a real folder-closed epic,
      reports PASS for `migration_complete`/`ticket_finalized`/`registry_entry_regenerated`
      (adjusted to whatever the real evidence requirements become once folder-awareness is added).
      `migration_complete` now reports `NA` (epic tier, same shape as hotfix — see Implementation
      Notes for why this, not a folder-specific fix, was the right adjustment); the other two
      report `PASS`.
- [x] Re-run against both real precedents named above (`TCK-20260915-MONITORING-ANOMALY-DETECTION-
      EPIC`, `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`) to confirm the fix generalizes, not
      just fixes whichever epic prompted the ticket. Both PASS, run live, not assumed.
- [x] No blocking gate is introduced — this stays report/index tooling, matching the existing
      report-only convention for `docs/REGISTRY.yaml` regeneration and `done_checker_static.py`'s
      own advisory-when-hand-orchestrated shape. Confirmed — no new gate, no new blocking status
      value, both tools' existing shapes preserved.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (done) — where this was found.
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the independent precedent confirming
  this isn't a one-off.
- `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` (done) — established the "regenerate unconditionally at
  close" convention this gap quietly undermines for folder-closed epics specifically.

## Related Docs
- `CLAUDE.md`'s "After Work" section — the folder-move rule this gap interacts with.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP/` (plan.md,
  investigation.md, test_plan.md).

## Related Code Areas
- `tools/generate_registry.py` (docstring lines 355-365 describe the flat-only `tickets/done/*.md`
  walk)
- `tools/gate_checks/done_checker_static.py` (`migration_complete`, `ticket_finalized`,
  `registry_entry_regenerated` finalize conditions)

## Assumptions / Open Questions
- Whether `generate_registry.py` already has special handling for `tickets/todos/{folder}/` (open
  epics) that could be mirrored for `tickets/done/{folder}/` (closed epics), or whether open-epic
  folders have the identical gap on the todos side too. Not checked as part of filing this ticket —
  first thing to verify when picked up.
- Whether the fix belongs in `generate_registry.py`'s walk logic, a small folder-aware helper both
  tools share, or something else entirely. Genuinely open.

## Implementation Notes
See `stored_artifacts/TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP/investigation.md`
for the full trace. Summary:
- Confirmed `tickets/todos/{folder}/` already recurses (`rglob`, from
  `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE`); `tickets/done/` did not.
  Mirrored that precedent rather than inventing a new pattern.
- Censused all 84 real `tickets/done/*/` folders before choosing depth: every one is exactly one
  level deep (an epic ticket + `SEQUENCE.md`, or `SEQUENCE.md` alone for an epic with no separate
  top-level ticket file) — `glob("*/*.md")`, not `rglob`, is correct and sufficient.
- Found `migration_complete`'s own FAIL is a *separate*, pre-existing gap unrelated to folder
  nesting: no epic ticket, flat or nested, has ever had its own `stored_artifacts/{ticket_id}/`
  (epic tier is "scope only," per CLAUDE.md's own Tier Routing table — child tickets carry the
  real investigation/plan/test_plan work). Fixed with an epic-tier `NA` branch, same shape as the
  pre-existing hotfix branch, scoped to `tier == "epic"` specifically — not folded into the
  folder-awareness fix, and recorded as such so it isn't misread as one.
- `registry_entry_regenerated` needed no direct change — its own `path.startswith("tickets/done/")`
  check already covers a nested path once `collect_tickets()` emits the entry; confirmed by
  re-running rather than assumed.
- Scope decision (per the ticket's own open question): the folder-awareness fix is generic (any
  ticket ending up in `tickets/done/{folder}/`, not epic-specific), matching the existing
  `todos/` precedent's own scope; the `migration_complete` fix is genuinely epic-tier-specific.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py \
  tests/tools/test_done_checker_audit.py tests/tools/test_registry_query.py \
  tests/tools/test_premise_staleness_check.py tests/integrity/test_registry_merge_driver.py \
  tests/tools/test_status_drift_check.py tests/tools/test_codebase_health_baseline.py -q
# 273 passed
```
Real acceptance check (per AC, not just synthetic fixtures) — both named precedents:
```
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC --tier epic --part finalize
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC --tier epic --part finalize
# Both: RESULT PASS
```
Both ticket IDs confirmed present in the regenerated `docs/REGISTRY.yaml` (`grep -c` returns 4 —
ticket_id + path field, 2 entries). `make docs-registry-check` confirms in sync. `graphify update .`
run, no topology changes.

## Files Changed
- `tools/generate_registry.py` — `collect_tickets()` also walks `tickets/done/*/*.md`, one level
  deep, excluding `SEQUENCE.md`.
- `tools/gate_checks/done_checker_static.py` — `check_ticket_finalized()` folder-aware; added an
  epic-tier `NA` branch to `check_migration_complete()`.
- `tests/tools/test_generate_registry.py` — new `TestFolderClosedDoneWalk` class (4 tests).
- `tests/tools/test_done_checker_static.py` — 4 new regression tests.
- `docs/REGISTRY.yaml` — regenerated; now includes both previously-invisible epic tickets.

## Completion Summary
Fixed the folder-visibility gap for epic tickets closed via CLAUDE.md's own folder-move rule.
`generate_registry.py` now walks one level into `tickets/done/{folder}/`, mirroring the `todos/`
precedent already in place for open epics. `done_checker_static.py`'s finalize conditions now
correctly report against both real named precedents: `ticket_finalized` and
`registry_entry_regenerated` PASS, and `migration_complete` correctly reports `NA` — a separate,
genuinely epic-tier-specific gap (not a folder-nesting consequence) found and fixed along the way,
since no epic ticket has ever had its own stored artifacts. No new blocking gate introduced; both
tools remain report/advisory-only, matching their existing shape. 8 new regression tests added,
scoped test suite (273 tests across both changed files and every adjacent registry-consuming test
file checked) all pass.
