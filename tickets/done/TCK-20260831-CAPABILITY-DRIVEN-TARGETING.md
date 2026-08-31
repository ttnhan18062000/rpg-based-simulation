---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-CAPABILITY-DRIVEN-TARGETING
phase: done
date: 2026-08-31
tags: [cognition, combat]
---

# TCK-20260831-CAPABILITY-DRIVEN-TARGETING

## Title
Let subjective capability estimates drive tactical target selection

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Let subjective capability drive tactical target selection instead of pure group-bias/HP/distance/trust scoring. TacticalDecisionSystem.target_score() has zero CapabilityEstimateService reads today, even though CapabilityContext.for_combat() already exists shaped exactly for this consumer, and a directly-reusable precedent (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) already established the accepted ad-hoc call-site-local pattern for working around the still-unpopulated upstream prerequisite.

## Scope
- Wire CapabilityContext.for_combat(enemy_ids, enemy_data) into TacticalDecisionSystem.target_score() (src/engine/tactical.py:394-426) so scoring reflects CapabilityEstimateService.estimate(...).combat.enemy_type for hostiles mapped into combat_enemies.
- Reuse the ad-hoc call-site-local CapabilityContext construction pattern from TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING (accepted per docs/mechanics/04_strategic_cognition.md §6.12, STRAT-227) rather than fixing the upstream SelfModelUpdatePhase prerequisite gap.
- Explicitly disclose that capability_context is still never populated in production (src/cognition/self_model_phase.py) as a known/accepted limitation, resolved locally per the precedent.
- Keep target_score() strictly read-only — no write-back into entity.self_model.

## Out of Scope
- Fixing SelfModelUpdatePhase's capability_context production-population gap upstream — out of scope, same as the precedent ticket.
- Any change to COMB-254's post-sort legality filter behavior.

## Acceptance Criteria
- [x] For a hostile mapped into CapabilityContext.combat_enemies, target_score()'s priority reflects a real CapabilityEstimateService.estimate(...).combat.enemy_type value instead of purely HP/distance/trust.
- [x] The capability_context-never-populated prerequisite is explicitly disclosed and resolved via an ad-hoc call-site-local CapabilityContext inside tactical.py, mirroring the precedent ticket.
- [x] target_score() stays read-only — no write-back into entity.self_model, existing CapabilityEstimateService unit tests pass unchanged.
- [x] COMB-254's post-sort legality filter still runs unchanged after the re-scored sort.

## Related Tickets
- TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py
- src/cognition/capability_estimate.py
- src/cognition/self_model_phase.py

## Assumptions / Open Questions
- The capability_context-never-populated-in-production prerequisite gap persists and is intentionally worked around here, not fixed upstream — matches the precedent ticket's accepted pattern.
- Existing CapabilityEstimateService unit tests must continue to pass unchanged.

## Implementation Notes
Implemented exactly per staging_artifacts/TCK-20260831-CAPABILITY-DRIVEN-TARGETING/plan.md, no
deviations.

- `src/engine/tactical.py`: imported `CapabilityEstimateService`, `CapabilityContext` from
  `src.cognition.capability_estimate`. Inside `TacticalDecisionSystem.target_score()` (closure of
  `evaluate_entity_intent()`), added an ad-hoc, read-only call
  `CapabilityEstimateService.estimate(entity, context=CapabilityContext.for_combat(enemy_ids=[h.kind]))`
  per candidate hostile `h`, reading `.estimates.get(f"combat.enemy_type.{h.kind}")` (`None`-guarded
  to `0.0`). The sort tuple gained a new field `-capability_confidence` (negated so a higher
  subjective win-estimate sorts as higher priority), inserted between `is_current_target` and
  `h.combat.hp` — after group focus-fire bias and target-selection hysteresis, but ahead of raw
  HP/distance. `target_score()`'s type annotation updated from `Tuple[float, int, float, int, int]`
  to `Tuple[float, int, float, float, float, int]`. No other line in `target_score()` or
  `evaluate_entity_intent()` changed; `select_best_target()` and the post-sort COMB-254 legality
  filter (`tactical.py:433-443`, now `445-455`) are untouched.
- `tests/unit/combat/test_capability_driven_targeting.py` (new): 7 tests covering AC1
  (differentiated-kind ordering), regression-confirming uniform-kind no-op, entity-owned-stats
  derivation (a zero-stat attacker's capability term ties, letting HP/distance decide; a real-stat
  attacker's capability term dominates and flips the choice), no self-model mutation, COMB-254
  legality-filter-still-runs (capability-preferred candidate placed out of range, a less-preferred
  one adjacent — the legal one is still chosen), hostile-kind/entity-owned-fields-only read (varying
  an unrelated hostile stat has no effect), and determinism. All 7 pass.
- `docs/parity_ledger/combat_movement.yaml`: added `COMB-316` via `tools/parity_ledger_writer.py`'s
  `write_entry()` (sanctioned schema-validating writer, single-entry append, index rebuilt
  in-process) — `status: verified`, `priority: P2`, `test_path` points at the new test file.
- Docs updated per Step 6: `docs/engine/contracts/tactical_contract.md` §2 (full current priority
  chain, previously stale even before this ticket), `docs/guidelines/intentional_divergences.md`
  §2.6 (capability-driven addition, rationale class Intentional Gameplay Change, Verification
  pointer fixed to the new real test file), `docs/cognition/capability_and_knowledge_contract.md`
  (new "How tactical targeting uses capability estimates" section + regression-tests list entry),
  `docs/cognition/README.md` (new row in "Relationship to other subsystems" for
  `src/engine/tactical.py`).
- `entity.self_model.capabilities.estimates` remains empty in production after this ticket —
  `SelfModelUpdatePhase.apply()` still never passes `capability_context=`. This is disclosed
  explicitly in every doc updated above and verified by `tests/unit/cognition/test_phase2_self_model_phase.py`
  (untouched, still passing) and by the new test's own
  `test_target_score_does_not_mutate_entity_self_model`.
- Verification: full regression surface from test_plan.md (combat/tactical/movement,
  cognition/capability-estimate + self-model-phase, social + read-only-guard, integration) all
  green; `git diff --stat` on `src/cognition/capability_estimate.py` and
  `tests/unit/cognition/test_phase2_capability_estimate_service.py` shows zero changes (AC3's
  byte-unchanged requirement). `make knowledge-index-update` run after doc edits.

## Test Summary
- New: `tests/unit/combat/test_capability_driven_targeting.py` — 7/7 passed.
- Regression (all green, no changes):
  - `pytest tests/unit/combat/ tests/unit/tactical/ tests/unit/movement/test_tactical_movement.py tests/unit/movement/test_mob_leashing.py` — 128 passed.
  - `pytest tests/unit/cognition/test_phase2_capability_estimate_service.py tests/unit/cognition/test_phase2_self_model_phase.py` — 20 passed.
  - `pytest tests/unit/social/test_domain_7_social.py tests/unit/core/test_read_only_guard.py` — 7 passed.
  - `pytest tests/integration/combat/test_relation_combat_integration.py tests/integration/strategic/test_occupation_change_reachability.py tests/integration/scenarios/test_phase2_self_model_scenarios.py` — 41 passed.
- `git diff --stat src/cognition/capability_estimate.py tests/unit/cognition/test_phase2_capability_estimate_service.py` — empty (byte-unchanged, confirmed).

## Files Changed
- `src/engine/tactical.py`
- `tests/unit/combat/test_capability_driven_targeting.py` (new)
- `docs/parity_ledger/combat_movement.yaml` (COMB-316 appended)
- `docs/engine/contracts/tactical_contract.md`
- `docs/guidelines/intentional_divergences.md`
- `docs/cognition/capability_and_knowledge_contract.md`
- `docs/cognition/README.md`
- `tickets/inprogress/TCK-20260831-CAPABILITY-DRIVEN-TARGETING.md` (this file)

## Completion Summary
Wired an ad-hoc, read-only `CapabilityEstimateService.estimate()` call into
`TacticalDecisionSystem.target_score()` (`src/engine/tactical.py`), so tactical target-selection
sorting now factors in the acting entity's own subjective combat-capability estimate against each
hostile's `kind` — placed ahead of raw HP/distance but behind group focus-fire bias and target
hysteresis, and negated so a higher perceived win-chance raises priority. This mirrors the accepted
ad-hoc-call-site pattern from `TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING` rather than
fixing the still-unpopulated `SelfModelUpdatePhase` prerequisite (out of scope, explicitly disclosed
in all updated docs). The call stays strictly read-only — no write-back to `entity.self_model` — and
the COMB-254 post-sort legality filter runs unchanged. 7 new tests added
(`tests/unit/combat/test_capability_driven_targeting.py`), full regression surface (196 tests across
combat/tactical/movement, cognition, social, and integration suites) passes unchanged, and
`src/cognition/capability_estimate.py` plus its existing unit test file are confirmed byte-identical
to their pre-ticket state. A new parity ledger entry (`COMB-316`) and four doc updates round out the
change.
