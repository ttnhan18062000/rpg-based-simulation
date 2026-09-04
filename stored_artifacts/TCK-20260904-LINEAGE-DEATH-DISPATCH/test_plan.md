---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260904-LINEAGE-DEATH-DISPATCH
artifact_type: test_plan
tags: [lifecycle, social]
---

# Test Plan — TCK-20260904-LINEAGE-DEATH-DISPATCH

## Regression Surface (existing tests that must pass)

- `tests/unit/progression/test_lifecycle.py` (all 35 pre-existing tests) -- `resolve_lifecycle`'s
  death/heir/heirloom logic is directly modified.
- `tests/unit/entity/test_phase11_cognition_model_schema.py`, `tests/unit/domains/motivation/
  test_phase14_motivation_models.py` -- `MotivationModel`/`CognitionModel` schema changed.
- `tests/unit/strategic/` (full directory) -- `BlockerState`/`StrategicUpdate` consumed by the new
  handler.
- `tests/architecture/test_phase18_cognition_migration_linter.py` -- cognition-model shape linter.
- `tests/unit/engine/test_hash_scheduler.py` -- determinism/canonical-hash coverage.
- `tests/unit/domains/campaigns/test_grief_urgency.py`, `tests/unit/kernel/
  test_grief_trigger_drain.py`, `tests/integration/campaigns/test_mid_episode_grief_trigger.py` --
  `NemesisRelationImporter`/Campaign-mode nemesis-blocker plumbing this ticket reads from.

## New Tests Required (per AC)

1. AC1 (single dispatch call): `test_death_dispatch_fires_both_handlers_from_single_call_site`.
2. AC2 (weakened feud transfer): `test_inherited_nemesis_blocker_is_weakened_relative_to_original`,
   plus a no-op-when-absent case: `test_death_with_no_nemesis_blocker_produces_no_feud_transfer`.
3. AC3 (named intention, honorable/round-trip): `test_named_intention_is_honorable_ignorable_never_auto_executing`.
4. AC4 (same-tick collision safety): `test_dying_wish_does_not_clobber_earlier_same_tick_cognition_write`.
5. AC5 (no reputation-branch changes): `test_lineage_dispatch_introduces_no_reputation_branch_changes`
   (source-text guard).

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py \
       tests/unit/entity/test_phase11_cognition_model_schema.py \
       tests/unit/domains/motivation/test_phase14_motivation_models.py \
       tests/unit/strategic/ \
       tests/architecture/test_phase18_cognition_migration_linter.py \
       tests/unit/engine/test_hash_scheduler.py \
       tests/unit/domains/campaigns/test_grief_urgency.py \
       tests/unit/kernel/test_grief_trigger_drain.py \
       tests/integration/campaigns/test_mid_episode_grief_trigger.py \
       -q
```

## Anti-Drift Test Guards

- `test_lineage_dispatch_introduces_no_reputation_branch_changes` is a source-text guard
  (`inspect.getsource`) ensuring `lifecycle.py` never references `public_reputation`,
  `ReputationUpdateService`, or `PublicReputationProfile` -- keeps the death-and-lineage and
  reputation branches of the M5 epic independently landable regardless of implementation order.
- `test_inherited_nemesis_blocker_is_weakened_relative_to_original` asserts `inherited.id !=
  nemesis_blocker.id`, guarding against a future edit accidentally reusing the `nemesis_{antagonist}`
  id and silently overwriting a heir's own independent nemesis relation.
