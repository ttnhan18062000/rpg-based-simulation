# Investigation — TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

## Storage: `CognitionModel.memory.combat.opponent_stats`

`src/core/cognition.py`'s `CombatMemory` dataclass:

```python
@dataclass(frozen=True, slots=True)
class CombatMemory:
    """Phase 4 Combat memory Shell."""
    opponent_stats: Mapping[str, Any] = field(default_factory=dict)
```

This is a real, existing, unclaimed field — "Phase 4" is this codebase's own historical phase
number for combat_engagement (see `tickets/done/TCK-20260528-COG-PHASE4-COMBAT.md`, "Implement
Phase 4 - Combat Engagement Cognition"). Confirmed via full-repo grep
(`grep -rn "CombatMemory\|memory\.combat\b\|opponent_stats" src/ tests/`) that **zero** other code
anywhere reads or writes this field — a genuine, previously-reserved-but-never-filled placeholder,
matching this arc's own repeated "already exists, unreachable" pattern.

`docs/simulation/domains/memory_contract.md` (the `src/domains/memory/` domain's own contract) never
mentions `combat`/`opponent_stats`/`CombatMemory` anywhere — confirming this field sits outside that
domain's write-scope, so retyping and writing to it does not conflict with the Memory Contract's own
"What It Must NOT Mutate" list or violate domain ownership.

**Decision**: retype `opponent_stats: Mapping[str, Any]` → `Mapping[str, OpponentModel]`
(`src/domains/combat_engagement/schema.py`'s existing type). This is the correct home per §13.6's
own reasoning (neither Memory-domain state nor `KnowledgeFact`) and requires no new field, no schema
migration risk beyond a type-narrowing on an already-empty-by-default field.

## Update mechanism: `EntityUpdate.cognition_bundle_set`

`src/core/updates.py`'s `EntityUpdate.cognition_bundle_set: Optional[Any] = None` is a whole-
`CognitionModel`-replace field (mirrors `self_model_bundle_set`'s own pattern for `self_model`).
Applied via `src/engine/patches.py`'s `CognitionPatch` — `changes["cognition"] = self.cognition_bundle_set`
on merge.

The real, working precedent for a read-modify-write cycle through this field is
`src/domains/memory/phase.py`'s `MemoryUpdatePhase.apply()`:

```python
new_entity_updates[new_entity.id] = replace(entity_up, cognition_bundle_set=new_entity.cognition)
```

— read `entity.cognition`, `dataclasses.replace()` the relevant nested sub-model, set the WHOLE new
`CognitionModel` via `cognition_bundle_set`. This is the template this ticket's own storage-write
wiring follows in `CombatEngagementPhase.apply()`.

## Real per-tick call site: `CombatEngagementPhase.apply()`

`src/domains/combat_engagement/phase.py` is the only real pipeline call site
(`src/engine/pipeline.py:315`, `run_phase("combat_engagement", ..., "ENABLE_COMBAT_ENGAGEMENT")`).
It already does real hostility-filtered nearest-target selection and calls
`CombatEngagementDecisionService.evaluate(actor, target, state)` — **with no `memory=` argument**.
Confirmed via grep: `CombatEngagementDecisionService.evaluate()`'s own `memory: Optional[OpponentModel]
= None` default is never overridden by any real caller anywhere in the codebase. This is exactly the
gap §13.6 names: "Enabling `ENABLE_COMBAT_ENGAGEMENT` alone would not produce memory — every tick
would pass `memory=None` again."

`CombatEngagementPhase.apply()` already builds a per-actor `EntityUpdate` every tick it evaluates a
hostile (property_updates for posture, `StrategicUpdate` for the `combat_risk` belief). The new
`cognition_bundle_set` write needs to merge into that SAME per-actor update, not overwrite it.

## `OpponentPerceptionService.estimate()` — current formula (to be replaced)

`src/domains/combat_engagement/perception.py`:
- Power term: `base_power = float(target_lvl * 20.0)` — the exact term §13.2 disproves via the real
  214-entity/5-world sample (every entity compiles at `evolution_level == 1`).
- HP-ratio condition adjustment (`hp_ratio < 0.3: *= 0.6`, `< 0.7: *= 0.85`) — this IS §13.2's
  `apparent_power()` concept already coded; keep, just name/extract it.
- Uncertainty: flat `if perception < 4: uncertainty += 0.15` — the exact threshold §13.3 replaces
  with power-gap-driven uncertainty.
- Dead code confirmed: `intel = getattr(attrs, "intelligence", 5)` at line 85 is read and never used
  anywhere else in the function — real, disclosed defect per §13.3's own citation.
- Memory blending (lines 73-80) already correctly blends `base_power` with `memory.estimated_power`
  when a real `OpponentModel` is passed — this logic is CORRECT already, it just never receives a
  real memory today (see call-site gap above). No change needed to this blending logic itself, only
  to what `base_power` is before blending (the true/apparent power fix) and to what feeds it a real
  `memory` (the storage wiring).

## `SelfCombatEstimateService` — confirmed NOT the observer's side of the gap

`src/domains/combat_engagement/self_estimate.py`'s `SelfCombatEstimate` is a condition-adjusted
self-power estimate (HP/stamina/equipment modifiers), used today by
`EngagementRiskEvaluator.evaluate()`'s `power_ratio = self_est.estimated_power /
opponent_est.estimated_power` for `win_confidence`/`death_risk`. This is a legitimate, different,
already-correct concern (how strong am I RIGHT NOW for this fight) — §13.2's law ("an entity's own
strength enters the gap as `true_power`, never as an estimate") applies specifically to the
OBSERVATION-error gap in §13.3, computed at perception time, not to this post-decision risk
calculation. Confirmed: no change needed to `self_estimate.py` or its consumer in
`risk_evaluator.py`; the new `gap` calculation in `perception.py` calls `true_power(actor)` directly,
a new, separate helper — not `SelfCombatEstimateService.estimate()`.

## `CombatLearning.learn()` — confirmed zero real call site

`src/domains/combat_engagement/learning.py`'s `CombatLearning.learn(memory, subject_key, outcome,
observed_damage, observed_skills, tick)` takes `outcome: str` in `{"WON_EASY", "LOST", "FLED",
"NEAR_DEATH"}` (its own docstring) — no vocabulary match exists anywhere in the real combat
resolution path today.

`src/engine/combat.py`'s `CombatResolutionSystem` (the real, authoritative combat resolver —
`resolve_attack()`, `resolve_skill_usage()`, `resolve_multi_attack()`, `resolve_aoe_attack()`) is the
actual per-tick combat outcome producer. Its `CombatUpdate.outcome_kind` real values:
`SURVIVE | KILL | DEFEAT | REBIRTH | PERMADEATH | REJECTED | SUCCESS`. No existing mapping from
these to `CombatLearning`'s own vocabulary exists. `SocialUpdate.combat_loss_delta={attacker.id: 1}`
(set on the DEFENDER's own `SocialUpdate` when `not alive`) is the one real, already-wired signal
this repo derives from a real combat outcome today (feeds `combat_loss_counts`, read by
`CombatEngagementDecisionService.evaluate()`'s own fear-avoidance branch) — the shape to follow for
wiring `CombatLearning.learn()` in similarly, from the same real resolution call sites, updating
BOTH participants' `OpponentModel`s (attacker learns about defender from `KILL`/`DEFEAT`/`SURVIVE`
outcome + damage dealt; defender learns about attacker from the same event, from the receiving side).

## Witnessed-combat third tier — confirmed buildable, no new field

Confirmed per §13.7: combat-resolution `SimulationEvent`s (`combat_damage`, `entity_killed`,
`combat_resolved` — real producers in `src/observability/event_shapers.py`) already carry real
`entity_id`/`attacker_id` (in `payload`) and `tick`. Positions are already on
`state.entities[...].navigation.position`. The same perception-radius neighbor scan §13.1 already
uses (`SimulationDomainLogic.get_neighbor_view()`) applies unchanged to a witness check — no new
event field needed, confirmed.

## Determinism precedent

`src/worldassembly/resolver.py:947`'s `_hash_point_in_bounds()`:
```python
hashlib.sha256(key.encode()).digest()
```
No RNG object. This is the exact pattern the new power-gap noise term must follow, keyed on
`(seed, tick, observer_id, observed_id)`.

## Feature flag

`src/domains/optimization/feature_flags.py:31`: `"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF` — the
single flip point, done last per peer direction.
