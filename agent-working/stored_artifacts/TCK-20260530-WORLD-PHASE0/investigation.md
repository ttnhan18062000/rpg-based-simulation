---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE0
artifact_type: investigation
tags: [world, phase0]
---

# Phase 0 Investigation Notes

This investigation involves identifying:
- Current hardcoded semantic constants, defaults, and type mappings in `src/`.
- Dependency directions to document the architecture freeze.
- Existing repository structures.

We will find the exact lines for:
1. `get_faction_enum` and `get_role_enum`
2. Hardcoded defaults in `WorldCompiler` (e.g. `hp=100`, `atk=10`,building HP, starting gold, faction IDs).
3. Hardcoded direct enum comparisons or checks in `src/engine/` or `src/world/`.
4. Dead recipe profile fields in `src/worldbuilding/recipe.py`.
