---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-RPG-CORE-HARDENING
artifact_type: investigation
tags: [rpg, core, hardening]
---

# Investigation: RPG Core Drift

## Findings
- Multi-Entity Updates: Domain logic previously only supported single-entity updates from actions, causing rewards or secondary effects to be lost.
- Target Lookup: Executor-side NeighborViews were often incomplete, requiring a fallback to context-level entity lookup.
- Mortality: Legacy code had complex generation rules that were partially missing in V2.
- Corpses: Corpse spawning was inconsistent and often failed to transfer inventory correctly.

## Resolution
- Unified update mapping in Worker/Executor.
- Authoritative generation logic (1-3 Rebirth, 4 Permadeath).
- Centralized corpse management in ApplyPath.
