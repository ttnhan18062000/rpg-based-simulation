---
status: active
layer: engine
authority: P1
audience: developer
---

# Progression Surface Support

Defines the official support boundary for the integrated resource progression loop. Identifies the authoritative behaviors verified by the engine and establishes the truth for current engine claims.

## Support Matrix

| Progression Layer | Support Level | Authority | Verification Gate | Determinism |
| :--- | :--- | :--- | :--- | :--- |
| **Grid Movement** | OFFICIAL | Authoritative Apply | MVM_PATH_20 | HASH_MATCH |
| **Interaction (Harvest)** | OFFICIAL | InteractionSystem | RES_HARVEST_3 | HASH_MATCH |
| **Town Resolution** | OFFICIAL | BlacksmithSystem | TOWN_PROG_LOOP | EQUIVALENT |
| **Strategic AI (Blockers)** | OFFICIAL | StrategicIntelligence | LOOP_INTEGRITY | HASH_MATCH |
| **Strategic AI (Leads)** | OFFICIAL | StrategicIntelligence | LOOP_INTEGRITY | HASH_MATCH |
| **Redirection (AI)** | OFFICIAL | StrategicRedirection | INTEG_RESOURCE_LOOP | PROTECTED |

## Supported Behavioral Boundaries

### Movement & Interaction
- **Supported**: 1×1 grid movement toward coordinates. Channeled interaction (harvesting) with time-bound progress.
- **Exclusion**: Pathfinding through dynamic obstacles (other entities) is currently best-effort only.

### Resource Progression Loop
- **Supported**: The full cycle of Fail → Block → Seek → Harvest → Resolve is verified.
- **Limitation**: Only `Material` blockers and `Location` leads are supported. Crafting blockers for non-material resources are excluded.

### Execution Modes
- **Sequential**: Supported.
- **Concurrent**: Supported where protected by `AuthoritativeState` application rules.

## Intentional Divergences from Legacy

| Feature | Legacy Behavior | Current Behavior | Reasoning |
| :--- | :--- | :--- | :--- |
| **Harvest Completion** | 1-tick delay | Immediate (tick 0) | Completion and item addition happen in the same tick as the threshold. |
| **Recipe Costs** | Steel Sword (2 ore) | Steel Sword (1 ore) | Simplified for single-loop certification scenarios. |
| **Redirection Speed** | Reactive (next tick) | Proactive (same tick) | AI reacts to inventory changes within the same resolution pass. |

## Certification Scenarios

All supported behaviors must pass the following scenarios to allow a release:
- `IDLE_CLEAN`
- `MVM_PATH_20`
- `RES_HARVEST_3`
- `INTEG_RESOURCE_LOOP` (Full Cycle Proof)

## Known Limitations
- Resource nodes do not yet support complex regeneration.
- The Blacksmith is the only supported town-resolution building.
- Multi-actor contention is handled by deterministic resolution order but lacks complex negotiation.
