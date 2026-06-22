# Investigation — TCK-20260619-E53Ac-DIRECTIVE-PROP

## Key Findings

### 1. Pipeline Ordering Issue (CRITICAL)
`faction_decision` block (Phase 8b, pipeline.py:221) runs AFTER `adventure_decision` (Phase 3, pipeline.py:167).
**Fix required**: move `faction_decision` block to before `adventure_decision` block.

### 2. RouteFamily Values
Confirmed from `src/domains/adventure/schema.py`. No `PATROL` or `TRADE` exist.
- patrol-type → `HUNT_WEAK_ENEMY`
- trade-type → `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD`
- quest-type → `QUEST_OPPORTUNITY`

### 3. EntityRole Values (src/core/enums.py)
- `HERO = 0`, `SHOPKEEPER = 1`, `GUARD = 5`
- No `MERCHANT` role — "MERCHANT" maps to `EntityRole.SHOPKEEPER` (confirmed assumption in ticket)

### 4. RegionState.owner_faction_id
`Optional[int]` (maps to old `Faction(IntEnum)`, not the new string faction_id).
The scoring logic must use `factions` dict (by string faction_id) for allied-region checks —
**not** via RegionState.owner_faction_id, which is a different identity space.

### 5. IdentityComponent.faction
Stored as `int` (old `Faction(IntEnum)` values). Entity-to-faction mapping via string ID is
unavailable from entity state alone — the faction directive scoring must work at the
population level (any matching directive in faction_directives), not per-entity faction lookup.

### 6. Call Chain
`pipeline.py` → `AdventureDecisionPhase.apply(state, context)` → `AdventureDecisionService.decide(entity, candidates, ..., faction_directives, factions)` → `AdventureRouteScorer.score(entity, route, ..., faction_directives, factions)`

### 7. Context Passthrough
`AdventureDecisionPhase.apply()` already accepts `context: Optional[dict]`. Pipeline can pass
`context={"faction_directives": faction_directives, "factions": state.factions}` — no signature
change needed on the phase entry point itself, just unpack from context inside.

### 8. Faction Directive → Score Logic
- GUARD + HUNT_WEAK_ENEMY: if any DEFEND_BORDER in faction_directives → urgency += 2.0
- SHOPKEEPER + GATHER_RESOURCE/SELL_LOOT_FOR_GOLD: if any faction has "allied" in diplomatic_relations.values() → urgency += 1.5
- HERO + QUEST_OPPORTUNITY: if any COMMISSION_QUEST in faction_directives → urgency += 3.0
- faction_directives=None guard: entire block skipped (no regression)

### 9. FactionDirective Import Strategy
Use TYPE_CHECKING in scoring.py for the FactionDirective type annotation to avoid circular
imports. Import DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST constants lazily inside the
scoring block (same pattern as EntityRole imports inside score()).

### 10. Docs Required
- `docs/systems/faction_contract.md` — new, DRAFT status pending E53Ad
- `docs/mechanics/04_strategic_cognition.md` — update to mention faction directive scoring rules
- `docs/parity_ledger/strategic_cognition.yaml` — add FACTION-DIR-001 entry
