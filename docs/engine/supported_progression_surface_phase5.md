# Supported Progression Surface Matrix (Phase 5)

## 1. Purpose
This document defines the official support boundary for the integrated resource progression loop in `src_v2`. It identifies the authoritative behaviors verified through Phase 5 recovery and establishes the truth for current engine claims.

## 2. Support Matrix

| Progression Layer | Support Level | Authority | Verification Gate | Determinism |
| :--- | :--- | :--- | :--- | :--- |
| **Grid Movement** | OFFICIAL | Authoritative Apply | MVM_PATH_20 | HASH_MATCH |
| **Interaction (Harvest)**| OFFICIAL | InteractionSystem | RES_HARVEST_3 | HASH_MATCH |
| **Town Resolution** | OFFICIAL | BlacksmithSystem | TOWN_PROG_LOOP | EQUIVALENT |
| **Strategic AI (Blockers)**| OFFICIAL | StrategicIntelligence | LOOP_INTEGRITY | HASH_MATCH |
| **Strategic AI (Leads)** | OFFICIAL | StrategicIntelligence | LOOP_INTEGRITY | HASH_MATCH |
| **Redirection (AI)** | OFFICIAL | StrategicRedirection | INTEG_RESOURCE_LOOP| PROTECTED |

## 3. Supported Behavioral Boundaries

### Movement & Interaction
- **Official Support**: 1x1 grid movement toward coordinates. Channeled interaction (harvesting) with time-bound progress.
- **Exclusion**: Pathfinding through dynamic obstacles (other entities) is currently best-effort only.

### Resource Progression Loop
- **Official Support**: The full cycle of Fail -> Block -> Seek -> Harvest -> Resolve is officially supported and verified.
- **Limitation**: Only "Material" blockers and "Location" leads are officially supported. Crafting blockers for non-material resources (e.g., specific NPC interactions) are EXCLUDED.

### Execution Modes
- **Sequential**: Officially supported.
- **Concurrent**: Officially supported where protected by `AuthoritativeState` application rules.

## 4. Intentional Divergences from Legacy (src)

| Feature | Legacy Behavior | V2 Behavior | Reasoning |
| :--- | :--- | :--- | :--- |
| **Harvest Completion** | 1-Tick Delay | Immediate (Tick 0) | **Logic Truth**: completion and item addition happen in the same tick as the threshold. |
| **Recipe Costs** | Steel Sword (2 Ore) | Steel Sword (1 Ore) | **Loop Proofing**: Simplified for single-loop certification scenarios. |
| **Redirection Speed** | Reactive (Next Tick) | Proactive (Same Tick) | **Effectiveness**: AI reacts to inventory changes within the same resolution phase. |

## 5. Certification Scenarios
All supported behaviors must pass the FOLLOWING certification scenarios to allow a release:
- `IDLE_CLEAN`
- `MVM_PATH_20`
- `RES_HARVEST_3`
- `INTEG_RESOURCE_LOOP` (Full Cycle Proof)

## 6. Known Limitations
- Resource nodes do not yet support complex regeneration.
- The Blacksmith is the only supported town-resolution building in Phase 5.
- Multi-actor contention is handled by deterministic resolution order but lacks complex negotiation.
