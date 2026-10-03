# Test Plan — TCK-20260619-E53Bd-LEDGER-WIRING

## Test Scope

All tests in `tests/unit/faction/test_diplomacy.py` (26 total, 5 new E53Bd).
All tests in `tests/unit/campaigns/` (69, regression only).

## New Tests (E53Bd)

| Test | What it verifies |
|---|---|
| `test_events_from_transitions_war_declared` | HOSTILE→WAR transition emits FACTION_WAR_DECLARED with correct subject/tick |
| `test_events_from_transitions_peace_treaty` | WAR→NEUTRAL emits FACTION_PEACE_TREATY; requires prior state was WAR |
| `test_events_from_transitions_alliance_formed` | Alliance updates → FACTION_ALLIANCE_FORMED; deduped to one per pair |
| `test_treaty_flows_through_narrative_ledger` | Full flow: WorldEvent → _extract_narrative_entries → NarrativeLedgerEntry (significance=0.75, entry_id format) |
| `test_war_declared_flows_through_narrative_ledger` | Full flow: WAR_DECLARED → significance=0.95 |

## Results

26/26 faction tests green. 69/69 campaign tests green.
