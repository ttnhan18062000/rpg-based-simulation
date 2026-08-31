---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
phase: done
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Title
Wire Structured Wound/Scar Data into Tactical Decision-Making

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Tactical Decision System already reacts to raw HP ratio, but it never reads the structured WoundState/ScarState data that already exists. The author wants the real structured data wired in.

## Scope
- Make TacticalDecisionSystem read entity.combat.wounds/.scars via the existing WoundService.get_wound_stat_penalties/get_scar_stat_penalties aggregator (not re-derived inline)
- An entity with an active WoundState of sufficient severity triggers cover-seeking/retreat behavior earlier/independently of the existing hp_percent checks (tactical.py:442-469), verified by a test with high hp_percent but a severe wound
- PROTECTOR-role 'guard wounded ally' selection (tactical.py:492-519) considers ally wound/scar severity as an additional signal, not just hp_ratio
- A scarred entity exhibits a durable behavior difference from an unwounded entity at the same hp_ratio
- Add a new parity_ledger entry or explicit extension note for the new wound/scar tactical branch, distinct from COMB-268's existing hp-ratio-only verified entry

## Out of Scope
- Duplicating the already-correct wound/scar stat-penalty pipeline (SkillScalingService.get_effective_stats -> apply.py) -- this ticket is scoped to decision-making (retreat/cover/guard) only
- Any change to the underlying WoundState/ScarState data model -- this ticket depends on, and must be re-validated against, whatever C2/C3/C4 land

## Acceptance Criteria
- [x] An entity with active WoundState of sufficient severity triggers cover-seeking/retreat behavior in TacticalDecisionSystem earlier/independently of existing hp_percent checks, verified by a test with high hp_percent but a severe wound
- [x] PROTECTOR-role 'guard wounded ally' selection considers ally wound/scar severity as an additional signal, not just hp_ratio
- [x] A scarred entity exhibits a durable behavior difference from an unwounded entity at the same hp_ratio
- [x] New reads reuse WoundService.get_wound_stat_penalties/get_scar_stat_penalties rather than re-deriving inline

## Related Tickets
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
- TCK-20260824-WOUND-HEALING-DECISION

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py
- src/core/state.py
- src/engine/rpg_depth.py
- src/engine/combat.py
- src/engine/apply.py

## Assumptions / Open Questions
- Explicit blocking dependency on TCK-20260824-WOUND-THRESHOLD-DECISION (C2), TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (C3), and TCK-20260824-WOUND-HEALING-DECISION (C4) landing first, since all three touch the same underlying WoundState/ScarState data model this ticket reads -- if those tickets change the data shape, this ticket's design must be re-validated

## Implementation Notes
Followed `staging_artifacts/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING/plan.md`'s 8 steps. All 4
threshold constants and the 3 distress-aggregation helpers (`_wound_distress`, `_scar_distress`,
`_combined_wound_scar_distress`) were added at module level in `src/engine/tactical.py`, each
wrapping `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` (never re-deriving
penalty math inline). Three read-only OR-widenings were wired in:
1. Cover-seeking/retreat gate (now `tactical.py:483-494`, was 442-443): added
   `wound_distress >= WOUND_DISTRESS_COVER_THRESHOLD` (9.0) as an OR-term, and replaced the
   literal `0.4` hp_percent threshold with `0.4 + scar_hp_bump` (capped +0.10, +0.01 per
   scar-distress point).
2. PROTECTOR guard-wounded-ally branch (now `tactical.py:542-582`, was 492-507): added
   `combined_wound_scar_distress >= PROTECTOR_GUARD_DISTRESS_THRESHOLD` (5.0) as an OR-term to
   both the leader-guard predicate and the "any other ally" predicate.
Both changes are additive-only: for zero-wound/zero-scar entities every new term evaluates to
`0.0`, reducing the conditions to their exact pre-change form (verified by regression tests below).

One deviation from plan.md, recorded in that file's own "Deviations" section: plan.md's Step 2
asserted that a lazy `from src.engine.rpg_depth import LeashService, WoundService` import inside
`evaluate_entity_intent` would bind `WoundService` into the *module* global namespace so the
module-level helper functions (`_wound_distress` etc.) could resolve it. That is incorrect --
Python function-local imports bind names into the function's local scope, not the module globals,
so the module-level helpers raised `NameError: name 'WoundService' is not defined` the first time
they were exercised. Fixed by adding a real module-level `from src.engine.rpg_depth import
WoundService` import at the top of `tactical.py` (confirmed safe: `rpg_depth.py` only imports
`src.core.state.TERRAIN_COST` at module level, no circular-import risk) and leaving the existing
lazy `LeashService` import at line 106 untouched, exactly as the plan's own Scope Guards required.

Docs (`docs/mechanics/02_combat_laws.md` Section 5) and the parity ledger (`COMB-315` in
`docs/parity_ledger/combat_movement.yaml`, purely additive -- confirmed via `git diff --stat`
showing 0 deletions) were updated per Steps 7-8.

## Test Summary
New file `tests/unit/combat/test_tactical_wound_scar_wiring.py` (5 tests, all passing):
- `test_severe_wound_triggers_cover_seeking_at_high_hp` (AC #1)
- `test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch` (negative control)
- `test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio` (AC #3)
- `test_protector_guards_wound_distressed_ally_over_healthier_ally` (AC #2)
- `test_wound_scar_tactical_reads_reuse_woundservice_aggregators` (AC #4, `patch.object(...,
  wraps=...)` spy on both aggregators)

Full scoped regression run (227 passed, 0 failed):
`pytest tests/unit/combat/ tests/unit/movement/ tests/unit/tactical/
tests/unit/social/test_domain_7_social.py tests/unit/core/test_rpg_depth.py
tests/unit/core/test_read_only_guard.py -v -m "not slow"` -- includes
`test_retreat_behavior` and `test_protector_guarding` (the untouched no-hostiles branch),
confirming zero-wound/zero-scar entities are unaffected.

Pre-existing, unrelated failure noted for the record (not caused by this ticket, not fixed here
per CLAUDE.md's baseline-drift triage rule): `tests/tools/test_parity_index_baseline.py::
test_baseline_manifest_does_not_coerce_missing_test_path` fails on the clean base commit
(`b18f0832`, verified via `git stash`) before any of this ticket's changes, expecting
`live_missing == 1332` but finding `1322` -- a hardcoded-baseline drift from other tickets'
concurrent work on this shared branch, unrelated to wound/scar tactical wiring.

## Files Changed
- `src/engine/tactical.py`
- `tests/unit/combat/test_tactical_wound_scar_wiring.py` (new)
- `docs/mechanics/02_combat_laws.md`
- `docs/parity_ledger/combat_movement.yaml`
- `tickets/inprogress/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING.md`
- `staging_artifacts/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING/plan.md` (Deviations section added)
- `docs/engine/contracts/tactical_contract.md` (Document-Update phase: new §8 "Wound/Scar Tactical Signals")
- `docs/guidelines/intentional_divergences.md` (Document-Update phase: DEV-005 update note confirming this ticket landed)

## Completion Summary
Wired `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` into
`TacticalDecisionSystem.evaluate_entity_intent` as three new, strictly read-only decision signals:
an independent wound-severity trigger and a scar-distress hp-threshold bump on the cover-seeking/
retreat gate, and a combined wound/scar-distress qualifier on the PROTECTOR guard-wounded-ally
branch. All three are additive OR-widenings that provably reduce to pre-existing behavior for
zero-wound/zero-scar entities (regression-tested). Added 5 new unit tests, a new Mechanics Bible
subsection, and parity ledger entry COMB-315 (distinct from COMB-268). No durable state, API
surface, or the WoundState/ScarState data model was touched -- this ticket is a pure new
*consumer* of the existing aggregator pipeline.
