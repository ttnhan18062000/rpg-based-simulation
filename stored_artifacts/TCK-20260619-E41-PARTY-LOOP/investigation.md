# Investigation — TCK-20260619-E41-PARTY-LOOP

## Summary

Group formation and social contracts exist. The `GroupRecord` at `src/core/state.py:L507` is the authoritative durable model for multi-entity coordination. It has `leader_id`, `member_ids`, `roles`, `contract_id`, and aptitude averages — but no `formation_tick`, `grievance_log`, `shared_inventory`, `escort_target_id`, or `reward_pool`. This epic adds sustained lifecycle *on top of* the existing group infrastructure.

## Key Findings

### What Already Exists

**GroupRecord** (`src/core/state.py:L507`):
```python
@dataclass(frozen=True, slots=True)
class GroupRecord:
    id: int
    leader_id: int
    member_ids: Set[int]
    anchor: tuple[float, float]
    shared_target_id: Optional[int] = None
    contract_id: Optional[str] = None
    cohesion_radius: float = 5.0
    last_updated_tick: int = 0
    roles: Dict[int, str]   # entity_id -> role_name
    str_apt, int_apt, agi_apt, vit_apt, end_apt: float
```

**ContractState** (`src/core/strategic.py:L159`):
- Formal obligations between two parties; `kind`, `terms`, `expiry_tick`, `status`

**D01 audit** (`docs/audits/D01_rpg_feature_impact.md`): Party lifecycle rated [PARTIAL] — formation done, no sustained lifecycle, no reward split, no escort.

**Stored artifacts** to read before implementing:
- `stored_artifacts/TCK-20260424-PH3-M2-GROUP-COORDINATION/` — formation logic
- `stored_artifacts/TCK-20260501-SOCIAL-LIFECYCLE/` — social lifecycle basics
- `stored_artifacts/TCK-20260410-PH4-SOCIAL-CONTRACTS/` — contract formation

### What Is Missing

1. **Sustained lifecycle fields** in GroupRecord: `formation_tick`, `escort_target_id`, `dissolution_tick`, `grievance_log[]`, `reward_pool`
2. **Leadership election** mechanism (Charisma = `sociability` in OCEAN model via `PersonalityComponent`)
3. **FairShareProtocol** — no reward distribution logic
4. **Class synergy bonuses** — no cross-class scoring modifiers in `src/domains/adventure/scoring.py`
5. **Defection mechanics** — no `betrayal_desertion` event in `src/observability/events.py`
6. **Escort behavior** — no ESCORT_TARGET role that re-weights route scoring

### Architecture Note

Do NOT create a separate `PartyState` class — extend `GroupRecord` with new optional fields. GroupRecord is already in `AuthoritativeState` via `groups: Dict[int, GroupRecord]`. Adding a second parallel class would create a state bifurcation problem.

Leadership election: `sociability` field of `PersonalityComponent` is the "Charisma-equivalent" (per mechanics bible chapter 01 — OCEAN model, Big Five traits stored in PersonalityComponent). Leadership switch ≥ every 100 ticks among members where `sociability > 0.6`.

Escort behavior: ESCORT_TARGET is a role value in `GroupRecord.roles` (string values). When an entity has `roles[entity_id] == "ESCORT_TARGET"`, all other group members should score `PROTECT_TARGET` route type above own survival routes in `src/domains/adventure/scoring.py`.

### Related Docs
- `docs/mechanics/04_strategic_cognition.md` §4 (route scoring — add synergy bonus and escort modifier)
- `docs/mechanics/02_combat_laws.md` §2 (combat modifier ranges — verify before adding synergy values)
- `docs/simulation/domains/social_systems_contract.md` (update boundary table)

## Unknowns Resolved
- "Charisma-equivalent" = `sociability` in PersonalityComponent (Big Five O/C/E/A/N; sociability ≈ Extraversion)
- GroupRecord is the correct place to add lifecycle fields — no parallel PartyState model needed
