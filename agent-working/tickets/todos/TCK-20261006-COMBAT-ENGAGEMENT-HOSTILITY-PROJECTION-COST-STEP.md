---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP
phase: open
date: 2026-10-06
tags: [performance, combat, regression, investigation]
---

# TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP

## Title
`combat_engagement` grew by about 3.3 s per tick at movement[5000] somewhere between `c84352465` and `132bf09ca` (`is_hostile_compat` → `project_relation`); isolate the commit, and do not add cost when making the check symmetric

## Status
OPEN

## Tier
standard

## Type
investigation

## Priority
P2

## Request Summary
Measured by `test-architecture-reviewer` on 2026-10-06, as a by-product of the bisect in `TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK` (same method: `BenchHarness`, `PERF_2GB_LOCAL`, `build_movement_state(5000)` with the 2026-08-26 scenario builder, wall clock, single runs). `combat_engagement` (avg ms per tick):
- absent from the top phases at bisect index 85, `c84352465` (11.9 s per tick, of which cooperation is 10.9 s);
- 3,364 ms at index 102, `132bf09ca` (16.5 s per tick);
- 3,226 ms on `origin/main` `d135dd6be041b51711411bfb9fad516c58fb2bfc`.

The CI traceback (run 37403688489, `test_perf_movement[5000]` and `test_perf_passive_scaling[5000]`) stops in `CombatEngagementPhase._consider` → `semantics_service.is_hostile_compat` → `projection_service.project_relation` (`src/content_semantics/relation.py`). The commit that introduced the step is not isolated. Separately, `collection` grew from about 50 ms to about 260 ms around index 85 (also not isolated).

## Scope
- Bisect within `c84352465..132bf09ca` (first parent, the method above, threshold `combat_engagement` > 1,000 ms) and name the commit and the mechanism.
- Lane B is about to make `is_hostile_compat` symmetric in its legality batch. That change must not add per-pair cost; measure `combat_engagement` before and after it.
- Fix the cost step if it is cheap and behaviour-neutral. Otherwise record the mechanism and file the fix.

## Out of Scope
- The cooperation scan (`TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK`, Lane A).
- Changing hostility semantics beyond Lane B's planned symmetry change.

## Acceptance Criteria
- [ ] The introducing commit is named, with before and after values at movement[5000].
- [ ] The symmetry change's cost is measured, and `combat_engagement` does not grow from it.
- [ ] Any fix is behaviour-neutral: identical canonical hashes on the corpus under `audit_mode`.
- [ ] The `collection` growth (~50 → ~260 ms) is either attributed or explicitly left open in the ticket.

## Related Tickets
- TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX (rows 5–8)
- TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK

## Related Docs
- PR #381 comment 6018086519

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`_consider`), `src/content_semantics/faction.py` (`is_hostile_compat`), `src/content_semantics/relation.py` (`project_relation`)

## Assumptions / Open Questions
- Owner: Lane B (`rpg-implementer-2`), alongside its legality batch (routing by `rpg-feature-planning`, 2026-10-06).

## Implementation Notes
None yet.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
