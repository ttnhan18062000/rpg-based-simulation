---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION
phase: open
date: 2026-10-04
tags: [world, content, root-cause]
---

# Investigation — TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION

## Findings
- AC-4a: all 24 composition worlds' committed snapshot equals a fresh resolve of their own `world.yaml`; resolve is byte-deterministic. No snapshot was stale against its source: the bug was `world.yaml` itself never receiving the fix. Positive control: the catalog copy resolves to something different from the snapshot.
- AC-5: catalog copy vs `world.yaml` differs for `dungeon_crawl` (the lost fix), `frontier_extended`, `frontier_living_world`, `swamp_border_world` (catalog lacks `trading_company_hub`) and `urban_political` (catalog lacks `hero_adventurers`); `highland_traverse` and `wilderness_survival` are identical, so wilderness_survival's half of the original fix did reach production. Closed tickets CAMP-STATE, DEMOGRAPHIC-COHORT and UNREACHABLE-CLASSIFY measured via the catalog copy of `frontier_living_world`; routed to `TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION`.
- A fourth stale artifact: `world_compile_report.json` still said 32 entities. `test_distinct_populated_factions` and the corpus registry read it.
- Census table (`EXPECTED_DISTINCT_POPULATED_FACTIONS`): only `dungeon_crawl` (4 -> 2) was wrong; the four entries for the other catalog-divergent worlds (9, 6, 4, 4) match fresh compiles.
- Compile-report `state_hash`/`canonical_state_hash` differ from fresh compiles in ~20 worlds and `place_count` in ~12; compile is deterministic, so this is the known compiler-version staleness (`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`), not asserted here.
- Live dungeon_crawl after the fix: 12 entities, 2 regions, 0 resource nodes, 0 buildings, 2 populated factions.
- Rendering pins affected: connectivity 15245 -> 12221, density CV 0.678 -> 0.283, TVD 0.2316 -> 0.2867, second forest and cave gone.

## Docs Requiring Update
- `docs/guidelines/intentional_divergences.md` — DEV-009.
- `docs/parity_ledger/substrate.yaml` — SUB-394.

## Risks and Open Questions
- Frozen rendering fixture no longer detects rendering regressions in the live dungeon_crawl; decision filed as `TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT`.
- `INFRA-373` (`TVD(sandbox_world, dungeon_crawl)`) is not moved: it now reproduces on the frozen fixture; `docs/parity_ledger/infrastructure.yaml` belongs to neither lane.
- `faction_tension_overrides` in `world.yaml` left unchanged (the resolver accepts them); the catalog copy had dropped them.
