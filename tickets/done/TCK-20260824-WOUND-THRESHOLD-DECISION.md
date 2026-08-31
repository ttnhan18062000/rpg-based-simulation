---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-THRESHOLD-DECISION
phase: done
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-THRESHOLD-DECISION

## Title
Resolve the Wound Threshold Discrepancy (25% Live vs 40% Dead Code)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The live wound-infliction threshold is 25%, but a 40% branch in WoundService.should_inflict_wound() is unreachable dead code, and two Mechanics Bible docs cross-reference the stale value. The author wants a decision made: delete the unreachable branch, or leave it and correct the docs.

## Scope
- Record a single documented decision: delete the unreachable 40% branch in WoundService.should_inflict_wound(), or keep it and correct the docs
- If delete: remove WoundService.should_inflict_wound(), WOUND_THRESHOLD_RATIO, and other zero-caller methods not made live by C3's wiring; remove/rewrite tests/unit/core/test_rpg_depth.py::TestWoundInfliction
- If keep: add an explicit dead/legacy annotation in code, add a docs/guidelines/intentional_divergences.md entry, and update COMB-290's v2_evidence
- Resolve the WOUND_THRESHOLD_RATIO identifier-name collision between docs/mechanics/01_entity_anatomy.md's pseudocode (0.25) and the dead code's 0.40 value so a grep no longer surfaces a contradiction
- Correct docs/parity_ledger/combat_movement.yaml COMB-290's test_path pointer (currently points to test_combat_matrix.py, which contains no wound-related test)

## Out of Scope
- The severity-scaled penalty formula wiring itself (owned by TCK-20260824-WOUND-PENALTY-FORMULA-WIRING)
- The wound-healing trigger decision (owned by TCK-20260824-WOUND-HEALING-DECISION)
- This ticket's final scope should exclude WoundService.create_wound() once C3 makes it live -- narrowing happens after C3 lands, not before

## Acceptance Criteria
- [x] A single documented delete-vs-keep decision is recorded with rationale
- [x] docs/mechanics/01_entity_anatomy.md, docs/mechanics/02_combat_laws.md, and COMB-290 stay internally consistent with the decision
- [x] If delete: should_inflict_wound()/WOUND_THRESHOLD_RATIO removed and TestWoundInfliction updated accordingly
- [x] If keep: code carries an explicit dead/legacy annotation and intentional_divergences.md gains an entry (N/A — delete path was chosen, not keep; see Implementation Notes)
- [x] COMB-290's v2_evidence and test_path are corrected to reflect ground truth regardless of which option is chosen

## Related Tickets
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
- TCK-20260824-WOUND-HEALING-DECISION

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/rpg_depth.py
- src/engine/combat.py
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Assumptions / Open Questions
- This ticket should be sequenced AFTER TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (C3) lands, since C3 wiring create_wound() into live combat narrows this ticket's dead-code scope to should_inflict_wound()/heal_wound() only
- The residual gap is an identifier-name collision in doc pseudocode, not a value error -- both Mechanics Bible docs already state the correct 25% figure
- Whether heal_wound() should be handled here or deferred entirely to TCK-20260824-WOUND-HEALING-DECISION (C4) needs confirming once C4's decision lands

## Implementation Notes

**Decision: DELETE.** `WoundService.should_inflict_wound()` and `WOUND_THRESHOLD_RATIO` (0.40) in
`src/engine/rpg_depth.py` were confirmed to have zero real (non-test) callers anywhere in `src/` —
the live wound-infliction gate is an independent inline literal at `src/engine/combat.py:607`
(`damage > defender.combat.max_hp * 0.25 and alive`), which calls `WoundService.create_wound()`
directly and never called `should_inflict_wound()`. This matches the evidentiary bar and precedent
already established the same day by the sibling ticket `TCK-20260824-WOUND-HEALING-DECISION`
(`heal_wound()`/`MedicalService` deletion, recorded as `DEV-005`) and, before that, `DEV-004`
(`AllocateAttributeAction`). Per that precedent, confirmed zero-caller dead code with an existing
sign-off ticket is deleted outright rather than kept and annotated dormant — so the "keep" path's
AC (dead/legacy annotation + `intentional_divergences.md` entry) does not apply here; it is marked
N/A above rather than left unresolved.

Work done, following `staging_artifacts/TCK-20260824-WOUND-THRESHOLD-DECISION/plan.md`'s six steps
exactly, in order:

1. Deleted `WOUND_THRESHOLD_RATIO = 0.40` and `WoundService.should_inflict_wound()` from
   `src/engine/rpg_depth.py:111-122`. Left `create_wound()`, `get_wound_stat_penalties()`,
   `get_scar_stat_penalties()` untouched — all three remain live (confirmed callers in
   `combat.py:611` and `rpg_depth.py`'s own `SkillScalingService.get_effective_stats()`).
2. Removed `WOUND_THRESHOLD_RATIO` from the import list in `tests/unit/core/test_rpg_depth.py`
   (would otherwise `ImportError` at collection). Removed only
   `TestWoundInfliction::test_wound_infliction_massive_hit` (and its preceding `# Logic ID:
   COMB-102` comment) — the other three methods on that class (`test_wound_stat_impact`,
   `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`) and `TestScarPermanence`
   are unchanged. Added a new negative-boundary test,
   `test_wound_infliction_below_live_threshold_produces_no_wound`, to
   `tests/unit/combat/test_direct_combat_outcomes.py`, patterned after the existing
   `test_wound_penalties_scale_with_severity_through_live_combat_path` — drives
   `CombatResolutionSystem.resolve_attack()` end-to-end and asserts `update.wound_update is None`
   when `damage_taken <= max_hp * 0.25`, replacing the coverage lost by the deletion with coverage
   of the live gate's negative boundary (which had no prior direct test).
3. Renamed the pseudocode identifier in `docs/mechanics/01_entity_anatomy.md`'s Section 6 fenced
   block from `WOUND_THRESHOLD_RATIO` to `WOUND_INFLICTION_RATIO` (both occurrences) — the 25%
   value and strict-`>` semantics are unchanged. This removes the last remaining reference to the
   now-deleted Python symbol's name anywhere in the repo, so a future grep for
   `WOUND_THRESHOLD_RATIO` returns nothing.
4. Repointed `COMB-290` (P1) in `docs/parity_ledger/combat_movement.yaml` via
   `tools.parity_ledger_writer.write_entry()` — `test_path` corrected from the wound-unrelated
   `tests/unit/combat/test_combat_matrix.py` to
   `tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`;
   `v2_evidence`'s stale `_get_wound_infliction() line 583` corrected to `lines 604-618`. Every
   other field preserved verbatim from the existing entry. Followed by a separate, visible
   `python3 tools/parity_index.py build` Bash call.
5. Repointed `COMB-102` (P0) the same way — its `test_path` pointed to the now-deleted
   `test_wound_infliction_massive_hit`, which would have left a P0 entry dangling as a mechanical
   consequence of Step 2. Repointed to the same live-path test used for COMB-290. `v2_evidence` was
   correctly describing the live `create_wound()` delegation already and needed no change — an
   intermediate write mistakenly added an extra sentence to it, caught immediately and corrected
   with a follow-up `write_entry()` call restoring the exact original `v2_evidence` string (see
   `plan.md`'s new Deviations section for the full trace). Ran sequentially after Step 4, never
   concurrently, per the plan's shard-write-safety note. Each `write_entry()` call (three total,
   including the one correction) was followed by its own visible `python3 tools/parity_index.py
   build` Bash call.
6. Confirmed `docs/mechanics/02_combat_laws.md:70-92` needs no change — no
   `WOUND_THRESHOLD_RATIO` string present, `0.25` value and strict-`>` semantics already correct,
   already cites `combat.py:605-617`. No edit made; verified read-only per the plan.

No other zero-caller `WoundService` methods existed to evaluate — `create_wound()`,
`get_wound_stat_penalties()`, `get_scar_stat_penalties()` are all live, and `heal_wound()`/
`MedicalService` no longer exist (already deleted by the completed sibling
`TCK-20260824-WOUND-HEALING-DECISION`).

`graphify update .` was run after the `src/`/`tests/` edits; it reported no code-graph topology
changes (deleting an unreferenced method/constant does not change the AST-derived graph shape).

## Test Summary

`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
tests/unit/core/test_rpg_depth.py tests/unit/combat/test_direct_combat_outcomes.py
tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_scan.py
tests/tools/test_validate_frontmatter.py -q -m "not slow"` — **153 passed, 0 failed.** Includes:
- All 65 tests in `test_rpg_depth.py` + `test_direct_combat_outcomes.py` (the new
  `test_wound_infliction_below_live_threshold_produces_no_wound` passes; both pre-existing sibling
  tests `test_wound_penalties_scale_with_severity_through_live_combat_path` and
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` pass unmodified).
- `pytest --collect-only tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
  — collects cleanly (proves both COMB-290 and COMB-102's new `test_path` resolves to a real test).
- `tests/tools/test_parity_ledger_schema.py` + `tests/tools/test_parity_ledger_scan.py` (5 tests) —
  pass, confirming the ledger writes are schema-valid.
- `tests/tools/test_validate_frontmatter.py` (83 tests) — pass, confirming
  `01_entity_anatomy.md`'s untouched frontmatter and this ticket/its artifacts remain valid.

## Files Changed
- `src/engine/rpg_depth.py` — deleted `WOUND_THRESHOLD_RATIO` and `WoundService.should_inflict_wound()`
- `tests/unit/core/test_rpg_depth.py` — removed `WOUND_THRESHOLD_RATIO` import and `test_wound_infliction_massive_hit`
- `tests/unit/combat/test_direct_combat_outcomes.py` — added `test_wound_infliction_below_live_threshold_produces_no_wound`
- `docs/mechanics/01_entity_anatomy.md` — renamed pseudocode identifier `WOUND_THRESHOLD_RATIO` → `WOUND_INFLICTION_RATIO`
- `docs/parity_ledger/combat_movement.yaml` — repointed COMB-290 and COMB-102 `test_path`/`v2_evidence` via `tools/parity_ledger_writer.write_entry()`
- `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md` — Idea 15 marked Resolved, citing this ticket's delete decision and outcome
- `staging_artifacts/TCK-20260824-WOUND-THRESHOLD-DECISION/investigation.md` — created this run's Investigate phase
- `staging_artifacts/TCK-20260824-WOUND-THRESHOLD-DECISION/plan.md` — created this run's Plan phase; Deviations section added during Implement
- `staging_artifacts/TCK-20260824-WOUND-THRESHOLD-DECISION/test_plan.md` — created this run's Investigate/Plan phase
- `tickets/inprogress/TCK-20260824-WOUND-THRESHOLD-DECISION.md` — this file (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

`docs/mechanics/02_combat_laws.md` was read and verified but not modified (Step 6, no-op per plan).

## Completion Summary
Deleted the confirmed zero-caller dead 40% wound-threshold branch (`WoundService.should_inflict_wound()`
/ `WOUND_THRESHOLD_RATIO`) from `src/engine/rpg_depth.py`, following the same-day precedent set by
`DEV-004`/`DEV-005`. Updated `tests/unit/core/test_rpg_depth.py` to match and added a new
negative-boundary test in `tests/unit/combat/test_direct_combat_outcomes.py` driving the live 25%
gate end-to-end. Renamed the now-unambiguous pseudocode identifier in
`docs/mechanics/01_entity_anatomy.md` to `WOUND_INFLICTION_RATIO`, confirmed `02_combat_laws.md`
needed no change, and repointed both `COMB-290` (P1) and `COMB-102` (P0, mechanically dangling as a
side effect of the test deletion) in `docs/parity_ledger/combat_movement.yaml` to the real, passing
`test_wound_penalties_scale_with_severity_through_live_combat_path`, using the sanctioned
`tools/parity_ledger_writer.write_entry()` path exclusively. The live 25% wound-infliction gate in
`src/engine/combat.py:607` was never touched — zero live behavior changed. 153 scoped tests pass.
