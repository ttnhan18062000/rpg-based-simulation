---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Time Domain Contract

**Source:** `src/domains/time/service.py`
**Related docs:** [domain_ownership_map.md](domain_ownership_map.md), [memory_contract.md](memory_contract.md), [motivation_contract.md](motivation_contract.md)

---

## Purpose

The time domain provides `TemporalPressureService`, which converts an entity's deadlines, cooldowns, and stale-fact ratings into a per-key urgency map. This urgency map is consumed by the motivation domain to bias routing decisions toward time-sensitive actions.

The time domain owns no entity lifecycle of its own — it is a pure read-pass utility that runs inside the Memory Update stage (alongside memory) on the entity's `cognition.subjective.time` state.

---

## RPG Meaning

Entities experience time pressure differently: a quest with an expiring deadline feels urgent; a just-used ability is on cooldown; a rumor last heard 500 ticks ago is stale and unreliable. This domain translates those subjective time states into urgency numbers (0.0–1.0) that the motivation domain can act on directly.

---

## Inputs

| Input | Type | Source |
|---|---|---|
| `entity.cognition.subjective.time.deadlines` | Dict[str, DeadlineEntry] | Set by quest/commitment systems |
| `entity.cognition.subjective.time.cooldowns` | Dict[str, CooldownEntry] | Set by action-completion events |
| `entity.cognition.subjective.time.stale_facts` | Dict[str, StalenessEntry] | Set by knowledge assimilation |
| `current_tick` | int | Engine tick counter |

---

## Core rules

### Deadline urgency

```python
ticks_left = dl.expiry_tick - current_tick
if ticks_left <= 0:
    urgency = 1.0          # expired — maximum pressure
elif ticks_left < 100:
    urgency = 1.0 - (ticks_left / 100.0) * 0.9   # scales from 0.95 (1 tick left) down to 0.1 (100 ticks left)
else:
    urgency = 0.1          # distant deadline — low background pressure
```

Expiry threshold is 100 ticks. Below 100 ticks the urgency rises linearly from 0.1 to 0.95. At or past expiry: 1.0.

### Cooldown urgency

```python
if current_tick < cd.ready_tick:
    urgency = 0.0    # blocked — cannot act
else:
    urgency = 0.5    # ready — medium priority to re-evaluate
```

A cooldown on a key signals "this action is blocked until tick N". While blocked, urgency is 0 (do not attempt). Once ready, urgency is 0.5 to prompt re-evaluation.

### Staleness urgency

```python
age = current_tick - stale.last_verified_tick
urgency = min(1.0, age * 0.002)
```

A fact becomes fully stale (urgency 1.0) after 500 ticks without re-verification. Staleness grows at 0.002 per tick.

---

## Output

`TemporalPressureService.calculate_urgencies()` returns `Mapping[str, float]` — a flat key→urgency dict. All keys from deadlines, cooldowns, and stale_facts are merged into this single map. If the same key appears in multiple categories, the last-evaluated value wins (deadlines → cooldowns → staleness in source order).

This map is not persisted — it is recalculated each tick and passed directly to the motivation domain.

---

## Lifecycle and mutation rules

- **No mutation:** `TemporalPressureService` is a pure function. It does not write to entity state.
- **No dirty tracking:** The time domain does not set dirty flags. It is called unconditionally when the motivation domain requests urgency data.
- **State ownership:** `cognition.subjective.time` (deadlines, cooldowns, stale_facts) is written by other systems (quest completion, action events, knowledge assimilation). The time domain only reads it.

---

## Edge cases

| Scenario | Behaviour |
|---|---|
| Entity has no deadlines/cooldowns/stale_facts | Returns empty map `{}` |
| Same key in both deadlines and cooldowns | Cooldown evaluation overwrites deadline value (order-dependent) |
| `ticks_left` exactly 100 | Urgency = `1.0 - (100/100) * 0.9` = 0.1 (boundary is exclusive — treated as "distant") |
| `age * 0.002 > 1.0` | Clamped to 1.0 by `min()` |

---

## Source areas

| File | Role |
|---|---|
| `src/domains/time/service.py` | `TemporalPressureService.calculate_urgencies()` — the entire domain |
| `src/core/cognition.py` | `DeadlineEntry`, `CooldownEntry`, `StalenessEntry` data models |

---

## Regression tests

- `tests/unit/domains/time/test_phase13_temporal_pressure_service.py` — deadline scaling boundary (ticks_left=0, 1, 100, 500), cooldown blocked/ready states, staleness growth rate, empty input → empty output

---

## Extension rules

1. To add a new urgency source (e.g., event-based pressure): add a new loop to `calculate_urgencies()` following the same key→urgency pattern. Do not add stateful logic — the service must remain a pure function.
2. To change the staleness rate constant (0.002): update it in `service.py` and update the full-stale tick threshold in this doc.
3. To add new entry types to `cognition.subjective.time`: extend `src/core/cognition.py` with the new model class, then add a corresponding evaluation block in `calculate_urgencies()`.
4. Never write to entity state from this service — urgency is a derived read-only signal.
