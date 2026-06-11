---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
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
