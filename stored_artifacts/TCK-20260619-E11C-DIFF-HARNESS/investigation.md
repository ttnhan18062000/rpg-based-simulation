---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260619-E11C-DIFF-HARNESS
artifact_type: investigation
tags: [entity-differentiation, test-harness, behavioral-quality, integration, phase-1]
---

# Investigation — TCK-20260619-E11C-DIFF-HARNESS
# E11-C · Build 400-tick differentiation test harness

---

## N-tick Execution Pattern

**Authoritative pattern** from `tests/integration/kernel/test_long_run_determinism.py`:

```python
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG

profile = RuntimeProfile(
    name="differentiation-test",
    hardware_class=HardwareClass.CLASS_B,
    max_ram_mb=1024,
    max_cpu_percent=100.0,
    max_worker_count=1,
    max_queue_depth=1000,
    max_replay_buffer_kb=0,
    max_observability_budget_percent=0.0,
    max_tick_budget_ms=100.0
)

rng = DeterministicRNG(seed)
kernel = Kernel(profile, initial_state, rng)
for _ in range(400):
    kernel.tick_once()
state = kernel.state   # AuthoritativeState after 400 ticks
```

`kernel.tick_once()` mutates `kernel._state` in-place (frozen dataclass replaced via
`object.__setattr__`). After the loop, `kernel.state` (property) returns the live
`AuthoritativeState`. There is no `advance_n_ticks` helper — the loop pattern above is the
canonical approach.

**Key flag**: `flags={"no_replay": True}` can be passed to skip replay buffer I/O for test
speed. `flags={"audit_mode": True}` enables `transaction_trace` accumulation across ticks
(see below), but is NOT required for this harness (route data comes from entity state).

---

## Route-Kind Data Source

### Primary source: `entity.strategic.projects` (per-entity, durable)

After each tick, the winning goal kind is written into a `ProjectState` on the entity's
`StrategicComponent`:

```python
# src/systems/strategic_systems/intelligence.py ~L1300
candidate_proj = ProjectState(
    id=f"proj_{cand_kind_str}_{current_tick}",
    kind=best_candidate.kind,   # GoalKind enum value, e.g. GoalKind.COMBAT_ENGAGE
    ...
)
```

**Access path** from a final `AuthoritativeState`:

```python
for entity in state.entities.values():
    for proj in entity.strategic.projects.values():
        if proj.kind == GoalKind.COMBAT_ENGAGE:
            # entity chose combat_engage at least once
```

**Limitation**: `StrategicComponent.projects` is a dict keyed by project `id`; a project may
persist across multiple ticks (lock_until_tick + 10). It records *which goals were selected
and became projects*, not a tick-by-tick histogram.

### Secondary source: `entity.strategic.current_project_id` (live pointer)

`StrategicComponent.current_project_id` holds the ID of the currently active project. Its
`kind` field gives the current route-kind. Sampling this at every tick would yield a per-tick
histogram, but requires hooking mid-loop.

### Histogram construction approach (recommended for the harness)

The cleanest approach for a 400-tick harness is to collect snapshots **inside** a
tick-level callback. The kernel emits `SimulationEvent` objects through
`self._entity_timeline_store` (type `EntityTimelineStore`). However, these only retain the
last N events (LIGHT mode = 20, DEBUG = 500). For 400 ticks × N entities this will overflow.

**Recommended approach** — manual per-tick sampling via a thin wrapper loop:

```python
from collections import defaultdict

# project_kind_history[entity_id] = list of GoalKind values (one per tick)
project_kind_history: dict[int, list[str]] = defaultdict(list)

rng = DeterministicRNG(seed)
kernel = Kernel(profile, initial_state, rng, flags={"no_replay": True})
for _ in range(400):
    kernel.tick_once()
    for eid, ent in kernel.state.entities.items():
        cur_proj_id = ent.strategic.current_project_id
        if cur_proj_id and cur_proj_id in ent.strategic.projects:
            kind = ent.strategic.projects[cur_proj_id].kind
            project_kind_history[eid].append(
                kind.value if hasattr(kind, "value") else str(kind)
            )
        else:
            project_kind_history[eid].append(None)
```

`kind.value` will be the string `"combat_engage"` (GoalKind enum is `str, Enum`).

### transaction_trace — NOT useful for route histogram

`AuthoritativeState.transaction_trace: List[str]` is populated only in `audit_mode=True`
and only when `apply.py` is in audit path. It contains economic/resource transfer strings
(from `economy.py`), NOT goal-selection events. It does NOT record per-entity route choices.
Confirmed: the only writes are via `update.transaction_trace` in `StateUpdate`, which is
populated by the economy pipeline, not the strategic intelligence pipeline.

### entity_timeline_store — secondary confirmation only

`kernel.entity_timeline_store.get_entity_timeline(entity_id)` returns `List[SimulationEvent]`
with `event_type` strings (e.g. `"combat_loss"`, `"died"`, `"failed_action"`). These are
observability events, not goal-selection events. The intelligence system logs goal selection
only to `logger.debug(...)` — it does NOT emit a `SimulationEvent`. Not reliable for
histogram collection at 400-tick scale (LIGHT mode retention = 20 events max).

---

## combat_engage Definition

**Exact string**: `"combat_engage"`
**Enum**: `GoalKind.COMBAT_ENGAGE = "combat_engage"` in `src/core/strategic.py` line 111.
**Scorer**: `CombatEngageScorer` registered at `src/ai/goals/__init__.py` line 14.
**Pipeline phase**: `"combat_engagement"` phase in `src/engine/pipeline.py` line 183, gated by
feature flag `"ENABLE_COMBAT_ENGAGEMENT"`.

A `"combat_engage"` route means a `ProjectState` with `kind=GoalKind.COMBAT_ENGAGE` was
selected as the best scoring goal for an entity in a given tick. It corresponds to the entity
choosing to move toward and engage a nearby hostile entity.

**Feature flag risk**: `ENABLE_COMBAT_ENGAGEMENT` defaults to `OFF` in
`src/domains/optimization/feature_flags.py`. It is enabled in rollout profiles
`FULL_FEATURED` and `EXTENDED_FEATURED` (`src/domains/optimization/rollout_profiles.py`
lines 61, 75). The harness must ensure this flag is enabled, either via:
- Passing `initial_state = replace(initial_state, feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"})`
- Or using a rollout profile that includes it

---

## PersonalityComponent Bravery Quartile Calculation Approach

`PersonalityComponent` fields (all `float`, range 0.0–1.0):
- `greed`, `bravery`, `sociability`, `industry`

Field path: `entity.identity.personality.bravery`

**Quartile split**:

```python
import statistics

alive_entities = [e for e in state.entities.values() if e.combat.alive]
bravery_values = [(e.id, e.identity.personality.bravery) for e in alive_entities]
bravery_values.sort(key=lambda x: x[1])

n = len(bravery_values)
q1_cutoff = n // 4
q3_cutoff = 3 * n // 4

bottom_quartile_ids = {eid for eid, _ in bravery_values[:q1_cutoff]}
top_quartile_ids    = {eid for eid, _ in bravery_values[q3_cutoff:]}
```

**Bravery → CombatEngageScorer formula** (`src/ai/goals/scorers.py` line 119-120):

```
utility = 40.0 + bravery * 40.0 + stamina_bonus (up to 20.0)
```

- `bravery=1.0` → utility ≈ 80.0 (always above the 20.0 threshold to become a project)
- `bravery=0.0` → utility = 40.0 (still above threshold, but lower than competing goals)

**Important constraint**: `CombatEngageScorer` returns `utility=0.0` if no hostile neighbors
are within radius=10.0. The world must have hostile entities in proximity to HERO entities
for the scorer to return non-zero values. `sandbox_world` has 5 monsters (faction=`monsters`)
and 3 heroes (faction=`villagers`) — they will be hostile to each other.

**Expected 2× rate**: With bravery=1.0 the COMBAT_ENGAGE utility = 80.0; with bravery=0.0
it = 40.0. Other competing goals (FATIGUE, HUNGER, HARVESTING) score 0.0–50.0 depending on
biological state. The 2× rate ratio may require calibration (E11D) to reliably achieve.
This is why E11C marks the assertion `@pytest.mark.xfail(strict=False)` until E11D is done.

---

## Mechanics / Engine Constraints

- **Tick loop**: `Kernel.tick_once()` is the only authoritative tick entry point (kernel.md,
  6-phase loop: Init → Governance → Scheduling → Packetization → Resolution → Persistence).
- **Feature flags**: Pipeline phases are gated; `ENABLE_COMBAT_ENGAGEMENT` must be active.
- **Project lock**: `lock_until_tick=current_tick + 10` means once `combat_engage` becomes
  a project, it persists for 10 ticks. The histogram will show runs of `combat_engage`, not
  isolated ticks.
- **Interruption resistance**: Projects use retention bonus logic; a project must be beaten by
  a significant margin to be replaced (docs/mechanics/04_strategic_cognition.md §2).
- **Hostile proximity**: `CombatEngageScorer` requires a hostile within radius=10.0. If
  monsters and heroes start far apart, early ticks will yield 0 utility.
- **Entity kind**: `sandbox_world` has `role: hero` entities. The E11A prerequisite ensures
  these have `PersonalityComponent` with distinct bravery values seeded by E11A.
- **State immutability**: `AuthoritativeState` is frozen; `kernel.state` returns the current
  immutable snapshot. Read-only access is safe.

---

## Parity Ledger Overlap

### strategic_cognition.yaml

- **STRAT-001** – Strategic state survives across ticks. The `projects` dict persisting
  `combat_engage` kind is the exact mechanism this harness relies on. No update needed.
- **STRAT-002** – `current_project_id`/`current_objective_id` continuity. Directly used in
  the histogram sampling logic. No update needed.
- **STRAT-003** – Project switching uses interruption resistance. Relevant to why combat_engage
  rate may not be proportional to utility alone. No update needed.
- **No new parity entries required** for the harness itself. The harness is purely a test
  consumer of existing verified behavior.

### infrastructure.yaml

- **INFRA-005** – Strategy observability consistency. The harness is the first test that
  directly measures per-entity strategic route rates. If the harness exposes a gap between
  what the inspector reports and what `projects` dict shows, INFRA-005 would need a test_path
  update.
- **INFRA-006** – Strategic decision driver traceability. Currently `legacy_verified` with no
  test_path. The harness indirectly validates that goal selection flows into `ProjectState`
  on the entity — could be cited as new evidence once the harness passes.

**No existing parity entries require immediate updates.** The harness validates behavior
already marked `verified`; it is additive evidence. If E11D calibration changes the scoring
formula (`CombatEngageScorer`), then no parity entries exist for the bravery coefficient
formula specifically — a new parity entry (e.g. `STRAT-NEW-bravery-combat-rate`) would be
needed at that point.

---

## Prior Work

- **TCK-20260527-COG-GOAL-REGISTRY** (done): Introduced `combat_engage`, `combat_retreat`,
  `recover`, `resolve_blocker` scorers into GoalRegistry. This is the foundation the harness
  measures.
- **TCK-20260528-COG-PHASE4-COMBAT** (done): Implemented Phase 4 Combat Engagement Cognition.
  `CombatEngagementDecisionService` is a separate service from `GoalKind.COMBAT_ENGAGE` —
  they are parallel but distinct systems. The goal scorer drives route selection; the
  CombatEngagementDecisionService drives posture (ENGAGE/PROBE/WATCH/AVOID).
- **TCK-20260619-E11A-HERO-AUTHORING** (prerequisite — inprogress or open): Must complete
  first to ensure HERO entities exist in sandbox_world with distinct personality vectors.
- **TCK-20260619-E11B-OBS-SNAPSHOT** (prerequisite): Must complete first to ensure
  `EntityInspectionSnapshot.personality` dict is populated (already implemented in current
  `entity_inspector.py`, so E11B may extend further).
- **D01 audit** `docs/audits/D01_rpg_feature_impact.md §"Personality → Long-Run Behavior Calibration"`:
  Describes this exact gap — no long-run behavioral differentiation test exists. E11C directly
  closes it.

---

## Risks and Open Questions

1. **Feature flag default is OFF**: `ENABLE_COMBAT_ENGAGEMENT` defaults to `FeatureMode.OFF`.
   If the harness builds an `AuthoritativeState` without setting `feature_flags`, no
   `combat_engage` events will ever fire. **Resolution**: Set
   `feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"}` in the initial state, or compile the
   world with a rollout profile that enables it.

2. **sandbox_world has no HERO entities yet (E11A prerequisite)**: Until E11A is complete,
   `sandbox_world` does not have HERO entities with distinct bravery distributions. The harness
   will need to either mock entities or depend on E11A completion. For
   `test_no_identical_personality_vectors_at_spawn`, E11A is strictly required.

3. **Entity proximity**: Monsters spawn in `woods` region (50–110), heroes in `town_center`
   (10–40). At tick 0 they are far apart; `CombatEngageScorer` returns 0.0 until they close
   range. The harness may need 400 ticks of natural movement or should place entities in
   proximity via test world spec.

4. **Quartile size**: With only 3 HERO entities in `sandbox_world`, quartile computation
   yields 0 or 1 entity per quartile. Consider using a test-specific WorldSpec with 8+ HERO
   entities with explicit bravery values (4 high, 4 low) rather than relying on sandbox_world.

5. **bravery seeding from E11A**: The harness depends on E11A to seed distinct personality
   vectors. If E11A seeds randomly within a narrow range, the quartile split may not produce
   meaningful bravery divergence. Investigation of E11A seeding contract needed.

6. **Project kind vs current_project_id**: A project persists with `lock_until_tick`. An
   entity might have a `combat_engage` project in `projects` dict from an earlier tick but
   `current_project_id` pointing to a different project. The histogram must track
   `current_project_id` → `projects[current_project_id].kind`, not just scan `projects`.

---

## Anti-Drift Hazards

- **Do not use `transaction_trace` for route histogram** — it is economic audit data, not
  goal-selection data. The ticket's Implementation Notes hint at this but the data structure
  contains transfer strings, not route-kind strings.
- **Do not use `entity_timeline_store` events for histogram** — LIGHT mode has 20-event
  retention cap; at 400 ticks this will lose >95% of events. Use direct `kernel.state`
  introspection in the tick loop.
- **Do not scan `projects` dict post-hoc** — only the `current_project_id` chain reflects
  per-tick choices. Scanning all projects would count a single project that lasted 50 ticks
  as one occurrence, not fifty.
- **Do not test against sandbox_world entity counts directly** — with 3 heroes, quartile math
  breaks. The test should use a custom minimal world spec with explicit entity bravery
  assignments.
- **Do not enable `audit_mode`** for the 400-tick run — it accumulates `transaction_trace`
  which is unbounded and will degrade performance with no benefit for this harness.
