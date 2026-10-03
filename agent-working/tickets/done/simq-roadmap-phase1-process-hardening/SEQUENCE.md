# SimQ Roadmap — Phase 1: Process Hardening

Scoped 2026-07-10 from `docs/plans/simq_development_roadmap.md`. Runs in parallel with Phase 0
relative to the rest of the roadmap.

**Goal:** Stop the same defect classes (missing `hazard_kind` content gaps; the `town_council`/
`bandit_road` hazard-exposure question) from recurring silently a 4th/3rd time.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` | Phase 1.2. **Land this first.** The roadmap originally assumed 1.1/1.2 were independent — both tickets' own Scope phases found that's wrong: running 1.1's corpus-wide test before this DA ruling lands hits the `town_council`/`bandit_road` case as a live failure. Landing 1.2 first means 1.1 never needs its temporary test exception at all. Also found to be more involved than originally estimated (`trading_company_hub.yaml` shares the same faction+hazard-region shape — needs a blast-radius check before any immunity grant), so budget real investigation time, not a five-minute ruling. |
| 2 | `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` | Phase 1.1. Extends `test_hazard_kind_matches_populating_faction_immunity` corpus-wide. Already scoped with a temporary exception for the `town_council`/`bandit_road` case in case 1.2 hasn't landed yet when this is picked up — reconcile (remove the temporary exception) once 1.2's ruling is live. |

See `docs/plans/simq_development_roadmap.md` §"Phase 1 — Process Hardening" (including its
2026-07-10 correction note) for the full dependency discovery and reasoning.

**Correction (2026-07-11):** Row 1's "why this order" claim — that running 1.1's corpus-wide test
before this DA ruling lands would hit `town_council`/`bandit_road` as a live failure — does not
hold. `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s investigation.md dry run found the corpus-wide
test's region-level "any populating faction" matching semantics already pass `bandit_road` via
`bandit_company`/`merchant_league`'s pre-existing immunities, independent of ordering or of this
DA ruling. Both tickets are now done regardless of this correction; the original row is left as-is
above as the historical record of why this order was chosen, but a future reader should not
conclude the clean landing validates the original coupling theory.
