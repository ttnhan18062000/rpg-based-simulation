---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION
phase: open
date: 2026-10-04
tags: [world, content, investigation, simulation-quality]
---

# TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION

## Title

Closed tickets and a 13-world census measured worlds through the catalog copy, which for five worlds is
not what production loads — find every such measurement and re-take or retire it

## Status

OPEN

## Tier

standard

## Type

repair

## Priority

P1

## Request Summary

For five corpus `world_id`s, `data/content/world_compositions/<id>.yaml` (the catalog copy) and
`data/worlds/<id>/world.yaml` (what production loads, via `src/worldbuilding/repository.py`'s redirect to
`resolved/`) declared **different module sets**. Any measurement taken through the catalog path therefore
describes a world that never ran. `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (PR #328) made
`world.yaml` the single source and deleted the catalog directory, so the divergence cannot recur — but it
did **not** go back and re-take the measurements that were already made through the wrong path.

Two independent instances are already known, which is why this is a class and not a one-off:

1. **Three closed tickets** — the CAMP-STATE, DEMOGRAPHIC-COHORT and UNREACHABLE-CLASSIFY work — took
   their measurements via the catalog copy of `frontier_living_world`, which differs from what runs.
   Reported by `rpg-implementer-2` during the AC-5 sweep of
   `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`.
2. **A 13-world census in a live test.** `EXPECTED_DISTINCT_POPULATED_FACTIONS` in
   `tests/unit/worldassembly/test_corpus_diversity.py` pinned `dungeon_crawl: 4`. The real post-fix
   number is 2; the 4 came from a stale `world_compile_report.json`. The table's own comment says the
   counts were "re-confirmed by `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC`'s own recompile cross-check" —
   so that cross-check was reading the artifact rather than what production loads, and the table has been
   asserting a stale number successfully for months.

The second instance makes the first one's blast radius much larger than three tickets: a *test* that
passes against a stale artifact is the mechanism that let the original `dungeon_crawl` defect hide from
June to October.

## Scope

- Enumerate the affected worlds authoritatively. The five divergent `world_id`s and, from the AC-5 sweep:
  `dungeon_crawl` (the lost balance fix), `frontier_extended`, `frontier_living_world` and
  `swamp_border_world` (catalog copy missing `trading_company_hub`), `urban_political` (missing
  `hero_adventurers`). `highland_traverse` and `wilderness_survival` were identical, so measurements
  through either path are valid for those two.
- Find every measurement taken through the catalog path: closed tickets, stored artifacts, the parity
  ledger, SimQ baselines, and **committed expectation tables in tests** — the last category is the one
  that was missed.
- For each: re-take it against `world.yaml`, or mark it explicitly as measured against a definition that
  never ran. **A measurement that cannot be re-taken cheaply is retired, not quietly kept.**
- Verify the four remaining census entries for the divergent worlds that appear in
  `EXPECTED_DISTINCT_POPULATED_FACTIONS`: `frontier_extended` (9), `frontier_living_world` (6),
  `swamp_border_world` (4), `urban_political` (4).

## Out of Scope

- Re-deciding any world's module set. The reconciliation decisions are made and recorded in
  `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`'s `plan.md`.
- Rendering-metric evidence — that is
  `TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT`.
- Re-opening the closed tickets' conclusions on their merits. This ticket establishes whether each
  conclusion still stands on a valid measurement; where it does not, it files the correction.

## Acceptance Criteria

1. A complete enumeration of measurements taken via the catalog copy, with the affected `world_id` named
   for each — covering closed tickets, stored artifacts, parity-ledger `v2_evidence`, SimQ baselines and
   test expectation tables.
2. Each enumerated measurement is re-taken against `world.yaml`, or annotated at its source as measured
   against a non-running definition, or retired with a reason. No entry is left undecided.
3. The four `EXPECTED_DISTINCT_POPULATED_FACTIONS` entries above are confirmed or corrected against
   freshly regenerated `world_compile_report.json` files.
4. Where a re-taken measurement changes a conclusion, a follow-up ticket exists and is linked here.
5. A guard exists that fails when a committed expectation table is asserted against a stale generated
   artifact — extending the freshness guard from
   `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` rather than adding a
   second mechanism. Without this, AC-1's enumeration decays the moment it is written.
6. The three closed tickets in Request Summary §1 each carry a note stating whether their conclusion
   survives re-measurement.

## Related Tickets

- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — made `world.yaml` authoritative (PR #328)
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` — closed `DUPLICATE`; the measurement-validity
  framing originated there and was folded into the ticket above
- `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` — found instance 1
- `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC`, `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — authored the census
  whose cross-check read the artifact
- `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` — open, and one of the three tickets
  named above is in its lineage; check whether its own numbers came through the catalog path
- `TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT`,
  `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` — open, same corpus surface

## Related Docs

- `docs/architecture/world_repository_layout.md` §1 — the single-source law
- `docs/mechanics/06_worldbuilding_foundation.md` §11 — cites §1 as a sibling law, deliberately not a §7
  compile gate
- `docs/parity_ledger/substrate.yaml` — `v2_evidence` entries to re-check

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/` —
  `investigation.md` has the 8-of-9 divergence comparison; `plan.md` has the per-world decisions
- `agent-working/staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2 — the census
  the test cites

## Related Code Areas

- `tests/unit/worldassembly/test_corpus_diversity.py` — `EXPECTED_DISTINCT_POPULATED_FACTIONS`
- `src/worldbuilding/repository.py` — the `resolved/` redirect that defines "what production loads"
- `src/worldassembly/resolver.py` — regenerates the snapshot and the compile report
- `data/worlds/*/resolved/`, `data/worlds/*/world_compile_report.json`, the corpus registry

## Assumptions / Open Questions

- **UQ-1:** how are the three closed tickets' conclusions to be recorded if a re-measurement overturns
  one? A closed ticket should not be silently edited. Likely a note in the closed ticket plus a new
  ticket — confirm the convention before writing to `agent-working/tickets/done/`.
- **UQ-2:** is the SimQ corpus baseline affected? If pillar scores were computed through the catalog
  path for any of the five worlds, the baselines move, which touches `simulation-quality` territory and
  may need that owner rather than this lane.
- Assumption: the AC-5 sweep results quoted in Scope are as reported by `rpg-implementer-2` on
  2026-10-04. **Re-derive them before acting** — they were relayed to this ticket, not independently
  measured by its author.

## Implementation Notes

_(to be filled during implementation)_

## Test Summary

_(to be filled during implementation)_

## Files Changed

_(to be filled during implementation)_

## Completion Summary

_(to be filled during implementation)_
