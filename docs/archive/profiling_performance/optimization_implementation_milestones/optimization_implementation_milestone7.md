---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 7 — LOD / Background Simulation

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
