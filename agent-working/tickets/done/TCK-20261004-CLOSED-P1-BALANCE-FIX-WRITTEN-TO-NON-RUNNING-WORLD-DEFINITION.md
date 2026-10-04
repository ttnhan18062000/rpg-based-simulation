---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION
phase: done
date: 2026-10-04
tags: [world, content, root-cause]
---

# TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION

## Title

A closed P1 balance fix was written to the one world definition production never loads, so
`dungeon_crawl` has run a measured 94–97% extinction configuration for three months while its ticket
reads DONE

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

**This is not a balance ticket.** The balance decision was already made, measured and closed. This ticket
is about the fix never reaching the code path that runs, and the ticket being marked DONE anyway.

`TCK-20260627-P1I-WORLD-BALANCE-FIX` (DONE, P1) was filed because **D08 measured `dungeon_crawl` at
94–97% entity attrition by tick 100** (Score 14/15), with the behavioural adventure pipeline never
activating because entities die before tick 201. Its remedy: remove `goblin_camp_conflict` and
`old_mine_resource_loop`, reduce `scalable_bandit_camp`'s `danger_scale` **4 → 2**, taking the entity
count **32 → 12**. All verified in that ticket at lines 30, 33, 42, 73–75, 101–103.

**Its `## Files Changed` lists exactly one file: `data/content/world_compositions/dungeon_crawl.yaml`**
(lines 59 and 93). That is the one location production **never** reads.

**Confirmed inert, directly:** `data/worlds/dungeon_crawl/resolved/world.resolved.yaml` — the file
production actually loads — **still contains `goblin_camp_conflict` and `old_mine_resource_loop`**, the
two modules the fix removed. The extinction configuration has been live since 2026-06-27.

### Root cause: there are three definitions of a world, and the fix went to the wrong one

| artifact | role | loaded by production? |
|---|---|---|
| `data/content/world_compositions/<id>.yaml` | catalog copy — **where the fix was written** | **No** |
| `data/worlds/<id>/world.yaml` | authored source of record | **No**, for a `worldcomposition.v1` world |
| `data/worlds/<id>/resolved/world.resolved.yaml` | generated projection | **Yes** |

`src/worldbuilding/repository.py:74-81`: `load_world()` reads `data/worlds/<id>/world.yaml`, sees
`schema_version` containing `worldcomposition`, and redirects to the `resolved/` snapshot, raising if it
is absent. So **two** separate hops had to be got right and neither was.

The two artifacts are also **not regenerated in lockstep**: `dungeon_crawl`'s resolved snapshot is dated
2026-09-08 against a `world.yaml` of 2026-08-31.

### Why this is a hard RPG bug and not parked balance

`owner_decision_memo.md` row 7 parks **balance work**. This is not a request to retune anything — the
tuning decision was made and accepted in June. What is wrong is **world truth**: a world runs a
configuration its own closed, accepted remedy replaced. Fixing it restores an existing decision rather
than making a new one.

## Scope

- Re-apply `TCK-20260627-P1I-WORLD-BALANCE-FIX`'s accepted remedy to the **authoritative** location:
  `data/worlds/dungeon_crawl/world.yaml` reduced to the 2 intended modules with `danger_scale: 2`.
- **Regenerate `data/worlds/dungeon_crawl/resolved/world.resolved.yaml`**, and verify production actually
  loads the reduced configuration. Editing `world.yaml` alone changes nothing — this is the step the
  original fix would also have needed.
- Verify the resulting entity count is the intended ~12, not just that the module list shrank.
- **A structural guard so this class cannot recur:** a check that re-resolving a composition world
  **deterministically reproduces its committed `resolved/` snapshot**.
  **Premise corrected 2026-10-04 by `world-rule-catalog-design`** — my original framing ("regenerate
  whenever `world.yaml` changes") was **too narrow**. The snapshot is a function of `world.yaml` **plus
  the module and catalog content the resolver reads at resolve time**, so a snapshot can go stale from a
  module or catalog edit with `world.yaml` untouched. The 09-08 vs 08-31 dates do **not** show which
  input moved. The comparison is therefore **equality against a fresh resolve**, never a field-by-field
  diff against `world.yaml` — the projection legitimately contains expanded content.
- **Run that check across EVERY composition world before re-applying anything.** The rule owner's
  suggestion, adopted: `dungeon_crawl` may not be the only stale snapshot, and the check tells you which
  worlds have been running something other than their source. Re-applying one world's fix while others
  are silently stale would fix the symptom and leave the class.
- Check whether **any other closed ticket** wrote a world-content change to
  `data/content/world_compositions/` only. This one was found incidentally; a second instance would turn
  a one-off into a pattern.
- Update `TCK-20260627-P1I-WORLD-BALANCE-FIX`'s record to state its remedy was inert until this ticket,
  so its DONE status stops being misleading.

## Out of Scope

- **Re-deciding the balance target.** 32 → 12 and `danger_scale` 4 → 2 are the accepted remedy; this
  ticket delivers them, it does not revisit them. If measurement shows 12 is now wrong, that is a new
  balance ticket and parked by row 7.
- `wilderness_survival`, the other half of the original balance ticket. Its change
  (`healer_hut`/`survivor_camp_shelter`) is **not** assessed here — whether it reached production is
  unknown and belongs to the "any other closed ticket" sweep above, not to this ticket's fix.
- Retiring `data/content/world_compositions/` and reconciling the other 8 pairs. That is
  `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`, which found this.
- Whether the ADR's normative sentence must name `world.yaml` as authored source and `resolved/` as
  generated projection. Routed to `world-rule-catalog-design` 2026-10-04; see Assumptions.

## Acceptance Criteria

1. `data/worlds/dungeon_crawl/world.yaml` carries the accepted remedy (2 modules, `danger_scale: 2`).
2. `data/worlds/dungeon_crawl/resolved/world.resolved.yaml` is regenerated and **no longer contains
   `goblin_camp_conflict` or `old_mine_resource_loop`**, asserted by a test that fails on today's files.
3. A real load through `WorldRepository.load_world("dungeon_crawl")` yields the reduced configuration,
   and the entity count is the intended ~12. **Assert non-empty before counting** — a vacuous assertion
   over an empty collection has already passed green in this repo once.
4. A structural check fails when **re-resolving** a composition world does not reproduce its committed
   `resolved/` snapshot. This is the anti-recurrence guard and the most important criterion here. It is
   **equality against a fresh resolve**, not a diff against `world.yaml` (see the corrected premise in
   Scope). **If a fresh resolve turns out not to be byte-deterministic today, that is itself a finding to
   file — not a reason to weaken this check to a subset comparison.** (Rule owner's instruction,
   2026-10-04.)
4a. The check from AC-4 is **run across every composition world** and its results recorded, before any
   re-application. A list of which worlds are currently stale is the deliverable, including "only
   `dungeon_crawl`" if that is the answer.
5. The "any other closed ticket wrote only to the catalog path" sweep is run and its result recorded —
   including "none found", which is a result.
6. `TCK-20260627-P1I-WORLD-BALANCE-FIX`'s record notes its remedy was inert from 2026-06-27 until this
   ticket closed.
7. The behaviour change is recorded in `docs/guidelines/intentional_divergences.md` with rationale class
   **`Bug Fix`**, and the relevant `docs/parity_ledger/` entry updated. Note `INFRA-373` pins
   `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` and **will move** when
   `data/worlds/dungeon_crawl/` changes — update it deliberately, do not let it fail and get patched.

## Related Tickets

- `TCK-20260627-P1I-WORLD-BALANCE-FIX` (done) — **the fix this ticket delivers.** Read its lines 73–75
  and 93 first; they are where the one-file scope is visible.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — found this during its Investigate phase;
  retires the catalog directory and reconciles the other pairs. **This ticket should land first or
  together**: that one's AC-5 was originally written to keep `danger_scale: 4`, which would have
  re-ratified the extinction config.
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` (done, DUPLICATE) — its measurement-validity
  framing is the same root problem one level out, and it only counted **two** definitions. There are three.

## Related Docs

- `docs/architecture/world_repository_layout.md` — the ADR; its §2 already specifies the `resolved/`
  sub-directory, so the three-artifact structure is by design, not accidental
- `docs/mechanics/06_worldbuilding_foundation.md` — integrity validation
- `docs/world/generator_contract.md` — the two generation paths
- `docs/plans/systemic_world/owner_decision_memo.md` — row 7, why this is a hard bug and not parked

## Related Stored Artifacts

- `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/investigation.md`
  — the Investigate phase that surfaced this, with the full three-artifact analysis and the parity-entry
  inventory

## Related Code Areas

- `src/worldbuilding/repository.py:74-81` — the redirect to `resolved/` that made the fix inert
- `data/worlds/dungeon_crawl/world.yaml`, `data/worlds/dungeon_crawl/resolved/world.resolved.yaml`
- `data/content/world_compositions/dungeon_crawl.yaml` — where the fix was written
- `src/worldassembly/resolver.py` — generates the resolved snapshot
- `tests/integration/worldassembly/test_real_content_world_compositions.py:424-452` — still asserts
  `danger_scale == 2` against the catalog copy, i.e. it has been testing the fix in the one place the fix
  had no effect

## Assumptions / Open Questions

- **Unverified: whether `wilderness_survival`'s half of the original fix also failed to reach
  production.** Deliberately out of scope above, but it is the obvious second instance to check and it
  would change this from an incident into a pattern.
- ~~Open with `world-rule-catalog-design`: whether the ADR must gain a clause, and whether the integrity
  check must assert source-vs-resolved agreement.~~ **ANSWERED 2026-10-04: yes to both.** The clause goes
  in ADR §1 directly after the normative sentence (wording supplied by the rule owner and recorded in
  `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`), Bible 06 states the invariant *"the world the
  engine loads is the one its authored definition resolves to"* and cites the ADR, and **no catalog Rule
  is added** — this is storage and build, below catalog scope, by analogy to `OWN-01`. The owner also
  corrected my premise about what makes a snapshot stale; see Scope.
  - One useful note from that ruling: the ADR **already** draws the source/projection line at
    `docs/architecture/world_repository_layout.md:41-54` (a `worldcomposition.v1` source is never passed
    to the compiler; the resolver writes `resolved/` output the loader reads). **What the ADR lacks is the
    authority and freshness rule**, which is the actual gap — not the structure.
  - The *mechanism* for AC-4 (CI test, a regenerate-and-diff make target, or both; and whether the
    provenance/report sidecars join the comparison or only `world.resolved.yaml`) is explicitly **not**
    the rule owner's and is left to this ticket or test-architecture.
- **Unverified: how `resolved/` snapshots are regenerated in practice** — on demand via
  `make world-resolve`, on a schedule, or never. The 8-day gap between `dungeon_crawl`'s two files
  suggests "manually, sometimes". Worth establishing before relying on regeneration as a step.
- Unverified: whether any other world's `resolved/` snapshot is stale against its `world.yaml`. If several
  are, AC-4's check will fail broadly on first run and that is information, not a reason to weaken it.

## Implementation Notes

- AC-4a result (run BEFORE any change): all 24 composition worlds' committed `resolved/world.resolved.yaml` equal a fresh resolve of their own `world.yaml`, and resolve is byte-deterministic. No snapshot was stale against its source; `dungeon_crawl`'s `world.yaml` itself never got the fix. Positive control: the catalog copy resolves to a different world than the snapshot.
- AC-5 result: catalog copy vs `world.yaml` differs for `dungeon_crawl`, `frontier_extended`, `frontier_living_world`, `swamp_border_world` (catalog lacks `trading_company_hub`) and `urban_political` (catalog lacks `hero_adventurers`); `highland_traverse` and `wilderness_survival` are identical (so wilderness_survival's half of the fix reached production). Measurements taken via a non-running definition are tracked in `TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION`.
- A fourth stale artifact: `world_compile_report.json` still said 32 entities; `test_distinct_populated_factions` and the corpus registry read it. Regenerated, and a guard added for its content-derived counts. Hashes and `place_count` are NOT guarded (stale in ~20 worlds from compiler changes; known as `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`).
- Census table: only `dungeon_crawl` (4 -> 2) changed, because the running world changed (the 4 was a faithful measurement of the unintended world); the entries for the other four catalog-divergent worlds (9, 6, 4, 4) match fresh compiles.
- Live world after the fix: 12 entities, 2 regions, 0 resource nodes, 0 buildings, 2 populated factions. `faction_tension_overrides` left as is.
- Blast radius, handled per planner ruling: six rendering-evidence tests now use a frozen copy of the old snapshot (`tests/fixtures/rendering/dungeon_crawl_pre_balance_fix.resolved.yaml`; assertions unchanged). **A frozen fixture no longer detects rendering regressions in the live corpus.** Follow-up decision: `TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT`. `INFRA-373` is therefore not moved; it reproduces on the fixture. `src/rendering/` and `docs/visual_quality/` untouched (assigned to neither lane).

## Test Summary

- New `tests/integration/worldassembly/test_resolved_snapshot_freshness.py` (49 cases): snapshot == fresh resolve per composition world, resolve determinism, compile-report counts == fresh compile per world, dungeon_crawl remedy at the loaded location (12 entities, non-empty first). Positive controls: the compile-report guard fails on the old report; the catalog copy differs from the snapshot.
- Updated: census pin (`dungeon_crawl` 4 -> 2), corpus registry regenerated, six rendering tests repointed.
- Final-tree run (after merging `origin/main` at `ad194bec4`, #328 included): scoped suites over rendering, worldassembly, worldgeneration, architecture, engine, social, cli, lab, simulation_quality, scenarios, content and related = 2547 passed, 1 failed; full `tests/tools` plus `tests/unit/tools` = 4243 passed, 0 failed after removing the three resurrected `todos/` ticket copies the merge brought back. The one failure, `tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x` (population guard), is not from this batch: it fails identically on a clean `origin/main` (`1c59e01f4`).

## Files Changed

`data/worlds/dungeon_crawl/{world.yaml,world_compile_report.json,resolved/*}`; `config/simulation_quality/corpus_registry.yaml`; `src/worldbuilding/cli.py` (shared `render_resolved_world_yaml`); `tests/integration/worldassembly/test_resolved_snapshot_freshness.py`; `tests/unit/worldassembly/test_corpus_diversity.py`; `tests/unit/rendering/{test_connectivity,test_density,test_shape,test_variants,frozen_dungeon_crawl}.py`; `tests/fixtures/rendering/dungeon_crawl_pre_balance_fix.resolved.yaml`; `docs/guidelines/intentional_divergences.md` (DEV-009); `docs/parity_ledger/substrate.yaml` (SUB-395); `agent-working/tickets/done/TCK-20260627-P1I-WORLD-BALANCE-FIX.md` (AC-6 note).

## Completion Summary

The accepted dungeon_crawl balance remedy (2 modules, danger_scale 2, 12 entities) now runs: world.yaml, resolved/ and world_compile_report.json are updated, and guards assert every composition world's snapshot equals a fresh resolve and every compile report's content-derived counts equal a fresh compile. Blast radius handled: census pin 4 to 2, corpus registry regenerated, six rendering-evidence tests moved to a frozen fixture (which no longer detects rendering regressions in the live world; follow-up filed). DEV-009 and SUB-395 recorded; the 2026-06-27 ticket annotated as inert until now.
