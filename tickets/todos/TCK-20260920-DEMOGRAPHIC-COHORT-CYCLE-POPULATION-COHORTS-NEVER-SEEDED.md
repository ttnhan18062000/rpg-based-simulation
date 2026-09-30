---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED
phase: open
date: 2026-09-20
tags: [world]
---

# TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED

## Title
`DemographicCycleService.process_demographics` is real and correctly wired, guarded by
`if not region.population_cohorts` — but no compiled or procedurally-generated world today ever
seeds `population_cohorts`, so the call is a permanent no-op in every real run

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`registries/mechanisms.yaml`'s own `demographic_cohort_cycle` entry has carried this exact finding
since 2026-09-16 (`verified.verdict: contradicted`, found by
`TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`'s own first real run) but was never given
its own tracking ticket — same gap as `camp`'s own entry (see
`TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`, filed alongside this one).

`DemographicCycleService.process_demographics` has a real, confirmed caller
(`engine/world_dynamics.py:178-179`), so the mechanism was previously mis-registered `orphan` and
already corrected to `done` — the code itself is not defective. But the caller is guarded by
`if not region.population_cohorts` (`worldbuilding/compiler.py:203`), and no compiled or
procedurally-generated world today seeds any region's `population_cohorts`, so the guard never
opens and the call never actually runs its own body in real play. Same "correct, wired code,
defeated by absent world data" shape as `camp`, `lair`-region-trauma, and `calamity_intensity`.

## Scope
- Confirm directly why no world seeds `population_cohorts` — check whether `WorldCompiler` has any
  code path that could populate this field at all, or whether it's a purely unauthored content gap.
- Check whether any content schema declares cohort data that composition could place.
- Propose a real fix (content-authoring or world-gen), reviewed with peer/user before
  implementation — same investment-cap discipline as the other instances of this pattern.

## Out of Scope
- `DemographicCycleService`'s own apply-path logic — already confirmed correct and wired.
- The other instances of this pattern (`camp`, `lair`, `calamity_intensity`) — each tracked
  separately.

## Acceptance Criteria
- [ ] A real, evidence-backed explanation for why no corpus world seeds `population_cohorts`.
- [ ] A proposed fix, reviewed with peer/user before any implementation.
- [ ] `docs/plans/world_composition_precondition_gap_finding.md` updated with this as a named
      instance.

## Related Tickets
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION` — found this finding originally.
- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` — sibling gap, filed alongside this
  ticket for the same "confirmed finding, never tracked" reason.
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
  NEVER-FIRES` — same pattern family.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the shared pattern document.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/demographics/cohort.py` (`DemographicCycleService`)
- `src/worldbuilding/compiler.py:203` (the `if not region.population_cohorts` guard)
- `src/engine/world_dynamics.py:178-179` (the real caller)

## Assumptions / Open Questions
Whether the gap is purely content-authoring or a deeper world-gen gap is not yet distinguished.

## Implementation Notes
**2026-09-30 — verdict recorded via `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED` (epic `T02`,
`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`): `STALE-PREMISE` (AC-7 fifth outcome, not
forced into `CONDITION` or `MISLABEL`).**

This ticket's own premise — "no compiled or procedurally-generated world today ever seeds
`population_cohorts`" — is **false as of today**, contradicted directly by executing (not reading)
`WorldCompiler.compile()` against a real, in-corpus world composition
(`data/content/world_compositions/frontier_living_world.yaml`, resolved via
`WorldAssemblyResolver.assemble()`, `tests/integration/worldassembly/test_real_content_world_
compositions.py`'s own fixture path). Result: **6 of 7 regions received non-empty
`population_cohorts`** (`hometown`, `bandit_road`, `goblin_camp`, `old_mine`,
`haunted_battlefield`, `wolf_den` — e.g. `hometown` → `{young: 4, adult: 6, elder: 3}` from a
declared population of 13, split by the documented 30/50/20 ratio). The seventh, `near_forest`, got
`{}` correctly — it has **zero** `PopulationSpec` entries with `spawn_region="near_forest"` in this
composition, which is `_seed_population_cohorts`'s own documented `declared_population == 0` → `{}`
behavior, not a seeding failure.

**The decisive fork (identified by `rpg-feature-planning`'s independent cross-check, 2026-09-30) is
resolved: `spawn_region` and `RegionSpec.id` do NOT diverge for real content.** Every
`PopulationSpec.spawn_region` value in this composition (`hometown`, `bandit_road`, `goblin_camp`,
`old_mine`, `haunted_battlefield`, `wolf_den`) matches a real `RegionSpec.id` exactly. There is no
key-space mismatch bug — `region_declared_population.get(r_spec.id, 0)` (`compiler.py:449`) finds
the entry every time a region has any declared population at all.

**Ticket-provenance finding (not a mechanism verdict — do not fold into future work on this
mechanism):** this ticket was filed 2026-09-20, three weeks after `TCK-20260831-POPULATION-COHORT-
SEEDING` closed `DONE` on 2026-08-31 and shipped the exact seeding code that contradicts this
ticket's premise. Per its own Request Summary, it was filed on the strength of a
`registries/mechanisms.yaml` `demographic_cohort_cycle` entry dated 2026-09-16 — itself six weeks
after the fix shipped — that was apparently never re-checked against the compiler's actual code
before this ticket copied its verdict forward. Routed to `agent-working-design` as a registry/
ticket-filing-staleness process finding, per the epic's own T02 scoping.

**Full experiment output, code, and reasoning:** `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED`'s
own Implementation Notes (this ticket's classifying parent).

## Test Summary
_(not started — this pass is classification-only; no test authored or run beyond the ad hoc
verification script above)_

## Files Changed
_(none — read-only verification; `registries/mechanisms.yaml` confirmed unchanged against
`origin/main`)_

## Completion Summary
Filed 2026-09-20 alongside `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` to close a
real tracking gap for a confirmed, contradicted finding that had lived in the registry since
2026-09-16 with no dedicated ticket of its own. **Verdict as of 2026-09-30: `STALE-PREMISE`** — the
premise this ticket exists to track no longer holds against real content; see Implementation Notes.
Still `OPEN` pending whoever owns the `registries/mechanisms.yaml` `demographic_cohort_cycle` entry
correction and this ticket's own closure — out of scope for the classifying pass itself
(`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`'s own scope guard: no registry edits).
