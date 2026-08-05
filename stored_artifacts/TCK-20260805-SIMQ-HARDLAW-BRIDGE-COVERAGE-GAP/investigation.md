---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP
artifact_type: investigation
tags: [simulation-quality, observability, world]
---

# investigation.md — TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP

## Current Behavior (file:line refs)

Confirmed via direct source read (already established when this ticket was filed):
`quality_hub.py::_translate_invariant()` had exactly 3 branches — `COMBAT*` → `combat_hard_law_violation`,
`CONSERVATION*` → `conservation_law_violated`, `LAW-SPAWN-OCCUPANCY` → `spawn_occupancy_violation`.
Of the 7 real `HardLawMonitor` laws (`docs/observability/hard_law_monitor.md`), only
`LAW-SPAWN-OCCUPANCY` matched anything — the other 6 fell through to `return env.event_type`
(untranslated, invisible to SimQ).

## Git History Check (the ticket's central Assumption)

`git log -p --follow -- src/simulation_quality/quality_hub.py` traced the `COMBAT`/`CONSERVATION`
prefix branches to their introduction (`TCK-20260628-SIMQ-EPIC`, the original SimQ scoring module
build). Grepped all of `docs/`, `tickets/done/`, `stored_artifacts/` for any `COMBAT-<number>` or
`CONSERVATION-<number>` style law_id ever being planned — no hits (only unrelated matches like
`RPG-COMBAT-NNN` checklist IDs, a different namespace). **Conclusion: these branches were
speculative/aspirational, never matched by a real law under that naming convention** — consistent
with `docs/plans/idea_placement_legality_check.md`'s independent observation that the
`CONSERVATION` branch looked like it was "planned... and never actually implemented." The real 7
laws all use a `LAW-*` prefix, not `COMBAT*`/`CONSERVATION*`.

## Decision: extend with new branches, don't repurpose or rename

Renaming the 6 real laws to match the speculative prefixes would mean editing
`HardLawMonitor`'s law-check code and its own test suite — explicitly out of this ticket's scope
("Do NOT touch HardLawMonitor... the laws' detection logic"). Added exact-match `law_id` routing
instead, reusing existing scorer signals where the semantics genuinely fit:

| Law | Domain (`hard_law_monitor.md`) | Routed to | Reasoning |
|---|---|---|---|
| `LAW-HP-NONNEGATIVE` | `DirtySet.combat_entities` | `combat_hard_law_violation` (CombatScorer, existing) | Read `CombatScorer.score()`: this signal's own description is generic — "hard law violated in combat pipeline" — not law-specific. HP is exactly this domain. |
| `LAW-READINESS-NONNEGATIVE` | `DirtySet.combat_entities` | `combat_hard_law_violation` (same) | Same domain, same reasoning. |
| `LAW-GOLD-NONNEGATIVE` | `DirtySet.inventory_entities` | `conservation_law_violated` (EconomyScorer, existing) | Economic invariant; matches the codebase's established "Atomic Conservation Law" vocabulary (`docs/mechanics/03_economic_laws.md`) closely enough to reuse rather than duplicate. |
| `LAW-STAMINA-NONNEGATIVE` | `DirtySet.biological_entities` | `world_hard_law_violation` (WorldDynamicsScorer, **new**) | No existing pillar-generic signal fits a biological-vitals invariant; doesn't belong in COMBAT (not combat-scoped) or ECONOMY. |
| `LAW-POSITION-FINITE` | `DirtySet.movement_entities` | `world_hard_law_violation` (new) | Movement/spatial-domain, same domain as `spawn_occupancy_violation` (already WORLD-owned). |
| `LAW-OCCUPANCY-COLLISION` | `DirtySet.movement_entities` | `world_hard_law_violation` (new) | Same reasoning — tile-collision correctness, same family as spawn-time occupancy. |

`world_hard_law_violation` follows `combat_hard_law_violation`'s own established pattern
(one generic signal per pillar-domain, not one signal per law) rather than adding 3 separate new
signals — keeps the design consistent with what's already shipped.

## Docs Requiring Update
- `docs/simulation_quality/quality_scoring_contract.md`: WORLD DYNAMICS pillar's event-types list
  and signal table — new `world_hard_law_violation` row.
- `docs/simulation_quality/event_type_coverage.md`: scored-event count (83→84), translation table
  rows for the 6 newly-routed laws, "Last updated" note.
- `docs/simulation_quality/extension_points.md`: axis 9 previously described this as an open gap
  (forward reference from an earlier session turn) — updated to reflect the fix is now landed.

## Parity Ledger Overlap

None — checked `docs/parity_ledger/` for any entry citing `_translate_invariant`,
`combat_hard_law_violation`, `conservation_law_violated`, or the 6 law_ids: no hits. This is
observability/SimQ-scoring routing, not a Mechanics-Bible-tracked gameplay behavior change (the
laws themselves are unchanged; only whether their violations reach SimQ changed).

## Prior Work
- `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` — established the exact pattern this ticket reuses for the
  6 new routes (translate → `EVENT_TYPES` → pillar contract row → weight).
- `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` — confirmed no 11th pillar needed; this ticket's new
  signal routes to an existing pillar (WORLD), consistent with that finding.

## Risks and Open Questions

None outstanding. All 516 `tests/simulation_quality/` tests pass (1 pre-existing, unrelated,
already-documented failure). One existing test
(`test_invariant_spawn_occupancy_no_violation_no_translation`) encoded the exact gap this ticket
closes — used `LAW-HP-NONNEGATIVE` as its "should NOT translate" example — corrected and renamed,
with new explicit tests added for the corrected behavior.
