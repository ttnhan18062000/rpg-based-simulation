---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 3 — Dirty Entity Tracking

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
