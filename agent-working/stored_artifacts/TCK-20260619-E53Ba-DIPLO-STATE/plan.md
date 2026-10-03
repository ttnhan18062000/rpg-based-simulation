---
ticket_id: TCK-20260619-E53Ba-DIPLO-STATE
phase: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E53Ba-DIPLO-STATE

## Changes

1. **src/core/enums.py** — add DiplomaticState(str, Enum) after EntityRole
2. **src/core/state.py** — import DiplomaticState; migrate FactionState.diplomatic_relations type + serialization/deserialization
3. **src/core/updates.py** — import DiplomaticState; migrate FactionUpdate.diplomatic_relations_set type
4. **src/engine/apply.py** — import DiplomaticState; add str→DiplomaticState coercion in merge
5. **src/domains/adventure/scoring.py** — fix "allied" → DiplomaticState.ALLIED comparison
6. **tests/unit/faction/test_faction_state.py** — update raw strings to typed enum values
7. **tests/unit/faction/test_faction_directive_propagation.py** — update raw strings to typed enum values
8. **tests/unit/faction/test_diplomacy.py** — new test file (round-trip, apply, serialization)
