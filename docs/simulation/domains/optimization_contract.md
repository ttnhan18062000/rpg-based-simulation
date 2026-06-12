---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [domains, optimization, performance, cache, degradation, feature-flags, contract]
---

# Optimization Domain Contract

**Source:** `src/domains/optimization/` (10 files)  
**Pipeline phase:** Phase 10 — Feature rollout control; cross-cutting performance utilities  
**Authoritative status:** NOT authoritative — advisory performance utilities only. Does not own simulation state.

---

## Purpose

The optimization domain provides cross-cutting performance and rollout utilities used by other domains and the engine. It is the only domain that may be imported by other domain packages (see [domain_ownership_map.md](domain_ownership_map.md) — interaction rule 3).

---

## CacheStrategy (`cache_strategy.py`)

LRU (Least Recently Used) bounded cache for expensive per-region or per-query lookups.

```
CacheKey(region_id, query_type, extra_param=None)  # frozen, hashable
CacheStrategy(max_size=100)
  .get(key) → Optional[Any]    # None on miss; moves key to MRU position
  .put(key, value) → None      # evicts LRU entry when max_size exceeded
```

**Eviction rule:** When `len(cache) >= max_size`, the oldest (least-recently-used) key is evicted before inserting the new entry.

**Constraint:** `max_size` must be set explicitly at construction. Callers must not create unbounded caches (no `max_size=None` or `max_size=0`).

---

## GracefulDegradationManager (`degradation.py`)

Monitors tick time pressure and enters degraded execution states to preserve frame rate.

### DegradationLevel Enum

| Level | Trigger condition (`ratio = tick_ms / limit_ms`) | Provider cap |
|---|---|---|
| `NORMAL` | ratio < 0.80 | Full cap |
| `CONSTRAINED` | 0.80 ≤ ratio < 0.95 | Reduced |
| `DEGRADED` | 0.95 ≤ ratio < 1.00 | original // 3 |
| `CRITICAL` | ratio ≥ 1.00 (limit exceeded) | original // 4 (min 1) |

`update_pressure(tick_time_ms, limit_ms)` → returns new `DegradationLevel`.  
`get_provider_cap(original_cap)` → returns adjusted provider cap for the current level.

**Stateful:** `GracefulDegradationManager` maintains `_level` across calls. One instance per Kernel run.

---

## FeatureFlagManager (`feature_flags.py`)

Manages Phase 10 feature rollout modes. Controls which domain features are active in a given run.

### FeatureMode Enum

| Mode | Meaning |
|---|---|
| `OFF` | Feature disabled — domain must not be called on the tick path |
| `SHADOW` | Feature runs but output is discarded (parallel shadow execution) |
| `ON` | Feature active; output applied |
| `STRICT` | Feature active; any failure raises immediately (no silent degradation) |

### Known Flags

| Flag | Controls |
|---|---|
| `ENABLE_WORLD_CAPABILITY_LAYER` | World capability domain activation |
| `ENABLE_SELF_MODEL_COGNITION` | Self-model cognition pipeline |
| `ENABLE_ADVENTURE_ROUTING` | Adventure/route resolution |
| `ENABLE_COMBAT_ENGAGEMENT` | combat_engagement domain (Phase 4) |
| `ENABLE_BELIEF_ASSIMILATION` | information domain (Phase 5) |
| `ENABLE_PROGRESSION_EVOLUTION` | progression domain |
| `ENABLE_SOCIAL_COOPERATION` | cooperation domain |

**Rule:** Before calling any domain on the tick path, check `FeatureFlagManager.get_flag(flag_name)`. If the mode is `OFF`, skip the domain call entirely. If the mode is `SHADOW`, run but do not apply output.

---

## BudgetManager (`budget_manager.py`)

Tracks compute budget allocation per tick phase. Enforces that no phase overspends its allocated ms budget.

---

## DirtyScheduler (`dirty_scheduler.py`)

Schedules entities for domain processing based on dirty-flag state — only processes entities whose relevant state changed since the last tick. Reduces unnecessary domain evaluations.

---

## MemoryLimits (`memory_limits.py`)

Declares per-domain RSS memory ceilings. If a domain's data structure exceeds its ceiling, it must evict or truncate (never silently grow unbounded).

---

## ProviderEnforcement (`provider_enforcement.py`)

Enforces provider count caps derived from `GracefulDegradationManager.get_provider_cap()`. Called by the scheduler before dispatching domain evaluations.

---

## RolloutProfiles (`rollout_profiles.py`)

Defines named rollout configurations (sets of feature flags) for different deployment profiles (development, staging, production, benchmark). Used by `FeatureFlagManager` initialization.

---

## TraceGovernor (`trace_governor.py`)

Controls trace/observability verbosity based on `DegradationLevel`. Under `CRITICAL`, tracing is suppressed to reduce overhead.

---

## Constraints

- `CacheStrategy.max_size` must always be a positive integer — never use unbounded caches.
- `GracefulDegradationManager` is stateful — do not share instances across parallel tick threads.
- `FeatureFlagManager` flag values must not be changed after kernel initialization — flags are set once per run.
- optimization utilities must not own simulation state — they are performance helpers only.
- Other domains may import from `src/domains/optimization/` — this is the only permitted cross-domain import.
