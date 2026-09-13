---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD
phase: open
date: 2026-09-14
tags: [engine, investigation, root-cause, cognition]
---

# TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD

## Title
`EntityUpdate.cognition_bundle_set`'s whole-object-replace merge semantics silently discard an
earlier same-tick phase's cognition write whenever two phases write it for the same entity in the
same tick — real instance found and fixed narrowly; the field's own merge semantics are the actual
defect and were never itself fixed.

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
While building `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (flipping `ENABLE_COMBAT_ENGAGEMENT`
to `ON` for the first time), the full `tests/integration/` regression run caught a real, silent
durable-state loss: `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py`, a test
with no connection to combat_engagement, started failing —
`defender_after_tick2.cognition.memory.causal.entries` came back empty when it should have held one
real entry.

**Root cause**: `EntityUpdate.merge()`'s own `cognition_bundle_set` field (`src/core/updates.py:787`)
is a whole-object REPLACE — `if other.cognition_bundle_set is not None: changes["cognition_bundle_set"]
= other.cognition_bundle_set` — not a per-subfield merge of the `CognitionModel` the field holds.
`memory_update` runs before `combat_engagement` in the pipeline
(`src/engine/pipeline.py`). `CombatEngagementPhase.apply()` built its own updated `CognitionModel` by
reading straight from `state.entities[...].cognition` (the tick-START snapshot) rather than checking
whether an earlier phase this same tick had already staged a `cognition_bundle_set` for that entity.
Merging combat_engagement's own write on top silently discarded whatever `memory_update` had just
written — no exception, no warning, the data was just gone.

The same bug class was independently found in `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`'s own
Step 5b (`src/engine/movement.py`'s FLED-learning write, wired through
`src/engine/pipeline_phases/movement.py::route_movement_intent()`), for the identical reason:
`MovementSystem.resolve_move()` has no access to the tick's accumulated `StateUpdate` at all and
reads the entity straight from `state.entities`.

**Both concrete instances were fixed narrowly** (a `_read_through_cognition()` helper in
`phase.py`; a targeted `.cognition` patch at the `movement.py` pipeline call site) as part of that
ticket, and are not this ticket's concern. **What was NOT fixed, and is this ticket's actual
scope, is the field's own unsafe merge semantics** — the mitigation was applied at two call sites;
nothing prevents a third, future writer from making the identical mistake, because the type itself
allows it silently.

**Why this was never caught before**: the hazard requires two independent `cognition_bundle_set`
writers to be live for the same entity in the same tick. Until `ENABLE_COMBAT_ENGAGEMENT` flipped
ON today, `combat_engagement` was the only writer that could ever collide with another — every
other writer either ran first in the pipeline (`memory_update`) or was the only writer active for
its own reason. One writer can never collide with itself. The bug was real and present in the type
the entire time; it was simply unreachable until a second live writer existed.

## Scope
- Decide (not implement without a decision) how to make this class of bug structurally impossible,
  not just patched at each call site as writers accumulate. At minimum, weigh:
  1. **Per-subfield merge** — teach `EntityUpdate.merge()` (and `CognitionPatch.merge()` in
     `src/engine/patches.py`, which reproduces the identical whole-object-replace pattern on the
     same field, confirmed dead/unexercised in the current call graph but a second instance of the
     same unsafe pattern) to merge `CognitionModel`'s own sub-trees (`memory.causal`, `memory.combat`,
     `memory.habit`, `subjective`, `motivation`, `role_model`, `relationships`, etc.) instead of
     replacing the whole object. Makes the hazard structurally impossible for every future writer,
     at the cost of `CognitionModel`'s own merge needing to stay in sync with its schema as fields
     are added.
  2. **A typed accessor / guarded write helper** that every phase must go through to write
     `cognition_bundle_set`, which internally does the read-through-then-replace pattern
     (`_read_through_cognition`-shaped) automatically — makes the unsafe direct-snapshot read the
     hard-to-reach path instead of the easy one, without changing `merge()`'s own semantics.
  3. **A corpus/architecture test** asserting no phase reads `entity.cognition` (or
     `state.entities[...].cognition`) directly when constructing a `cognition_bundle_set` write,
     forcing every future writer through whichever pattern is chosen — a guardrail rather than a
     structural fix, weakest of the three but cheapest and compatible with either 1 or 2.
  This ticket should investigate feasibility/cost of each against the real schema
  (`src/core/cognition.py::CognitionModel`) and bring a recommendation with tradeoffs, not
  silently pick one.
- Full enumeration of every real `cognition_bundle_set` writer as of 2026-09-14 (from
  `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`'s own investigation, re-verify before acting on
  it since this list will drift):

  | Site | Phase / call site | Pipeline position | Verdict |
  |---|---|---|---|
  | `src/domains/memory/phase.py:51` | `memory_update` | Earliest cognition writer in the tick | Safe **only because it runs first** — reads `state.entities` directly, no read-through. **Latent risk**: would silently clobber any writer inserted before it in the future. |
  | `src/domains/emotion/habit_phase.py:58` | `habit_bias` | Runs right after `memory_update` | Safe — explicit read-through (`entity_update.cognition_bundle_set` then `entity.cognition`), documented as deliberately mirroring the pattern below. |
  | `src/strategy/role_model_phase.py:83` | `role_model` | Runs after `habit_bias` | Safe — explicit read-through, cites `habit_phase.py` as its own precedent. |
  | `src/engine/quests.py:261` | `quest_rewards` (ESCORT reputation) | Line 363 in pipeline.py | Safe — explicit read-through (checks a locally-built `reputation_cognition_update` first, then `ent_upd.cognition_bundle_set`, then `entity.cognition`). |
  | `src/engine/pipeline_phases/hardening.py:106` | `near_death_hardening` | Line 410 in pipeline.py | Safe — explicit read-through. |
  | `src/systems/lifecycle_systems/lifecycle.py:118` | `lifecycle` (heir cognition on death) | Line 414 in pipeline.py | Safe — explicit read-through, same documented pattern. |
  | `src/engine/domain/combat_actions.py:137,139` | `action_routing` (combat-learning, Step 5a) | Line 297 in pipeline.py | Safe — **not** via explicit read-through code, but structurally safe: `ActionRoutingPhase.route()` materializes a full sliding-state working copy (every prior-this-tick `EntityUpdate` applied via `ApplyPath._apply_entity_update`) before dispatching action handlers, so `entity.cognition` is already current by construction. |
  | `src/domains/combat_engagement/phase.py:174,177,445` | `combat_engagement` (Steps 2/4/5a passive observation, witnessed-combat) | Line 320 in pipeline.py | **Was unsafe** (this bug's own trigger) — **fixed** in `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` via a new `_read_through_cognition()` helper. |
  | `src/engine/movement.py:317` via `src/engine/pipeline_phases/movement.py` | `movement_routing` (Step 5b, FLED) | Line 299 in pipeline.py | **Was unsafe** (found independently during the same investigation) — **fixed** in the same ticket, at the pipeline call site (patches `.cognition` before calling `resolve_move()`, since `resolve_move()` itself has no access to the tick's accumulated update). |
  | `src/engine/patches.py:738,809` (`CognitionPatch`) | Not a per-tick phase — a downstream single-`EntityUpdate`-to-`EntityState` applier (`ApplyPath._apply_entity_update_to_dict`) | N/A | Not a live writer-collision site today (its own `merge()` is never exercised against two colliding `CognitionPatch` objects in the current call graph) — but its `merge()` method reproduces the identical whole-object-replace pattern, confirming the hazard exists in a second, independent implementation, not only `EntityUpdate.merge()`. Relevant to whichever fix option is chosen (a per-subfield merge fix should cover this too). |

## Out of Scope
- Re-fixing the two already-fixed call sites (`combat_engagement`/`movement.py`) — done, tested,
  landed in `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`.
- `self_model_bundle_set` (`src/core/updates.py`), which has the identical whole-object-replace
  shape on a sibling field — worth a similar audit, but a separate field/schema
  (`SelfModelBundle`, not `CognitionModel`) and a separate ticket if warranted.
- Making `memory_update`'s own read defensive just because it currently runs first — that's covered
  by whichever structural fix this ticket picks (option 1 or 2 above would make it safe by
  construction; option 3 would catch a future regression via the test).

## Acceptance Criteria
- A decision is recorded (with tradeoffs, not silently picked) among per-subfield merge / typed
  accessor / corpus test — or a documented reason to accept the status quo (mitigation-at-each-
  call-site) if that's judged sufficient given the small and slow-growing writer count.
- Whichever option is chosen is implemented and tested against the real `CognitionModel` schema.
- If a per-subfield merge is chosen, `src/engine/patches.py::CognitionPatch.merge()` is fixed to
  match (currently dormant, but a second instance of the same unsafe pattern).
- The enumeration table above is re-verified as part of this ticket's own investigation (writer
  sites may have changed since 2026-09-14).

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` — where this was found; the two narrow
  mitigations already landed there.
- `TCK-20260830-ENTITY-EVENT-LEDGER-COGNITION-BUNDLE-SET-MISSING` — unrelated (observability ledger
  coverage), but documents the field's history and its 3 real write sites as of 2026-08-30 (before
  `habit_bias`/`role_model`/`combat_engagement`/`movement.py` existed).
- `TCK-20260831-HABIT-BIAS-WIRING` — introduced `habit_phase.py`'s own read-through pattern.
- `TCK-20260831-ROLE-MODEL-IMITATION` — introduced `role_model_phase.py`'s own read-through pattern,
  explicitly citing `habit_phase.py` as precedent.

## Related Docs
- `docs/core/state.md` — immutability law, authoritative vs non-authoritative state partitioning.
- `docs/engine/authoritative_mutation_pipeline_contract.md` — mutation rules and apply-path law.

## Related Stored Artifacts
_(none yet — standard-tier investigation/plan/test_plan artifacts to be created when this ticket
moves to `tickets/inprogress/`)_

## Related Code Areas
- `src/core/updates.py` (`EntityUpdate.merge()`, `cognition_bundle_set` field)
- `src/core/cognition.py` (`CognitionModel` schema)
- `src/engine/patches.py` (`CognitionPatch`)
- All 9 real writer sites enumerated above.

## Assumptions / Open Questions
- Is `CognitionModel`'s own sub-tree structure stable enough that a per-subfield merge function
  won't itself become a maintenance burden every time a new cognition sub-model is added? (Compare:
  `EntityUpdate.merge()` already does this per-component for `combat`/`social`/`strategic`/etc. —
  precedent exists, but `CognitionModel` is deeper/more nested than those.)
- Does a typed write helper (option 2) need to be mandatory (enforced by a lint/architecture test)
  or just a documented convention, given 6 of today's 9 real writers already independently arrived
  at the correct pattern by copying each other's precedent?

## Implementation Notes
_(pending)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
