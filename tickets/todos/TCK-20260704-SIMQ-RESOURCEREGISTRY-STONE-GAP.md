---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP
phase: open
date: 2026-07-04
tags: [simulation_quality, world, ecology, resource-registry, bug]
---

# TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP

## Title
Fix ResourceRegistry KeyError("STONE") crash in world/ecology.py's dynamic resource-node generation

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/world/ecology.py`'s dynamic resource-node generator emits a resource kind (`STONE`) that is
never registered in `ResourceRegistry`, causing a `KeyError: Resource not found in ResourceRegistry:
STONE` crash. This is a genuine, pre-existing engine bug, independently observed twice during the
2026-07-03/04 SimQ Uplift Batch 3 work:

1. `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s regression sweep hit the same crash on an unrelated test path.
2. `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4a existing-anchor drift check needed to
   re-run `simq_routing_test`'s calibration (`ENABLE_ADVENTURE_ROUTING=ON`) to verify its 3
   already-committed anchor entries were unaffected by that ticket's content changes — but the
   re-run crashes with this exact error, blocking verification. Confirmed via `git stash`
   bisection (in the WORLD-CORPUS ticket) that this crash is 100% pre-existing and reproduces
   identically with or without that ticket's changes — not a regression it introduced.

Net effect: `simq_routing_test`'s 3 calibration anchor entries (`seed{42,123,456}_500t`) could not
be re-verified after WORLD-CORPUS's content changes and were left unchanged (not marked verified).
This bug should be fixed so that world can be recalibrated and its anchors properly confirmed.

## Scope
1. Re-verify the finding against current `src/` (this ticket may be picked up after other changes land).
2. Trace `src/world/ecology.py`'s dynamic resource-node generation to find where it emits `STONE`
   (or a similarly unregistered kind) and confirm the exact trigger condition (which world/scenario
   configuration reaches this code path — confirmed to reproduce for `simq_routing_test` with
   `ENABLE_ADVENTURE_ROUTING=ON`; check whether it also reproduces without that flag, or is specific
   to routing-enabled runs).
3. Fix by either (a) registering `STONE` (and any other similarly-missing kinds found during
   investigation) in `ResourceRegistry`, or (b) fixing the generator to only emit registered kinds
   — pick whichever is architecturally correct after reading `ResourceRegistry`'s registration
   source of truth (likely a content catalog file) to determine if `STONE` was an intentional
   omission or an oversight.
4. Re-run `simq_routing_test`'s calibration (`seed{42,123,456}_500t`, `ENABLE_ADVENTURE_ROUTING=ON`)
   after the fix and confirm its 3 existing anchor entries in `grade_anchors.json` are still
   accurate (update in place if the fix itself causes any grade drift, following the same
   documented-attribution pattern used in `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4a).
5. Add a regression test proving the dynamic resource-node generator never emits an unregistered
   kind.

## Out of Scope
- Any other content/world changes beyond what's needed to fix this specific crash
- Changing `ENABLE_ADVENTURE_ROUTING`'s default or scope
- Re-litigating `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s already-completed work (that ticket's
  8-of-10 `dungeon_crawl` anchor updates and 15 new world anchors are done and correct; this ticket
  only closes the `simq_routing_test` gap that ticket could not verify)

## Acceptance Criteria
- [ ] Root cause confirmed with file:line evidence
- [ ] Fix applied (either register `STONE` or fix the generator, whichever is correct)
- [ ] `simq_routing_test`'s calibration (`seed{42,123,456}_500t`, routing ON) runs to completion
      without crashing
- [ ] `simq_routing_test`'s 3 existing anchor entries in `grade_anchors.json` re-verified (updated
      in place only if the fix causes genuine grade drift, with a documented attribution note)
- [ ] New regression test prevents recurrence
- [ ] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (done) — found this bug via Step 4a, could not fix it
  (out of scope for that ticket), left `simq_routing_test`'s anchors unverified
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (done) — independently hit the same crash in an unrelated
  regression sweep, confirming it's not scenario-specific to WORLD-CORPUS's changes

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — WORLD-CORPUS's drift-check note documents
  this exact blocker

## Related Stored Artifacts
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md` — Step 4a's drift-check
  procedure, which this ticket should re-run once the crash is fixed

## Related Code Areas
- `src/world/ecology.py` — dynamic resource-node generation, the emission site
- Wherever `ResourceRegistry` is populated (likely a content catalog loader) — the registration
  source of truth to check `STONE`'s absence against

## Assumptions / Open Questions
- UQ-1: Is this crash specific to `ENABLE_ADVENTURE_ROUTING=ON` runs, or does it reproduce in any
  world/scenario that exercises `ecology.py`'s dynamic resource-node path? Confirm during
  investigation — this affects whether other calibration worlds are also silently at risk.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
