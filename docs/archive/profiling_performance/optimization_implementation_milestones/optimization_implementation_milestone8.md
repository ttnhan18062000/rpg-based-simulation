---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 8 — ApplyPath and State Update Efficiency

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
