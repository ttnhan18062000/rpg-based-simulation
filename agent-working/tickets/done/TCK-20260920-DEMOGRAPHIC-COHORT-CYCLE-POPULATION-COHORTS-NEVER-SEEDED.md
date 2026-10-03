---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED
phase: done
date: 2026-09-20
tags: [world]
---

# TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED

## Title
`DemographicCycleService.process_demographics` is real and correctly wired, guarded by
`if not region.population_cohorts` — but no compiled or procedurally-generated world today ever
seeds `population_cohorts`, so the call is a permanent no-op in every real run

## Status
DONE

## Disposition
STALE-PREMISE

## Disposition Rationale
This ticket's premise — that no compiled or procedurally-generated world seeds any region's
`population_cohorts`, so the `if not region.population_cohorts` guard
(`src/worldbuilding/compiler.py:203`) never opens — was already false when the ticket was filed on
2026-09-20, and had been since 2026-08-31. Closed without implementation in `791e6bf6b`; zero
`src/` files changed.

Evidence: a real `WorldAssemblyResolver.assemble()` → `WorldCompiler.compile(seed=42)` of
`frontier_living_world` seeds **non-empty cohorts in 6 of 7 regions** — `hometown` declares a
population of 13 and yields `{young: 4, adult: 6, elder: 3}`, the exact 30/50/20 split from
`_seed_population_cohorts` (`src/worldbuilding/compiler.py:190`). The 7th region (`near_forest`)
correctly receives `{}` because it has zero `PopulationSpec` entries, not because of a key
mismatch; every `spawn_region` value has a matching `RegionSpec.id`. The seeding code shipped in
`TCK-20260831-POPULATION-COHORT-SEEDING` on 2026-08-31 — three weeks before this ticket, and
before the `registries/mechanisms.yaml` verdict it quoted (dated 2026-09-16). Reproduced
independently from two worktrees with identical per-region figures.

AC-1 through AC-3 are **void rather than met** — each presupposed a seeding gap that does not
exist.

**This disposition covers the seeding claim only, and closing it does not mean the demographic
cohort cycle works.** The mechanism's real status now lives in
`TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO`: cohorts are seeded, the guard does
open, and the birth/death cycle still never fires, for an unrelated reason. These are separate
claims on separate evidence — do not let the second weaken the first.

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

**Independently reproduced by `rpg-feature-planning`, 2026-09-30**, from a separate worktree run of
the same composition — identical per-region cohort figures, and explicit confirmation that no
`spawn_region` value lacks a matching `RegionSpec.id` in this content. `STALE-PREMISE` is
independently reproduced, not a single-run finding.

**What this verdict does NOT establish, flagged by that same independent check so it isn't lost:**
`STALE-PREMISE` retires the *seeding* claim only — that `population_cohorts` starts non-empty. It
says nothing about whether `DemographicCycleService.process_demographics`'s per-200-tick birth/death
math (`birth_rate=0.02`, `mortality_rate=0.01`, `cohort.py:41-42`) produces any *observable* change
over a real corpus run length (~25 cycles at 5,000 ticks, applied to seeded counts of 5–13 — a 2%
rate may round to zero every cycle). That is a distinct, unmeasured, open question — not claimed
either way here, and deliberately not folded into the `STALE-PREMISE` verdict above. Whether it
warrants its own ticket is left for after this epic's other classification passes finish, not
decided by this pass.

## Test Summary
_(not started — this pass is classification-only; no test authored or run beyond the ad hoc
verification script above)_

## Files Changed
_(none — disposition-only closure; nothing under `src/` changed)_

## Completion Summary
Closed 2026-09-30 as **STALE-PREMISE**; no code change. The premise that no world seeds
`population_cohorts` is false: 6 of 7 regions seed non-empty cohorts (`hometown` declares 13 →
`{young:4, adult:6, elder:3}`, exact 30/50/20); the 7th correctly gets `{}` for having zero
`PopulationSpec`. Seeding shipped 2026-08-31. Reproduced from two worktrees with identical figures.

**Closing this does NOT mean the demographic cycle works.** The open question in Implementation Notes
resolved badly: `cohort.py:377-381` computes `net = int(count * 0.01)`, which needs `count >= 100` to be
non-zero, against seeded brackets of 3–6. The cycle therefore never changes a count and never emits a
`POPULATION_BIRTH`/`DEATH` event. That defect is tracked as
`TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` (P1, open) — that ticket, not this closure,
is the status of the mechanism.

AC-1 and AC-2 are void (no gap to explain or fix). AC-3 is void, not met: the finding doc is retired
(`f70f58706`) and cohorts were never an instance. The `registries/mechanisms.yaml`
`demographic_cohort_cycle` verdict correction is owned by
`TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`.
