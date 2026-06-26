---
status: active
layer: simulation
authority: P1
audience: agent
tags: [audit, behavioral-emergence, simulation-quality, stasis, rejections, quest-system, economy, root-cause-confirmed]
---

# D03 — Behavioral Emergence Quality

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` |
| **Impact** | 5 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 10 |
| **Method** | run-sim + code-read |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Do entities in the simulation behave like RPG characters — pursuing goals, completing quests, using resources, trading, fighting — or do they fall into a repetitive loop of rejected actions? This audit extended into code-read investigation after run-sim data revealed stasis. The root causes of the stasis are now confirmed at the source level.

**Related dimensions:**

| Dimension | Relationship |
|---|---|
| D07 (Content Coverage) | Zero quest activity directly caused by F5 (no wired opportunity feed), not only D07 F1 |
| D10 (Test Coverage) | F2 (ItemStack.position bug) causes final_integrity overruns at ticks 35, 100, 105, 130, 191 |
| D06 (Long-Run Health) | Blocked — running D06 now would reproduce identical stasis; fix F5 first |
| D04 (Balance & Tuning) | Blocked — zero economic output makes tuning analysis impossible until F5 is resolved |

---

## Scoring Method — Emergence Gap Score

Each finding is scored as: **Variety Gap × Lifespan Gap × System Silence**

| Axis | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **Variety Gap** | Many goal kinds observed | 3-4 distinct kinds | 2 kinds | 1 kind, minimal variety | Zero variety, pure stasis |
| **Lifespan Gap** | Active for full run | Active for 75%+ of ticks | Active for 50%+ | Active for <25% | Collapses before tick 20 |
| **System Silence** | Multiple systems produce output | 2-3 systems active | 1 system marginally active | 1 system active for <5 ticks | All systems silent after tick 7 |

Maximum score: 15 (worst).

---

## Pre-condition Bug

Before any simulation could run, `data/worlds/sandbox_world/world.yaml` had a schema error: `quest_definitions: []` (line 53) instead of `quests: []`. `WorldTemplateSpec` (`recipe.py:87`) declares the field as `quests:`; `extra="forbid"` caused an immediate ValidationError on start.

Fixed: renamed the field in the YAML. `WorldTemplateExpander` maps `quests → quest_definitions` internally (`recipe.py:140`).

---

## Run Summary

| Metric | Seed 42 (ticks 1-100) | Seed 42 (ticks 101-200) | Seed 137 (ticks 1-100) | Seed 137 (ticks 101-200) |
|---|---|---|---|---|
| Alive avg | 15.3 | 15.0 | 15.43 | 15.0 |
| Active avg | 20.0 | 20.0 | 20.0 | 20.0 |
| Rejections (cumulative) | 94 | 194 | 426 | 926 |
| Sim events | 8 | 0 | 9 | 0 |
| Quests active | 0.0 | 0.0 | 0.0 | 0.0 |

**Last behavioral event:** tick 7 (seed 42), tick 20 (seed 137).

Both runs: LifecycleOutcome.SUCCESS, governor stays NORMAL, zero hard law violations, deterministic state hash.

**Note on rejection counter:** `rejections` in metric_windows reflects `state.rejection_registry`, a cumulative dict that never resets within a run (`engine/apply.py:259-260`). It is written by `engine/interaction.py:87`, `engine/pipeline_phases/movement.py:270`, and `engine/economy.py:150,224` — not by the adventure phase, which defers silently.

---

## Root Cause Analysis

Code investigation following the run-sim phase confirmed four compounding structural causes for the stasis. These are not hypotheses — each is confirmed at the source level.

### RC1 — Dead pipeline link: `AdventureDecisionPhase` never calls `ResourceOpportunityProvider` (PRIMARY)

> **RESOLVED: TCK-20260619-RC1 (2026-06-19):** AdventureDecisionPhase now passes opportunities= to generate(); primary route loop executes every tick.

**Files:** `src/domains/adventure/phase.py:60`, `src/domains/adventure/generator.py:47-48`

```python
# phase.py:60 — actual call
candidates = AdventureRouteGenerator.generate(hero, state)

# generator.py:28 — signature
def generate(entity, state=None, opportunities=()):

# generator.py:47 — primary route path
for opp in opportunities:   # ← loops zero times, every entity, every tick
    ...
```

`ResourceOpportunityProvider` (`src/world/providers/resources.py`) is a fully implemented class that reads live resource node state and returns `Opportunity` objects. It is **never imported or called** from `AdventureDecisionPhase`. The `opportunities` parameter defaults to an empty tuple and is never populated.

The generator's primary path (lines 47-82) — which maps visible opportunities to route families (`GATHER_RESOURCE`, `BUY_UPGRADE`, `CRAFT_UPGRADE`, etc.) — executes zero iterations for every entity on every tick.

Only structural defaults fire:
- `RECOVER` if entity has `low_health` or `healing` in perceived weaknesses/needs
- `ASK_INFORMATION` if entity has `weak_weapon` or `equipment_improvement` needs
- `DEFER_WITH_REASON` for all other cases (healthy entities with no known weakness)

`DEFER_WITH_REASON` results are silently skipped at `phase.py:66`:
```python
if not result.selected or result.selected.family == RouteFamily.DEFER_WITH_REASON:
    continue
```
No project update is written. No tactical action is queued. The engine produces zero output and reports SUCCESS.

### RC2 — `near_service` requirement hardcoded to `"hometown"`, always fails in sandbox_world (COMPOUNDING)

> **RESOLVED: TCK-20260619-RC1 (2026-06-19):** region_id == "hometown" hardcode removed; requirement checks actual region.

**File:** `src/world/providers/requirements.py:152-158`

```python
current_region = getattr(entity.navigation, "region_id", None) or "hometown"
if current_region == "hometown":
    near = True
```

`RequirementEvaluator.evaluate()` for `kind="near_service"` returns `True` only if `current_region == "hometown"`. `sandbox_world` uses region IDs `"town_center"` and `"woods"` — neither equals `"hometown"`. Every `near_service` requirement fails for every sandbox_world entity.

`ResourceOpportunityProvider` attaches `Requirement(kind="near_service", subject=current_region)` to every resource opportunity (line 76). This means every generated opportunity would be blocked by the requirement evaluator, even if RC1 were fixed.

### RC3 — `PerformanceBudgets` class-level counter: would cap opportunity provision at tick ~25 (COMPOUNDING)

> **RESOLVED: TCK-20260619-RC1 (2026-06-19):** provider_calls_total reset each tick; opportunity provider no longer exhausts at tick ~25.

**File:** `src/world/providers/resources.py:34-35`, `src/world/providers/requirements.py:24-36`

```python
class PerformanceBudgets:
    provider_calls_total: int = 0  # class-level, shared across all entities and ticks

# ResourceOpportunityProvider.get_opportunities():
if PerformanceBudgets.provider_calls_total > 500:
    return []
```

`PerformanceBudgets` is a class with class-level attributes. At 20 entities per tick, the 500-call budget would exhaust at tick 25 — coinciding with the observed stasis onset. If RC1 and RC2 were fixed, RC3 would terminate all opportunity provision at tick 25.

`PerformanceBudgets.reset()` exists but no evidence it is called between runs or at tick start. Between runs in the same process, the counter would not reset, making the second run immediately return empty.

### RC4 — Rejection cascade is from stale spawn-projects, not adventure deferrals (DIAGNOSTIC CLARIFICATION)

**Files:** `src/engine/interaction.py:86-88`, `src/engine/pipeline_phases/movement.py:270`, `src/engine/economy.py:149-151`

The 194-926 cumulative rejections in `rejection_registry` do NOT come from the adventure phase (which defers silently, never writing to `rejections_delta`). They come from entities with **stale initial-spawn projects** that were assigned at world assembly: entities try to execute project objectives, which fail legality/movement/economy checks, and each failure increments `rejections_delta[reason]`.

The monotonic increase between windows (seed 137: 426 → 926) is explained by this mechanism: without RC1 being fixed, no new projects are assigned, so entities keep retrying the same stale objectives indefinitely. The counter grows monotonically because there is no cooldown or adaptation mechanism.

Seed 137 having 4.8× more rejections than seed 42 (926 vs 194) is consistent with placement sensitivity: entities that spawn in more constrained positions generate more invalid movement/interaction intents from their initial projects.

---

## Findings

### F1 — Behavioral Stasis: Onset by Tick 20

> **RESOLVED: TCK-20260619-RC1 (2026-06-19):** Behavioral stasis eliminated. D06 1,000-tick run confirmed 240–253 events per run with last event at tick 997/999; pipeline active from tick ~201 onward.

**Score: 15/15** (Variety Gap=5, Lifespan Gap=5, System Silence=5) *(pre-fix observation)*

**Root cause confirmed: RC1 (dead pipeline link).**

Both seeds enter complete behavioral stasis within the first 20 ticks and hold it for the remaining 180-193 ticks. The engine considers all 20 entities "active" (processes each through the goal-selection pipeline) but produces zero committed actions.

- Seed 42: last event at tick 7. 193 ticks of silence.
- Seed 137: last event at tick 20. 180 ticks of silence.

The stasis is mechanically explained: healthy entities with no perceived weaknesses receive `DEFER_WITH_REASON` from the route generator every tick, which is silently skipped without producing any project update or tactical action. The simulation runs to completion while appearing to process 20 active entities per tick.

**Evidence:** `simulation_events.jsonl` shows all events in ticks 3-20, then empty for the remaining ~190 lines. `adventure/phase.py:60` confirmed to call generator with no opportunities argument.

---

### F2 — Zero Output from Economy, Quest, and Resource Systems

> **RESOLVED: TCK-20260619-RC1, TCK-20260619-E21-RESOURCE-ECOLOGY (2026-06-19/20):** urban_political runs now produce `town_return`, `harvesting`, and `combat_engage` routes (D08 F4). Food-kind resource nodes added; hunger satiation no longer permanently suppresses economic goals (D06 F1 resolved).

**Score: 12/15** (Variety Gap=5, Lifespan Gap=5, System Silence=4) *(pre-fix observation)*

**Root cause confirmed: RC1 + RC2.**

| System | Seed 42 output | Seed 137 output |
|---|---|---|
| Quests (active) | 0.0 | 0.0 |
| Resource nodes (charges) | 0 changes | 0 changes |
| Economy (gold) | 0.0 avg | 0.0 avg |
| Trade events | 0 | 0 |
| Entity movement | 9 moves total | 12 moves total |

The quest, resource, and economic systems are all structurally dependent on the adventure routing pipeline producing non-DEFER outcomes. Since the route generator never receives opportunities (RC1), and any opportunity that did arrive would be blocked by the `near_service` region check (RC2), these systems have no mechanism to activate.

Combat did fire early (5 `combat_damage` events, seed 42 ticks 3-7), confirming the combat legality pipeline is functional. Combat was triggered from initial spawn adjacency, not from adventure routing — this explains why it stops at tick 7 (monsters die, combat targets exhausted).

---

### F3 — Rejection Cascade: Cumulative 194–926 Rejections per Run

**Score: 9/15** (Variety Gap=3, Lifespan Gap=3, System Silence=3) *(revised down from 11/15 — cause is now understood, not a deeper systemic failure)*

**Root cause confirmed: RC4 (stale spawn-projects retrying forever).**

The rejection counter (`state.rejection_registry`) is cumulative and written by the interaction, movement, and economy layers — not by the adventure phase. It represents stale initial-spawn projects continuously retrying objectives that fail legality or movement checks.

| Run | Total rejections (tick 200) | Rate (per tick) |
|---|---|---|
| Seed 42 | 194 | 0.97 |
| Seed 137 | 926 | 4.63 |

The 4.8× variance between seeds is placement-sensitive: seed 137's initial entity positions produce more invalid intents from their spawn-assigned projects. The monotonic increase (never decreasing) confirms no adaptation or cooldown mechanism exists for stale projects.

This is a consequence, not an additional root cause. Once RC1 is fixed and entities receive fresh project assignments each tick, stale-project rejections would stop accumulating.

---

### F4 — Entity Attrition Without Replenishment

**Score: 7/15** (Variety Gap=3, Lifespan Gap=2, System Silence=4)

5 of 20 entities die within the first ~15 ticks (count stabilises at 15). No entity is spawned, recruited, or replaced at any point in either 200-tick run.

For a 200-tick evaluation window this is manageable, but D06 (long-run health) must assess whether attrition-without-replacement causes entity count to approach zero over 1,000+ tick runs. With no productive goal pipeline (RC1), surviving entities have no mechanism to recruit or revive allies.

---

### F5 — `ObservabilityMode` Naming Mismatch: STANDARD ≠ Richer Data

**Score: 8/15** (Variety Gap=3, Lifespan Gap=3, System Silence=2)

Investigation revealed that `src/lab/orchestrator.py:147-153` maps all three lab-level modes to engine-level LIGHT:
```python
obs_mode_mapping = {
    "LIGHTWEIGHT": ObservabilityMode.LIGHT,
    "MINIMAL":     ObservabilityMode.LIGHT,
    "STANDARD":    ObservabilityMode.LIGHT,  # ← same as LIGHT
    "LONG_RUN":    ObservabilityMode.LONG_RUN
}
```

The engine's `ObservabilityMode` enum has richer modes (`NORMAL`, `FULL`, `RESEARCH`, `DEBUG`) that enable `OBS_BEHAVIOR_NORMALIZATION`, `OBS_BEHAVIOR_TIMELINE`, `OBS_BEHAVIOR_METRICS`, and cognition snapshots. These are inaccessible from the lab pipeline. The only available upgrade is `LONG_RUN`, which adds behavior normalization and metrics but still caps cognition snapshots to anomaly-only.

Cognition snapshots (which would expose entity project, blockers, and concerns per tick) only fire in `DEBUG` or `CERTIFICATION` mode via env var `SIM_OBS_MODE=DEBUG`.

The practical impact: a developer trying to diagnose stasis by switching to "STANDARD" mode would receive identical output to "LIGHTWEIGHT". The D03 initial recommendation to "switch to STANDARD mode" was incorrect — the correct diagnostic is `SIM_OBS_MODE=DEBUG` via env var, not a lab observability setting.

---

## Key Findings Summary

| Finding | Score | Description |
|---|---|---|
| F1 | 15/15 | Behavioral stasis onset tick 7-20 — root cause RC1 confirmed |
| F2 | 12/15 | Zero economy/quest/resource output — root cause RC1+RC2 confirmed |
| F3 | 9/15 | 194-926 cumulative rejections — stale spawn-projects retrying, not a deeper failure |
| F4 | 7/15 | 25% entity attrition with no replenishment mechanism |
| F5 | 8/15 | STANDARD lab mode maps to LIGHT engine mode — diagnosis tooling gap |

**Positive observations:**
- Both 200-tick runs complete with LifecycleOutcome.SUCCESS and zero hard law violations
- Final state hash is deterministic across multiple runs of same seed
- Governor stays NORMAL; no emergency throttling
- Average tick compute 12-13ms (well within 50ms budget)
- `ResourceOpportunityProvider` implementation is correct — only wiring is missing
- `RequirementEvaluator` logic is correct — only the `"hometown"` hardcode is wrong
- Combat legality pipeline confirmed functional (5 events in early ticks)

---

## Recommended Follow-Up

**P0 — Wire `ResourceOpportunityProvider` into `AdventureDecisionPhase`**
`src/domains/adventure/phase.py:60` must call `ResourceOpportunityProvider.get_opportunities(hero, state)` before calling the route generator, and pass the result as `opportunities=`. This is a 3-line change that unlocks the entire primary path in the route generator. Verify by re-running sandbox_world and checking that `GATHER_RESOURCE` routes appear in entity projects.

**P0 — Fix `near_service` region fallback in `RequirementEvaluator`**
`src/world/providers/requirements.py:152-158`: replace the `if current_region == "hometown"` hardcode with a check against the actual service registry or building catalog for the entity's current region. Until fixed, all resource opportunities generated by `ResourceOpportunityProvider` will be blocked regardless of wiring.

**P1 — Add `PerformanceBudgets.reset()` call at run start**
`src/world/providers/requirements.py:32-36`: confirm `reset()` is called at the start of each simulation run. If runs share a process (e.g. sweep or mutation lab), the class-level counter accumulates across runs and would terminate opportunity provision immediately from the second run onward.

**P1 — Add stale-project cooldown or timeout**
Entities with stale projects keep retrying rejected objectives indefinitely. Add a max-retry count or tick-expiry to `ProjectState` such that a project is abandoned after N consecutive rejections or M ticks without progress.

**P2 — Expose `DEBUG` mode via a Makefile target**
Add `make sim-debug` that sets `SIM_OBS_MODE=DEBUG`. Currently, the only way to get cognition snapshots is via raw env var, which is undiscoverable. A documented target would make root-cause diagnosis accessible without reading the source.

---

## Related Dimensions

- **D07** (Content Coverage) — quest and content gaps are secondary; the primary gate is RC1 (no opportunity wiring)
- **D10** (Test Coverage) — F2 (ItemStack.position bug) explains final_integrity overruns; RC1 explains why no harvest tests fired in the live pipeline
- **D06** (Long-Run Health) — blocked until RC1 is fixed; running now would reproduce identical stasis for 1,000 ticks
- **D04** (Balance & Tuning) — blocked; zero economic output until RC1+RC2 are resolved
