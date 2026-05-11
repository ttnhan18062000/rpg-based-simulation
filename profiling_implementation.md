Yes. Python profiling is exactly what you should add before deciding optimization.

Use profiling in this order:

```text
1. cProfile / pstats
2. py-spy or Scalene for real runtime view
3. line_profiler only for confirmed hot functions
4. tracemalloc / memory_profiler for memory growth
```

# 1. Start with `cProfile`

Best first tool because it is built into Python.

It answers:

```text
Which functions consume the most total time?
Which functions are called too many times?
Which function causes downstream cost?
```

## Add profiling script

Create:

```text
scripts/profile_engine.py
```

```python
from __future__ import annotations

import cProfile
import pstats
from pathlib import Path

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


OUT_DIR = Path("reports/profile")


def make_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="PROFILE_ENGINE",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=4096,
        max_cpu_percent=90.0,
        max_worker_count=0,
        max_queue_depth=1000,
        max_replay_buffer_kb=8192,
        max_tick_budget_ms=50.0,
        max_observability_budget_percent=5.0,
        max_work_debt=10000,
    )


def make_state(entity_count: int) -> AuthoritativeState:
    entities = {
        entity_id: (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(float(entity_id), 0.0)
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .combat(
                hp=100,
                max_hp=100,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )
        for entity_id in range(1, entity_count + 1)
    }

    return AuthoritativeState(
        tick=0,
        seed=42,
        entities=entities,
    )


def run_engine_ticks(entity_count: int, ticks: int) -> None:
    state = make_state(entity_count)
    kernel = Kernel(
        make_profile(),
        state,
        DeterministicRNG(42),
        flags={"audit_mode": False},
    )

    for _ in range(ticks):
        kernel.tick_once()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    profile_path = OUT_DIR / "engine_idle_1000.prof"
    text_path = OUT_DIR / "engine_idle_1000.txt"

    profiler = cProfile.Profile()
    profiler.enable()

    run_engine_ticks(
        entity_count=1000,
        ticks=200,
    )

    profiler.disable()
    profiler.dump_stats(profile_path)

    with text_path.open("w", encoding="utf-8") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumtime")
        stats.print_stats(80)

    print(f"Wrote {profile_path}")
    print(f"Wrote {text_path}")


if __name__ == "__main__":
    main()
```

Run:

```bash
[x] Implement `scripts/profile_engine.py`
[x] Identify first major hotspot (`dataclasses.replace`)

Read:
```text
reports/profile/idle_1000.txt
```

### Initial Findings (IDLE_1000):
- **Hotspot**: `dataclasses.replace` is called ~20,000 times in 50 ticks (1000 entities).
- **Orchestration**: `AuthoritativeApplyPipeline.refine` and `apply_passive`/`apply_generation` are the dominant costs.
- **State Churn**: High `ncalls` to `replace` and `_replace` indicates immutable object overhead is a primary target for optimization.

---

# 2. How to read `cProfile` output

Important columns:

```text
ncalls      number of calls
tottime     time spent inside this function only
cumtime     time spent inside this function + child calls
percall     average time per call
filename    source location
```

Focus on:

```text
cumtime
ncalls
```

Example interpretation:

```text
High cumtime, low tottime
→ this function orchestrates expensive child calls

High tottime
→ this exact function is expensive

Huge ncalls
→ probably repeated scanning / object churn / unnecessary loop
```

Good hotspot candidates:

```text
AuthoritativeApplyPipeline.refine
ApplyPath.apply_generation
ResourceTransactionResolver
StrategicIntelligenceSystem
DetourSuggestionSystem
MovementPhase
OccupancyPhase
LegalityServiceV2
StateFingerprinter
StatePresenter
copy.deepcopy
dataclasses.replace
```

---

# 3. Add scenario-specific profiling

Do not profile only idle.

Create multiple profile runs:

```text
[x] IDLE_1000 (DONE - identified `dataclasses.replace` bottleneck)
[ ] IDLE_5000
[ ] RESOURCE_1000
[ ] MOVEMENT_1000
[ ] COMBAT_100v100
[ ] STRATEGIC_1000
[ ] MIXED_1000
```

Each scenario can write its own file:

```text
reports/profile/idle_1000.txt
reports/profile/resource_1000.txt
reports/profile/strategic_1000.txt
```

This matters because bottlenecks differ:

```text
idle          → kernel overhead / apply / lifecycle / observability
resource      → inventory / resolver / interaction
movement      → spatial / occupancy / legality
combat        → target selection / tactical / legality / damage
strategic     → blockers / leads / projects / detours
API           → deepcopy / presenter / serialization
```

---

# 4. Add py-spy for real runtime profiling

`cProfile` adds overhead and changes timing.

For more realistic runtime view, use `py-spy`.

Install:

```bash
pip install py-spy
```

Run your script normally, then attach:

```bash
py-spy top --pid <PID>
```

Or record flamegraph:

```bash
py-spy record -o reports/profile/engine.svg -- python scripts/profile_engine.py
```

Output:

```text
reports/profile/engine.svg
```

Use this to see:

```text
where runtime is actually spent
whether threads are idle
whether GIL blocks concurrency
whether sleep/wait dominates
```

Very useful for checking:

```text
Does concurrent execution help?
Are workers actually busy?
Is Python overhead dominating?
```

---

# 5. Use Scalene for CPU + memory

`Scalene` is good when you suspect memory allocation or Python-vs-native cost.

Install:

```bash
pip install scalene
```

Run:

```bash
python -m scalene scripts/profile_engine.py --html --outfile reports/profile/scalene_engine.html
```

Use it to find:

```text
high allocation lines
memory growth
CPU-heavy Python lines
```

Good for this engine because there may be many:

```text
dataclasses.replace
dict copies
list copies
deepcopy
StateUpdate construction
EntityUpdate construction
```

---

# 6. Use `line_profiler` only after you know hotspots

Do not start with line profiling.

Use it only after `cProfile` says:

```text
StrategicIntelligenceSystem.evaluate_strategic_intent is hot
```

or:

```text
ResourceTransactionResolver.resolve is hot
```

Then add:

```bash
pip install line_profiler
```

Example:

```python
@profile
def resolve(...):
    ...
```

Run:

```bash
kernprof -l -v scripts/profile_engine.py
```

This tells you which exact lines are slow.

---

# 7. Use `tracemalloc` for memory bottlenecks

Add script:

```text
scripts/profile_memory.py
```

```python
from __future__ import annotations

import tracemalloc
from pathlib import Path

from scripts.profile_engine import run_engine_ticks


OUT = Path("reports/profile/memory_top.txt")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    tracemalloc.start()

    run_engine_ticks(
        entity_count=1000,
        ticks=200,
    )

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    with OUT.open("w", encoding="utf-8") as f:
        f.write("Top memory allocation lines:\n\n")
        for stat in top_stats[:80]:
            f.write(str(stat))
            f.write("\n")

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/profile_memory.py
```

This finds allocation-heavy lines.

Likely suspects:

```text
copy.deepcopy
dataclasses.replace
StatePresenter.present_full
StateFingerprinter
replay payload creation
transaction_trace append
strategic project/lead/blocker creation
```

---

# 8. Add profiling into the benchmark runner

After `scripts/run_perf_baseline.py`, add optional profile mode:

```bash
python scripts/run_perf_baseline.py --profile IDLE_1000
```

Or create separate:

```text
scripts/profile_perf_scenario.py
```

Arguments:

```bash
python scripts/profile_perf_scenario.py --scenario idle --entities 1000 --ticks 200
python scripts/profile_perf_scenario.py --scenario resource --entities 1000 --nodes 1000 --ticks 200
python scripts/profile_perf_scenario.py --scenario strategic --entities 1000 --ticks 200
```

This gives repeatable profiling.

---

# 9. What to look for in results

## Case A: `dataclasses.replace` is hot

Meaning:

```text
Too much immutable object churn.
```

Possible improvement:

```text
phase-local mutable accumulator
skip no-op updates
compact StateUpdate
avoid repeated replace of same entity
```

---

## Case B: `copy.deepcopy` is hot

Meaning:

```text
API snapshot or worker packet/state copy is expensive.
```

Improvement:

```text
DTO snapshot instead of full state copy
paged API
copy only visible/needed data
```

---

## Case C: `StateFingerprinter` is hot

Meaning:

```text
Fingerprint includes too much data or runs too often.
```

Improvement:

```text
fingerprint only in audit/certification mode
entity-level fingerprint cache
versioned strategic/inventory fingerprints
```

---

## Case D: `StrategicIntelligenceSystem` is hot

Meaning:

```text
Strategic cognition is too frequent or scans too much.
```

Improvement:

```text
cadence
dirty strategic entities
cap leads/blockers/projects
cache detour suggestions
```

---

## Case E: spatial/proximity functions are hot

Meaning:

```text
Full scans are killing performance.
```

Improvement:

```text
TickSpatialCache
SpatialHashV2 everywhere
chunk/region partitioning
```

---

## Case F: `pstats` shows huge `ncalls`

Example:

```text
1,000,000 calls to ItemRegistry.get
500,000 calls to distance function
300,000 calls to replace
```

Improvement:

```text
cache static registry lookups
batch distance queries
reduce repeated object construction
```

---

# 10. TDD around profiling discoveries

Profiling itself does not become a normal test.

But each bottleneck should create a regression test.

Example:

## If spatial scan is hot

Add:

```python
@pytest.mark.perf
def test_spatial_query_1000_entities_budget():
    ...
```

## If API deepcopy is hot

Add:

```python
@pytest.mark.perf
def test_api_snapshot_1000_entities_budget():
    ...
```

## If strategic cognition is hot

Add:

```python
@pytest.mark.perf
def test_strategic_1000_entities_cadence_budget():
    ...
```

## If ApplyPath is hot

Add:

```python
@pytest.mark.perf
def test_applypath_5000_updates_budget():
    ...
```

---

# Recommended profiling flow

Use this workflow:

```text
1. [x] Run benchmark
2. [x] Identify slow scenario (IDLE_1000)
3. [x] Run cProfile for that scenario
4. [x] Inspect top cumulative functions (`dataclasses.replace`)
5. [ ] Run py-spy flamegraph for real runtime confirmation
6. [ ] If memory issue, run tracemalloc / Scalene
7. [ ] Pick one bottleneck
8. [ ] Add perf regression test
9. [ ] Optimize
10. [ ] Re-run benchmark and profile
```

---

# First profiling target I recommend

Start with:

```bash
python scripts/profile_engine.py
```

for:

```text
[x] IDLE_1000 (DONE)
[ ] IDLE_5000
```

Then add:

```text
RESOURCE_1000
STRATEGIC_1000
```

Why?

```text
IDLE shows base engine overhead.
RESOURCE shows transaction/inventory cost.
STRATEGIC shows deep mechanism cost.
```

Do not start with mixed scenario first, because mixed scenario makes it harder to know which subsystem is slow.

---

# Final recommendation

Yes, add Python profiling.

Start with:

```text
cProfile + pstats
```

Then use:

```text
py-spy flamegraph
```

Then use:

```text
Scalene / tracemalloc
```

for memory.

Do not optimize based on intuition. For your engine, the likely bottlenecks are:

```text
strategic cognition
full scans without spatial index
dataclass replace/object churn
API deepcopy/full presenter
replay/fingerprint payload size
resource transaction resolution
```

But profiling should confirm the real order.
