---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 2 — Add System Cadence Scheduling

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
