---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Real-world scenarios when profile resources hit limits

Current design is basically:

```text
PressureSignals
→ ResourceGovernor
→ RuntimeMode
→ GovernorPolicy
→ subsystems should reduce work
```

This is a good foundation, but the real-world behavior depends on whether every expensive subsystem actually obeys the policy.

---

# Scenario 1 — Entity count grows too large

Example:

```text
A long-running world keeps spawning monsters, NPCs, corpses, ground items, camps, resource nodes, and groups.
```

## What may happen

Memory slowly increases:

```text
entities
corpses
ground_items
transaction_trace
strategic projects/leads/blockers
replay buffers
API snapshots
```

Eventually:

```text
memory_estimate_mb >= profile.max_ram_mb
```

Then governor enters:

```text
SURVIVAL
```

## Current pros

```text
Good:
- Governor can detect memory pressure.
- SURVIVAL policy disables optional behavior conceptually.
- Replay can be turned off by policy.
- Diagnostics can be muted.
- Concurrency can be reduced.
```

## Current cons

```text
Weak:
- Detection does not automatically reclaim memory.
- Existing entities/items/corpses remain in memory.
- If world spawning systems do not obey policy, memory can keep growing.
- API deepcopy/full inspect can still be expensive if not gated.
```

## Improvements

```text
1. Add spawn backpressure:
   - no new non-critical entities in DEGRADED/SURVIVAL
   - no new camps/bosses/ambient NPCs under pressure

2. Add cleanup priority:
   - remove expired corpses
   - compact ground items
   - clean old transaction traces
   - trim strategic memories/leads/concerns

3. Add LOD:
   - distant entities become background/dormant
   - dormant entities do not run deep logic

4. Add memory recovery action:
   - Survival mode should actively free nonessential state.
```

---

# Scenario 2 — CPU spike from strategic cognition

Example:

```text
1000 entities all have projects, blockers, leads, concerns, contracts, source trust, and detour logic.
```

## What may happen

The tick becomes slow:

```text
tick_compute_ms >= max_tick_budget_ms
```

Then:

```text
DEGRADED
```

If worse:

```text
tick_compute_ms >= max_tick_budget_ms * 1.5
→ SURVIVAL
```

## Current pros

```text
Good:
- Governor can detect tick budget pressure.
- There is already a concept of reducing non-authoritative work.
- Some strategic functions already have cadence-like behavior.
```

## Current cons

```text
Weak:
- Strategic systems may still scan too many entities.
- If cadence is not consistently enforced, many entities can evaluate at once.
- Deep strategic state can grow and become expensive over time.
```

## Improvements

```text
1. Strategic cadence:
   - not every entity every tick
   - use (tick + entity_id) % N

2. Hard caps from CognitionProfile:
   - max_active_projects
   - max_leads
   - max_concerns
   - max_blockers
   - max_contracts

3. Dirty strategic updates:
   - evaluate only entities whose blocker/project/intent changed

4. Budgeted strategic phase:
   - process only N entities per tick
   - defer the rest
```

---

# Scenario 3 — Combat arena with many entities

Example:

```text
100v100 or 500v500 entities in the same region.
```

## What may happen

High cost from:

```text
target selection
legality checks
range checks
tactical decisions
group coordination
occupancy conflicts
combat resolution
```

If proximity queries scan all entities, this becomes very expensive.

## Current pros

```text
Good:
- The architecture separates combat, tactical, legality, movement, occupancy.
- Occupancy phase is deterministic.
- Worker/concurrent path exists.
```

## Current cons

```text
Weak:
- If target selection uses full scans, combat becomes O(N²).
- Group coordination can add extra scans.
- Concurrency may not help if work items are too small or Python overhead dominates.
```

## Improvements

```text
1. Spatial index for nearby enemies.
2. Region/chunk partitioning.
3. Batch combat by region.
4. Limit target candidates:
   - nearest K enemies
   - visible enemies only
   - same region only
5. Tactical cadence:
   - full tactical decision every N ticks
   - simple repeat/continue behavior between decisions
```

---

# Scenario 4 — Replay backlog grows

Example:

```text
Large simulation emits many replay events per tick:
combat, movement, rejection, transaction trace, strategic updates.
```

## What may happen

Replay backlog grows:

```text
replay_backlog_kb >= max_replay_buffer_kb * 0.9
```

Then:

```text
DEGRADED
```

In survival:

```text
replay OFF
```

## Current pros

```text
Good:
- Governor already has replay backlog as a pressure signal.
- Policy has replay richness levels.
- SURVIVAL can disable replay conceptually.
```

## Current cons

```text
Weak:
- If ReplaySink does not strictly obey policy, backlog continues.
- Rich event payloads can consume memory.
- Full StateUpdate objects in replay payloads may be heavy.
```

## Improvements

```text
1. Replay richness levels:
   FULL:
      full event payload
   MINIMAL:
      event type, tick, entity ids, reason
   OFF:
      no replay writes

2. Replay compression/chunking.
3. Hard cap replay events per tick.
4. Drop low-priority replay events under pressure.
5. Avoid storing full objects in replay payloads.
```

---

# Scenario 5 — API/UI causes engine slowdown

Example:

```text
Browser keeps polling /api/v1/inspect on a large world.
```

## What may happen

Even if the engine tick is fine, API can become expensive because:

```text
full state presentation
deepcopy
JSON serialization
large response payload
```

This may increase CPU and memory.

## Current pros

```text
Good:
- API presenter exists.
- Minimal state endpoint exists.
- WebSocket stream sends minimal state.
```

## Current cons

```text
Weak:
- Full inspect can be expensive for large worlds.
- Deepcopy per tick is dangerous at scale.
- No obvious pagination/filtering for large entity lists.
```

## Improvements

```text
1. Minimal snapshot every tick.
2. Full snapshot only on demand.
3. Paginated endpoints:
   /entities?offset=&limit=
   /entity/{id}
   /regions
   /groups

4. Disable full inspect in SURVIVAL.
5. Cache DTO snapshots, not AuthoritativeState deepcopy.
6. Add API response size limits.
```

---

# Scenario 6 — Queue/work debt explosion

Example:

```text
Scheduler creates too many work items:
1000 entities × movement + combat + strategic + social + resource work.
```

## What may happen

Queue utilization and work debt grow:

```text
queue_utilization >= 0.9
work_debt_total >= max_work_debt
```

Then governor enters:

```text
DEGRADED or SURVIVAL
```

## Current pros

```text
Good:
- Governor tracks queue utilization and work debt.
- Policy can disable opportunistic work.
- Worker manager/executor has concurrency concept.
```

## Current cons

```text
Weak:
- If scheduler still creates too much work, debt remains high.
- If every work item is tiny, concurrency overhead may hurt.
- No clear work shedding policy yet.
```

## Improvements

```text
1. Work admission control:
   - critical work always allowed
   - important work allowed in constrained
   - opportunistic work dropped in degraded/survival

2. Work coalescing:
   - multiple movement updates for same entity collapse to latest
   - repeated strategic reevaluation collapses to one

3. Batch work:
   - movement batch
   - combat batch
   - strategic batch

4. Backpressure:
   - scheduler checks current mode before generating work
```

---

# Scenario 7 — World dynamics keeps spawning under pressure

Example:

```text
The world keeps spawning monsters, bosses, raids, camps, resource nodes.
```

## What may happen

The governor enters degraded/survival, but the world continues to add entities.

That causes:

```text
memory grows
tick cost grows
recovery becomes impossible
```

## Current pros

```text
Good:
- World dynamics is separated, so it can be gated.
- Runtime mode/policy exists.
```

## Current cons

```text
Weak:
- If world systems do not consume policy, they can make pressure worse.
```

## Improvements

```text
1. In CONSTRAINED:
   - reduce spawn rates

2. In DEGRADED:
   - disable non-critical spawning
   - allow only quest-critical or recovery-critical spawn

3. In SURVIVAL:
   - no spawning
   - cleanup first
   - convert distant entities to abstract/background state
```

---

# Scenario 8 — Memory leak-like growth from strategic history

Example:

```text
Every tick creates new leads, concerns, blockers, contracts, hypotheses, turning points.
```

## What may happen

Even if entity count is stable, memory grows.

## Current pros

```text
Good:
- CognitionProfile concept exists.
- Strategic structures are explicit.
```

## Current cons

```text
Weak:
- If caps are not enforced everywhere, collections grow.
- If old resolved blockers/leads are retained forever, memory grows.
```

## Improvements

```text
1. Enforce caps in ApplyPath or StrategicIntelligenceSystem.
2. Add TTL for stale leads/concerns.
3. Remove resolved blockers after N ticks.
4. Keep only top-K leads by certainty/relevance.
5. Keep bounded turning point history.
```

---

# Scenario 9 — Concurrency makes performance worse

Example:

```text
Small or medium work batches use concurrent path with worker overhead.
```

## What may happen

Concurrent mode is slower than local due to:

```text
thread overhead
packet creation
result sorting
copying data
GIL overhead
small task size
```

## Current pros

```text
Good:
- Local and concurrent execution paths exist.
- Determinism tests exist.
```

## Current cons

```text
Weak:
- Concurrency may not be adaptive enough.
- Work granularity may be too small.
```

## Improvements

```text
1. Use local execution below threshold:
   if work_count < 50: local

2. Batch small jobs.
3. Use concurrency only for expensive domains:
   combat-heavy
   strategic-heavy
   large resource resolution

4. Measure worker utilization.
5. Disable concurrency in SURVIVAL if overhead dominates.
```

---

# Scenario 10 — Recovery thrashing

Example:

```text
Engine alternates between NORMAL and DEGRADED every few ticks.
```

## What may happen

Mode changes themselves cause unstable behavior:

```text
diagnostics on/off
replay on/off
work scheduling changes
throughput oscillates
```

## Current pros

```text
Good:
- Governor has dwell/recovery logic.
- Recovery confidence window exists.
```

## Current cons

```text
Weak:
- If thresholds are too close, mode can still flap.
- If recovery does not check all pressure signals, it may recover too early.
```

## Improvements

```text
1. Hysteresis:
   degrade at 90%, recover at 60%

2. Minimum dwell time:
   stay in degraded for at least N ticks

3. Multi-signal recovery:
   memory, queue, tick time, replay backlog must all be safe

4. Log mode transitions clearly.
```

---

# Overall pros of current implementation

```text
1. Good separation of responsibility:
   governor detects pressure
   policy describes degradation
   systems can consume policy

2. Multiple pressure dimensions:
   memory
   tick time
   work debt
   queue
   worker utilization
   replay backlog

3. Runtime modes are clear:
   NORMAL
   CONSTRAINED
   DEGRADED
   SURVIVAL

4. Recovery is not immediate, which helps avoid thrashing.

5. Design is testable:
   pressure signal → mode → policy
```

---

# Overall cons / risks

```text
1. Policy may not be enforced everywhere yet.

2. Hitting memory max does not automatically free memory.

3. Strategic/world/social systems can still be expensive if not cadence-gated.

4. Replay/API can still become hidden performance costs.

5. Full scans can become expensive with large entity counts.

6. Concurrency may hurt if work granularity is too small.

7. There may be no clear resource admission control:
   - spawning
   - work generation
   - replay event creation
   - full API inspect
```

---

# Recommended improvement direction

## Short term

```text
1. Add tests proving each subsystem obeys GovernorPolicy.
2. Add performance benchmarks for 512 MB / 1 GB / 2 GB / 4 GB.
3. Add cadence for strategic/world/social systems.
4. Add API snapshot optimization.
5. Add replay richness enforcement.
```

## Medium term

```text
1. Dirty entity tracking.
2. Spatial index adoption across all proximity systems.
3. Work admission control.
4. Work batching.
5. Strategic memory caps.
```

## Long term

```text
1. LOD/background simulation.
2. Abstract offscreen regions.
3. Adaptive profile tuning.
4. Auto-scaling work budget by runtime mode.
```

---

# Best practical next step

I would add a new test suite:

```text
tests/unit/core/test_governor_policy_enforcement.py
tests/integration/kernel/test_pressure_mode_behavior.py
```

Cover these laws:

```text
SURVIVAL disables replay.
SURVIVAL disables non-authoritative periodic work.
SURVIVAL blocks spawning.
DEGRADED drops opportunistic work.
CONSTRAINED reduces diagnostics.
Memory max enters SURVIVAL.
Tick budget overflow enters DEGRADED/SURVIVAL.
Recovery requires stable low pressure.
```

Because right now the biggest question is not:

```text
Can the governor detect pressure?
```

It likely can.

The bigger question is:

```text
Do all expensive systems actually obey the pressure policy?
```

That is where the real-world protection will succeed or fail.
