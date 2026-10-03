---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX
artifact_type: plan
tags: [observability, combat, simulation-quality]
---

# plan.md — TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX

## Unresolved Questions

None — investigation.md's Bug 1/2/3 analysis is complete, with the final discriminant
(`attacker_id is not None`, not a plain `outcome_kind` allow-list) verified against every real
`hp_delta`-setting call site in `src/`. One deliberately-deferred question is disclosed, not left
ambiguous: whether `CombatKillEvent` should itself require `_real_combat_update` before firing
(currently unchanged — fires on any death, matching prior behavior) is flagged as a real, separate
design question in this ticket's Out of Scope and in the parity ledger entry's support_boundary,
not silently decided either way.

## Steps

1. Add `_NON_COMBAT_OUTCOME_KINDS` and `_real_combat_update(e_upd)` helper to
   `event_extractor.py`, implementing the `attacker_id`-primary / `outcome_kind`-defense-in-depth
   discriminant from investigation.md.
2. Fix the 4 `combat_upd` → `combat` attribute-name bugs (despawn-branch `has_attacker`,
   combat-damage, kill-events, combat-initiated), routing all 4 through the new helper.
3. Add the same helper guard to `near_death_survival`, which previously had no causal check at
   all.
4. Fix the 3 test-fixture bugs in `test_event_extractor_simq.py` that mocked the wrong attribute
   name (`combat_upd=` instead of `combat=`), which is why they never caught Bug 2.
5. Add new regression tests: hazard damage not misclassified (2 new tests), biological damage not
   misclassified (1 new test, directly targeting the Bug 3 finding), `attacker_id` correctly
   populated for real combat (1 new test), plus a dedicated real-state-diff hazard-vs-combat test
   in `test_event_extractor_world.py` (the existing hazard tests there use identical prior/curr
   state objects, so HP never actually changes — insufficient to exercise the interaction this fix
   is about).
6. Add a new P1 parity ledger entry (`INFRA-323`) documenting the fix, cross-referenced against
   `INFRA-273`'s existing (accurate, unaffected) claim about combat_damage/entity_killed's
   delta-gating mechanism.

## Scope guard

No change to `world_dynamics.py`'s already-correct `hazard_drain_applied` detection, or to
`combat.py`'s `outcome_kind` tagging (both already correct — this was purely a read-side bug).
`CombatKillEvent`'s own firing condition is explicitly left unchanged, per the Unresolved
Questions note above.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| `outcome_kind` filter added | Step 2-3, superseded by the more robust `attacker_id`-primary design (Bug 3 finding) |
| Unit tests cover hazard-vs-combat | Step 5 |
| Existing test suite passes | Verified: 759/759 non-skipped tests in `tests/unit/observability/` pass |
| Re-run sample scenarios | Deferred — this ticket's scope corrected mid-investigation to a source-level fix with full unit coverage; a corpus re-run is better suited to the migration epic's own validation ticket (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`), which already re-runs the full corpus and would silently mask this ticket's fix if done here too |
| `grade_anchors.json`/parity updated | Parity ledger updated (`INFRA-323`); `grade_anchors.json` not touched — this fix changes event *classification*, not scoring deltas, and COMBAT's real corpus-wide grade impact (if any) is exactly what the migration epic's validation ticket will measure properly against real calibration data |
