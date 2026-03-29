This is a comprehensive technical proposal that synthesizes the architectural core of **v1** with the advanced deterministic, AI, and optimization strategies of **v2**.

This document is designed to serve as a **specification for implementation**.

---

# Technical Specification: Deterministic Concurrent RPG Engine

**Version:** 2.0 (Merged & Revised)
**Status:** Approved for Implementation

---

## 1. Executive Summary

The goal is to engineer a high-fidelity **2D RPG simulation** that balances complex entity behavior with absolute architectural strictness. The system simulates a living world containing autonomous agents (NPCs), generators, and environmental rules.

**Key Technical Differentiators:**
1.  **Concurrency without Race Conditions:** Heavy AI logic runs in parallel threads; world mutation is serialized and single-threaded.
2.  **Absolute Determinism:** Given a `WorldSeed` and `InputLog`, the simulation will reproduce the exact same state, byte-for-byte, on any machine.
3.  **Observability:** The split between "Intent" (AI) and "Result" (World) allows for deep debugging and replayability.

---

## 2. Architectural Axioms (The Hard Rules)

These constraints are non-negotiable. Breaking them breaks the engine.

1.  **Single-Writer / Multi-Reader:**
    *   Only the `WorldLoop` thread may mutate the `WorldState`.
    *   Worker threads (AI) only read **Immutable Snapshots**.
2.  **Intent vs. Effect:**
    *   Workers produce **Intent** (e.g., `ActionProposal: Move(North)`).
    *   The World produces **Effect** (e.g., `Entity moves to (x, y-1)` OR `Blocked by Wall`).
3.  **Deterministic Randomness:**
    *   `random()` is banned in logic code.
    *   All entropy is derived from hashed seeds keyed by `(Domain, EntityID, Tick)`.
4.  **Atomic Ticks:**
    *   Time advances in discrete steps (ticks). All actions scheduled for `Tick N` are resolved before `Tick N+1` begins.

---

## 3. High-Level Architecture

```mermaid
graph TD
    subgraph "Parallel Worker Pool"
        W1[Worker Thread 1]
        W2[Worker Thread 2]
        W3[Worker Thread 3]
    end

    subgraph "Shared Memory"
        Q[Action Queue (Thread-Safe)]
        S[Immutable Snapshot (Read-Only)]
    end

    subgraph "Authoritative Core"
        WL[WorldLoop (Single Thread)]
        WS[Mutable World State]
        RNG[Deterministic Seed Generator]
    end

    WL -- 1. Creates --> S
    S -.-> W1 & W2 & W3
    W1 & W2 & W3 -- 2. Compute Intent --> Q
    Q -- 3. Consumed by --> WL
    WL -- 4. Mutates --> WS
    RNG -.-> WL
```

---

## 4. The Data Model

### 4.1 World State (Mutable, Private)
The "Truth" acts as a database. It is never exposed directly to workers.

```python
class WorldState:
    tick: int
    entities: Dict[int, Entity]
    map: Grid[Material]
    spatial_index: SpatialHash  # Optimization for neighbor lookups
    
    # Global RNG Configuration
    seed: int
```

### 4.2 The Entity
Entities are strictly identifiers with attached state components.

```python
@dataclass
class Entity:
    id: int             # Unique, Monotonic, Never Reused
    kind: str           # "goblin", "generator", "hero"
    pos: Vector2        # (x, y)
    stats: Stats        # HP, ATK, SPD, Level
    state: AIState      # "IDLE", "COMBAT", "FLEEING"
    next_act_at: float  # The absolute time this entity can act again
```

### 4.3 The Immutable Snapshot (Public)
To prevent locking, the WorldLoop generates a "View" of the world.
*   **Optimization:** Uses `MappingProxyType` or Copy-on-Write to avoid deep copying the whole world every tick.
*   **Scope:** Contains only what is necessary for AI (Map, Visible Entities).

---

## 5. The WorldLoop (Engine Core)

The `WorldLoop` is the heartbeat. It does not "sleep" on individual entities; it manages a priority queue of events.

### 5.1 The Loop Cycle
1.  **Phase 1: Scheduling**
    *   Identify entities whose `next_act_at <= current_time`.
    *   If Entity is a `Generator`: Immediate execution (Spawn).
    *   If Entity is a `Character`: Dispatch to **Worker Pool**.
2.  **Phase 2: Wait & Collect**
    *   Wait for workers to return `ActionProposals`.
    *   *Hard Timeout:* If a worker hangs, the entity misses its turn (prevents engine stall).
3.  **Phase 3: Conflict Resolution & Application**
    *   Sort actions deterministically (see Section 7).
    *   Apply valid actions to `WorldState`.
    *   Reject invalid actions (log reason).
4.  **Phase 4: Cleanup & Advancement**
    *   Remove dead entities.
    *   Update Spatial Index.
    *   Advance `current_time` to the next scheduled event.

---

## 6. The Intelligence Layer (AI)

AI logic is stateless. It receives a Snapshot and outputs a Proposal.

### 6.1 State Machine + Utility Scoring
Instead of simple if/else, AI uses a tiered approach:
1.  **State Check:** (e.g., Am I low HP? $\to$ Switch to `FLEE`).
2.  **Utility Scoring:** Score all possible actions.
    *   `Score(MoveAway) = Distance * SafetyWeight`
    *   `Score(Attack) = Damage * AggressionWeight`
3.  **Tie-Breaking:** If scores are equal, prefer the action with the lowest internal enum ID.

### 6.2 Perception
AI is not omniscient. The Worker calculates:
*   **Vision:** Raycast or Manhattan distance check against the Snapshot.
*   **Memory:** If the entity saw a player 5 ticks ago, it remembers the location (stored in `AIState`), even if the player is now hidden.

### 6.3 Output: Action Proposal
```python
@dataclass
class ActionProposal:
    actor_id: int
    verb: ActionType    # MOVE, ATTACK, REST
    target: Any         # Coordinates or EntityID
    reason: str         # For debugging ("Fleeing low HP")
```

---

## 7. Determinism & Randomness (The RNG Model)

To guarantee replayability, we implement **Domain-Separated Hashing**.

### 7.1 The Golden Rule
**The outcome of Tick `T` depends ONLY on WorldSeed + State at `T-1`.** It implies that thread scheduling order must strictly **not** matter.

### 7.2 RNG Domains
We do not use a single `random` object. We use a hashing function to generate pseudo-random numbers on the fly.

**Formula:**
`RNG_Value = Hash(WorldSeed, Domain, EntityID, Tick)`

**Domains:**
*   `COMBAT`: Hit chance, Crit chance, Damage variance.
*   `LOOT`: Item drops.
*   `AI_DECISION`: Choosing between two equal-score tiles.
*   `SPAWN`: Stats of newly generated monsters.

**Example Implementation:**
```python
def get_combat_roll(attacker_id, tick):
    # Returns float 0.0 to 1.0
    return xxhash64(seed + "COMBAT" + attacker_id + tick) / MAX_UINT64
```
*Benefits:* If we add a new feature (e.g., Weather) using a `WEATHER` domain, it will not change the combat rolls of existing replays.

---

## 8. Conflict Resolution Policies

When parallel workers submit conflicting intents, the WorldLoop arbitrates deterministically.

### 8.1 Movement Conflicts (The "Doorway Problem")
*Scenario:* Entity A and Entity B both try to move to $(5, 5)$ in the same tick.
*   **Policy:** The Entity with the **earliest** `next_act_at` wins.
*   **Tie-Breaker:** If times are equal, the **lowest EntityID** wins.
*   **Result:** Winner moves. Loser stays put (or performs a "Wait" action) and is rescheduled slightly later.

### 8.2 Combat Conflicts
*Scenario:* A and B both attack C. C dies from A's hit.
*   **Policy:** Actions are processed sequentially based on initiative (Speed).
*   **Result:** A kills C. B's attack validates against C (who is now dead), fails validation, and converts to a "Whiff" or "Look confused" action.

---

## 9. Optimization Strategy

### 9.1 Spatial Hashing
Instead of iterating 1000 entities to find "nearest enemy":
*   The World maintains a dictionary: `Map<(int, int), List[EntityID]>`.
*   Workers query this map (via Snapshot) for O(1) adjacency checks.

### 9.2 Data-Oriented Design (Future Proofing)
While Python classes are used for the prototype, the design is compatible with **ECS (Entity Component System)** arrays (using `numpy` or `structs`) if performance becomes a bottleneck > 10,000 entities.

---

## 10. Roadmap

### Phase 1: The Skeleton
*   Implement `WorldLoop`, `ActionQueue`, and basic `Entity`.
*   Implement `Snapshot` generation.
*   **Goal:** A dot moving on a grid with deterministic logs.

### Phase 2: The Brain
*   Implement Worker ThreadPool.
*   Implement `MoveAction` and `RestAction`.
*   Implement Domain-RNG.
*   **Goal:** Multiple dots wandering randomly but reproducibly.

### Phase 3: The Conflict
*   Implement `CombatAction` and `Stats`.
*   Implement Conflict Resolution (Resolution Policy).
*   **Goal:** Entities kill each other until one remains. Replay file works.

### Phase 4: The Simulation
*   Implement Generators and AI State Machines (Flee/Hunt).
*   Add Spatial Hashing.
*   **Goal:** Self-sustaining ecosystem.