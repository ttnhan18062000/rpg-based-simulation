---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED
artifact_type: investigation
tags: [investigation, root-cause, corpus, world]
---

# Investigation — TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED

## Summary

Four independent classification checks against the epic's four-value verdict axis
(`DEFECT`/`CONDITION`/`UNDECLARED`/`MISLABEL`, plus the AC-7 fifth-outcome escape hatch). No `src/`
change in any check. Full evidence lives in the ticket's own Implementation Notes and in each
covered ticket's own body (per the epic's Deliverable 2) — this file summarizes and points there
rather than duplicating the evidence wholesale.

## Check 1 — `demographic_cohort_cycle` (`TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-...`)

Compiled a real, in-corpus world composition (`data/content/world_compositions/
frontier_living_world.yaml`) end-to-end via `WorldAssemblyResolver.assemble()` →
`WorldCompiler.compile(seed=42, ...)` — no mocks. Compared the `spawn_region`-keyed
`region_declared_population` dict against every `RegionSpec.id`, then read the resulting
`RegionState.population_cohorts` per region.

**Result:** keys agree everywhere real content declares population; 6 of 7 regions seed non-empty
cohorts (e.g. `hometown`: declared 13 → `{young:4, adult:6, elder:3}`, exact 30/50/20 split); the
7th (`near_forest`) correctly gets `{}` because it has zero `PopulationSpec` entries, not because of
a key mismatch. Independently reproduced by `rpg-feature-planning` from a separate worktree with
identical figures.

**Verdict: `STALE-PREMISE`** (AC-7). The ticket's premise ("no world seeds `population_cohorts`") is
false today — has been since `TCK-20260831-POPULATION-COHORT-SEEDING` shipped the seeding code on
2026-08-31, three weeks before this ticket was filed on a `registries/mechanisms.yaml` verdict dated
2026-09-16 that was never re-checked against it.

## Check 2 — `camp` (`TCK-20260920-CAMP-STATE-NEVER-SEEDED-...`)

Same composition, same compile, checked `state.camps` instead. **Result:** 2 real `CampState`
entries (`goblin_camp_place`, `wolf_den_nest`), both fully constructed. Root cause: two constituent
world modules (`goblin_camp_conflict.yaml`, `wolf_den_near_forest.yaml`) declare `creature_kind` on
a `CAMP`/`NEST` `PlaceSpec` — content committed `cb0b23b07` (2026-09-08), 8 days before the registry
verdict (2026-09-16) and 12 days before this ticket's filing (2026-09-20).

**Verdict: `STALE-PREMISE`** (AC-7), same shape as `demographic_cohort_cycle`. Bonus finding:
`docs/world/raid_boss_camp_contract.md` (`last_verified: 2026-09-04`) is itself stale on this exact
point — flagged in the covered ticket's own body, not corrected here (out of this epic's scope).

## Check 3 — `enemy_data` / `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER`

No `registries/mechanisms.yaml` verdict cited (confirmed via grep) — registry-dating method doesn't
apply. Confirmed directly instead: `src/cognition/capability_estimate.py:124-127`'s
`_ENEMY_DANGER.get(enemy_id, 0.5)` fallback runs on every real combat capability estimate (real
caller: `src/engine/tactical.py:405`), since `enemy_data` is always `{}`. The mechanism fires
correctly every time — it just always uses a generic per-species table instead of per-entity
learned data, because no mechanism anywhere produces the latter. `NO-MECHANISM-RECORDS`'s own
Completion Summary already concluded "nothing declares this," reported for a user-level design
decision.

**Verdict: `UNDECLARED`** — matches the axis's operative test ("needs a design decision before any
code change") even though the root shape (zero declared producers) differs from the axis's literal
"competing implementations" description; recorded as a shape-mismatch-but-operative-fit, not forced.

## Check 4 — `region_data` (`CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s other half)

Independent of Check 3. Confirmed `RouteFamily.SCOUT_LOCATION` is declared in 3 separate type-level
tables (`schema.py:27`, `mapper.py:41`, `scoring.py:44,179,271`) but absent from every branch of
`src/domains/adventure/generator.py` — grepped every `RouteFamily.` reference in that file; every
other generatable family is listed, `SCOUT_LOCATION` is in none of them. The one route family that
would naturally supply `travel_regions` a real caller was scoped into 3 tables and never
implemented in the generator.

**Verdict: `UNDECLARED`** — same label as Check 3 via the same operative test, but a genuinely
different root shape (declared-and-scaffolded-but-unbuilt, vs. Check 3's zero-declared-intent);
`CAPABILITY-CONTEXT`'s `enemy_data` half inherits Check 3's verdict rather than being independently
re-derived, since that ticket's own text already names `NO-MECHANISM-RECORDS` as the cause of its
own symptom.

## What this pass did not do

- No `CONDITION` verdict was reached for any of the 4 covered tickets — the epic's AC-6
  (corpus-run-length vs. world-content split) is N/A this pass.
- Did not update `docs/plans/world_composition_precondition_gap_finding.md` or
  `docs/world/raid_boss_camp_contract.md` — flagged as stale in the affected tickets' own bodies,
  correction deferred (out of this epic's scope; the shared classification doc itself is deferred
  to `T06`).
- Did not touch `registries/mechanisms.yaml` — confirmed byte-for-byte unchanged against
  `origin/main` after every check.
