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

Three closed tickets measured `frontier_living_world` through the catalog copy, which is not what
production loaded — establish whether their conclusions survive re-measurement

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
`resolved/`) declared **different module sets**. A measurement taken through the catalog path therefore
describes a world that never ran. `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (PR #328) made
`world.yaml` the single source and deleted the catalog directory, so the divergence cannot recur — but it
did not go back and re-take measurements already made through the wrong path.

**Known affected work:** the CAMP-STATE, DEMOGRAPHIC-COHORT and UNREACHABLE-CLASSIFY closed tickets took
their measurements via the catalog copy of `frontier_living_world`, whose catalog copy lacked
`trading_company_hub`. Reported by `rpg-implementer-2` during the AC-5 sweep of
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`.

**This ticket stays P1 for one specific reason:** `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-
TO-ZERO` is **open** and sits in the lineage of one of those three tickets, so an open ticket's premise
may rest on a measurement of a world that never ran. If that dependency turns out not to exist, this is a
P2.

### Corrected 2026-10-04 — the original second instance in this ticket was wrong

This ticket was first filed claiming that a 13-world census
(`EXPECTED_DISTINCT_POPULATED_FACTIONS` in `tests/unit/worldassembly/test_corpus_diversity.py`) had also
been corrupted by the catalog path, on the reasoning that its `dungeon_crawl: 4` entry came from a stale
`world_compile_report.json`. **That was wrong, and the correction matters more than the original claim.**

`rpg-implementer-2` freshly compiled all 24 worlds and compared: every entry in the table agrees with a
fresh compile, including the four divergent worlds the original premise singled out —
`frontier_extended` 9, `frontier_living_world` 6, `swamp_border_world` 4, `urban_political` 4. Verified
independently here: `origin/main`'s `data/worlds/dungeon_crawl/world.yaml` carries four modules, so the
census `4` was a **faithful measurement of the world that actually ran**. The defect was never that the
census read the wrong artifact — it was that the running world was the unintended one, because the June
balance fix landed only in the catalog copy. A census that correctly records a world nobody intended to
ship is a different problem from a census that reads the wrong file, and only the second one would have
made the table unsound.

Two consequences: (1) the census needs no re-baselining beyond the single `dungeon_crawl` entry, already
corrected 4 → 2 in that ticket; (2) **the catalog/`world.yaml` divergence is not by itself evidence that
a measurement is invalid** — what matters is which path the measurement was taken through. Any
investigation under this ticket must establish the path, not infer corruption from the divergence.

### Related finding, not this ticket's scope

Committed `world_compile_report.json` `state_hash`/`canonical_state_hash` differ from a fresh compile in
~20 of 24 worlds, and `place_count` in ~12, while **no content-derived count differs anywhere**. Compile
was run twice and is deterministic, so this is compiler-version staleness, not content drift — the
already-filed, still-unresolved `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`. It is recorded
here because it is why the new freshness guard asserts only the six content-derived count fields: a
whole-report guard would fail on ~20 worlds for a reason unrelated to correctness. See parity entry
SUB-394's `support_boundary`.

## Scope

- Establish, for each of the three closed tickets, **which path its measurements were taken through**,
  and whether its stated conclusion survives a re-measurement against `world.yaml`.
- Determine whether `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO`'s premise depends on
  any of those measurements, and correct that ticket if so.
- Search for any other measurement taken through the catalog path — stored artifacts, parity-ledger
  `v2_evidence`, SimQ baselines — restricted to the five divergent worlds and to the period before #328.
- For each: re-take against `world.yaml`, or annotate at its source as measured against a definition
  that never ran. **A measurement that cannot be re-taken cheaply is retired, not quietly kept.**

## Out of Scope

- Re-baselining `EXPECTED_DISTINCT_POPULATED_FACTIONS`. Verified sound; see the correction above.
- `world_compile_report.json` hash/`place_count` staleness — `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-
  STALENESS` owns it.
- Re-deciding any world's module set; those decisions are recorded in
  `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`'s `plan.md`.
- Rendering-metric evidence — `TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT`.
- Building a new freshness guard. One already exists (see Acceptance Criteria 4).

## Acceptance Criteria

1. For each of the three closed tickets: the measurement path is stated as a fact (which loader, which
   file), not inferred, and the conclusion is marked as surviving, overturned, or unverifiable.
2. The `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` dependency question is answered
   explicitly. If its premise is affected, that ticket is corrected and this one's priority is restated.
3. Any further catalog-path measurement found in artifacts, parity `v2_evidence` or SimQ baselines is
   enumerated with its world named, and each is re-taken, annotated or retired. Finding none is an
   acceptable result **only** if the search method is stated.
4. Confirmed that the guard added by `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-
   DEFINITION` (committed vs fresh compile across the six content-derived count fields, positive-
   controlled against the old `dungeon_crawl` report) is sufficient to catch a recurrence of **this**
   defect class, or extended with a stated reason. Do not add a second parallel mechanism.
5. Where a re-taken measurement changes a conclusion, a follow-up ticket exists and is linked here.

## Related Tickets

- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — made `world.yaml` authoritative (PR #328)
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` — closed `DUPLICATE`; the measurement-validity
  framing originated there and was folded into the ticket above
- `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` — found this; authored the
  guard in AC-4 and corrected the one wrong census entry
- `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` — **open**; the reason this is P1
- `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS` — open; owns the hash/`place_count` drift
- `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC`, `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — authored the census
  that was wrongly suspected here

## Related Docs

- `docs/architecture/world_repository_layout.md` §1 — the single-source law
- `docs/mechanics/06_worldbuilding_foundation.md` §11 — cites §1 as a sibling law, deliberately not a §7
  compile gate
- `docs/parity_ledger/substrate.yaml` — SUB-394 and the `v2_evidence` entries to re-check

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/` —
  `investigation.md` has the 8-of-9 divergence comparison; `plan.md` has the per-world decisions
- `agent-working/stored_artifacts/TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION/`
  — the AC-5 sweep and the all-24-world fresh-compile comparison

## Related Code Areas

- `src/worldbuilding/repository.py` — the `resolved/` redirect that defines "what production loads"
- `src/worldassembly/resolver.py` — regenerates the snapshot and the compile report
- `tests/integration/worldassembly/test_resolved_snapshot_freshness.py` — the guard in AC-4
- `data/worlds/*/resolved/`, `data/worlds/*/world_compile_report.json`

## Assumptions / Open Questions

- **UQ-1:** how is a closed ticket's conclusion to be corrected if re-measurement overturns it? A closed
  ticket should not be silently edited. Likely a note in the closed ticket plus a new ticket — confirm
  the convention before writing to `agent-working/tickets/done/`.
- **UQ-2:** is the SimQ corpus baseline affected? If pillar scores were computed through the catalog path
  for any of the five divergent worlds, baselines move, which is `simulation-quality` territory and may
  need that owner rather than this lane.
- **UQ-3:** the three closed tickets are identified here by shorthand (CAMP-STATE, DEMOGRAPHIC-COHORT,
  UNREACHABLE-CLASSIFY) as relayed. Resolve them to full ticket IDs first; do not assume the shorthand
  maps to the ticket you expect.
- The AC-5 sweep results and the all-24-world comparison quoted above were **reported by
  `rpg-implementer-2`, not measured by this ticket's author**. The `dungeon_crawl` four-module claim and
  the `StrategicUpdate` location were independently re-verified; the rest were not. Re-derive before
  acting.

## Implementation Notes

_(to be filled during implementation)_

## Test Summary

_(to be filled during implementation)_

## Files Changed

_(to be filled during implementation)_

## Completion Summary

_(to be filled during implementation)_
