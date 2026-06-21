---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Ba-DIPLO-STATE
phase: open
date: 2026-06-22
tags: [faction, diplomacy, diplomatic-state, enum, core-model, phase-5]
---

# TCK-20260619-E53Ba-DIPLO-STATE

## Title
Epic 5.3Ba · DiplomaticState Enum + FactionState Migration

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add `DiplomaticState` as a typed str-enum in `src/core/enums.py` and migrate `FactionState.diplomatic_relations` from `Dict[str, str]` (raw label strings, planned in E53Aa) to `Dict[str, DiplomaticState]`. Update `FactionUpdate.diplomatic_relations_set` to match. Update apply-path coercion so serialized string values round-trip correctly.

**Requires:** TCK-20260619-E53Aa-FACTION-STATE (FactionState + FactionUpdate must exist)

## Scope

**DiplomaticState enum** (in `src/core/enums.py`, after `EntityRole`):
```python
class DiplomaticState(str, Enum):
    NEUTRAL = "NEUTRAL"
    TENSE = "TENSE"
    HOSTILE = "HOSTILE"
    WAR = "WAR"
    ALLIED = "ALLIED"
    VASSAL = "VASSAL"
```

**FactionState migration** (in `src/core/state.py`):
- Change field type annotation: `diplomatic_relations: Dict[str, DiplomaticState] = field(default_factory=dict)`
- Update `to_canonical_dict()` to serialize as `{k: v.value for k, v in ...}` (string values)
- Update `from_dict()` to deserialize as `{k: DiplomaticState(v) for k, v in ...}`

**FactionUpdate migration** (in `src/core/updates.py`):
- Change field type annotation: `diplomatic_relations_set: Dict[str, DiplomaticState] = field(default_factory=dict)`
- `is_noop()` check: `diplomatic_relations_set` empty dict counts as noop

**Apply path** (`src/engine/apply_plan.py` or `src/engine/apply.py`):
- When applying `FactionUpdate.diplomatic_relations_set`, merge into `FactionState.diplomatic_relations` (replace specific keys, not full dict overwrite).
- Coerce any raw string values from deserialization via `DiplomaticState(v)` before storing.

## Out of Scope
- Transition logic (E53Bc)
- Diplomatic action types (E53Bb)
- NarrativeLedger wiring (E53Bd)

## Acceptance Criteria
- `DiplomaticState` enum is importable from `src.core.enums`
- `FactionState(faction_id="A", diplomatic_relations={"B": DiplomaticState.ALLIED})` constructs, serializes, and deserializes with round-trip fidelity
- `FactionUpdate(faction_id="A", diplomatic_relations_set={"B": DiplomaticState.HOSTILE})` applies correctly via apply path — only the specified key is updated; other keys are preserved
- `FactionState.to_canonical_dict()` emits string values ("ALLIED", "HOSTILE", etc.) for JSON compatibility
- `FactionState.from_dict()` with string values reconstructs typed `DiplomaticState` values
- `test_diplomatic_state_enum_round_trip` passes
- `test_faction_state_diplomatic_relations_apply` passes
- Existing faction state and AuthoritativeState tests continue to pass

## Related Tickets
- TCK-20260619-E53B-DIPLOMACY (parent epic)
- TCK-20260619-E53Aa-FACTION-STATE (required — FactionState must exist)
- TCK-20260619-E53Bb-DIPLO-ACTIONS (depends on this)

## Related Docs
- `docs/core/state.md` (immutability law, serialization convention)
- `docs/engine/authoritative_mutation_pipeline_contract.md` (apply-path rules)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`

## Related Code Areas
- `src/core/enums.py` (add DiplomaticState after EntityRole)
- `src/core/state.py` (FactionState.diplomatic_relations type + serialization)
- `src/core/updates.py` (FactionUpdate.diplomatic_relations_set type)
- `src/engine/apply_plan.py` or `src/engine/apply.py` (apply logic)
- `tests/unit/faction/test_diplomacy.py` (new or existing test file)

## Assumptions / Open Questions
- `DiplomaticState(str, Enum)` ensures that string coercion (`DiplomaticState("ALLIED")`) works without a custom validator — confirmed by existing `str`-based enums in the codebase (`EntityRole`, `Faction` are IntEnum; `DiplomaticState` will be the first str-enum in `enums.py`; verify no import cycle introduced).
- Default relation between any two unlinked factions is implicitly `NEUTRAL`; absence of a key in `diplomatic_relations` means NEUTRAL — do NOT populate the dict with all-NEUTRAL pairs at construction time.
- The `Faction(IntEnum)` on `IdentityComponent` is a separate numeric entity tag and must NOT be replaced or confused with the string `faction_id` key used in `FactionState`.

## Implementation Notes
- Follow the same serialization pattern as `QuestOpportunityStatus` or `ProjectStatus` in existing enums.
- Apply-path merge for `diplomatic_relations_set`: iterate the update dict and set each key on the reconstructed `FactionState` — since `FactionState` is frozen, this requires constructing a new `FactionState` via `dataclasses.replace()`.
- `is_noop()` on `FactionUpdate` must treat empty `diplomatic_relations_set` (not just None) as noop — verify existing `is_noop()` implementation handles dict fields correctly.

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
pytest tests/unit/core/test_state.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
