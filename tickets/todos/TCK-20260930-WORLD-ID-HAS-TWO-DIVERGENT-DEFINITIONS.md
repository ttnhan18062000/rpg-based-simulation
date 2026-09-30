---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS
phase: open
date: 2026-09-30
tags: [world, architecture]
---

# TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS

## Title
Five corpus `world_id`s have two divergent definitions — `data/worlds/<id>/world.yaml` (what
production runs) and `data/content/world_compositions/<id>.yaml` (what the catalog declares) — so
a measurement taken via the catalog path describes a world that never runs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found 2026-09-30 while reconciling a region-count disagreement between two runtime probes of
`dungeon_crawl` (2 regions / 12 population vs 4 regions / 32). The cause is not a stale cache: the
same `world_id` is defined **twice, differently**, in two locations, and the two loaders read
different files.

- `WorldRepository.load_world_with_context` (`src/worldbuilding/repository.py:89-114`) reads
  `data/worlds/<id>/`. **This is the production path** — `src/cli/entry.py:226`,
  `campaigns/orchestrator.py:746`, `tools/execution_census.py`, and the calibrate tools all use it.
- `WorldAssemblyResolver.assemble()` re-resolves from `data/content/world_compositions/<id>.yaml`
  against current module sources.

**Of the 7 `world_id`s that exist in both locations, 5 diverge. Only 2 match.**

| world_id | runs as (`data/worlds/`) | catalog declares |
|---|---|---|
| `dungeon_crawl` | 4 modules (`+goblin_camp_conflict`, `+old_mine_resource_loop`), `danger_scale: 4`, plus `faction_tension_overrides` | 2 modules, `danger_scale: 2`, no overrides |
| `frontier_living_world` | 7 modules (**`+trading_company_hub`**) | 6 |
| `frontier_extended` | 9 modules (**`+trading_company_hub`**) | 8 |
| `swamp_border_world` | 4 modules (**`+trading_company_hub`**) | 3 |
| `urban_political` | 4 modules (**`+hero_adventurers`**) | 3 |

A further 17 `world_id`s exist **only** in `data/worlds/` with no catalog composition at all
(including `generated_frontier_3_42`, `crowded_frontier`, `quest_dense_frontier`,
`simq_scale_stress_seed42`). Zero exist only in the catalog.

**This is a measurement-validity problem before it is a content problem.** Any investigation that
compiles a world via the catalog path is describing a world that is not the one the simulation
runs. Four of the five divergences add exactly one module, and in three cases the same one
(`trading_company_hub`), so the divergence is systematic rather than random — it looks like the
catalog copies were forked and then not kept up.

## Scope
- Determine which location is intended to be authoritative, and why two exist. Check git history
  on both sides for each of the 5 divergent pairs — which was edited last, and did any commit
  intend to update both?
- Decide the target state. Candidates, **not chosen here**:
  - **Catalog authoritative**, `data/worlds/` becomes generated build output (and should then be
    `.gitignore`d or clearly marked generated).
  - **`data/worlds/` authoritative**, the catalog compositions are retired or reduced to
    test fixtures.
  - **Both legitimate but must not share an id** — rename one side so a `world_id` is unambiguous.
- Add a validation check that fails when a `world_id` resolves to two different module sets, so
  this cannot silently reappear.
- Assess the blast radius on existing measurements (see Assumptions).

## Out of Scope
- Fixing the content of any individual world. Which module set is *correct* for
  `frontier_living_world` is a content decision, separate from the structural problem that two
  answers exist.
- The 17 `data/worlds/`-only worlds. They are unambiguous — one definition each — and only matter
  here as evidence about which location is authoritative.
- `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO`, which surfaced this. Its own
  conclusion survives (see Assumptions).

## Acceptance Criteria
- [ ] A documented decision on which location is authoritative, with the reasoning.
- [ ] The 5 divergent pairs reconciled to a single definition each, or explicitly renamed apart.
- [ ] A check that fails when one `world_id` resolves to two different module sets.
- [ ] A written assessment of which prior measurements used the non-running definition, and
      whether any recorded conclusion changes as a result.
- [ ] `docs/mechanics/06_worldbuilding_foundation.md` and/or the world-repository architecture doc
      updated to state which location is authoritative — currently neither says.

## Related Tickets
- `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` — surfaced this via the region-count
  disagreement between two probes of `dungeon_crawl`.
- `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` — requires a runtime instrument
  for absence verdicts. This ticket sharpens that: a runtime instrument must also load the world
  the way production does, or it is measuring a different world.
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — same family (one id, two
  meanings) one level down, at region rather than world scope.
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — its evidence base is partly affected.

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology and integrity validation;
  the natural home for a "one id, one definition" law.
- `docs/architecture/` — world assembly and world repository layout docs.
- `docs/plans/world_composition_precondition_gap_finding.md` — retired 2026-09-30, but note its §3
  discussed `frontier_living_world` composing `merchant_league` via `trading_company_hub`. That
  module is present only in the **running** definition, so §3 was describing `data/worlds/`.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md` — used the
  catalog path (`data/content/world_compositions/frontier_living_world.yaml`) for its compile.

## Related Code Areas
- `src/worldbuilding/repository.py:89-114` (`load_world_with_context`, the production path)
- `src/worldassembly/resolver.py` (`WorldAssemblyResolver.assemble`, the catalog path)
- `src/cli/entry.py:226`, `campaigns/orchestrator.py:746`, `tools/execution_census.py` — production
  callers
- `data/worlds/*/world.yaml` and `data/worlds/*/resolved/`
- `data/content/world_compositions/*.yaml`

## Assumptions / Open Questions
- **Which is authoritative is genuinely unknown.** `data/worlds/` wins on usage (every production
  caller) but that may be incidental rather than designed. Not assumed either way here.
- **The cohort ticket's conclusion survives this.** Its decisive evidence came from
  `agent-working-implementer`'s probe, which used `load_world_with_context` — the running
  definitions — across 21 worlds, and still found the largest bracket ever observed to be 8, far
  below the 100 needed for `net >= 1`. So that defect is confirmed against the worlds that
  actually run. My own catalog-path compile agreed directionally (largest 6), which is why the
  discrepancy went unnoticed until a region count disagreed.
- **The camp `STALE-PREMISE` closure survives.** Its two modules (`goblin_camp_conflict`,
  `wolf_den_near_forest`) are present in **both** definitions of `frontier_living_world`, so the
  2-`CampState` result holds either way. Verified before filing.
- **Unassessed:** every other measurement in the classification epic and the wave before it. Some
  used the catalog path. Whether any conclusion actually flips is unknown and is AC-4.
- Are `data/worlds/<id>/resolved/` artifacts regenerated on a schedule, on demand, or never? If
  they are generated from `data/worlds/<id>/world.yaml` rather than from the catalog, that is
  evidence for `data/worlds/` being authoritative.
- `urban_political` running with `hero_adventurers` is worth a second look: `hero_adventurers` is
  described elsewhere as the corpus's only source of `hero`-kind entities, and at least one prior
  finding reasoned about which worlds compose it.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
