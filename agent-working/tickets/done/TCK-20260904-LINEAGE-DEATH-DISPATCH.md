---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260904-LINEAGE-DEATH-DISPATCH
phase: done
date: 2026-09-04
tags: [lifecycle, social]
---

# TCK-20260904-LINEAGE-DEATH-DISPATCH

## Title
Ideas 55+58 — On-Death Lineage Dispatch (Inherited Feud + Dying Wish)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design ideas 55 (Feuds Outlive the Feuders) and 58 (A Dying Wish) from `docs/brainstorm/rpg_feature_atlas.html` both fire at the identical trigger moment — death, once `heir_entity_id` resolves — so the M5 epic doc (`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`) scopes them as one ticket: one on-death dispatch hook, two thin handlers. Investigation (2026-09-04) confirmed the dispatch point is real and cheap: `LifecycleSystem.resolve_lifecycle` (`src/systems/lifecycle_systems/lifecycle.py`, PP-33 in the pipeline) already resolves `heir_entity_id` deterministically before its heirloom-transfer block, after TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX and TCK-20260824-DEFAULT-HEIR-ASSIGNMENT both landed — a single new call site inserted right after heir resolution is architecturally sufficient, no new phase needed. Idea 55's transfer target is a real but Campaign-mode-only signal (`entity.strategic.blockers['nemesis_*']`, populated via `NemesisRelationImporter` at episode start from `CampaignState.nemesis_relations`), distinct from the always-live legacy `SocialComponent.nemesis_ids`/`grudge_history` mechanism. Idea 58 needs genuinely new typed state: no `MotivationUpdate`/`CognitionUpdate` class exists today, only an opaque whole-object-replace `EntityUpdate.cognition_bundle_set` field (applied by `CognitionPatch.apply()`/`merge()` as last-write-wins, not a field merge) — a real same-tick-collision risk this ticket must handle.

## Scope
- Add a single dispatch call inside `LifecycleSystem.resolve_lifecycle`'s existing death-handling block (`src/systems/lifecycle_systems/lifecycle.py`), placed right after `heir_entity_id` resolution and before the existing heirloom-transfer block, that invokes two thin handler functions when `heir_entity_id` is non-null.
- Idea 55 handler: when the dying entity has an active Campaign-mode Nemesis blocker (`entity.strategic.blockers['nemesis_*']`, from `NemesisRelationImporter`/`CampaignState.nemesis_relations`), transfer a weakened-severity version of that hostility to the heir via a typed `StrategicUpdate`, reusing the authoritative-Kernel-injection pattern established by TCK-20260824-GRIEF-NEMESIS-REACHABILITY. Explicitly scoped to the Campaign-mode blocker representation, not the always-live legacy `SocialComponent.nemesis_ids`/`grudge_history` mechanism — document this scope decision explicitly in Implementation Notes so it isn't mistaken for an oversight.
- Idea 58 handler: seed one specific, named, source-attributed intention ("avenge me", "protect your sibling") onto the heir's cognition at the moment `heir_entity_id` resolves — honorable, ignorable, or rejectable by the heir, never auto-executing. Requires a new typed model (e.g. `NamedIntention` or `DyingWish` — must NOT reuse the name "Intention", which already names a distinct self-generated multi-step-planning model on `StrategicComponent` per TCK-20260812-COMMITTED-INTENTION-SEQUENCE) with a defined lifecycle, a stable location on cognition state, and either a new granular typed sub-update wired into `CognitionPatch`, or explicit, tested handling of `cognition_bundle_set`'s whole-object-replace semantics so this write cannot silently clobber or be clobbered by another same-tick `cognition_bundle_set` writer on the same heir.
- Add Mechanics Bible / parity ledger coverage: idea 55 in `docs/parity_ledger/combat_movement.yaml` and `docs/parity_ledger/social_narrative.yaml`; idea 58 in `docs/parity_ledger/strategic_cognition.yaml` and `docs/mechanics/04_strategic_cognition.md` (no existing chapter or ledger entry covers death-triggered hostility transfer or intention-seeding today).

## Out of Scope
- Any change to the always-live legacy `SocialComponent.nemesis_ids`/`grudge_history` mechanism itself — tracked separately by TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS.
- Extending idea 55's trigger beyond Campaign-mode Nemesis data to the default single-episode Kernel path — accepted as a real, disclosed scope limit for this ticket, not solved here.
- Any change to the existing `StrategicComponent` "Intention" multi-step-planning model.
- Idea 60/53/54 (the reputation branch) — tracked as separate sibling child tickets of the same epic.

## Acceptance Criteria
- A death that resolves `heir_entity_id` triggers exactly one dispatch call inside `resolve_lifecycle`'s death block, verified by a test asserting both handlers are invoked from a single call site rather than two separately-hooked triggers.
- When the dying entity has an active Campaign-mode Nemesis blocker, the heir receives a weakened-severity version of that blocker via a typed `StrategicUpdate` applied through the authoritative pipeline, verified by a test comparing pre/post severity between the deceased's original blocker and the heir's inherited one.
- A named intention (new typed model, source-attributed to the deceased) is written onto the heir's cognition through the authoritative apply path, is honorable/ignorable/rejectable rather than auto-executing, and round-trip serializes correctly, verified by a dedicated test.
- A same-tick collision between this ticket's cognition write and any other existing `cognition_bundle_set` writer on the same heir does not silently clobber either write, verified by a collision test.
- This ticket introduces zero changes to `SocialComponent.public_reputation` or any other reputation-branch field — verified by a source-text guard test, to keep the death-and-lineage and reputation branches independently landable.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
- TCK-20260824-GRIEF-NEMESIS-REACHABILITY
- TCK-20260812-COMMITTED-INTENTION-SEQUENCE
- TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
- TCK-20260628-E43F-GRIEF-URGENCY
- TCK-20260628-E43G-NEMESIS-RELATION

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/parity_ledger/combat_movement.yaml
- docs/parity_ledger/social_narrative.yaml
- docs/parity_ledger/strategic_cognition.yaml
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/engine/pipeline.py
- src/domains/campaigns/grief_urgency.py
- src/domains/campaigns/state.py
- src/core/models/social.py
- src/core/cognition.py
- src/core/updates.py
- src/engine/patches.py
- tests/unit/progression/test_lifecycle.py

## Assumptions / Open Questions
- Idea 55's trigger is scoped to Campaign-mode Nemesis data only; most default single-episode Kernel runs will never populate this signal — accepted as a real, disclosed scope limit rather than a gap to silently work around.
- The exact "weakened" hostility-transfer formula (severity multiplier/decay) is a Plan-phase decision, not resolved by investigation.
- Whether idea 58's new typed model needs a fully granular `CognitionPatch` sub-update or can safely use careful whole-object-replace handling is a Plan-phase decision.
- `layer: systems` was chosen because the dispatch hook and both handlers live in `src/systems/lifecycle_systems/` and are wired through the systems layer; this is a straightforward fit, not a fallback.

## Implementation Notes
Added `NamedIntentionBundle` (`src/core/cognition.py`) as a new `MotivationModel.named_intention`
field, and two thin static handlers on `LifecycleSystem`
(`src/systems/lifecycle_systems/lifecycle.py`): `_transfer_inherited_feud` (idea 55) and
`_seed_dying_wish` (idea 58), both called from a single new dispatch point inside
`resolve_lifecycle`'s death block, right after `heir_entity_id` resolution and before the existing
heirloom-transfer logic.

**Idea 55 scope decision (as flagged in the ticket).** Explicitly targets only the Campaign-mode
`entity.strategic.blockers["nemesis_*"]` signal (populated by `NemesisRelationImporter`) — the
always-live legacy `SocialComponent.nemesis_ids`/`grudge_history` mechanism is untouched, per the
ticket's own Out of Scope. Transfers a weakened copy (`severity * 0.5`) under a distinct
`inherited_nemesis_{antagonist}` id so a heir's own independent nemesis relation against the same
antagonist is never silently overwritten.

**Idea 58 architecture decision.** Rather than inventing a new granular `CognitionPatch` sub-update
(one of the two options the ticket's own Scope section left open), `_seed_dying_wish` reuses this
codebase's already-established read-through-then-replace convention for `cognition_bundle_set`
(the same shape as `src/strategy/role_model_phase.py`, `src/domains/emotion/habit_phase.py`, and
`src/engine/quests.py`'s reputation write) — it reads whatever `cognition_bundle_set` an earlier
same-tick phase already staged on the heir, replaces only `motivation.named_intention`, and writes
back. This satisfies AC4 (no same-tick clobbering) without duplicating existing infrastructure.

**Minor structural fix alongside the dispatch wiring (disclosed, not silently made).** The
pre-existing heirloom-transfer code only wrote `refined_entity_updates[heir_id] = heir_upd` back
*inside* the `if all_transfer_items:` branch. Since the new dispatch handlers can now mutate
`heir_upd` even when the deceased has no items/heirlooms to transfer, that write-back was moved to
run unconditionally at the end of the `if heir:` block — otherwise a death with no inheritable
items but an active nemesis blocker or a seeded dying wish would silently drop both handlers'
output. This is a direct, necessary consequence of this ticket's own scope (wiring a new dispatch
point into that exact code path), not an unrelated fix.

Wish text (idea 58) is deterministic, not narratively generated: references the deceased's active
nemesis antagonist when `_transfer_inherited_feud` found one, otherwise a generic remembrance
string — a Plan-phase content decision, since no existing spec selects among multiple wish
templates.

## Test Summary
6 new tests added to `tests/unit/progression/test_lifecycle.py`, one per Acceptance Criteria item
(plus one extra no-op-case test for idea 55). Combined scoped regression (lifecycle, cognition-model
schema, motivation-model schema, full `tests/unit/strategic/`, cognition-migration architecture
linter, determinism/canonical-hash scheduler test, grief/nemesis Campaign-mode tests): 401 passed,
0 failed.
```
pytest tests/unit/progression/test_lifecycle.py tests/unit/entity/test_phase11_cognition_model_schema.py tests/unit/domains/motivation/test_phase14_motivation_models.py tests/unit/strategic/ tests/architecture/test_phase18_cognition_migration_linter.py tests/unit/engine/test_hash_scheduler.py tests/unit/domains/campaigns/test_grief_urgency.py tests/unit/kernel/test_grief_trigger_drain.py tests/integration/campaigns/test_mid_episode_grief_trigger.py -q
```

## Files Changed
- `src/core/cognition.py` — new `NamedIntentionBundle` dataclass, `MotivationModel.named_intention` field
- `src/systems/lifecycle_systems/lifecycle.py` — `_transfer_inherited_feud`, `_seed_dying_wish`, dispatch wiring, unconditional heir-update write-back
- `tests/unit/progression/test_lifecycle.py` — 6 new tests
- `docs/mechanics/04_strategic_cognition.md` — new Section 12
- `docs/parity_ledger/combat_movement.yaml` — new entry, originally written as COMB-321, renumbered to COMB-322 during the PR merge (an unrelated concurrent PR #123 independently used COMB-321 first)
- `docs/parity_ledger/social_narrative.yaml` — new entry, originally written as SOC-265, renumbered to SOC-269 during the PR merge (PR #123 independently used SOC-265 first)
- `docs/parity_ledger/strategic_cognition.yaml` — new entry STRAT-270

## Completion Summary
Ideas 55 and 58 land as one on-death dispatch hook with two thin handlers inside
`LifecycleSystem.resolve_lifecycle`, exactly matching the M5 epic doc's own consolidation. Idea 55
transfers a weakened Campaign-mode nemesis blocker to the heir; idea 58 seeds a source-attributed,
honorable/ignorable/rejectable named intention onto the heir's cognition, reusing the codebase's
established same-tick-safe cognition-write pattern rather than inventing a new one. All 5 acceptance
criteria are covered by dedicated tests; the reputation branch (ideas 60/53/54) remains untouched and
independently landable, verified by a source-text guard test.
