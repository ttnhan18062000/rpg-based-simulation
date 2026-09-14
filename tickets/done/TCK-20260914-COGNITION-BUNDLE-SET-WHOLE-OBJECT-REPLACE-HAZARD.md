---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD
phase: done
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
DONE

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

**Why a convention/guardrail fix is probably not enough, evidenced by the enumeration itself**: 5 of
the 6 already-safe writers got there by explicitly copying each other's read-through pattern —
`role_model_phase.py`'s own docstring cites `habit_phase.py` as its precedent, and the same citation
chain runs through `hardening.py`, `lifecycle.py`, and `quests.py`. The convention exists, is
documented, and propagated well — 5-of-6 real adoption is a genuinely good track record for an
unenforced convention. **And it still failed, in exactly the case it always fails**: both of the two
broken sites (`combat_engagement`, `movement.py`) were new writers built without looking at a
neighbor first. The failure mode here isn't ignorance of an existing pattern — it's not knowing a
pattern is *needed at all*, which only a type or the merge logic itself can surface; a comment or a
doc cannot. That a well-adopted convention still produced silent data loss is a stronger argument for
the structural options (1/2 above) than any argument from first principles would be — option 3 (a
guardrail test) mechanically enforces awareness where the convention already achieves it 83% of the
time on its own, but does nothing about the 17% who don't know to look.

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

**Recommended first action when this ticket is picked up** (do this regardless of which structural
option above is ultimately chosen — it is not conditional on that decision and shouldn't wait for
it): give `src/domains/memory/phase.py:51` the same read-through the other 5 safe writers already
use. It is a ~3-line change matching an existing, well-established pattern, and it removes a
tripwire that arms itself silently the moment anyone ever reorders the pipeline to put another
cognition writer before `memory_update` — nobody reordering phases for an unrelated reason would
think to check cognition-write ordering first, and the failure would be the identical invisible
data loss this ticket exists because of. Cheap, safe, and load-bearing independent of the larger
structural question.

## Acceptance Criteria
- [x] A decision is recorded (with tradeoffs, not silently picked) among per-subfield merge / typed
  accessor / corpus test — or a documented reason to accept the status quo (mitigation-at-each-
  call-site) if that's judged sufficient given the small and slow-growing writer count. **Decision:
  Option 2 (typed write helper) + Option 3 (architecture-test guardrail), not Option 1** — see
  investigation.md's "Recommendation" section, including the empirical verification (peer-directed)
  that Option 1's one concrete justification (a dict-key-collision case) is already handled
  correctly by Option 2 given how the pipeline actually threads its accumulator.
- [x] Whichever option is chosen is implemented and tested against the real `CognitionModel` schema.
  `src/core/cognition_write.py::read_through_cognition()` built and unit-tested (7 cases); all 8
  real writer sites migrated to call it (including `src/engine/quests.py`, found during this build,
  not in the original enumeration); the architecture guardrail
  (`tests/architecture/test_cognition_bundle_set_read_through_guard.py`) built, verified against a
  synthetic violation, and passing clean against the real repo.
- [x] If a per-subfield merge is chosen, `src/engine/patches.py::CognitionPatch.merge()` is fixed to
  match. **N/A** — Option 1 (per-subfield merge) was not chosen; `CognitionPatch.merge()` stays
  untouched and dormant per the investigation's own recommendation (confirmed still not a live
  collision site).
- [x] The enumeration table above is re-verified as part of this ticket's own investigation (writer
  sites may have changed since 2026-09-14). Re-verified in investigation.md's own opening section;
  one additional real writer found during the Option 2 build itself
  (`src/engine/quests.py::enforce()`'s ESCORT reputation write, using a dict-subscript build-up
  shape the original grep-based enumeration didn't match) and migrated + folded into the guardrail's
  own detection logic.

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
See staging_artifacts (→ stored_artifacts on close) `plan.md`/`investigation.md` for full detail.
Summary:

1. **Recommended first action** (`memory_update` ordering fix) done first, independent of the
   larger decision: `src/domains/memory/phase.py::MemoryUpdatePhase.apply()` now reads through any
   `cognition_bundle_set` an earlier phase already staged this same tick.
2. **Peer directly challenged one specific claim** in the initial investigation draft — that a
   dict-key-collision case (`opponent_stats`, two writers touching different keys for the same
   entity, same tick) was a real gap Option 2 alone couldn't close, requiring Option 1. Verified
   empirically with a real 3-entity `AuthoritativeApplyPipeline.refine()` run rather than re-arguing
   from the writer table: the claim was **wrong** — `action_routing` and `combat_engagement` share
   the pipeline's single, linearly-threaded `update`/`tick_update` accumulator, so both writers'
   dict keys landed correctly without any additional merge logic. investigation.md corrected;
   Option 1's "deferred escalation path" framing retired as unnecessary, not just softened.
3. **Built Option 2**: `src/core/cognition_write.py::read_through_cognition(fallback_cognition,
   *candidate_updates)` — a single, minimal, accumulator-shape-agnostic helper. Migrated all 8 real
   writer sites to call it (see Files Changed) instead of hand-rolling the lookup, including
   `combat_engagement/phase.py`'s own `_read_through_cognition()`, now a thin delegating wrapper
   preserving that phase's own two-accumulator priority order.
4. **Found an unenumerated 9th real writer during the migration itself**:
   `src/engine/quests.py::enforce()`'s ESCORT-completion reputation write, which builds
   `replace_kwargs["cognition_bundle_set"] = ...` as a dict entry later splatted into `replace()`,
   not a literal keyword argument — invisible to the original grep-based enumeration (`grep
   'cognition_bundle_set='`) and, initially, to the Option 3 guardrail's own keyword-only AST check.
   It was already correctly read-through before this change; migrated to the shared helper for
   consistency, and the guardrail's detection was broadened to catch this shape too (see below) so a
   future writer using it doesn't slip past the guardrail the way this one slipped past the
   original enumeration.
5. **Built Option 3**: `tests/architecture/test_cognition_bundle_set_read_through_guard.py` — an
   AST walk flagging any function that stages a `cognition_bundle_set` write (keyword argument OR
   dict-subscript build-up) while reading `.cognition` raw, without calling
   `read_through_cognition()` or a function that itself transitively calls it (computed via
   fixed-point closure over the call graph, not a hardcoded name list). One documented allowlist
   entry: `MovementSystem.resolve_move()` (`src/engine/movement.py`), safe because its only caller
   (`pipeline_phases/movement.py::route_movement_intent()`) pre-patches `.cognition` before invoking
   it. A second test guards that allowlist entry from silently going stale. Detection logic
   sanity-checked against a synthetic violating snippet before trusting a clean real-repo run as
   meaningful.
6. Deliberately left untouched: `src/engine/domain/combat_actions.py` /
   `src/domains/combat_engagement/learning_outcome.py` (safe via `ActionRoutingPhase`'s sliding-
   state materialization, a different real mechanism, not a read-through call) and
   `src/engine/patches.py::CognitionPatch.merge()` (confirmed still dormant, no live collision site,
   per the investigation's own recommendation).

## Test Summary
See staging_artifacts (→ stored_artifacts) `test_plan.md` for the full table. Headline numbers, all
run under `.venv313` (CI parity):
- New: `test_memory_update_reads_through_an_earlier_same_tick_cognition_write` (1), 
  `tests/unit/core/test_cognition_write.py` (7), `tests/architecture/
  test_cognition_bundle_set_read_through_guard.py` (2, including the allowlist-staleness guard).
- Regression across all 8 migrated call sites: 46 passed (combined bundle) + 104 passed
  (combat_engagement suite) + 44 passed (lifecycle/lineage) + 35 passed/1 xfailed (quests/reputation).
- `tests/architecture/` in full: 111 passed.
- Full fast-tier sweep (`tests/unit tests/integration tests/architecture -m "not slow and not
  extra_slow"`): 6518 passed, 9 skipped, 95 deselected, 7 failed — all 7 in
  `tests/unit/domains/progression/` (recipe/material-lookup tests, zero relation to this ticket's
  diff), confirmed to pass in isolation (18/18) — a pre-existing full-suite cross-test-pollution
  issue, disclosed, not fixed here (out of scope).

## Files Changed
- `src/core/cognition_write.py` (new) — the shared `read_through_cognition()` helper.
- `src/domains/memory/phase.py` — Step 1 fix + migrated to the shared helper.
- `src/domains/combat_engagement/phase.py` — `_read_through_cognition()` now delegates to the
  shared helper.
- `src/domains/emotion/habit_phase.py` — migrated.
- `src/engine/pipeline_phases/hardening.py` — migrated.
- `src/systems/lifecycle_systems/lifecycle.py` — migrated.
- `src/strategy/role_model_phase.py` — migrated.
- `src/engine/pipeline_phases/movement.py` — migrated.
- `src/engine/quests.py` — migrated (9th real writer, found during this build).
- `tests/unit/domains/memory/test_memory_update_phase_apply.py` — new regression test.
- `tests/unit/core/test_cognition_write.py` (new) — helper unit tests.
- `tests/architecture/test_cognition_bundle_set_read_through_guard.py` (new) — Option 3 guardrail.
- `staging_artifacts/TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD/{investigation,plan,test_plan}.md`.

## Completion Summary
Decided and built Option 2 (mandatory typed write helper) + Option 3 (architecture-test guardrail)
for the whole-object-replace hazard on `EntityUpdate.cognition_bundle_set`. Option 1 (recursive
per-subfield merge) was investigated and explicitly rejected: its one concrete justification — a
same-tick dict-key collision in `opponent_stats` — was verified empirically (per peer's direct
challenge to the original investigation's claim) to already be handled correctly by Option 2, since
every real writer shares the pipeline's single linearly-threaded accumulator. All 9 real
`cognition_bundle_set` writers (one more than the ticket's original enumeration, found during the
build) now route through one sanctioned, shape-agnostic helper, and a new architecture test makes
skipping that helper a CI failure rather than a silent future data-loss bug — closing this hazard
class structurally rather than leaving it as an accumulating pile of individually-patched call
sites.
