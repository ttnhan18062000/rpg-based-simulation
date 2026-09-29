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
Not yet started. Filed to give this finding the same dedicated tracking its sibling instances
already have.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
Open. Filed 2026-09-20 alongside `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` to
close a real tracking gap for a confirmed, contradicted finding that had lived in the registry
since 2026-09-16 with no dedicated ticket of its own.
