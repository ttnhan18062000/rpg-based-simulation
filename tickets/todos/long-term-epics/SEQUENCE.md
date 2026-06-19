# Long-Term Epics — Implementation Sequence

Source documents: `docs/plans/long_term_development_roadmap.md` + `docs/plans/engine_future_epics_roadmap.md`
Generated: 2026-06-19

---

## Dependency Tree

```
PARALLEL (no dependencies):
  TCK-20260619-P0-CI-AUTOMATION      Phase 0 — 30 lines of YAML
  TCK-20260619-P0-DETERMINISM        Phase 0 — bare random replacement
  TCK-20260619-P0-HUNGER-SATIATION   Phase 0 — food node + satiation
  TCK-20260619-P0-ENTITY-INIT        Phase 0 — WorldCompiler seeding
  TCK-20260619-P0-DOC-REPAIR         Phase 0 — stale doc fixes
  TCK-20260619-P0-CODE-INTEGRITY     Phase 0 — 3 surgical fixes
  TCK-20260619-PARITY-P0-BUGS        Parity debt — independent of all phases

Phase 0 complete ──►
  PARALLEL:
    TCK-20260619-E11-ENTITY-IDENTITY     (requires P0-4)
    TCK-20260619-E13-CONTENT-FOUNDATION  (no Phase 0 dep, but benefits from P0-3)
    TCK-20260619-E22-DECISION-EXPLAIN    (no content dep — can start after P0)
    TCK-20260619-E-PHASE-PERMISSIONS     (no content dep)
    TCK-20260619-E-CAP-REGISTRY          (no content dep)
    TCK-20260619-E-READ-MODEL            (no content dep)
    TCK-20260619-COMBAT-ECOLOGY          (verify-first, minimal dep)

  E12-BALANCE-BASELINE requires P0-3 + P0-4 + (ideally E11 for personality measurement)
  ──► TCK-20260619-E12-BALANCE-BASELINE

Phase 1 complete (E11 + E12 + E13) ──►
  PARALLEL:
    TCK-20260619-E21-RESOURCE-ECOLOGY  (requires E13 — content to deplete)
    TCK-20260619-E22-DECISION-EXPLAIN  (can run in Phase 1 if not started)

  E21 complete + E13 complete ──►
    TCK-20260619-E23-QUEST-GENERATION  (requires E21 + E13)

Phase 2 complete (E21 + E22 + E23) ──►
  PARALLEL:
    TCK-20260619-E31-SCENARIO-RUNTIME  (requires E23 for meaningful objectives)
    TCK-20260619-E33-MACRO-ECONOMY     (can start after P0-3)

  E31 complete ──►
    TCK-20260619-E32-CAMPAIGN-RUNTIME  (requires E31)

Phase 3 complete (E31 + E32 + E33) ──►
  PARALLEL:
    TCK-20260619-E41-PARTY-LOOP        (requires E32 NarrativeLedger + E11 HERO entities)
    TCK-20260619-E42-INFO-SEEKING      (requires E32)
    TCK-20260619-E43-SOCIAL-MEMORY     (requires E32 — hard block)

Phase 4 complete (E41 + E42 + E43) ──►
  PARALLEL:
    TCK-20260619-E51-CHRONICLE         (requires E32 + E43)
    TCK-20260619-E52-DEMOGRAPHICS      (requires E21 + E32)

  E51 + E53 complete ──►
    TCK-20260619-E53-FACTION-DIPLOMACY (requires E32 + E21; unlocks E62 + E63)

Phase 5 complete ──► Re-evaluate Phase 6 scope
  TCK-20260619-E61-PROGRESSION         (requires E32 + E43; re-scope at Phase 5 end)
  TCK-20260619-E62-CULTURE-DRIFT       (requires E51 + E53; re-scope at Phase 5 end)
  TCK-20260619-E63-FEATURE-PACKS       (decision gate: ≥3 extension-point features used; XL)
```

---

## Critical Path

```
P0-2 (determinism) → P0-3 (hunger) → P0-4 (entity init)
  → E11 (entity identity) → E12 (balance baseline)
  → E21 (resource ecology) + E13 (content) → E23 (quest gen)
  → E31 (scenario runtime) → E32 (campaign runtime)
  → E43 (social memory) → E51 (chronicle)
  → E53 (faction & diplomacy) [XL]
```

Everything else can be parallelized around this spine.

---

## Quick-Start Order (highest ROI first)

All Phase 0 items can run in parallel. Start all 6 simultaneously:

| Order | Ticket | Why first |
|---|---|---|
| 1 | TCK-20260619-P0-CI-AUTOMATION | Every merge currently unvalidated |
| 1 | TCK-20260619-P0-DETERMINISM | Silent replay divergence |
| 1 | TCK-20260619-P0-HUNGER-SATIATION | Unblocks entire economic layer |
| 1 | TCK-20260619-P0-ENTITY-INIT | ~20 lines, unlocks all differentiation |
| 1 | TCK-20260619-P0-DOC-REPAIR | Most-referenced docs give wrong info |
| 1 | TCK-20260619-PARITY-P0-BUGS | P0 debt per Authoritative Mechanics Rule |
| 2 | TCK-20260619-P0-CODE-INTEGRITY | 3 surgical fixes, no arch change |

---

## Duplicate Work Detected During Investigation

These items from the source plans overlap with already-done tickets and should NOT be re-implemented:

| Plan Item | Already Done | Note |
|---|---|---|
| Static quest generation | TCK-20260425-PH8-M2 | Level-scaled static quest gen is done. Epic 2.3 adds *pressure-driven* generation on top |
| Quest identity/rewards | TCK-20260427-QUEST-IDENTITY | Done. Epic 2.3 extends, not replaces |
| Group/party formation | TCK-20260424-PH3-M2-GROUP-COORDINATION, TCK-20260410-PH4-SOCIAL-CONTRACTS | Formation done. Epic 4.1 adds sustained lifecycle, reward split, escort |
| Life-arc campaigns | TCK-20260528-PHASE9-LIFE-ARCS | Analysis-only campaigns done. Epic 3.2 adds *persistent-consequence* campaigns — different concept |
| Ecology tick infra | TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION | Infrastructure documented. Epic 2.1 adds regen logic not yet implemented |
| Worldgen modules/composition | worldgen-module-epic (13 tickets done) | World module system done. Epic 1.3 adds *content* (quest defs, recipes) not system |

---

## Total Ticket Count

| Category | Count |
|---|---|
| Phase 0 (hotfix/standard) | 6 |
| Phase 1 epics | 3 |
| Phase 2 epics | 3 |
| Phase 3 epics | 3 |
| Phase 4 epics | 3 |
| Phase 5 epics | 3 |
| Phase 6 epics (speculative) | 3 |
| engine_future_epics additions | 5 |
| **Total** | **29** |
