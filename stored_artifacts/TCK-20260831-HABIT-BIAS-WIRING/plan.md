---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-HABIT-BIAS-WIRING
artifact_type: plan
tags: [cognition]
---

# Implementation Plan — TCK-20260831-HABIT-BIAS-WIRING

## Summary

Wire `HabitBiasService` into a real, non-inert ActionStyle bias point. The investigation's own
finding is decisive: `get_action_style_for_bravery` (`src/content_semantics/personality.py:66`)
runs only at entity-construction time (3 call sites), so any habit input fed into that function
would always see an empty `habit.patterns` and be a structural no-op. The plan instead (a) gives
`HabitBiasService.record_outcome` a real per-tick production writer — a new, independently-gated
pipeline phase (`HabitBiasUpdatePhase`) that reuses the exact `combat_loss` trigger-event list
`MemoryUpdatePhase` already builds at `src/engine/pipeline.py:149-153`, and writes
`HabitMemory.patterns` back through the same `entity_update.cognition_bundle_set` authoritative
apply path `NearDeathHardeningPhase`/`MemoryUpdatePhase` already use — and (b) re-derives
`ActionStyle` live at both real runtime consumers named by `SUB-381`
(`docs/parity_ledger/substrate.yaml`) and `get_action_style_for_bravery`'s own docstring —
`src/engine/tactical.py:491` (kiting distance) and `src/engine/movement.py:185`
(opportunity-attack suppression on a deliberate EVASIVE retreat) — by feeding
`HabitBiasService.apply_habit_bias`-adjusted bravery into the existing
`get_action_style_for_bravery` (reused as a pure function, not re-implemented) at each site. Both
consumers are re-derived identically so neither reads a stale value while the other reads a live
one under the same flag. All three sides (write, and both read sites) are
gated by one new flag, `ENABLE_HABIT_BIAS_ACTION_STYLE`, default OFF, checked via a direct
`state.feature_flags`/`state_or_context.feature_flags` dict read (the same pattern
`GuildNeedScorer.score()` already uses at `src/ai/goals/scorers.py:253`) since `tactical.py`'s
`evaluate_entity_intent` is a per-entity, per-tick call that already receives
`state: AuthoritativeState` directly, and `movement.py`'s `resolve_move` already receives its
(more loosely typed `Any`) `state_or_context` directly — no `FeatureFlagManager` injection needed
at either site. `record_outcome` can only ever record `success=False`
in this plan: `WorldEventCategory` (`src/domains/world_emergence/schema.py:15-45`) and `WorldEvent`
(`schema.py:54-60`, fields `category`/`tick`/`region_id`/`subject`/`severity`/`payload` — no
attacker/killer field) provide `COMBAT_LOSS` but no win/victory category or actor-of-victory
signal, so recording a `success=True` outcome would require inventing a new event category —
explicitly out of scope per the ticket's own "not building new accumulation state" guard. This is
gradual-accumulation-only, failure-direction-only; `record_outcome`'s existing `success` parameter
is exercised with `False` from the one real signal the pipeline already computes, nothing more.
`get_action_style_for_bravery`'s 3 construction-time call sites and `CombatComponent.action_style`
itself are untouched — the flag-OFF path is bit-identical to shipped behavior.

## Steps

### Step 1 — Add the `ENABLE_HABIT_BIAS_ACTION_STYLE` flag
**Files:** `src/domains/optimization/feature_flags.py`
**Change:** Add `"ENABLE_HABIT_BIAS_ACTION_STYLE": FeatureMode.OFF,` to
`FeatureFlagManager.__init__`'s `self._flags` dict (verified dict literal at
`src/domains/optimization/feature_flags.py:13` onward; confirmed shape via the adjacent
`"ENABLE_CREATURE_TERRITORY_LIFECYCLE"` and `"ENABLE_MEMORY_UPDATE"` entries, each with a
comment block explaining default-OFF rationale). Add a comment matching the existing style:
new gameplay behavior, DEV-002 default-OFF policy applies (brand-new mechanic, no corpus
profile turns it on, no SHADOW-validation history), referencing this ticket ID.
**Do NOT touch:** any other flag's default value (in particular do not touch
`ENABLE_MEMORY_UPDATE`'s existing OFF default — the new phase must not be nested under that flag;
see Step 3's rationale for why they must be independently gated).
**Verify:** `test_habit_bias_action_style_flag_default_off` (new) —
`FeatureFlagManager().get_flag_mode("ENABLE_HABIT_BIAS_ACTION_STYLE") == FeatureMode.OFF`.

### Step 2 — Give `HabitMemory` a durable write pattern_id constant
**Files:** `src/domains/emotion/habit_service.py`
**Change:** Add a module-level constant, `HABIT_PATTERN_COMBAT_ENGAGEMENT = "combat_engagement"`,
directly in `habit_service.py` (co-located with `HabitBiasService`, which already imports nothing
from a shared constants module — verified no existing shared-constant module for domain/emotion
pattern IDs via the file's current imports at lines 1-9). This is the single `pattern_id` used by
both the write side (Step 3) and read side (Step 4) so they can never drift apart into
mismatched keys. No change to `HabitBiasService.record_outcome`/`apply_habit_bias` themselves —
both are already correct per the investigation (`record_outcome` at line 15, `apply_habit_bias`
at line 27, confirmed read directly this session).
**Do NOT touch:** `record_outcome`/`apply_habit_bias`'s signatures, clamping behavior, or the
±0.1 / `(patterns[tag]-0.5)*0.4` formulas — these are already shipped and covered by
`tests/unit/domains/emotion/test_phase16_habit_bias_service.py`.
**Verify:** existing `test_habit_bias_service` still passes unchanged (regression guard, no new
test needed for a constant addition).

### Step 3 — New `HabitBiasUpdatePhase`: authoritative write side (`record_outcome`)
**Files:** new file `src/domains/emotion/habit_phase.py`; `src/engine/pipeline.py`
**Change:**
Create `HabitBiasUpdatePhase` in `src/domains/emotion/habit_phase.py`, mirroring
`NearDeathHardeningPhase.apply()`'s read-through-then-replace shape
(`src/engine/pipeline_phases/hardening.py:92-107`, confirmed this session) rather than
`MemoryUpdatePhase.run()`'s shape, which reads `state.entities` directly instead of the incoming
`entity_update.cognition_bundle_set` (`src/domains/memory/phase.py:42-46` — confirmed this
session; safe there only because nothing runs before it in the pipeline that writes
`cognition_bundle_set`, which will no longer be true once this phase exists — see writer
enumeration below):

```python
@staticmethod
def apply(state, update, trigger_events=None):
    entity_updates = dict(update.entity_updates)
    for trigger in (trigger_events or []):
        entity_id = trigger["entity_id"]
        entity = state.entities.get(entity_id)
        if entity is None:
            continue
        entity_update = entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
        base_cognition = (
            entity_update.cognition_bundle_set
            if entity_update.cognition_bundle_set is not None
            else entity.cognition
        )
        new_habit = HabitBiasService.record_outcome(
            base_cognition.memory.habit, HABIT_PATTERN_COMBAT_ENGAGEMENT, success=False
        )
        new_memory = replace(base_cognition.memory, habit=new_habit)
        new_cognition = replace(base_cognition, memory=new_memory)
        entity_updates[entity_id] = replace(entity_update, cognition_bundle_set=new_cognition)
    return replace(update, entity_updates=entity_updates)
```

`success=False` is hardcoded: `trigger["kind"]` will always be `"combat_loss"` (see below), the
only outcome kind this plan wires. `trigger_events` reuses the exact list already built at
`src/engine/pipeline.py:149-153` (`_memory_trigger_events`, filtered on
`WorldEventCategory.COMBAT_LOSS`) — do not build a second, parallel trigger-event list.

In `src/engine/pipeline.py`, add a new `run_phase` call immediately after the existing
`memory_update` call (after line 158, before the `self_model` call at line 164):
```python
update = run_phase(
    "habit_bias_action_style", update,
    lambda u: HabitBiasUpdatePhase.apply(state, u, _memory_trigger_events),
    "ENABLE_HABIT_BIAS_ACTION_STYLE",
)
```
Placed after `memory_update` (not nested inside it) so it is independently gated by the new flag
— `memory_update` stays gated by `ENABLE_MEMORY_UPDATE` alone (currently OFF by default per
`feature_flags.py`), and habit-bias recording must not require also turning that unrelated flag
on. Because the new phase reads `entity_update.cognition_bundle_set` as its base (falling back to
`entity.cognition`) rather than re-deriving fresh from `state.entities`, ordering relative to
`memory_update` does not create a clobber risk in either direction.

**Every other writer to `EntityUpdate.cognition_bundle_set` this step must not collide with**
(field declared `Optional[Any] = None` at `src/core/updates.py:660`; `EntityUpdate.merge()` at
line 719 does whole-value overwrite — `other.cognition_bundle_set` wins if not None — so any two
writers that do NOT read-through would silently clobber each other):
1. `MemoryUpdatePhase.apply()` (`src/domains/memory/phase.py:51`) — runs at
   `pipeline.py:154-158`, gated `ENABLE_MEMORY_UPDATE`, writes causal/spatial memory. Runs
   immediately *before* this new phase in the pipeline; since this new phase reads
   `entity_update.cognition_bundle_set` as its base, any same-tick causal/spatial write from
   `memory_update` is preserved, not overwritten.
2. `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py:106`) — runs at
   `pipeline.py:357` (`near_death_hardening`, unconditional, no flag), writes
   `EmotionalModel`/fear-panic changes. Runs *after* this new phase; it already reads
   `entity_update.cognition_bundle_set` as its base (`hardening.py:92-96`), so it will correctly
   layer its emotion write on top of this phase's habit write, not clobber it.
3. `src/engine/quests.py:249` (reputation-driven cognition update inside quest-reward
   resolution) — runs at `pipeline.py:319` (`quest_rewards`, unconditional). Confirmed at
   `quests.py:226-227` it also reads `ent_upd.cognition_bundle_set` (falling back if None) before
   replacing — same read-through discipline, runs after this new phase, composes correctly.
4. `AuthoritativeApplyPipeline` itself has no other direct writer; `src/engine/patches.py:671-686`
   (`CognitionPatch`) and `:748-749` are the Persistence-phase consumer that turns the final
   `cognition_bundle_set` into the committed `entity.cognition` — not a competing writer, the
   apply-path sink all of the above eventually feed into once, at end of tick.
No writer needs to change because of this addition — all four (three existing + this new one)
already follow, or are made in this step to follow, read-through-then-replace-whole-bundle, which
is order-independent by construction.
**Do NOT touch:** `MemoryUpdatePhase.run()`/`MemoryUpdatePhase.apply()` themselves (no field or
trigger-kind change there — matches the test plan's explicit guard that
`tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py` and
`SpatialMemory`/`CausalMemory` behavior must stay unaffected). Do NOT invent a new
`WorldEventCategory` (e.g. `COMBAT_WIN`) to get a `success=True` signal — out of scope, see Summary.
**Verify:** new `test_record_outcome_wired_through_authoritative_pipeline` (integration) — a
`combat_loss`-kind trigger event results in `entity.cognition.memory.habit.patterns` changing via
`entity_update.cognition_bundle_set`, flag ON only; and
`tests/architecture/test_memory_update_phase_pipeline_ordering.py` still passes unchanged
(regression guard on the pre-existing ordering assumptions this step's placement must respect).

### Step 4 — Live re-derivation at both real runtime consumers (`apply_habit_bias`)
**Files:** `src/engine/tactical.py`, `src/engine/movement.py`
**Change:** `ActionStyle` (`src/core/enums.py`) has exactly 2 real, already-wired production
consumers, per `get_action_style_for_bravery`'s own docstring (`src/content_semantics/
personality.py:66-75`, read this session) and `docs/parity_ledger/substrate.yaml`'s `SUB-381`
entry (`substrate.yaml:4523-4537`, read this session, `status: verified`, `priority: P1`): kiting
distance for `SKIRMISHER`-role entities in `tactical.py`, and opportunity-attack suppression on a
deliberate EVASIVE retreat in `movement.py`. Both must be re-derived live from habit-biased
bravery, in sync, or the flag-ON state creates an entity that "decided" to retreat evasively under
a habit-shifted bravery reading in `tactical.py` but is still checked against its stale
construction-time `action_style` for OA suppression in `movement.py` — a real, observable
inconsistency in the same tick, not a hypothetical. This step therefore has two sub-parts:

**4a — `tactical.py`.** At line 491 (`style = entity.combat.action_style`, inside
`TacticalDecisionSystem.evaluate_entity_intent(state, entity, neighbors, region_trauma)` —
signature confirmed at `src/engine/tactical.py:81-86`, `state: AuthoritativeState` already a
parameter), replace the bare read with a flag-gated live re-derivation:

```python
style = entity.combat.action_style
flags = getattr(state, "feature_flags", None) or {}
if flags.get("ENABLE_HABIT_BIAS_ACTION_STYLE", "OFF") == "ON":
    from src.domains.emotion.habit_service import HabitBiasService
    from src.domains.emotion.habit_phase import HABIT_PATTERN_COMBAT_ENGAGEMENT
    from src.content_semantics.personality import get_action_style_for_bravery
    effective_bravery = HabitBiasService.apply_habit_bias(
        entity.cognition.memory.habit,
        [HABIT_PATTERN_COMBAT_ENGAGEMENT],
        entity.identity.personality.bravery,
    )
    effective_bravery = max(0.0, min(1.0, effective_bravery))
    style = get_action_style_for_bravery(effective_bravery)
```
`flags.get(..., "OFF") == "ON"` mirrors the exact pattern already used for a per-entity,
per-tick, `state`-available read site: `GoalScore.score()` in `src/ai/goals/scorers.py:253`
(`flags = getattr(state, "feature_flags", None) or {}` /
`if flags.get("ENABLE_GUILD_QUEST_GENERATION", "OFF") != "ON": ...`), confirmed this session —
not `FeatureFlagManager` injection, which is not available at this call site and is unnecessary
since `state.feature_flags` (declared `Dict[str, Any]` at `src/core/state.py:1196`) already
carries the same flag values by the time `refine()` reaches `action_routing`/tactical evaluation.
`entity.identity.personality.bravery` path confirmed via `IdentityComponent.personality:
PersonalityComponent` at `src/core/state.py:488`. The explicit `max(0.0, min(1.0, ...))` clamp is
required because `apply_habit_bias` documents itself (and
`docs/simulation/domains/emotion_contract.md:104`) as unclamped, caller's responsibility;
`get_action_style_for_bravery`'s thresholds (0.65/0.35) assume a bravery-shaped [0,1] input.
`style` remains an `int`-compatible value either way (`entity.combat.action_style` is a raw
`int`, `get_action_style_for_bravery` returns `int(ActionStyle.X)` — confirmed at
`personality.py:76-82`), so the existing `style == ActionStyle.AGGRESSIVE` / `ActionStyle.EVASIVE`
comparisons at line 631 need no further change.

**4b — `movement.py`.** At line 185
(`if mode == MovementMode.RETREAT and entity.combat.action_style == 2: # EVASIVE`, inside
`MovementSystem.resolve_move(state_or_context: Any, entity: EntityState, target_pos, mode)` —
signature confirmed at `movement.py:27-32`, read this session), apply the identical live
re-derivation pattern, inserted immediately before the existing `skip_oa` check:

```python
skip_oa = False
style = entity.combat.action_style
flags = getattr(state_or_context, "feature_flags", None) or {}
if flags.get("ENABLE_HABIT_BIAS_ACTION_STYLE", "OFF") == "ON":
    from src.domains.emotion.habit_service import HabitBiasService
    from src.domains.emotion.habit_phase import HABIT_PATTERN_COMBAT_ENGAGEMENT
    from src.content_semantics.personality import get_action_style_for_bravery
    effective_bravery = HabitBiasService.apply_habit_bias(
        entity.cognition.memory.habit,
        [HABIT_PATTERN_COMBAT_ENGAGEMENT],
        entity.identity.personality.bravery,
    )
    effective_bravery = max(0.0, min(1.0, effective_bravery))
    style = get_action_style_for_bravery(effective_bravery)
if mode == MovementMode.RETREAT and style == 2:  # EVASIVE
    skip_oa = True
```

Data-availability check for this call site (required before reusing Step 4a's pattern here,
since `movement.py` differs from `tactical.py` in one respect): `resolve_move`'s first parameter
is typed `state_or_context: Any` (`movement.py:28`), not `state: AuthoritativeState` — the name
itself signals this function is sometimes called with a lighter context object, unlike
`tactical.py:81`'s `state: AuthoritativeState`. This is not a blocker: the flag read already uses
the same defensive `getattr(..., "feature_flags", None) or {}` fallback as Step 4a, so a caller
passing a context object without `feature_flags` safely falls through to flag-OFF behavior (the
correct, conservative default) rather than raising. `entity`, by contrast, is typed
`EntityState` here exactly as it is in `tactical.py` (`movement.py:29`) — the same full entity
object flows through both call sites, so `entity.cognition.memory.habit` and
`entity.identity.personality.bravery` are available identically to Step 4a; there is no
entity-side data-availability gap. This confirms Option A (live re-derivation in both consumers)
is safe to implement as-is, with no scope reduction needed.
**Do NOT touch:** the dead sub-branches already removed by
`TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` (confirmed still absent, `tactical.py:672`+
is now a removal comment) — do not resurrect an `attack_range`-style computation while editing
this function. Do NOT change `entity.combat.action_style` itself (the frozen, construction-time
field) — this step only shadows the local `style` variable used in this function's own logic; it
never writes back to `CombatComponent`. Do NOT touch `get_action_style_for_bravery`'s 3
construction-time call sites (`worldbuilding/compiler.py:466`,
`entities/archetype_factory.py:111`, `worldassembly/entity_spawner.py:138`) — those stay exactly
as-is; the function itself is reused as a pure helper, not modified. For 4b specifically, do NOT
touch the `skip_oa`/OA-resolution logic itself (`movement.py:206` onward, the
`resolve_multi_attack` call and the `escape_tag`/`combat_escape` observability block at
`movement.py:194-199`) — this step only changes what feeds the pre-existing
`entity.combat.action_style == 2` comparison (now a live `style` local), it does not alter how
`skip_oa` is consumed downstream. Do NOT change `resolve_move`'s `state_or_context: Any` signature
or tighten it to `AuthoritativeState` — that is a pre-existing looseness unrelated to this
ticket's scope.
**Verify:** new `test_habit_bias_shifts_action_style_when_flag_on` and
`test_habit_bias_flag_off_preserves_construction_time_action_style` (both unit, per test_plan.md,
covering 4a); new `test_habit_bias_shifts_movement_oa_suppression_when_flag_on` and
`test_habit_bias_flag_off_preserves_movement_oa_suppression` (both unit, covering 4b — construct
an entity mid-`RETREAT` with a habit-shifted effective bravery crossing the EVASIVE threshold
(≤0.35) while `entity.combat.action_style` itself stays at its construction-time BALANCED/
AGGRESSIVE value; assert `skip_oa`/OA-resolution behavior follows the live value when the flag is
ON and the stale field when OFF); existing
`tests/unit/combat/test_tactical_legality.py::test_tactical_legality_filtering` and any
kiting-distance test located via `grep -rl "kite\|KITING" tests/unit/tactical/
tests/unit/combat/` (test_plan.md's own required pre-implementation lookup — run this grep before
writing Step 4's tests to confirm the exact file set), plus any existing opportunity-attack/
disengagement test located via `grep -rl "skip_oa\|EVASIVE_SUCCESS\|opportunity_attack"
tests/unit/engine/ tests/integration/` must still pass unchanged with the flag OFF.

### Step 5 — Architecture guard: `PersonalityComponent` stays frozen
**Files:** new test file `tests/architecture/test_habit_bias_personality_frozen.py` (or extend an
existing file in `tests/architecture/` if a closer-fitting one exists — check via `ls
tests/architecture/ | grep -i "personality\|frozen"` before creating a new file)
**Change:** Add `test_personality_component_stays_frozen_after_habit_bias_wiring` (per
test_plan.md): assert no `PersonalityUpdate` type exists anywhere reachable from
`src/core/updates.py` (confirmed absent this session via
`grep -n "PersonalityUpdate" src/core/updates.py src/engine/patches.py` — zero matches), and that
Step 3/4's code changes introduce no new construction of `PersonalityComponent` with altered
field values. This is a pure test-only step — no production code change.
**Do NOT touch:** `PersonalityComponent`'s dataclass definition (`src/core/state.py:417-423`) —
this step only adds a regression guard, it does not modify the frozen dataclass.
**Verify:** the new test itself, run once to confirm it passes against Steps 1-4's actual diff.

## Scope Guards

- No discrete milestone-event mechanism (e.g. "three near-deaths fighting alone" event-counting
  state) — gradual-accumulation-only, confirmed final (see "Gradual-Only Confirmation" below).
- No new `WorldEventCategory` (e.g. `COMBAT_WIN`/`COMBAT_VICTORY`) or any other new event
  instrumentation to obtain a `success=True` signal for `record_outcome` — this plan wires
  `record_outcome` with `success=False` only, driven by the existing `COMBAT_LOSS` category.
- No change to `get_action_style_for_bravery`'s 3 construction-time call sites
  (`worldbuilding/compiler.py:466`, `entities/archetype_factory.py:111`,
  `worldassembly/entity_spawner.py:138`) or to `CombatComponent.action_style`'s
  construction-time-only write path — `SUB-381`'s already-verified behavior must stay
  bit-identical with the new flag OFF.
- No resurrection of the `attack_range`/EVASIVE-reposition sub-branches removed by
  `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` (`tactical.py:672`+) while editing the
  same function in Step 4a.
- No change to `movement.py`'s `skip_oa`/OA-resolution logic, `resolve_multi_attack` call, or the
  `escape_tag`/`combat_escape` observability block (`movement.py:194-206`+) while editing the same
  function in Step 4b — only the `style` value feeding the existing `action_style == 2` comparison
  changes.
- No change to `MemoryUpdatePhase.run()`/`.apply()` (`src/domains/memory/phase.py`) — habit-bias
  recording is a new, sibling phase (`HabitBiasUpdatePhase`), not an addition inside the existing
  memory phase, specifically so `ENABLE_MEMORY_UPDATE` and `ENABLE_HABIT_BIAS_ACTION_STYLE` stay
  independently toggleable and `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py`
  / `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` need no changes.
- No new `PersonalityUpdate` type or any other live mutation path for `PersonalityComponent`.
- Flag `ENABLE_HABIT_BIAS_ACTION_STYLE` must default OFF through every step, including test setup
  (explicit `overrides` constructor argument only, per `FeatureFlagManager.__init__`'s existing
  pattern — never flip the module-level default to exercise the ON path in a test).
- No `record_outcome`/`apply_habit_bias` formula changes (±0.1 clamp-to-[0,1], `(patterns[tag] -
  0.5) * 0.4` deviation scaling) — both are already shipped and correct per the investigation.

## Dependency Map

- Step 1 (flag) has no dependencies; Steps 3 and 4 both depend on it (both read the flag).
- Step 2 (shared constant) has no dependencies; Steps 3 and 4 both depend on it (both import
  `HABIT_PATTERN_COMBAT_ENGAGEMENT` to guarantee matching pattern IDs).
- Step 3 (write side) and Step 4 (read side, both 4a and 4b) are independently implementable and
  independently testable once Steps 1-2 land — Step 3's
  `test_record_outcome_wired_through_authoritative_pipeline` does not require Step 4, and Step 4's
  tests can be written against a manually-constructed `HabitMemory.patterns` fixture without
  running Step 3's pipeline phase. They must both land in the same ticket, however — per the
  investigation's Risk finding, Step 4 alone (read side only) is behaviorally inert without Step 3
  (nothing ever populates `habit.patterns`), and Step 3 alone (write side only) produces no
  observable gameplay effect without Step 4. Within Step 4, 4a and 4b have no dependency on each
  other (each reads `entity`/`state_or_context` independently) but both must land together — per
  this session's architecture-review resolution, shipping only 4a would create the exact flag-ON
  inconsistency (`tactical.py` live, `movement.py` stale) the review flagged. Recommended
  implementation order: 1, 2, 3, 4a, 4b, 5 (sequential is simplest given the shared constant and
  flag; 3 and 4 could be parallelized by two implementers but do not need to be).
- Step 5 (architecture guard) depends on Steps 3-4 existing (it asserts against their actual diff)
  but is otherwise independent of their internals.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Ticket explicitly corrects the atlas's "no scaffolding" premise and scopes as WIRING HabitBiasService, not building new accumulation state | Already satisfied in the ticket body (Request Summary) and this plan's Summary/Scope Guards — no code step | N/A (ticket-text AC, not a code AC) |
| `HabitBiasService.apply_habit_bias` gains at least one real production consumer at the ActionStyle bias point, closing the current zero-call-site gap | Step 4 (both 4a `tactical.py` and 4b `movement.py` — the ticket's "the ActionStyle bias point" spans both of `SUB-381`'s documented consumers, kept synchronized rather than wiring only one) | `test_habit_bias_shifts_action_style_when_flag_on`, `test_habit_bias_shifts_movement_oa_suppression_when_flag_on` |
| Mechanism is gated behind a FeatureMode flag, default OFF | Step 1 (flag definition), Step 3 + Step 4a + Step 4b (all read sites gated) | `test_habit_bias_action_style_flag_default_off`, `test_habit_bias_flag_off_preserves_construction_time_action_style`, `test_habit_bias_flag_off_preserves_movement_oa_suppression` |
| PersonalityComponent stays frozen/immutable; habit-accumulation state is applied only through the authoritative apply path | Step 3 (`entity_update.cognition_bundle_set`, never a direct `state.entities` mutation), Step 5 (guard) | `test_record_outcome_wired_through_authoritative_pipeline`, `test_personality_component_stays_frozen_after_habit_bias_wiring` |
| Ticket makes an explicit choice between gradual-accumulation-only vs. discrete milestone-event marks, not left ambiguous | Already resolved in this plan's Summary and "Gradual-Only Confirmation" below | N/A (ticket-text AC) |

Note: `apply_habit_bias` also needs `record_outcome` wired (Step 3) for AC2 to be non-inert per
the investigation's Risk finding — both steps together, not Step 4 alone, are what actually
"closes the zero-call-site gap" in an observable way. AC2's literal text names only
`apply_habit_bias`; Step 3 is included because an inert integration would satisfy the AC's letter
while contradicting its evident intent (a real, working habit-bias mechanic), which this plan's
Summary explains and this session's resolution of "Wiring shape" (Resolved Design Decisions item 1,
below) makes explicit rather than assumed.

## Anti-Drift Notes

- **`get_action_style_for_bravery` is a pure, reusable helper, not the wiring point.** The
  ticket's own Scope text names it as "the ActionStyle bias point," but per the investigation it
  runs only at entity construction, before any habit data can exist. Step 4 reuses the function
  unmodified as a pure `bravery -> ActionStyle` mapper, called a second time at each of its two
  live read sites (4a `tactical.py:491`, 4b `movement.py:185`) — it does not add a habit
  parameter to the function itself, which would be a no-op at its 3 existing construction-time
  call sites and would force those call sites to pass a meaningless empty-`HabitMemory` argument
  for no benefit.
- **`tactical.py` and `movement.py` must stay synchronized under the flag — wiring only one is a
  regression, not a smaller/safer version of this ticket.** `SUB-381` and
  `get_action_style_for_bravery`'s own docstring both name these two call sites as reading the
  same `ActionStyle` value. If a future edit touches only one of Step 4a/4b (e.g. "just fix the
  kiting behavior" or "just fix opportunity-attack suppression"), it recreates the exact flag-ON
  inconsistency this session's architecture review caught — resist any drift toward treating the
  two consumers as separable follow-up work.
- **`cognition_bundle_set` is a shared, multi-writer field — read-through discipline is
  load-bearing, not optional.** Step 3's writer enumeration above is the concrete anti-drift
  guard: any future edit to `HabitBiasUpdatePhase` that switches it to reading fresh from
  `state.entities` (matching `MemoryUpdatePhase.run()`'s internal shape instead of
  `NearDeathHardeningPhase.apply()`'s) would silently drop `NearDeathHardeningPhase`'s and
  `quests.py`'s same-tick cognition writes for any entity this phase also touches, once the ticket
  correlates `combat_loss` triggers with near-death events on the same entity in the same tick
  (both draw from `state.recent_world_events`/combat resolution).
- **No win-signal exists without new instrumentation — do not let this gap "sneak in" a new
  `WorldEventCategory` mid-implementation.** If Step 3's implementer is tempted to add a
  `COMBAT_WIN` category to make the mechanism feel more complete, stop — that is a new
  accumulation/instrumentation surface explicitly out of scope per the ticket's Out of Scope
  section ("Building a new discrete milestone-event accumulation mechanism" is the named
  exclusion, but a new win-event category is the same class of scope expansion by the ticket's
  own "not building new accumulation state" framing in Scope).
- **`ENABLE_MEMORY_UPDATE` and `ENABLE_HABIT_BIAS_ACTION_STYLE` must stay independently OFF/ON
  toggleable.** Nesting Step 3's phase inside `MemoryUpdatePhase` (gated only by
  `ENABLE_MEMORY_UPDATE`) was considered and rejected — it would make habit-bias recording
  silently inert whenever `ENABLE_MEMORY_UPDATE` is OFF (its current default), an unwanted
  coupling to an unrelated flag's rollout state.
- **Determinism.** Neither `record_outcome` nor `apply_habit_bias` introduce RNG (confirmed
  unchanged formulas, Step 2). The new phase's trigger-event iteration must stay
  deterministically ordered — reuse `_memory_trigger_events`'s existing order (built by
  `pipeline.py`'s list comprehension over `state.recent_world_events`, itself tick-ordered) rather
  than iterating over an unordered structure.

## Resolved Design Decisions (per this session's directed resolution)

1. **Wiring shape:** Option (a) — both `record_outcome` (Step 3, real writer) and a live
   `apply_habit_bias`-based re-derivation at both real runtime consumers of `ActionStyle`
   (`tactical.py:491`, Step 4a, and `movement.py:185`, Step 4b). This is the only shape that makes
   AC1 (apply_habit_bias production consumer) and the investigation's own non-inertness
   requirement simultaneously true, per the Acceptance Criteria Map note above.
2. **Trigger and read-site locations:** `record_outcome` fires from the existing `combat_loss`
   `WorldEventCategory` signal already computed at `src/engine/pipeline.py:149-153` (no new event
   kind); the live re-derivation happens at both of `ActionStyle`'s documented real consumers —
   `src/engine/tactical.py:491` (`TacticalDecisionSystem.evaluate_entity_intent`, the confirmed
   real runtime consumer at line 631) and `src/engine/movement.py:185`
   (`MovementSystem.resolve_move`'s opportunity-attack-suppression check on a `RETREAT`-mode,
   EVASIVE-style entity) — not at any of `get_action_style_for_bravery`'s 3 construction-time call
   sites.
3. **Authoritative apply-path chain:** `HabitMemory` (frozen, `src/core/cognition.py:291-297`) →
   `MemoryModel.habit` (`cognition.py:324`) → `CognitionModel.memory` → written back only via
   `EntityUpdate.cognition_bundle_set` (`src/core/updates.py:660`, `Optional[Any]`, whole-bundle
   replace semantics confirmed at `updates.py:719`) → consumed at Persistence by
   `src/engine/patches.py:748-749` (`CognitionPatch`). No new Update dataclass field is needed —
   `cognition_bundle_set` already accepts a full replacement `CognitionModel`, and Step 3 builds
   one via `dataclasses.replace()` exactly as `NearDeathHardeningPhase`/`MemoryUpdatePhase` already
   do. No silent-drop point: Step 3's writer-enumeration in Step 3 above traces every other writer
   to this same field and confirms all of them (including the new one) read the incoming value
   through before replacing, which is what prevents the double-write/silent-drop failure class
   this session's CLASS-TIER-BRANCHING/CREATURE-TERRITORY-LIFECYCLE tickets hit.
4. **Gradual-only confirmed.** Discrete milestone-event marks (e.g. "three near-deaths fighting
   alone") are explicitly out of scope — no new event-counting/threshold-crossing state is added
   anywhere in this plan; `HabitMemory.patterns` remains the sole state, updated by the existing
   ±0.1-per-outcome gradual formula only.
5. **Flag gating pattern:** direct `state`/`state_or_context` `.feature_flags` dict reads at all
   three call sites (Step 3's `run_phase(..., "ENABLE_HABIT_BIAS_ACTION_STYLE")` in `pipeline.py`;
   Step 4a's `flags.get("ENABLE_HABIT_BIAS_ACTION_STYLE", "OFF") == "ON"` in `tactical.py`; Step
   4b's identical `flags.get(...)` check in `movement.py`, reading `state_or_context.feature_flags`
   defensively via `getattr(..., None) or {}` since that parameter is typed `Any` rather than
   `AuthoritativeState`), not `FeatureFlagManager` injection into either `tactical.py` or
   `movement.py` — matching the existing per-entity, per-tick precedent at
   `src/ai/goals/scorers.py:253`, confirmed this session.
6. **Parity ledger entries:** `STRAT-262` (next free ID after the existing final entry `STRAT-261`
   in `docs/parity_ledger/strategic_cognition.yaml`, confirmed via this session's own scan of the
   file). To be added by the Parity phase (`parity-updater` agent) after implementation, per the
   investigation's "Docs Requiring Update" section: `status: verified`, `priority: P2`,
   `test_path` pointing at Step 4's new tests (both 4a's and 4b's), describing the
   habit-bias-into-ActionStyle wiring as new gameplay behavior (flag-gated OFF by default), not a
   correctness fix to existing shipped behavior. Additionally, `SUB-381`
   (`docs/parity_ledger/substrate.yaml:4523-4537`, `status: verified`, `priority: P1`) must be
   updated in the same Parity phase pass — not left as-is — because its `text` describes both
   `tactical.py` and `movement.py` as reading "2 real, already-wired combat-behavior consumers" of
   the same `ActionStyle` value; once this ticket lands (flag ON), that value is live-re-derived
   identically at both consumers (Step 4a/4b), so `SUB-381`'s `v2_evidence` should gain a note that
   the two consumers stay synchronized under the new flag, and its `status`/`priority` are
   unaffected (still `verified`/`P1` — the construction-time, flag-OFF behavior `SUB-381`
   originally verified is unchanged bit-for-bit). `docs/mechanics/04_strategic_cognition.md`'s §6.3
   "ActionStyle wiring" subsection (lines 431-442) and `docs/simulation/domains/emotion_contract.md`
   also need updates — handled by the Docs-Update phase (`doc-updater` agent), not this plan's code
   steps, but the required *content* of those updates is specified here so the doc-updater agent
   does not have to re-derive it:
   - `04_strategic_cognition.md` §6.3's new subsection must state that both `tactical.py` and
     `movement.py` consumers now re-derive `ActionStyle` live from habit-biased bravery when
     `ENABLE_HABIT_BIAS_ACTION_STYLE` is ON, replacing (for that computation only) the
     construction-time value described in the paragraph immediately above it. It must also state,
     per this session's non-blocking review finding, that because `record_outcome` can only ever
     be called with `success=False` in this ticket (Step 3's Summary/Anti-Drift Notes: no win/
     victory `WorldEventCategory` exists), `habit.patterns["combat_engagement"]` is a **monotonic
     one-way decay** from its 0.5 neutral baseline toward a 0.0 floor, with **no recovery path** —
     not a bidirectional bias that can climb back toward 1.0 — until a future ticket adds a
     success-signal writer.
   - `docs/simulation/domains/emotion_contract.md` line 46 (`- Action outcome (success/failure) →
     'HabitBiasService.record_outcome'`) must be corrected: this bullet is a **pre-existing
     inaccuracy that predates this ticket** — every sibling bullet in the same list explicitly
     states "no production call site wired yet" where true, but this bullet has always omitted
     that qualifier despite `record_outcome` having had no production caller until this ticket's
     Step 3. Correct it to read accurately for both before-and-after states this ticket spans: prior
     to this ticket, no production call site existed; as of this ticket (flag ON only), Step 3's
     `HabitBiasUpdatePhase` is the first production caller, `success=False`-only per the
     monotonic-decay note above.
7. **`movement.py:185` scope decision (architecture-review resolution):** Option A — extend Step 4
   to also live-re-derive `style` at `movement.py:185`, not just `tactical.py:491`. `SUB-381`
   (`substrate.yaml:4523-4537`) and `get_action_style_for_bravery`'s own docstring
   (`personality.py:66-75`) both explicitly pair `tactical.py` and `movement.py` as the same
   ticket's 2 wired consumers of the same `ActionStyle` value — leaving `movement.py` reading only
   the frozen construction-time field while `tactical.py` reads a live habit-biased value would
   create an undisclosed flag-ON inconsistency between two consumers both authoritative sources
   describe as reading "the same" wiring. Verified before choosing this option, not assumed:
   `movement.py:27-32`'s `resolve_move(state_or_context: Any, entity: EntityState, ...)` signature
   was read this session. `entity` is the same full `EntityState` type used in `tactical.py`, so
   `entity.cognition.memory.habit`/`entity.identity.personality.bravery` are available identically
   to Step 4a — no entity-side gap. `state_or_context: Any` is looser than `tactical.py`'s
   `state: AuthoritativeState`, but Step 4b's flag read reuses the same defensive
   `getattr(state_or_context, "feature_flags", None) or {}` fallback Step 4a already uses, so a
   caller passing a context object without `feature_flags` safely resolves to flag-OFF (the
   conservative default) rather than erroring. No genuine data-availability or safety gap was
   found that would justify Option B (scoping `movement.py` out); Option A is adopted in full,
   with no divergence-note or SUB-381-inaccuracy exposure remaining.

## Deviations (recorded during Implement)

- **Step 2/4 import path inconsistency, resolved in favor of Step 2's explicit placement
  instruction.** Step 2 above explicitly says `HABIT_PATTERN_COMBAT_ENGAGEMENT` lives "directly
  in habit_service.py," but the Step 4a/4b code snippets show
  `from src.domains.emotion.habit_phase import HABIT_PATTERN_COMBAT_ENGAGEMENT` -- a
  plan-internal inconsistency (Step 3's own `habit_phase.py` code never re-exports the constant).
  Implementation kept the constant's single source of truth in `habit_service.py` (per Step 2)
  and imported it from there in `tactical.py`, `movement.py`, and `habit_phase.py` alike, rather
  than adding a re-export in `habit_phase.py` that Step 3's own code snippet never showed. No
  behavioral difference; avoids an unnecessary re-export layer.
- All other steps (1, 3, 4a, 4b, 5) landed exactly as specified, including the pipeline
  placement (strictly after `memory_update`, before `self_model`), the
  read-through-then-replace shape (`NearDeathHardeningPhase` pattern, not `MemoryUpdatePhase`),
  and both 4a/4b consumers wired together in the same run.
