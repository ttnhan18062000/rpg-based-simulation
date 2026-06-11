---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Engine Performance Improvement Plan

Goal:

```text
Improve large-entity performance without breaking the correctness-first architecture.
```

Main idea:

```text
Do not optimize randomly.
First measure.
Then reduce unnecessary work.
Then add scheduling, dirty tracking, spatial indexing, and LOD.
```

---

# Milestone 0 — Baseline Performance Measurement

## Objective

Before changing engine behavior, measure current limits.

You need to know:

```text
How many entities can the engine handle now?
Which phase is slow?
How much memory is used?
Does memory grow over time?
Does concurrency help or hurt?
```

## Technical tasks

### 0.1 Add performance profiles

Create:

```text
src/perf/profiles.py
```

Profiles:

```text
PERF_512MB_LOCAL
PERF_1GB_LOCAL
PERF_2GB_LOCAL
PERF_4GB_LOCAL

PERF_512MB_CONC
PERF_1GB_CONC
PERF_2GB_CONC
PERF_4GB_CONC
```

Each profile controls:

```text
max_ram_mb
max_worker_count
max_tick_budget_ms
max_queue_depth
max_replay_buffer_kb
max_observability_budget_percent
```

Recommended starting values:

```text
512 MB, 1 GB, 2 GB, 4 GB
workers: 0 and 4
tick budget: 50 ms
queue depth: 1000
replay buffer: 8 MB
```

---

### 0.2 Add benchmark scenarios

Create:

```text
src/perf/scenarios.py
```

Scenario builders:

```text
build_idle_state(entity_count)
build_movement_state(entity_count)
build_combat_state(team_size)
build_resource_state(entity_count, node_count)
build_strategic_state(entity_count)
build_mixed_state(entity_count)
```

Start with only:

```text
idle
resource-heavy
mixed
```

Then add the rest.

---

### 0.3 Enhance `BenchHarness`

Current `BenchHarness` already measures basic tick performance.

Enhance it to collect:

```text
avg_tick_compute_ms
p50_tick_compute_ms
p95_tick_compute_ms
p99_tick_compute_ms
max_tick_compute_ms
avg_tps
peak_rss_mb
memory_delta_mb
memory_trend_mb_per_tick
phase_breakdown
worker_utilization
queue_utilization
replay_backlog_kb
```

Important:

```text
BenchHarness should only measure.
It should not decide pass/fail.
```

---

### 0.4 Add `tests/perf`

Create:

```text
tests/perf/
  conftest.py
  test_perf_idle.py
  test_perf_resource.py
  test_perf_mixed.py
  test_perf_api_snapshot.py
```

Mark all tests:

```python
@pytest.mark.perf
```

Do not run them with normal unit tests.

Run separately:

```bash
pytest tests/perf -m perf -q
```

---

## Exit criteria

You should have:

```text
reports/perf/latest.json
```

with numbers for:

```text
IDLE_100
IDLE_500
IDLE_1000
IDLE_5000
RESOURCE_1000
MIXED_1000
```

For each profile:

```text
512 MB
1 GB
2 GB
4 GB
```

---

# Milestone 1 — Choose Realistic Runtime Profiles

## Objective

You said current profiles are too low and you can use up to 4 GB.

This milestone finds the smallest good profile instead of guessing.

---

## Technical tasks

### 1.1 Run profile matrix

Test these combinations:

```text
IDLE_1000:
  512 MB
  1 GB
  2 GB
  4 GB

IDLE_5000:
  512 MB
  1 GB
  2 GB
  4 GB

RESOURCE_1000:
  1 GB
  2 GB
  4 GB

MIXED_1000:
  1 GB
  2 GB
  4 GB
```

For each, record:

```text
p95 tick ms
peak RSS
memory delta
phase breakdown
worker utilization
```

---

### 1.2 Define profile decision rules

A profile is acceptable if:

```text
p95 tick < 50 ms
peak RSS < 75% of max RAM
memory_delta is stable
no conformance failure
no replay backlog growth
```

Example:

```text
1 GB profile:
  Accept if peak_rss < 750 MB

2 GB profile:
  Accept if peak_rss < 1500 MB

4 GB profile:
  Accept if peak_rss < 3000 MB
```

---

### 1.3 Update runtime profile defaults

After measurement, define:

```text
DEFAULT_PROFILE
LARGE_WORLD_PROFILE
STRESS_PROFILE
CERTIFICATION_PROFILE
```

Recommended likely starting point:

```text
DEFAULT_PROFILE:
  2 GB RAM
  4 workers
  50 ms tick budget

STRESS_PROFILE:
  4 GB RAM
  4 or 8 workers
  50 ms tick budget
```

But only set this after measurement.

---

## Exit criteria

You can answer:

```text
For 1000 entities, use profile X.
For 5000 entities, use profile Y.
4 GB is needed only when scenario Z exceeds 2 GB.
```

---

# Milestone 2 — Add System Cadence Scheduling [STATUS: COMPLETE]

## Objective

Stop running deep systems every tick for every entity.

This is usually the biggest performance win.

---

## Current problem

The engine has many deep mechanisms:

```text
strategic cognition
detour suggestion
social memory
world dynamics
ecology
shops
resources
lifecycle
groups
combat
movement
replay
observability
```

Not all of them need to run every tick.

---

## Target design

Add a system cadence model:

```text
critical systems: every tick
fast systems: every 2-5 ticks
strategic systems: every 10 ticks
world systems: every 50-100 ticks
```

---

## Technical tasks

### 2.1 Add system cadence config

Create:

```text
src/engine/cadence.py
```

Example:

```python
@dataclass(frozen=True)
class SystemCadence:
    movement: int = 1
    combat: int = 1
    interaction: int = 1
    resource_transactions: int = 1

    shop: int = 5
    town_resolution: int = 5
    lifecycle: int = 10
    groups: int = 5

    strategic_intelligence: int = 10
    concern_evaluation: int = 10
    detour_suggestion: int = 10
    social_memory: int = 20

    world_dynamics: int = 50
    ecology: int = 100
    boss_spawn: int = 100
```

---

### 2.2 Add cadence helper

```python
def should_run(tick: int, entity_id: int | None, cadence: int) -> bool:
    if cadence <= 1:
        return True

    if entity_id is None:
        return tick % cadence == 0

    return (tick + entity_id) % cadence == 0
```

This avoids all entities running strategic cognition on the same tick.

---

### 2.3 Apply cadence to strategic systems first

Start with:

```text
StrategicIntelligenceSystem.evaluate_strategic_intent
evaluate_all_concerns
StrategicRedirectionSystem
DetourSuggestionSystem
```

Do not cadence movement/combat yet.

Reason:

```text
Strategic cognition is expensive and does not need every-tick updates.
```

---

### 2.4 Add tests

Add:

```text
tests/unit/core/test_system_cadence.py
```

Tests:

```text
should_run returns true every N ticks
entity_id staggers execution
cadence=1 always runs
```

Add integration test:

```text
tests/integration/pipeline/test_strategic_cadence.py
```

Test law:

```text
Strategic update does not run every tick unless force=True.
force=True bypasses cadence.
Different entities evaluate on staggered ticks.
```

---

## Exit criteria

Strategic systems no longer run for every entity every tick.

Benchmark should show:

```text
strategic-heavy scenario p95 improves
mixed scenario p95 improves
no strategic correctness tests fail
```

---

# Milestone 3 — Dirty Entity Tracking [STATUS: COMPLETE]

## Objective

Only process entities affected by relevant changes.

---

## Current problem

Many systems likely scan:

```text
all entities
all groups
all resources
all buildings
```

even when only a few things changed.

---

## Target design

Introduce dirty sets:

```text
dirty_movement_entities
dirty_combat_entities
dirty_inventory_entities
dirty_strategic_entities
dirty_social_entities
dirty_group_entities
dirty_regions
dirty_resources
```

---

## Technical tasks

### 3.1 Add `DirtySet`

Create:

```text
src/engine/dirty.py
```

```python
@dataclass
class DirtySet:
    movement_entities: set[int] = field(default_factory=set)
    combat_entities: set[int] = field(default_factory=set)
    inventory_entities: set[int] = field(default_factory=set)
    strategic_entities: set[int] = field(default_factory=set)
    social_entities: set[int] = field(default_factory=set)
    group_ids: set[int] = field(default_factory=set)
    region_ids: set[str] = field(default_factory=set)
    resource_node_ids: set[int] = field(default_factory=set)
```

---

### 3.2 Derive dirty sets from `StateUpdate`

Create helper:

```python
DirtySet.from_update(state, update)
```

Rules:

```text
new_position/navigation changed
  → movement dirty

combat changed
  → combat dirty
  → group dirty
  → strategic dirty if near-death/death

inventory changed
  → inventory dirty
  → strategic dirty if full/empty/resource blocker

strategic changed
  → strategic dirty

social changed
  → social dirty

group_id changed
  → group dirty

region/world changed
  → region dirty
```

---

### 3.3 Use dirty sets in selected systems

Start with:

```text
GroupSystem
ShopSystem
StrategicIntelligenceSystem
Resource-related checks
```

Do not change everything at once.

Example:

```text
ShopSystem should only check:
- entities on shop tile
- entities with inventory dirty
- entities that moved into shop tile
```

---

### 3.4 Add tests

Tests:

```text
inventory update marks inventory dirty
combat death marks group dirty
movement update marks movement dirty
strategic update marks strategic dirty
dirty set is deterministic
```

Integration:

```text
ShopSystem still sells when inventory dirty.
GroupSystem dissolves group when leader combat dirty.
Strategic detour triggers when blocker dirty.
```

---

## Exit criteria

Benchmarks show fewer scans.

Expected improvement:

```text
resource-heavy
strategic-heavy
mixed
```

---

# Milestone 4 — Spatial Index Consistency [STATUS: COMPLETE]

## Objective

Avoid full-world scans for proximity queries.

---

## Current problem

Any logic that does this is dangerous:

```python
for entity in state.entities.values():
    distance(...)
```

This becomes expensive at large entity counts.

---

## Target design

Use spatial index for:

```text
nearby entities
nearby resource nodes
nearby buildings
nearby corpses/items
region lookup
occupancy lookup
```

---

## Technical tasks

### 4.1 Audit full scans

Search:

```bash
grep -R "for .* in state.entities.values" -n src
grep -R "for .* in state.resource_nodes.values" -n src
grep -R "for .* in state.buildings.values" -n src
```

Classify each scan:

```text
acceptable small global scan
should use spatial index
should use dirty set
should run by cadence
```

---

### 4.2 Add shared spatial query service

Create or centralize:

```text
src/engine/spatial_query.py
```

API:

```python
class SpatialQueryService:
    def entities_near(state, position, radius) -> list[int]: ...
    def resource_nodes_near(state, position, radius) -> list[int]: ...
    def buildings_near(state, position, radius) -> list[int]: ...
    def occupied_tiles(state) -> dict[tuple[float, float], int]: ...
```

Internally use:

```text
SpatialHashV2
SpatialGrid
cached per tick
```

---

### 4.3 Cache spatial index per state/tick

Avoid rebuilding repeatedly.

Simple cache key:

```text
state.tick
state.movement_count
entity_count
```

Better:

```text
state.spatial_version
```

If not available, start with per-tick cache.

---

### 4.4 Replace high-cost scans

Prioritize:

```text
movement/occupancy
tactical target selection
resource searching
goal scorers
group coordination
town/service lookup
```

---

### 4.5 Tests

Tests:

```text
spatial query returns same result as brute-force
spatial query deterministic ordering
spatial index invalidates after movement_count changes
spatial query excludes inactive/dead entities where needed
```

Performance tests:

```text
1000 entity nearby query must be faster than brute-force baseline
```

---

## Exit criteria

Large movement/combat/resource scenarios improve.

You should see lower phase cost for:

```text
movement
tactical
resource
strategic goal scoring
```

---

# Milestone 5 — API and Replay Snapshot Optimization [STATUS: COMPLETE]

## Objective

Avoid copying or serializing too much state every tick.

---

## Current likely issue

API manager currently deep-copies state every tick.

That is safe but expensive for large worlds.

---

## Target design

```text
minimal snapshot every tick
full snapshot only on request
paged/filtered inspect endpoint
compact replay deltas
bounded trace storage
```

---

## Technical tasks

### 5.1 Replace full deepcopy with snapshot DTO

Current behavior concept:

```python
self._latest_state = copy.deepcopy(state)
```

New behavior:

```python
self._latest_minimal_snapshot = StatePresenter.present_minimal(state)
```

Add:

```python
get_snapshot()
get_full_snapshot()
```

Keep `get_state()` only for internal/debug if needed.

---

### 5.2 Full inspect should be on-demand

For `/api/v1/inspect`:

```text
do not maintain full copy every tick
generate from current state under lock
or generate paged DTO
```

Better API:

```text
/api/v1/state              minimal
/api/v1/entities?offset=&limit=
/api/v1/entity/{id}
/api/v1/regions
/api/v1/groups
```

---

### 5.3 Bound replay and traces

Check these collections:

```text
transaction_trace
latest_intent_results
rejection_events
replay buffer
diagnostic history
strategic memory
```

Add limits:

```text
max_transaction_trace_per_tick
max_intent_results_per_entity
max_rejection_events_per_tick
max_replay_buffer_kb
```

---

### 5.4 Tests

Tests:

```text
API snapshot does not expose mutable AuthoritativeState
minimal snapshot update is below budget for 1000 entities
full inspect can page entities
replay buffer respects size limit
transaction trace is bounded
```

---

## Exit criteria

API and replay overhead does not grow linearly without control.

Benchmark:

```text
API snapshot for 1000 entities < target ms
API snapshot for 5000 entities still acceptable
memory_delta stable
```

---

# Milestone 6 — Work Batching and Worker Policy

## Objective

Reduce overhead from per-entity work items.

---

## Current issue

Large entity counts can create many small work items:

```text
one packet per entity
one result per entity
many merges
many events
```

This overhead can dominate.

---

## Target design

Batch by work kind:

```text
movement batch
combat batch
resource batch
strategic batch
lifecycle batch
```

---

## Technical tasks

### 6.1 Add work batch model

```python
@dataclass(frozen=True)
class WorkBatch:
    work_kind: str
    work_class: WorkClass
    owner_ids: tuple[int, ...]
    payload_by_owner: dict[int, dict]
```

---

### 6.2 Add batching policy

Batch when:

```text
same work_kind
same work_class
same tick
same region/chunk if useful
```

Do not batch:

```text
unique scripted action
high-priority single action
debug/audit exact source needed
```

---

### 6.3 Local vs concurrent threshold

Do not use concurrent path for tiny batches.

Add policy:

```text
if work_count < 50:
    use local
else:
    use concurrent
```

Make configurable:

```text
concurrency_min_batch_size
```

---

### 6.4 Tests

Tests:

```text
small batch uses local executor
large batch uses concurrent executor
batched and unbatched results are equivalent
batch result ordering is deterministic
```

Performance tests:

```text
1000 movement work items local vs concurrent
batching reduces collection phase cost
```

---

## Exit criteria

Worker collection phase improves in large scenarios.

---

# Milestone 7 — LOD / Background Simulation [STATUS: PARTIAL - STAGGERED PASSIVE]

## Objective

Support thousands of entities by not fully simulating everyone.

---

## Target design

Entity simulation levels:

```text
LOD 0: full simulation
LOD 1: active simplified
LOD 2: background abstracted
LOD 3: dormant
```

---

## LOD rules

### LOD 0 — Full

Runs:

```text
movement
combat
interaction
inventory
strategic cognition
social contracts
group coordination
```

Used for:

```text
near player/camera
active combat
quest-critical entities
recently interacted entities
```

---

### LOD 1 — Simplified active

Runs:

```text
movement
combat simplified
resource simplified
strategic every 50 ticks
```

Used for:

```text
active region but not immediately important
```

---

### LOD 2 — Background

Runs:

```text
abstract resource gain/loss
abstract combat outcome
strategic every 100-500 ticks
```

Used for:

```text
distant regions
offscreen groups
```

---

### LOD 3 — Dormant

Runs:

```text
nothing except scheduled wake condition
```

Used for:

```text
inactive/dead/sleeping/far-away entities
```

---

## Technical tasks

### 7.1 Add LOD component or property

Option:

```text
entity.lifecycle.simulation_lod
```

or:

```text
entity.identity.properties["simulation_lod"]
```

Better:

```text
LifecycleComponent.simulation_lod
```

---

### 7.2 Add LOD classifier

```python
SimulationLODService.classify(entity, state) -> SimulationLOD
```

Inputs:

```text
distance to active focus
region activity
combat state
quest relevance
recent events
group role
```

---

### 7.3 Gate systems by LOD

Example:

```text
LOD 0: all systems
LOD 1: skip deep strategic/social
LOD 2: abstract systems only
LOD 3: skip
```

---

### 7.4 Add tests

Tests:

```text
combat entity becomes LOD 0
inactive entity becomes LOD 3
quest-critical entity stays LOD 0
far idle entity becomes LOD 2
LOD classification is deterministic
```

Integration:

```text
LOD does not break deterministic replay
LOD entities can wake up when event happens
```

---

## Exit criteria

Mixed 5000 entity scenario becomes feasible under 4 GB.

---

# Milestone 8 — ApplyPath and State Update Efficiency [STATUS: COMPLETE]

## Objective

Reduce object churn in the hottest apply path.

---

## Current concern

The engine uses immutable replacement heavily. That is good for correctness but can be expensive.

Do not remove immutability globally.

---

## Target design

```text
immutable at phase boundaries
mutable local accumulators inside phases
single final StateUpdate merge
single final apply pass
```

---

## Technical tasks

### 8.1 Profile ApplyPath first

Add micro-benchmark:

```text
ApplyPath applying 1000 EntityUpdates
ApplyPath applying 5000 EntityUpdates
```

Measure:

```text
time
allocations if possible
memory delta
```

---

### 8.2 Optimize merge patterns

Look for repeated patterns:

```python
replace(entity, ...)
replace(update, ...)
dict copy many times
list copy many times
```

Improve by:

```text
local mutable maps
single dict copy
skip no-op updates
avoid replace if field unchanged
```

---

### 8.3 Add no-op detection

Before applying:

```text
if EntityUpdate is empty:
    skip
```

Add:

```python
EntityUpdate.is_noop()
StateUpdate.compact()
```

---

### 8.4 Tests

Tests:

```text
compact removes no-op entity updates
compact preserves semantic updates
apply_generation same before/after optimization
```

Performance:

```text
ApplyPath 5000 no-op updates stays below target
```

---

## Exit criteria

Apply/advancement phase cost improves without changing behavior.

---

# Milestone 9 — CI Performance Regression Guard

## Objective

Prevent future performance regression.

---

## Technical tasks

### 9.1 Add baseline file

```text
reports/perf/baseline.json
```

Contains:

```text
scenario_id
profile
p95_tick_compute_ms
peak_rss_mb
memory_delta_mb
phase_breakdown
```

---

### 9.2 Add regression comparison

Tolerance:

```text
30% initially
15% later
```

Rules:

```text
p95 tick cannot regress > 30%
peak RSS cannot regress > 30%
memory delta cannot regress > 30%
```

---

### 9.3 Add CI job

Do not run on every commit first.

Run:

```text
nightly
manual
release candidate
```

GitLab example:

```yaml
perf_tests:
  stage: test
  rules:
    - if: '$RUN_PERF == "true"'
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  script:
    - pytest tests/perf -m perf -q
    - python scripts/run_perf_baseline.py
  artifacts:
    paths:
      - reports/perf/
```

---

## Exit criteria

Performance regression becomes visible before release.

---

# Milestone 10 — Tune Final Profiles [STATUS: COMPLETE]

## Objective

After optimization, define production-ready profiles.

---

## Final profile examples

### Small profile

```text
RAM: 1 GB
Workers: 2
Target: up to 500 entities
Tick budget: 50 ms
```

### Normal profile

```text
RAM: 2 GB
Workers: 4
Target: 1000-2000 entities
Tick budget: 50 ms
```

### Large profile

```text
RAM: 4 GB
Workers: 4-8
Target: 5000+ entities with LOD
Tick budget: 50 ms
```

### Certification profile

```text
RAM: 4 GB
Workers: fixed
Replay: enabled
Observability: enabled
Tick budget: stricter
```

---

# Recommended execution order

Do not do all milestones at once.

Recommended order:

```text
Milestone 0: Baseline measurement
Milestone 1: Profile selection
Milestone 2: Cadence scheduling
Milestone 3: Dirty tracking
Milestone 4: Spatial indexing
Milestone 5: API/replay snapshot optimization
Milestone 6: Worker batching
Milestone 7: LOD
Milestone 8: ApplyPath optimization
Milestone 9: CI regression guard
Milestone 10: Final profile tuning
```

---

# First 3 implementation tasks to start now

## Task 1

Add:

```text
src/perf/profiles.py
src/perf/scenarios.py
```

With only:

```text
idle scenario
resource scenario
512MB / 1GB / 2GB / 4GB profiles
```

---

## Task 2

Enhance:

```text
src/perf/bench_harness.py
```

To output:

```text
p95
p99
max
RSS
memory delta
phase breakdown
```

---

## Task 3

Add:

```text
tests/perf/test_perf_idle.py
tests/perf/test_perf_api_snapshot.py
scripts/run_perf_baseline.py
```

Then run:

```bash
pytest tests/perf -m perf -q
python scripts/run_perf_baseline.py
```

After that, inspect `reports/perf/latest.json`.

That report decides whether you should optimize:

```text
strategic cadence
dirty tracking
spatial indexing
API snapshot
worker batching
ApplyPath
```

not guess.
