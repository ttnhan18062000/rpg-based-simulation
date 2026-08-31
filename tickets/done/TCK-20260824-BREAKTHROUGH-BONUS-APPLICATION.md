---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
phase: done
date: 2026-08-24
tags: [progression]
---

# TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION

## Title
Finish BreakthroughService.apply_bonuses()

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
BreakthroughService.apply_bonuses() is a literal pass stub even though three real breakthroughs with real attribute bonuses already sit in the registry, earned but never applied. The author wants this stub actually finished so the bonuses take effect.

## Scope
- Implement BreakthroughService.apply_bonuses() so apply_bonuses({'iron_will'}, base_attributes) returns spirit+2/wisdom+2 matching the REGISTRY, correctly summing bonuses when multiple breakthrough_ids are passed
- Ensure empty/unknown breakthrough ids return unchanged attributes with no raise
- Wire active_breakthroughs into the effective-stats recompute path (apply.py -> rpg_depth.py -> leveling.py's SkillScalingService.get_effective_stats) so an entity with populated active_breakthroughs shows the bonus in recomputed combat stats, not just isolated calls
- Decide a concrete typed signature for apply_bonuses (bonus-delta dict vs new AttributeComponent), following leveling.py:143-149's existing trait pattern
- Decide whether fleet_foot's non-attribute evasion_flat bonus type is in scope for this pass
- Correct docs/parity_ledger/progression.yaml PROG-024 (currently claims verified/P0 with test_path=null despite the pass-stub) and add a docs/mechanics/ chapter section documenting breakthroughs

## Out of Scope
- Building a system that actually grants breakthroughs to entities in gameplay -- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION already found breakthroughs_add is constructed nowhere in production code; that is a separate, larger gap

## Acceptance Criteria
- [x] apply_bonuses({'iron_will'}, base_attributes) returns spirit+2/wisdom+2 matching REGISTRY
- [x] apply_bonuses correctly sums bonuses when multiple breakthrough_ids are passed
- [x] Empty/unknown id returns attributes unchanged with no raise
- [x] After wiring active_breakthroughs into the effective-stats recompute path, an entity with populated active_breakthroughs shows the bonus in recomputed combat stats

## Related Tickets
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION

## Related Docs
- docs/parity_ledger/progression.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/breakthroughs.py
- src/engine/apply.py
- src/engine/rpg_depth.py
- src/progression/leveling.py
- src/core/state.py
- src/engine/patches.py
- src/core/updates.py

## Assumptions / Open Questions
- apply_bonuses' signature (bonus-delta dict vs new AttributeComponent) is an open decision this ticket must make concrete
- Whether fleet_foot's non-attribute evasion_flat bonus is in scope is an open decision
- layer registered as `core` — no `progression` layer exists in registries/layer_registry.jsonl; `core` was chosen because the scope centers on entity attribute/state primitives (src/core/state.py, src/core/updates.py) rather than a dedicated progression layer

## Implementation Notes

Implemented per plan.md's 6 steps, no deviations:

1. `BreakthroughService.apply_bonuses` (`src/progression/breakthroughs.py`) implemented as a pure
   function: sums each known breakthrough's `attribute_bonuses` from `REGISTRY` into a delta dict,
   ignores unknown ids and `fleet_foot`'s sibling `evasion_flat` key (never entered since the loop
   only reads `attribute_bonuses`), and returns a new `AttributeComponent` via `dataclasses.replace`.
   Returns the input unchanged (same object) for empty/all-unknown ids — no raise. Added
   `import dataclasses` and `from src.core.state import AttributeComponent`; updated the signature's
   type hints from `Any -> Any` to `AttributeComponent -> AttributeComponent`.
2. `SkillScalingService.get_effective_stats` (`src/engine/rpg_depth.py`) gained
   `active_breakthroughs: Optional[Set[str]] = None`. Before calling
   `LevelingService.recalculate_combat_stats`, it now computes
   `effective_attributes = BreakthroughService.apply_bonuses(active_breakthroughs or set(), attributes)`
   and passes `effective_attributes` (not raw `attributes`) as the first positional argument.
   `recalculate_combat_stats`'s formulas are untouched. Added `Set` to the file's `typing` import
   (was missing).
3. `ApplyPath._apply_entity_update_to_dict` (`src/engine/apply.py`): added
   `update.identity.breakthroughs_add` as a disjunct in the `stats_dirty` OR-condition (cheap
   truthiness check, same style as the adjacent `learned_skills`/`traits_add`/`traits_remove`
   checks), and added `active_breakthroughs=new_id.active_breakthroughs` to the
   `get_effective_stats` call. `new_id` is post-patch state (patches already applied earlier in the
   same function), so this reflects the current tick's `breakthroughs_add` immediately.
4. Wrote all 9 new tests exactly as specified in test_plan.md: 5 in
   `tests/unit/progression/test_breakthroughs.py` (pure `apply_bonuses` unit tests), 2 in
   `tests/unit/core/test_rpg_depth.py::TestEffectiveStats` (`get_effective_stats` wiring +
   backward-compat guard), 2 in new class `tests/unit/core/test_rpg_depth.py::TestBreakthroughApplyIntegration`
   (full apply-path integration, including the `stats_dirty`-gap regression guard). Used
   `titan_grip` for every assertion that must show up in recomputed combat stats, per the plan's
   Anti-Drift Note (`recalculate_combat_stats` never reads spirit/wisdom). Did not modify
   `test_breakthrough_addition`/`test_duplicate_breakthrough_suppression`.
5. Corrected `docs/parity_ledger/progression.yaml` PROG-024: `test_path` now points to
   `tests/unit/progression/test_breakthroughs.py::test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two`;
   `v2_evidence` replaced with a concrete string citing the real implementation and test file.
   `status` left as `verified` (now backed by a real passing test). PROG-023/PROG-003 untouched.
6. Added `### Breakthroughs (Passive Perks)` subsection to `docs/mechanics/01_entity_anatomy.md`
   Section 5, immediately after `### Level Up Rewards` and before the `---` separator. Lists all
   three `REGISTRY` entries with their `attribute_bonuses`, flags `fleet_foot`'s `evasion_flat` as a
   distinct, not-yet-wired bonus type, and states the application rule. `WOUND_THRESHOLD_RATIO`
   divergence, Section 2, and Section 6 left untouched.

`graphify update .` run after src/tests changes — no topology changes detected.

Document-Update phase (run after Implement) additionally swept docs/ for other now-stale
references to `apply_bonuses` being a placeholder, beyond the two docs flagged by
investigation.md. Found and corrected three more: `docs/mechanics/attribute_progression_contract.md`
(rewrote its "breakthrough placeholder" section to reflect the real implementation, added a "Known
gap" callout for `fleet_foot`'s unwired `evasion_flat`), `docs/simulation/domains/progression_contract.md`
(two table rows describing `breakthroughs.py` as "not yet implemented" corrected), and
`docs/mechanics/README.md` (index blurb "breakthrough placeholder status" corrected to "breakthrough
bonus application"). These are added to Files Changed below for traceability.

## Test Summary

Ran the three scoped pytest commands from test_plan.md's "Scoped Pytest Commands" section using
the project venv (`.venv/bin/python3 -m pytest ...`, since bare `python3` lacks `pydantic` in this
sandbox):
- `pytest tests/unit/progression/test_breakthroughs.py tests/unit/progression/test_leveling.py -v`
  — 9 passed (7 in test_breakthroughs.py including the 5 new tests + 2 unmodified existing tests;
  2 in test_leveling.py, unmodified, confirming no formula drift).
- `pytest tests/unit/core/test_rpg_depth.py -v` — 58 passed (56 pre-existing + 2 new
  `TestEffectiveStats` tests + confirms `TestBreakthroughApplyIntegration`'s 2 new tests import
  correctly — full file total after also adding the integration class is captured in the next run).
- `pytest tests/unit/progression/ -v` — 56 passed (full progression regression surface, including
  `test_progression_v2.py::test_recalculate_combat_stats_consistency`, confirms
  `recalculate_combat_stats` bit-identical for entities with no active breakthroughs).
All existing tests in the regression surface named by test_plan.md passed unmodified. No full
suite run (out of scope for Implement phase per instructions; Test phase runs separately).

Test phase (run after Implement) re-scoped the pytest command to use the literal
`tests/unit/progression/` directory path (rather than enumerating individual files within it), per
the structural test-scope-coverage backstop check — `src/progression/breakthroughs.py` maps to that
whole directory, and a file-enumerated command would silently miss any future test file added there.
Final command: `.venv/bin/python3 -m pytest tests/unit/progression/ tests/unit/core/test_rpg_depth.py
tests/unit/core/test_domain_6_hardening.py tests/unit/core/test_rpg_math.py -v` — 122 passed, 0 failed.

## Files Changed
- src/progression/breakthroughs.py
- src/engine/rpg_depth.py
- src/engine/apply.py
- tests/unit/progression/test_breakthroughs.py
- tests/unit/core/test_rpg_depth.py
- docs/parity_ledger/progression.yaml
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/attribute_progression_contract.md
- docs/simulation/domains/progression_contract.md
- docs/mechanics/README.md
- tickets/inprogress/TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION.md

## Completion Summary

Implemented `BreakthroughService.apply_bonuses` as a pure function that sums registered
breakthroughs' `attribute_bonuses` onto a base `AttributeComponent` via `dataclasses.replace`, and
wired it into the effective-stats recompute chain (`get_effective_stats` -> `apply.py`'s
`_apply_entity_update_to_dict`, including fixing the `stats_dirty` gap so a `breakthroughs_add`-only
update alone triggers recomputation). Added all 9 tests from test_plan.md, all passing; corrected
the false `test_path`/`v2_evidence` on parity ledger entry PROG-024; and documented the three
`REGISTRY` breakthroughs and the application rule in `docs/mechanics/01_entity_anatomy.md` Section
5. All four acceptance criteria are satisfied. This is new logic (previously a `pass` stub), so
observable behavior changes for any entity with populated `active_breakthroughs`.
