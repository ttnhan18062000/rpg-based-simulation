# E53D — Faction History Integration

**Parent epic:** TCK-20260619-E53D-HISTORY (EPIC_SCOPED)
**Inter-epic prerequisites:**
- E53Bd (ledger wiring) must be done before E53Da (event types must exist to name them)
- E53Bc + E53Cb (siege model + state machine) must be done before E53Db (siege events to harvest)
- E53Da + E53Db must be done before E53Dc (compiler integration tests need named events)
- E53Dc must be done before E53Dd (doc archive comes last)

## Sequence (partially parallel, then serial)

1. **TCK-20260619-E53Da-SIGNIFICANCE-NAMING** — fix naming.py TEMPLATES to use lowercase keys (`war_declared` not `WAR_DECLARED`); add 6 faction event types to `EventSignificanceScorer`; dual-faction `subject_id`; parity entries SOC-FAC-001..006
   - **Requires:** E53Bd (war_declared etc. must be emitted before this ticket runs)
2. **TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER** — emit `SIEGE_BEGINS` and `BETRAYAL` WorldEvents in the engine; harvest them into `CampaignOrchestrator._advance_state()` as NarrativeLedgerEntries
   - **Requires:** E53Cb (SiegeState) + E53Bc (state machine transitions)
   - **Can run in parallel with E53Da**
3. **TCK-20260619-E53Dc-COMPILER-INTEGRATION** — integration tests: `test_faction_war_declared_event_in_narrative_ledger`, `test_chronicle_names_the_war`, `test_chronicle_names_territory_transfer`
   - **Requires:** E53Da + E53Db both complete
4. **TCK-20260619-E53Dd-DOC-ARCHIVE** — archive `docs/strategy/grand_strategy.md`; create V2 `docs/simulation/domains/faction_contract.md`; `make knowledge-index-update`
   - **Requires:** E53Dc complete

## Key Known Bug (fix in E53Da)

`naming.py` TEMPLATES uses uppercase keys (`WAR_DECLARED`, `TERRITORY_TRANSFERRED`) but
E53Bd emits lowercase event_type strings (`war_declared`, `territory_transferred`).
This mismatch causes all faction events to fall through to the generic naming fallback.
**E53Da must normalise all keys to lowercase** and add the 6 missing faction event types
to `EventSignificanceScorer` (currently they score 0.1, below the 0.5 CHRONICLE_THRESHOLD).

## Significance Values (authoritative — from E53Cc)

`territory_transferred` significance = 0.85 (set by E53Cc, not the epic spec value of 0.9).
