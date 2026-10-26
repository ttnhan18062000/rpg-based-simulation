---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP
phase: inprogress
date: 2026-10-06
tags: [performance, combat, regression, investigation]
---

# TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP

## Title
`combat_engagement` grew by about 3.3 s per tick at movement[5000] somewhere between `c84352465` and `132bf09ca` (`is_hostile_compat` → `project_relation`); isolate the commit, and do not add cost when making the check symmetric

## Status
INPROGRESS

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
- combat_engagement is strongly box-dependent on identical code: ~16 s per tick on Lane A's box (all arms, ±1.3 s) vs ~3.2 s on the reviewer's, while cooperation matched (10.2 vs 10.8 s) — rpg-implementer, 2026-10-07. Measure before and after on one box with a pinned method; suspect memory/cache behaviour in the projection.
- Owner: Lane B (`rpg-implementer-2`), alongside its legality batch (routing by `rpg-feature-planning`, 2026-10-06).

## Implementation Notes
Owner Lane B (`rpg-implementer-2`), branch `rpg-hostility-projection-cost`. Plan approved by `rpg-planner` 2026-10-26.
- Mechanism (read from code): each `is_hostile_compat` call built a new `RelationProjectionService` and scanned `perspectives` twice and `faction_relationships` once, and `project_relation` scanned them again (and `species_relations` when a species context is given). `_consider` calls it per pair per tick.
- Fix (code done, timing pending the host): `RelationLookup` (first-match indexes, `setdefault`, rebuilt when a table object or size changes) on one reused `RelationProjectionService` per `FactionSemanticsService`. No label cache (the label depends on context). No semantics change.
- The symmetry change is already on main (#395, 7aa6f997b), so it is measured as part of origin/main, not as a separate arm; the bisect notes whether #395 itself added per-pair cost.
- Equivalence test: `tests/unit/content_semantics/test_relation_lookup_matches_scan.py` (all faction pairs, perspectives incl. missing ids, species, duplicate keys, growth, shared-vs-fresh service labels).
- Pending the host ("host free"): bisect timing `c84352465..132bf09ca` (+ #395 parent vs #395), before/after `combat_engagement` ms on one box, 3-world hash equal, `--neutral` IDENTICAL.

### Evidence from TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION (2026-10-15)
**Confirmed with call-site evidence.** `is_hostile_compat` (`faction.py:206/207/226`) and `project_relation` (`relation.py:75/76/190`) are 29 to 62 % of the tick in synthetic profiles (36 % at `idle_100`, 59 % at `movement_1000`; self-time of the two about 43 % at `movement_500`). `combat_engagement` at `movement`: 55 ms (100 entities), 989 ms (500), 3632 ms (1000), 7279 ms (2000): exponent about 1.8 to 1.9 up to 1000 entities. With full trees (`src config content registries data`) it is **absent at `c84352465`** and **2.2 s at `132bf09ca`** (1000 entities, live contract, loaded host), 2.2 s at `d135dd6be`, 3.5 s at `dc9b63c99`, 2.5 s now: introduced between `c84352465` and `132bf09ca`, no second jump since. The 5000-entity 3.2 s of this ticket is not reproducible on this host (the ticket records 3.2 s versus 16 s on another box for the same code); a pinned 5000-entity tick is estimated at 25 to 100 s. The fix stays with rpg Lane B; hand-off item 2 in `docs/performance/tick_cost_growth.md` section 7.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
