# Plan — TCK-20260619-E53-FACTION-DIPLOMACY

## Approach

XL epic scoped as 4 child epics. Each child epic is independently testable. E53A must ship before B; B before C; D can start during B.

## Sequence

**E53A → E53B → E53C → E53D** (strictly sequential at epic level; D can begin during B)

---

## E53A · Faction as Agent (child epic — M)

**FactionState** added to `AuthoritativeState`:
```python
@dataclass(frozen=True, slots=True)
class FactionState:
    faction_id: str
    territory: Tuple[str, ...] = ()
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)   # faction_id → DiplomaticState
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0
```

**FactionDecisionPhase** registered in `GovernorPolicy`:
- Runs at governance layer
- Reads faction territory, resources, tension
- Produces `FactionDirective(faction_id, directive_kind, target_faction, priority)`

**Entity-level directive propagation**:
- GUARD entities near contested border: patrol route urgency +2.0
- MERCHANT near allied region: trade route urgency +1.5
- HERO: quest route from faction commission +3.0

**Faction awareness**: factions observe world events (resource depletion, calamity, entity deaths) and update `tension_level`.

---

## E53B · Diplomacy (child epic — M)

Diplomatic state machine: `DiplomaticState` enum with NEUTRAL, TENSE, HOSTILE, WAR, ALLIED, VASSAL.

Diplomatic actions:
- `TreatyOffer(from_faction, to_faction, terms)` → sent as `FactionDirective`
- `TradeAgreement`, `NonAggressionPact`, `AllianceProposal`, `Betrayal`

Transition rules:
- NEUTRAL→TENSE: tension_level > 0.4
- TENSE→HOSTILE: tension_level > 0.7 OR resource conflict
- HOSTILE→WAR: FactionDecisionPhase chooses war when military_strength > opponent's
- WAR→NEUTRAL: war_exhaustion depletes military_strength below 0.3
- Any→ALLIED: via AllianceProposal acceptance

All diplomatic events flow through `NarrativeLedger`.

---

## E53C · Territorial Conflict & War (child epic — L)

**MilitaryConflictPhase** added at governance layer after `FactionDecisionPhase`:
- War declaration: `FactionDirective(WAR_DECLARED, target_faction)`
- Squad commitment: faction commits entity subset to contested region via `GroupRecord.roles["FACTION_SQUAD"]`
- Siege mechanics: besieging faction reduces target region's `service_availability` by 5% per tick; defender emits reinforcement directives
- Territory transfer: `RegionSovereigntyUpdate(region_id, new_faction_id)` via authoritative pipeline after siege victory

**War exhaustion**: `military_strength -= 0.001 per tick at war`. Both factions incentivized to end war when `military_strength < 0.3`.

---

## E53D · History Integration (child epic — S)

Wire all faction-level events to `NarrativeLedger`:
- `WAR_DECLARED`, `SIEGE_BEGINS`, `TERRITORY_TRANSFERRED`, `ALLIANCE_FORMED`, `PEACE_TREATY`
- `significance`: WAR_DECLARED=0.95, TERRITORY_TRANSFERRED=0.9, ALLIANCE_FORMED=0.8

`ChronicleCompiler` (E51) names wars: `"The {source_faction} War against {target_faction} (Year {era})"`.

Archive `docs/systems/grand_strategy.md` → `docs/archive/grand_strategy_v1.md`.
Create `docs/systems/faction_contract.md` (V2 contract, NOT based on grand_strategy.md).

### Implementation Notes for E53

Each child epic produces its own standard child tickets at scope time. E53A is the gating deliverable — without `FactionState` in `AuthoritativeState`, nothing else can proceed.
