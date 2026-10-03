# Investigation — TCK-20260619-E53-FACTION-DIPLOMACY

## Summary

Zero engine behavior code for factions exists. `src/content_semantics/faction.py` is catalog data only (faction IDs, names, relationships). `docs/systems/grand_strategy.md` documents V1 legacy behavior — **NOT a design source** per epic ticket; archive after Phase A. XL epic scoped as 4 child epics (A, B, C, D). Build entirely fresh against V2 architecture.

## Key Findings

### What Already Exists

**Faction enum** (`src/core/enums.py:L15`):
- `class Faction(IntEnum)` — numeric IDs for catalog factions (16 factions per D07 audit)

**GovernorPolicy** (`src/engine/policy.py:L10`):
- Governance phase insertion point — `FactionDecisionPhase` runs here
- Check actual GovernorPolicy fields before implementing to understand insertion pattern

**AuthoritativeState** (`src/core/state.py:L982`):
- No `FactionState` field — must be added as `factions: Dict[str, FactionState] = field(default_factory=dict)`

**D07 audit**: 16 factions, only 14 explicit relationships in catalog — relationship matrix is sparse. E53A must populate the full relationship matrix in `FactionState`.

**V1 grand_strategy.md** (reference only):
- V1 used `aggression` level + diplomacy thresholds: NEUTRAL→TENSE→HOSTILE→WAR→ALLIED
- V1 siege used building_state depletion
- **Do NOT port any V1 code or semantics**. Read V1 to know what to NOT repeat.

### Architecture Plan

**FactionState** is a V2 typed durable model:
```python
@dataclass(frozen=True, slots=True)
class FactionState:
    faction_id: str
    territory: Tuple[str, ...] = ()          # region_ids controlled
    resources: Dict[str, int] = field(...)   # gold, manpower, etc.
    diplomatic_relations: Dict[str, str] = field(...)  # faction_id → DiplomaticState enum value
    active_doctrines: Tuple[str, ...] = ()   # e.g. "EXPAND", "DEFEND", "SEEK_ALLIANCE"
    military_strength: float = 1.0
    tension_level: float = 0.0              # 0.0–1.0
```

**FactionDecisionPhase** runs at governance layer (after GovernorPolicy, or as a registered governance step). Produces `FactionDirective` events that propagate to entity route scoring.

### What Is Missing (entire system)
1. `FactionState` model + `AuthoritativeState.factions` field
2. `FactionDecisionPhase` governance step + `FactionDirective` model
3. Diplomatic state machine (NEUTRAL/TENSE/HOSTILE/WAR/ALLIED/VASSAL)
4. Diplomatic actions (treaty offer, trade agreement, non-aggression, alliance, betrayal)
5. `MilitaryConflictPhase`: war declaration, squad commitment, siege mechanics
6. Territory transfer via authoritative pipeline
7. `NarrativeLedger` integration: all faction events → narrative
8. Archive `docs/systems/grand_strategy.md` → `docs/archive/grand_strategy_v1.md`

### Child Epics (4 sub-epics, not standard tickets)

E53 is XL — each phase is a child epic requiring its own investigation at implementation time:
- **E53A** (M): FactionState model + FactionDecisionPhase + directive propagation
- **E53B** (M): Diplomatic actions + state machine (NEUTRAL → ... → WAR/ALLIED)
- **E53C** (L): Territorial conflict, war declaration, siege, territory transfer
- **E53D** (S): History integration — all faction events → NarrativeLedger + Chronicle names
