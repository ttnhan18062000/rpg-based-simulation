---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260904-LINEAGE-DEATH-DISPATCH
artifact_type: investigation
tags: [lifecycle, social]
---

# Investigation — TCK-20260904-LINEAGE-DEATH-DISPATCH

## Current Behavior (file:line refs)

- `src/systems/lifecycle_systems/lifecycle.py:39-188` (`LifecycleSystem.resolve_lifecycle`, PP-33):
  deterministically resolves `heir_entity_id` (manual or `_select_default_heir`) before transferring
  heirlooms (line 132 `if heir_id is not None:`, heirloom logic at 133-158). No dispatch hook exists
  today for anything beyond heirloom/inventory transfer.
- `src/domains/campaigns/grief_urgency.py:92-149` (`NemesisRelationImporter`): the only writer of
  `entity.strategic.blockers["nemesis_*"]`, called exclusively from
  `CampaignOrchestrator._build_initial_state()` at Campaign episode start. No mid-episode/live-Kernel
  writer exists. The blocker id format is `nemesis_{antagonist_id}`, `BlockerState(kind=SOCIAL,
  subject=str(antagonist_id), severity=relation.strength)`.
- `src/core/models/social.py:32-57` (`SocialComponent`): the always-live legacy
  `nemesis_ids`/`grudge_history` mechanism -- distinct from the Campaign-mode blocker above, tracked
  separately by `TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`.
- `src/core/cognition.py:417-434` (pre-change `MotivationModel`): `doctrine`, `values`, `role_fit`,
  `ambition`, `moral` -- no field shaped for a source-attributed named intention.
- `src/core/strategic.py:379-386` (`CommittedIntention`): the existing "Intention" concept, a
  self-generated multi-step-planning sequence on `StrategicComponent` -- must not be renamed/reused.
- `src/core/updates.py:674-770` (`EntityUpdate`): has a proper mergeable `strategic:
  Optional[StrategicUpdate]` field (merge() at 752 delegates to `StrategicUpdate.merge()`), but
  `cognition_bundle_set: Optional[Any]` (line 706) merges as last-write-wins whole-object-replace
  (line 767: `if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] =
  other.cognition_bundle_set`).
- `src/engine/patches.py:720-737` (`CognitionPatch`): confirms `cognition_bundle_set` applies as a
  whole `entity.cognition` replacement, not a per-field merge.
- Established codebase convention for safely writing `cognition_bundle_set` under this constraint:
  `src/strategy/role_model_phase.py:44-49`, `src/domains/emotion/habit_phase.py:49-58`,
  `src/engine/quests.py:228-261` all follow the same "read entity_update.cognition_bundle_set if not
  None else entity.cognition, replace one sub-field, write back" shape. This is the real, live
  pattern for multiple same-tick `cognition_bundle_set` writers to coexist safely -- not a new
  mechanism this ticket must invent.

## Mechanics/Engine Constraints

- Durable State Rule (CLAUDE.md): any new durable field needs a typed model, stable
  `AuthoritativeState` location, defined lifecycle, and tests. `NamedIntentionBundle` satisfies this
  via `MotivationModel.named_intention`, applied only through `CognitionPatch`/`ApplyPath`.
  `_transfer_inherited_feud`'s output satisfies this via the existing `StrategicUpdate`/`ApplyPath`
  mechanism -- no new typed model needed there.
- Authoritative Mutation Pipeline Rule: both handlers write only through typed `EntityUpdate`
  sub-fields (`strategic`, `cognition_bundle_set`), never direct `EntityState` mutation.
- docs/mechanics/04_strategic_cognition.md Section 3 ("Grief Urgency & Nemesis Relations: Two
  Injection Paths") already documents `NemesisRelationImporter`'s Campaign-mode scope -- this
  ticket's Section 12 addition must be consistent with, not contradict, that existing scope framing.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: new Section 12 documenting the on-death dispatch hook, both handlers, and the same-tick cognition-write safety pattern.
- `docs/parity_ledger/combat_movement.yaml`: new entry (idea 55, strategic-blocker mechanics).
- `docs/parity_ledger/social_narrative.yaml`: new entry (idea 55, social/narrative-continuity framing).
- `docs/parity_ledger/strategic_cognition.yaml`: new entry (idea 58, named-intention seeding).

## Parity Ledger Overlap (IDs + status)

None pre-existing for this exact mechanism (death-triggered hostility transfer, intention-seeding).
`next_available_id()` at investigation time: `combat_movement.yaml` -> COMB-321,
`social_narrative.yaml` -> SOC-265, `strategic_cognition.yaml` -> STRAT-270. (Post-hoc note: COMB-321
and SOC-265 were each independently claimed by a concurrent PR #123 entry during the later merge into
origin/main and had to be renumbered to COMB-322/SOC-269 — see the ticket's own Files Changed section
for the final IDs. This artifact is left as an accurate historical record of investigation-time state.)

## Prior Work

- `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX` (DONE) -- makes `outcome_kind=="PERMADEATH"`
  deactivate correctly; this ticket's precondition.
- `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` (DONE) -- `_select_default_heir`; this ticket's precondition.
- `TCK-20260824-GRIEF-NEMESIS-REACHABILITY` (DONE) -- established the authoritative-Kernel-injection
  pattern for mid-episode `StrategicUpdate` writes this ticket's idea-55 handler reuses.
- `TCK-20260831-ROLE-MODEL-IMITATION` -- established the read-through-then-replace
  `cognition_bundle_set` convention this ticket's idea-58 handler follows.

## Risks and Open Questions

- Idea 55's trigger is scoped to Campaign-mode Nemesis data only -- most default single-episode
  Kernel runs never populate it, so the handler is frequently a no-op. Accepted, disclosed limit.
- Idea 58's wish-text content is deterministic and template-based (references the deceased's active
  nemesis antagonist if one exists, otherwise a generic remembrance) -- no narrative-generation
  subsystem exists or is introduced. A Plan-phase content decision, not resolved by any existing spec.
- Whether to add a fully new granular `CognitionPatch` sub-update vs. reuse the established
  read-through-then-replace convention: resolved in favor of reuse -- it is the real, live,
  already-multiply-adopted pattern in this codebase, and inventing a parallel mechanism would
  duplicate existing infrastructure without a concrete benefit this ticket's scope requires.

## Anti-Drift Hazards

- `_transfer_inherited_feud` must use a distinct blocker id (`inherited_nemesis_{antagonist}`), never
  reusing `nemesis_{antagonist}` -- a heir with their own independently-formed nemesis relation
  against the same antagonist must not be silently overwritten.
- `_seed_dying_wish` must read `heir_upd.cognition_bundle_set` before falling back to `heir.cognition`
  -- writing straight from `heir.cognition` would silently clobber any earlier same-tick writer.
