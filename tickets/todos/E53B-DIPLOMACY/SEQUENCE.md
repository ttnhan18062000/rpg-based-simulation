# E53B — Faction Diplomacy

**Parent epic:** TCK-20260619-E53B-DIPLOMACY (EPIC_SCOPED)
**Inter-epic prerequisite:** E53A complete (FactionState + FactionDecisionPhase must exist)
**Inter-epic unlocks:** E53C-WAR (requires DiplomaticStateMachine WAR state + tension threshold)

## Sequence (linear)

1. **TCK-20260619-E53Ba-DIPLO-STATE** — `DiplomaticRelationState` frozen dataclass (faction_a, faction_b, status, tension, treaty_terms) + `AuthoritativeState.diplomatic_relations` field
2. **TCK-20260619-E53Bb-DIPLO-ACTIONS** — `DiplomaticAction` enum (PROPOSE_TREATY, BREAK_TREATY, DECLARE_WAR, SUE_FOR_PEACE, FORM_ALLIANCE) + `DiplomaticActionExecutor`
3. **TCK-20260619-E53Bc-STATE-MACHINE** — `DiplomaticStateMachine` in `src/domains/faction/` (not `src/engine/` — avoids circular imports); valid transitions: NEUTRAL↔HOSTILE↔WAR↔TRUCE↔ALLIED
4. **TCK-20260619-E53Bd-LEDGER-WIRING** — emit `war_declared`, `treaty_signed`, `alliance_formed` NarrativeLedgerEntry events; wire into `CampaignOrchestrator._advance_state()`

## Key Notes

- `DiplomaticStateMachine` must live in `src/domains/faction/` — importing from `src/engine/` creates circular imports.
- E53Bd emits event_type strings in **lowercase** (e.g. `war_declared`). The Chronicle naming.py TEMPLATES currently uses **uppercase** keys (e.g. `WAR_DECLARED`) — this mismatch is a known bug to be fixed in E53Da.
- `diplomatic_relations` key: tuple `(min(faction_a, faction_b), max(faction_a, faction_b))` — canonical ordering prevents duplicate pairs.
