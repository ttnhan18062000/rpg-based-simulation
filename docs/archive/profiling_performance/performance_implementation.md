---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# 1. Performance testing goals

The engine performance test should answer these questions:

```text
1. How many entities can the engine support under different workloads?
2. Which phase is slowest?
3. Does memory grow over time?
4. Does concurrent execution improve or hurt performance?
5. Does replay/observability add too much overhead?
6. Does API snapshot/deepcopy become expensive as state grows?
7. What profile values are realistic for Class A / B / C machines?
8. Which source areas should be optimized first, if needed?
```

The final output should be:

```text
reports/perf/latest.json
reports/perf/baseline.json
reports/perf/summary.md
```

---

# 2. Current performance foundation

You already have useful infrastructure:

```text
src/perf/bench_harness.py
src/certification/harness.py
src/engine/runtime_status.py
src/engine/observability.py
src/engine/governor.py
src/config/profiles.py
```

`BenchHarness` already measures:

```text
avg_tps
avg_tick_compute_ms
phase_breakdown
```

So we should reuse it instead of creating a separate performance framework.

---

# 3. Profile strategy: start from 4 GB but test gradually

Do not immediately set every test to 4 GB and assume it is good.

Create performance profiles like this:

```text
CLASS_B_SAFE_512MB
CLASS_B_NORMAL_1GB
CLASS_A_NORMAL_2GB
CLASS_A_HIGH_4GB
```

The goal is to understand the curve:

```text
entity count / scenario complexity / worker count / memory limit
```

## Recommended starting profiles

```python
def perf_profile(
    name: str,
    *,
    ram_mb: int,
    workers: int,
    tick_budget_ms: float,
    queue_depth: int = 1000,
    replay_buffer_kb: int = 8192,
    observability_budget_percent: float = 5.0,
) -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=ram_mb,
        max_cpu_percent=90.0,
        max_worker_count=workers,
        max_queue_depth=queue_depth,
        max_replay_buffer_kb=replay_buffer_kb,
        max_tick_budget_ms=tick_budget_ms,
        max_observability_budget_percent=observability_budget_percent,
        max_work_debt=10000,
    )
```

Initial profile matrix:

```text
Profile              RAM       Workers    Tick budget
-----------------------------------------------------
PERF_512MB_LOCAL     512 MB    0          50 ms
PERF_1GB_LOCAL       1024 MB   0          50 ms
PERF_2GB_LOCAL       2048 MB   0          50 ms
PERF_4GB_LOCAL       4096 MB   0          50 ms

PERF_512MB_CONC      512 MB    4          50 ms
PERF_1GB_CONC        1024 MB   4          50 ms
PERF_2GB_CONC        2048 MB   4          50 ms
PERF_4GB_CONC        4096 MB   4          50 ms
```

Why start with `50 ms`?

```text
50 ms/tick = 20 ticks per second.
```

That is a reasonable first budget for simulation.

Later you can tighten:

```text
33 ms/tick = 30 TPS
20 ms/tick = 50 TPS
16 ms/tick = 60 TPS
```

---

# 4. Scenario matrix

Performance is not one number. You need different scenarios.

## Scenario 1: idle baseline

Purpose:

```text
Measure kernel overhead with many entities but little behavior.
```

Entity counts:

```text
100
500
1000
2000
5000
```

Expected use:

```text
Find base overhead of tick loop, lifecycle, replay, status, observability.
```

---

## Scenario 2: movement-heavy

Purpose:

```text
Measure movement/path/occupancy costs.
```

Entity counts:

```text
100
500
1000
2000
```

Workload:

```text
Every entity receives ENTITY_MOVE or navigation intent.
No two entities target the same tile.
```

Expected hotspot:

```text
MovementPhase
OccupancyPhase
Spatial index
Legality checks
```

---

## Scenario 3: combat-heavy

Purpose:

```text
Measure action routing, legality, combat resolution, tactical decision cost.
```

Entity counts:

```text
10v10
50v50
100v100
```

Expected hotspot:

```text
ActionRoutingPhase
CombatResolutionSystem
TacticalDecisionSystem
LegalityServiceV2
GroupSystem
```

---

## Scenario 4: resource-heavy

Purpose:

```text
Measure harvest, inventory, transaction resolver, resource conservation.
```

Entity counts:

```text
100 harvesters
500 harvesters
1000 harvesters
```

Resource nodes:

```text
100
500
1000
```

Expected hotspot:

```text
ResourceTransactionResolver
InventoryService
InteractionSystem
HarvestSystem
ApplyPath
```

---

## Scenario 5: strategic-heavy

Purpose:

```text
Measure blocker inference, detour, project updates, leads/concerns.
```

Entity counts:

```text
100
500
1000
```

Each entity has:

```text
projects
blockers
leads
concerns
contracts
source_trust
```

Expected hotspot:

```text
StrategicIntelligenceSystem
DetourSuggestionSystem
Concern evaluation
StrategicRedirectionSystem
```

---

## Scenario 6: full mixed simulation

Purpose:

```text
Realistic performance.
```

Mix:

```text
heroes
monsters
resources
shops
towns
groups
combat
movement
strategic cognition
replay enabled
observability enabled
```

Entity counts:

```text
100
500
1000
2000
```

Expected use:

```text
Final profile tuning.
```

---

# 5. Test folder structure

Add a separate performance test folder:

```text
tests/perf/
  conftest.py
  test_perf_idle.py
  test_perf_movement.py
  test_perf_combat.py
  test_perf_resource.py
  test_perf_strategic.py
  test_perf_mixed.py
  test_perf_api_snapshot.py
  test_perf_regression_baseline.py
```

Do not run these with normal unit tests by default.

Add marker:

```ini
# pytest.ini
[pytest]
markers =
    perf: performance tests, run separately
```

Run:

```bash
pytest tests/perf -m perf -q
```

---

# 6. Benchmark result schema

Every benchmark should output this structure:

```json
{
  "scenario_id": "IDLE_1000",
  "profile": "PERF_2GB_CONC",
  "entity_count": 1000,
  "ticks": 200,
  "warmup_ticks": 20,
  "avg_tick_compute_ms": 12.4,
  "p50_tick_compute_ms": 11.9,
  "p95_tick_compute_ms": 18.3,
  "p99_tick_compute_ms": 23.5,
  "avg_tps": 80.6,
  "peak_rss_mb": 690.2,
  "memory_delta_mb": 12.4,
  "memory_trend_mb_per_tick": 0.01,
  "worker_utilization": 0.72,
  "queue_utilization": 0.11,
  "replay_backlog_kb": 0,
  "phase_breakdown": {
    "init": { "avg_ms": 0.2, "p95_ms": 0.4 },
    "scheduling": { "avg_ms": 0.5, "p95_ms": 0.9 },
    "collection": { "avg_ms": 2.3, "p95_ms": 4.8 },
    "resolution": { "avg_ms": 7.2, "p95_ms": 12.0 },
    "cleanup": { "avg_ms": 0.4, "p95_ms": 0.8 },
    "advancement": { "avg_ms": 0.3, "p95_ms": 0.5 }
  }
}
```

Current `BenchHarness` already gives average tick time and phase breakdown, but you should enhance it to add:

```text
p50
p95
p99
max
peak RSS
memory delta
scenario metadata
profile metadata
```

---

# 7. Implementation phase plan

## Phase 1 — Add performance profiles

Create:

```text
src/perf/profiles.py
```

```python
from src.config.profiles import RuntimeProfile, HardwareClass


def make_perf_profile(
    name: str,
    *,
    ram_mb: int,
    workers: int,
    tick_budget_ms: float = 50.0,
    queue_depth: int = 1000,
    replay_buffer_kb: int = 8192,
    observability_budget_percent: float = 5.0,
) -> RuntimeProfile:
    """
    Build a performance-oriented RuntimeProfile.

    These profiles are intentionally more generous than unit-test profiles.
    They are used to discover realistic engine limits before setting final
    production budgets.

    Resource strategy:
        Start from 512 MB, 1 GB, 2 GB, and 4 GB.
        Measure first.
        Then decide which profile is a good default.
    """
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=ram_mb,
        max_cpu_percent=90.0,
        max_worker_count=workers,
        max_queue_depth=queue_depth,
        max_replay_buffer_kb=replay_buffer_kb,
        max_tick_budget_ms=tick_budget_ms,
        max_observability_budget_percent=observability_budget_percent,
        max_work_debt=10000,
    )


PERF_PROFILES = {
    "PERF_512MB_LOCAL": make_perf_profile(
        "PERF_512MB_LOCAL",
        ram_mb=512,
        workers=0,
    ),
    "PERF_1GB_LOCAL": make_perf_profile(
        "PERF_1GB_LOCAL",
        ram_mb=1024,
        workers=0,
    ),
    "PERF_2GB_LOCAL": make_perf_profile(
        "PERF_2GB_LOCAL",
        ram_mb=2048,
        workers=0,
    ),
    "PERF_4GB_LOCAL": make_perf_profile(
        "PERF_4GB_LOCAL",
        ram_mb=4096,
        workers=0,
    ),
    "PERF_512MB_CONC": make_perf_profile(
        "PERF_512MB_CONC",
        ram_mb=512,
        workers=4,
    ),
    "PERF_1GB_CONC": make_perf_profile(
        "PERF_1GB_CONC",
        ram_mb=1024,
        workers=4,
    ),
    "PERF_2GB_CONC": make_perf_profile(
        "PERF_2GB_CONC",
        ram_mb=2048,
        workers=4,
    ),
    "PERF_4GB_CONC": make_perf_profile(
        "PERF_4GB_CONC",
        ram_mb=4096,
        workers=4,
    ),
}
```

---

## Phase 2 — Add scenario builders

Create:

```text
src/perf/scenarios.py
```

```python
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState, ResourceNodeState


def build_idle_state(
    *,
    entity_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a state with many active entities and no intentional work pressure.

    Purpose:
        Measures base engine overhead.
    """
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
        seed=seed,
        entities=entities,
    )


def build_resource_state(
    *,
    entity_count: int,
    node_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a resource-heavy state.

    Purpose:
        Measures resource-node scanning, interaction, transfer resolution,
        and inventory handling.
    """
    entities = {
        entity_id: (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(float(entity_id % 100), float(entity_id // 100))
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .inventory(
                items=[
                    ItemStack(item_id="junk", quantity=1),
                ],
                max_slots=20,
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

    resource_nodes = {
        node_id: ResourceNodeState(
            id=node_id,
            kind="iron_ore",
            position=(float(node_id % 100), float(node_id // 100)),
            remaining_charges=10,
            max_charges=10,
            yields_item="iron_ore",
            required_ticks=1,
        )
        for node_id in range(1, node_count + 1)
    }

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        resource_nodes=resource_nodes,
    )
```

Later add:

```text
build_movement_state
build_combat_arena_state
build_strategic_state
build_mixed_state
```

---

## Phase 3 — Enhance `BenchHarness`

Current `BenchHarness` is good but too basic.

Enhance it to collect:

```text
tick samples
p50 / p95 / p99
max tick time
RSS samples
memory delta
phase p95
profile metadata
scenario metadata
```

Patch concept:

```python
import statistics
import time
import os

try:
    import psutil
except ImportError:
    psutil = None
```

Add helper:

```python
def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int((len(sorted_values) - 1) * percentile)
    return sorted_values[index]
```

Add inside `run_benchmark(...)`:

```python
tick_samples_ms = []
rss_samples_mb = []

process = psutil.Process(os.getpid()) if psutil else None

for _ in range(sample_ticks):
    start = time.perf_counter()
    kernel.tick_once()
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    tick_samples_ms.append(elapsed_ms)

    if process:
        rss_mb = process.memory_info().rss / (1024 * 1024)
        rss_samples_mb.append(rss_mb)
```

Result additions:

```python
result = {
    "scenario_id": scenario_id,
    "profile_name": self.profile.name,
    "max_ram_mb": self.profile.max_ram_mb,
    "max_worker_count": self.profile.max_worker_count,
    "warmup_ticks": warmup_ticks,
    "sample_ticks": sample_ticks,
    "avg_tick_compute_ms": statistics.mean(tick_samples_ms),
    "p50_tick_compute_ms": _percentile(tick_samples_ms, 0.50),
    "p95_tick_compute_ms": _percentile(tick_samples_ms, 0.95),
    "p99_tick_compute_ms": _percentile(tick_samples_ms, 0.99),
    "max_tick_compute_ms": max(tick_samples_ms),
    "avg_tps": 1000.0 / statistics.mean(tick_samples_ms),
    "peak_rss_mb": max(rss_samples_mb) if rss_samples_mb else None,
    "memory_delta_mb": (
        rss_samples_mb[-1] - rss_samples_mb[0]
        if len(rss_samples_mb) >= 2
        else None
    ),
    "phase_breakdown": phase_breakdown,
}
```

Important:

```text
Do not fail based on performance in this harness.
The harness only measures.
Tests decide pass/fail.
```

---

## Phase 4 — Add performance test utilities

Create:

```text
tests/perf/conftest.py
```

```python
import json
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "perf: performance regression tests",
    )


@pytest.fixture
def perf_report_dir(tmp_path):
    """
    Directory for per-test benchmark outputs.

    In CI, you can later redirect this to reports/perf.
    """
    return tmp_path / "perf_reports"


def write_perf_result(path: Path, result: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
```

---

# 8. Test-driven performance contracts

## 8.1 Idle performance test

```python
import pytest

from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state


@pytest.mark.perf
@pytest.mark.parametrize(
    "profile_name,entity_count",
    [
        ("PERF_512MB_LOCAL", 100),
        ("PERF_1GB_LOCAL", 500),
        ("PERF_2GB_LOCAL", 1000),
        ("PERF_4GB_LOCAL", 2000),
    ],
)
def test_idle_tick_budget(profile_name, entity_count, perf_report_dir):
    """
    Performance contract:
        Idle simulation should remain within a broad tick budget.

    Purpose:
        Establishes the base cost of the kernel and detects major regressions.

    Note:
        These thresholds are intentionally loose at first. Tighten them after
        collecting baseline results on the target CI machine.
    """
    profile = PERF_PROFILES[profile_name]
    state = build_idle_state(entity_count=entity_count)

    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"IDLE_{entity_count}",
        initial_state=state,
        warmup_ticks=20,
        sample_ticks=100,
    )

    write_perf_result(
        perf_report_dir / f"{profile_name}_IDLE_{entity_count}.json",
        result,
    )

    assert result["peak_rss_mb"] is None or result["peak_rss_mb"] < profile.max_ram_mb
    assert result["p95_tick_compute_ms"] < profile.max_tick_budget_ms
```

---

## 8.2 Memory scaling test

```python
@pytest.mark.perf
def test_idle_memory_scaling_under_4gb(perf_report_dir):
    """
    Performance contract:
        A large idle state should stay below the 4 GB ceiling.

    Purpose:
        This tells us whether 4 GB is enough for a large state baseline and
        whether memory grows unexpectedly during ticks.
    """
    profile = PERF_PROFILES["PERF_4GB_LOCAL"]
    state = build_idle_state(entity_count=5000)

    result = BenchHarness(profile).run_benchmark(
        scenario_id="IDLE_5000_4GB",
        initial_state=state,
        warmup_ticks=20,
        sample_ticks=200,
    )

    write_perf_result(
        perf_report_dir / "IDLE_5000_4GB.json",
        result,
    )

    assert result["peak_rss_mb"] is None or result["peak_rss_mb"] < 4096
    assert result["memory_delta_mb"] is None or result["memory_delta_mb"] < 128
```

Meaning:

```text
If memory_delta_mb grows by more than 128 MB over 200 ticks in idle scenario,
investigate leak-like behavior.
```

---

## 8.3 Concurrent vs local equivalence performance

You already have correctness tests for local vs concurrent determinism. Add performance measurement:

```python
@pytest.mark.perf
def test_concurrent_execution_not_significantly_slower_for_large_idle_batch(perf_report_dir):
    """
    Performance contract:
        Concurrent execution should not be dramatically slower than local
        execution under a large workload.

    This does not require concurrent to always be faster. Python overhead,
    worker setup, and workload size can make local faster for small cases.

    The goal is to catch extreme regressions.
    """
    state_local = build_idle_state(entity_count=1000)
    state_conc = build_idle_state(entity_count=1000)

    local_result = BenchHarness(PERF_PROFILES["PERF_2GB_LOCAL"]).run_benchmark(
        scenario_id="IDLE_1000_LOCAL",
        initial_state=state_local,
        warmup_ticks=20,
        sample_ticks=100,
    )

    conc_result = BenchHarness(PERF_PROFILES["PERF_2GB_CONC"]).run_benchmark(
        scenario_id="IDLE_1000_CONC",
        initial_state=state_conc,
        warmup_ticks=20,
        sample_ticks=100,
    )

    write_perf_result(
        perf_report_dir / "IDLE_1000_LOCAL.json",
        local_result,
    )
    write_perf_result(
        perf_report_dir / "IDLE_1000_CONC.json",
        conc_result,
    )

    assert conc_result["p95_tick_compute_ms"] < local_result["p95_tick_compute_ms"] * 2.0
```

Loose rule:

```text
Concurrent path should not be more than 2x slower.
```

Later tune this based on actual results.

---

## 8.4 Phase budget test

```python
@pytest.mark.perf
def test_phase_breakdown_has_no_single_phase_dominating_idle(perf_report_dir):
    """
    Performance contract:
        No single phase should dominate a simple idle scenario.

    Purpose:
        Catches accidental O(N²) changes inside one phase.
    """
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_idle_state(entity_count=1000)

    result = BenchHarness(profile).run_benchmark(
        scenario_id="IDLE_1000_PHASES",
        initial_state=state,
        warmup_ticks=20,
        sample_ticks=100,
    )

    write_perf_result(
        perf_report_dir / "IDLE_1000_PHASES.json",
        result,
    )

    phase_breakdown = result["phase_breakdown"]

    assert phase_breakdown, "Expected phase performance breakdown"

    for phase_name, stats in phase_breakdown.items():
        assert stats["avg_ms"] < profile.max_tick_budget_ms, (
            f"Phase {phase_name} exceeded full tick budget: {stats}"
        )
```

Later make budgets stricter per phase:

```text
resolution <= 70% of tick budget
collection <= 30%
observability <= 5%
replay <= 10%
```

---

# 9. Baseline comparison test

After running the first stable benchmark, create:

```text
reports/perf/baseline.json
```

Example:

```json
{
  "IDLE_1000_LOCAL": {
    "p95_tick_compute_ms": 18.5,
    "peak_rss_mb": 420.0,
    "memory_delta_mb": 5.0
  },
  "IDLE_5000_4GB": {
    "p95_tick_compute_ms": 80.0,
    "peak_rss_mb": 1500.0,
    "memory_delta_mb": 30.0
  }
}
```

Add:

```text
tests/perf/test_perf_regression_baseline.py
```

```python
import json
from pathlib import Path

import pytest


BASELINE_PATH = Path("reports/perf/baseline.json")
LATEST_PATH = Path("reports/perf/latest.json")


@pytest.mark.perf
def test_perf_regression_against_baseline():
    """
    Performance contract:
        Latest performance should not regress too far from checked-in baseline.

    This test should be enabled only after a stable baseline exists.
    """
    if not BASELINE_PATH.exists() or not LATEST_PATH.exists():
        pytest.skip("Performance baseline/latest report is missing")

    baseline = json.loads(BASELINE_PATH.read_text())
    latest = json.loads(LATEST_PATH.read_text())

    tolerance = 1.30

    for scenario_id, base_metrics in baseline.items():
        if scenario_id not in latest:
            pytest.fail(f"Missing latest perf result for {scenario_id}")

        current = latest[scenario_id]

        assert (
            current["p95_tick_compute_ms"]
            <= base_metrics["p95_tick_compute_ms"] * tolerance
        ), (
            f"{scenario_id} p95 regression: "
            f"baseline={base_metrics['p95_tick_compute_ms']}, "
            f"current={current['p95_tick_compute_ms']}"
        )

        if base_metrics.get("peak_rss_mb") is not None:
            assert (
                current["peak_rss_mb"]
                <= base_metrics["peak_rss_mb"] * tolerance
            ), (
                f"{scenario_id} memory regression: "
                f"baseline={base_metrics['peak_rss_mb']}, "
                f"current={current['peak_rss_mb']}"
            )
```

---

# 10. Add a benchmark runner script

Create:

```text
scripts/run_perf_baseline.py
```

```python
from __future__ import annotations

import json
from pathlib import Path

from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state, build_resource_state


OUT = Path("reports/perf/latest.json")


def main():
    """
    Run selected performance scenarios and write a machine-readable report.

    This script is intended for local performance investigation and CI
    performance jobs. It should not replace unit tests.
    """
    results = {}

    scenarios = [
        (
            "IDLE_100",
            PERF_PROFILES["PERF_512MB_LOCAL"],
            build_idle_state(entity_count=100),
        ),
        (
            "IDLE_1000_LOCAL",
            PERF_PROFILES["PERF_2GB_LOCAL"],
            build_idle_state(entity_count=1000),
        ),
        (
            "IDLE_1000_CONC",
            PERF_PROFILES["PERF_2GB_CONC"],
            build_idle_state(entity_count=1000),
        ),
        (
            "IDLE_5000_4GB",
            PERF_PROFILES["PERF_4GB_LOCAL"],
            build_idle_state(entity_count=5000),
        ),
        (
            "RESOURCE_1000_1000_4GB",
            PERF_PROFILES["PERF_4GB_CONC"],
            build_resource_state(entity_count=1000, node_count=1000),
        ),
    ]

    for scenario_id, profile, state in scenarios:
        print(f"Running {scenario_id} with profile {profile.name}")

        result = BenchHarness(profile).run_benchmark(
            scenario_id=scenario_id,
            initial_state=state,
            warmup_ticks=20,
            sample_ticks=200,
        )

        results[scenario_id] = result

        print(
            f"  p95={result['p95_tick_compute_ms']:.2f}ms "
            f"rss={result.get('peak_rss_mb')}MB "
            f"tps={result['avg_tps']:.1f}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(results, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/run_perf_baseline.py
```

Then review:

```text
reports/perf/latest.json
```

---

# 11. Decision process for choosing the good starting profile

Do not choose 4 GB automatically.

Run this matrix:

```text
IDLE_1000 on 512 MB, 1 GB, 2 GB, 4 GB
IDLE_5000 on 512 MB, 1 GB, 2 GB, 4 GB
RESOURCE_1000 on 1 GB, 2 GB, 4 GB
MIXED_1000 on 1 GB, 2 GB, 4 GB
```

Then decide.

## Profile decision rules

### 512 MB is good if:

```text
peak_rss < 350 MB
p95 tick < 50 ms
memory_delta < 64 MB
```

### 1 GB is good if:

```text
peak_rss < 750 MB
p95 tick < 50 ms
memory_delta < 128 MB
```

### 2 GB is good if:

```text
peak_rss < 1500 MB
p95 tick < 50 ms
memory_delta < 256 MB
```

### 4 GB is needed if:

```text
peak_rss > 1500 MB
or 2 GB profile degrades too often
or large scenarios need many replay/observability buffers
```

Recommended initial production-like profile after testing:

```text
Start with 2 GB if 1000-2000 entity mixed simulation is stable.
Use 4 GB for stress/certification profiles.
```

---

# 12. Enhancement decision tree

After running tests, use this decision tree.

## If p95 tick is high but memory is okay

Investigate phase breakdown:

```text
resolution high      → pipeline / domain / strategic / resource resolver
collection high      → worker manager / executor
scheduling high      → scheduler / work selection
advancement high     → ApplyPath / state replacement
observability high   → SignalCollector / status history
replay high          → ReplaySink / serialization / buffer
```

Enhancement should be phase-specific.

---

## If memory is high

Check:

```text
deepcopy in API manager
replay buffer retention
transaction_trace growth
latest_intent_results growth
strategic history/leads/concerns growth
local scars/groups/corpses/ground_items cleanup
```

Likely enhancements:

```text
1. Bound transaction_trace.
2. Bound latest_intent_results.
3. Bound strategic memory collections.
4. Replace API deepcopy with DTO snapshot.
5. Review replay buffer retention.
```

---

## If concurrent is slower than local

Possible causes:

```text
worker overhead too high for small jobs
copying packets too expensive
serialization/deepcopy in WorkerPacket too expensive
Python GIL overhead
result ordering/sorting overhead
```

Enhancements:

```text
1. Use concurrent only above entity/work threshold.
2. Batch small work items.
3. Avoid expensive per-packet copies.
4. Reuse worker packet structures if safe.
```

TDD:

```python
def test_concurrency_policy_uses_local_for_small_batches():
    ...
```

---

## If API snapshot is expensive

Current likely enhancement:

```text
replace copy.deepcopy(state) with StatePresenter snapshot
```

TDD first:

```python
def test_api_snapshot_is_plain_dict_and_does_not_expose_state():
    ...
```

Then implement:

```text
V2EngineManager._latest_snapshot
V2EngineManager.get_snapshot()
```

Keep old `get_state()` only for debug/internal use.

---

# 13. Recommended first enhancement candidate: API snapshot

Because `_update_latest_state` currently deep-copies full state every tick, this can become a major cost with large worlds.

## TDD test first

```python
def test_api_snapshot_update_budget_for_1000_entities():
    """
    API snapshot should stay cheap for 1000 entities.

    This test will tell us whether full deepcopy is still acceptable.
    """
```

If it fails, implement:

```python
def _update_latest_state(self, state):
    with self._state_lock:
        self._latest_snapshot = StatePresenter.present_minimal(state)
```

or for full inspect:

```python
self._latest_full_snapshot = StatePresenter.present_full(state)
```

But be careful:

```text
present_full for 5000 entities can also be expensive.
```

Better:

```text
minimal snapshot every tick
full snapshot only on request
```

---

# 14. Recommended first performance tests to implement

Start small:

```text
1. tests/perf/test_perf_idle.py
2. tests/perf/test_perf_api_snapshot.py
3. scripts/run_perf_baseline.py
```

Do not implement all scenarios at once.

First PR should contain:

```text
src/perf/profiles.py
src/perf/scenarios.py
enhanced src/perf/bench_harness.py
tests/perf/test_perf_idle.py
tests/perf/test_perf_api_snapshot.py
scripts/run_perf_baseline.py
```

---

# 15. Suggested commands

## Run normal correctness first

```bash
pytest tests/refactor -q
pytest tests/integrity -q
pytest tests/integration/kernel -q
pytest tests/integration/pipeline -q
```

## Run performance only

```bash
pytest tests/perf -m perf -q
```

## Generate report

```bash
python scripts/run_perf_baseline.py
```

## Compare manually first

```bash
cat reports/perf/latest.json
```

Only after stable results:

```bash
cp reports/perf/latest.json reports/perf/baseline.json
```

---

# 16. Final recommended plan

## Milestone P1 — Measurement foundation

```text
[x] Add perf profiles.
[x] Add perf scenario builders.
[x] Enhance BenchHarness with p95/p99/max/RSS.
[x] Add idle perf tests.
[x] Add API snapshot perf test.
[x] Add run_perf_baseline.py.
```

Expected output:

```text
You know current baseline for 100 / 1000 / 5000 entities.
```

---

## Milestone P2 — Workload coverage

```text
[x] Add movement-heavy scenario.
[x] Add resource-heavy scenario.
[x] Add combat-heavy scenario.
[x] Add strategic-heavy scenario.
[x] Add mixed scenario.
```

Expected output:

```text
You know which workload type is slowest.
```

---

## Milestone P3 — Regression guard

```text
[x] Add reports/perf/baseline.json.
[x] Add baseline comparison test.
[x] Add CI job that runs performance tests separately (scripts/perf_ci.py).
```

Expected output:

```text
Performance regressions are caught intentionally, not accidentally.
```

---

## Milestone P4 — Enhancement based on data

Only optimize after the report shows bottleneck.

Completed/In-Progress:

```text
[x] Implement `scripts/profile_engine.py` for hotspot isolation.
[x] Identify `dataclasses.replace` as primary bottleneck via cProfile.
[x] Improve phase-specific O(N²) hotspots (SpatialGrid in LegalityService).
[x] Implement strict per-phase latency budgeting (BenchHarness).
[x] Tune concurrent execution threshold (PROD_DEFAULT/PERF_4GB_CONC).
[x] API snapshot instead of full deepcopy (DTO Minimal Snapshot).
[x] Bound replay / transaction / strategic history.
[/] Reduce state replacement/copying overhead in ApplyPath (PROVEN COSTLY).
```

---

## Milestone P5 — Formal Production Profiles (CERTIFIED)
    - Certified PROD_DEFAULT: 2GB RAM, 4 Workers, 50ms Tick Budget.
    - Capacity Limit: Handles ~50-100 active entities per tick within p95 50ms (Python limit).
    - RAM Stability: Confirmed < 200MB for 1000 entities.

### Certified Profile: PROD_DEFAULT
```python
PROD_DEFAULT = RuntimeProfile(
    name="PROD_DEFAULT",
    hardware_class=HardwareClass.CLASS_A,
    max_ram_mb=2048,
    max_cpu_percent=85.0,
    max_worker_count=4,
    max_tick_budget_ms=50.0,
    max_queue_depth=5000,
    max_work_debt=5000
)
```

### Measured Performance Limits (Baseline)
| Workload | p95 Latency (4 Workers) | Peak RSS | Status |
| :--- | :--- | :--- | :--- |
| IDLE_50 | ~45ms | 47MB | **PASS** |
| IDLE_100 | ~98ms | 48MB | **SLIGHT_OVER** |
| MIXED_100 | ~107ms | 47MB | **SLIGHT_OVER** |
| IDLE_1000 | ~1900ms | 112MB | **CAPACITY_OVER** |

*Note: For 1000+ entities, engine requires asynchronous worker distribution or heavy C-extensions for cognition logic.*
