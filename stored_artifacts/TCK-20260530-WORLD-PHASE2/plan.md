---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE2
artifact_type: plan
tags: [world, phase2]
---

# Phase 2 Execution Plan

We will implement the content semantics layer systematically:

1. **Task 2.1**: Implement `FactionSemanticsService` in `src/content_semantics/faction.py`:
   - Resolve `Faction` enum from definitions.
   - Calculate hostility relations (`is_hostile(faction_a, faction_b)`).
   - Check sovereign alignments (defender, invader, neutral).
2. **Task 2.2**: Implement `RoleSemanticsService` in `src/content_semantics/role.py`:
   - Resolve `EntityRole` enum from definitions.
   - Identify combatants, workers, and civilian families.
   - Fetch default stats, inventory, and cognition profile mappings.
3. **Task 2.3**: Implement `DefaultSemanticsService` in `src/content_semantics/defaults.py` providing normalized fallback parameters.
4. **Task 2.4**: Update mappers in `src/worldbuilding/compiler.py` (`get_faction_enum` and `get_role_enum`) to delegate to these services when a repository catalog is available, preserving fallback rules.
5. **Task 2.5**: Write focused tests in `tests/unit/content_semantics/` and run the unit test suite.
