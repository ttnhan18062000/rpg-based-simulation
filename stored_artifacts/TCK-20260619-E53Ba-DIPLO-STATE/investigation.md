---
ticket_id: TCK-20260619-E53Ba-DIPLO-STATE
phase: investigate
date: 2026-06-22
---

# Investigation — TCK-20260619-E53Ba-DIPLO-STATE

## What Exists

### FactionState (src/core/state.py:570)
- `diplomatic_relations: Dict[str, str]` — raw string labels ("allied", "hostile", etc.)
- `to_canonical_dict()` emits `dict(sorted(self.diplomatic_relations.items()))` (raw strings pass through)
- `from_dict()` loads `dict(d.get("diplomatic_relations", {}))` (no coercion)

### FactionUpdate (src/core/updates.py:837)
- `diplomatic_relations_set: Dict[str, str]` — matching raw string type
- `is_noop()` checks `not self.diplomatic_relations_set` — correct for dict

### Apply path (src/engine/apply.py:342)
- Merges with `{**existing.diplomatic_relations, **fu.diplomatic_relations_set}` (no coercion)

### Scoring (src/domains/adventure/scoring.py:131)
- Checks `any("allied" in fs.diplomatic_relations.values() ...)` — LOWERCASE "allied"
- After migration to DiplomaticState.ALLIED ("ALLIED"), this check silently breaks — MUST fix

### Existing tests with raw strings
- `tests/unit/faction/test_faction_state.py:13` — uses "hostile", "allied" raw strings
- `tests/unit/faction/test_faction_state.py:137` — FactionUpdate with "hostile" raw string
- `tests/unit/faction/test_faction_directive_propagation.py:74,91,158` — "allied", "hostile" raw strings

## Key Decisions

1. **DiplomaticState placement**: After EntityRole in enums.py (ticket spec); no @unique decorator (follows ReasonCode(str, Enum) pattern)
2. **Coercion in apply path**: apply.py merges dicts, must coerce any raw str values via DiplomaticState(v) for safety during transition / deserialization edge cases
3. **scoring.py fix is in scope**: migration breaks the "allied" check — silent regression if not fixed
4. **Existing tests**: must be updated to use DiplomaticState enum values in all FactionState/FactionUpdate construction

## Import Chains (no cycles)
- `src.core.enums` → no project imports (safe)
- `src.core.state` already imports from `src.core.enums` (Faction, EntityRole)
- `src.core.updates` imports `from src.core.enums import ReasonCode` (add DiplomaticState)
- `src.engine.apply` imports `from src.core.enums import EntityRole, Faction, ReasonCode` (add DiplomaticState)
- `src.domains.adventure.scoring` imports from `src.engine.faction_constants` — `src.core.enums` is safe to add
