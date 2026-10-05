---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE
phase: open
date: 2026-10-05
tags: [world, investigation]
---

# TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE

## Title
Probe the 24 corpus worlds for four silent world-composition failures — duplicate place ids,
unvalidated compiles dropping populations/resources/buildings, first-wins faction id merges, and
namespace-stripped biome provenance — and report which actually fire

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Candidates found by a read-only survey from `world-rule-catalog-design`, routed to `rpg-planner` for
filing. **None was measured at runtime.** This ticket exists because the survey's own guidance was
right: these are hard-bug candidates **if they fire on corpus content**, and priority should follow
the measurement rather than the code reading. Filing four unmeasured suspicions as four P1 tickets
would invert that.

The four, each with the cited site:

**(a) Place ids are never checked for uniqueness.** `src/worldbuilding/compiler.py:409-410` is a bare
`places[p_spec.id] = PlaceState(...)` dict assignment, so a second module contributing the same place
id silently overwrites the first.

> **Correction to the survey's own assessment, found while filing this.** The comment immediately
> above that line (`:406-409`, `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`) reads "Empty for all
> existing content today -- new, opt-in only; existing worlds compile with places=[] exactly as
> before this ticket." **That comment is stale.** At least nine modules under
> `data/content/world_modules/` now declare region-level `places:` (`frontier_village_core`,
> `goblin_camp_conflict`, `wolf_den_near_forest`, `moon_cult_ruins`, `settled_quarter`,
> `survivor_camp_shelter`, `undead_battlefield`, `ruins_mystery_quest`,
> `camp_maturity_calibration_pilot`), and resolved worlds including `frontier_extended`,
> `dungeon_crawl` and `lifecycle_full_coverage_world` carry place entries. So (a) is **reachable**,
> not dormant — a reader trusting that comment would conclude the opposite, which is exactly what
> nearly happened here. **Whether any real composition contains a duplicate place id is still
> unmeasured and is this ticket's first question.** The stale comment is itself a finding to fix.

**(b) The compiler never calls `WorldValidator`.** Three paths compile without validating:
`orchestrator.py:733` (Campaign), `cli/entry.py:228`, `api/engine_manager.py:136`. On those paths a
population, resource node or building whose region is unknown is skipped with **no warning**
(`compiler.py:498-499`, `:537-538`, `:575-576`).

> **(b) is largely RESOLVED before this ticket was dispatched — 2026-10-05.** `rpg-implementer-2`
> closed `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` and found the same
> defect from the other side: every placement loop in `WorldCompiler.compile` was wrapped in
> `if region:` with no `else`, so a population, resource node or building naming an undefined region
> was silently dropped. It added a `_assert_region_references_resolve(spec)` pre-pass raising
> `InvalidWorldSpecError` and listing every offender, with 4 tests and a confirmed negative control.
> Because the guard sits in `compile` itself, **all three unvalidated paths inherit it** — the fix
> does not depend on any of them calling `WorldValidator`. It also measured the corpus: **0 of 24
> worlds dangle**, which is the count this probe would have taken for (b).
>
> **What is left of (b), and it is narrower:** `WorldValidator` is still not called on those three
> paths, so whatever *else* it checks beyond region-reference resolution is still skipped there. That
> residue is worth one pass — enumerate what `WorldValidator` validates, subtract what the new
> pre-pass now covers, and report the remainder. If the remainder is empty, say so and `WorldValidator`
> is arguably dead on those paths, which is a different finding. Do **not** re-probe region references;
> that is measured and fixed.

**(c) Faction ids merge first-wins across modules, silently** (`resolver.py:382`). #335's namespacing
does **not** rewrite faction ids, place `owner_faction_id`, or quest ids — only region ids.

**(f) Biome provenance strips a namespace with `split("_", 1)`** (`resolver.py:366-367`). The
generator namespaces with module ids, which themselves contain `_`, so a namespaced region can look
up the wrong catalog biome. The survey flagged this UNCONFIRMED and named `generated_frontier_3_42`
as the world to check.

Sites are at `405cbd77b`. **Re-derive every line number** at the commit this starts from.

## Scope
1. Build one probe that resolves and compiles all 24 `data/worlds/*` compositions and reports, per
   world: duplicate place ids; populations, resource nodes and buildings dropped for an unknown
   region; faction ids contributed by more than one module with differing definitions; and regions
   whose biome provenance lookup after `split("_", 1)` does not match the authored biome.
2. Report the counts **whatever they are**. Zero across all four is a valid, valuable result and must
   be stated as such, not treated as a failed investigation.
3. For each of the four that fires, state whether it changes **world truth** (a place absent or
   replaced, a population never spawned, a faction mis-identified, a region with the wrong biome) or
   is merely untidy. That distinction, not the raw count, sets the priority of the follow-up.
4. Fix the stale comment at `compiler.py:406-409` regardless of what the probe finds. It is wrong
   today and it actively misleads.
5. Do **not** fix (a)-(c) or (f) in this ticket. File a follow-up per confirmed defect, scoped by
   what the probe showed. One of them may deserve to be a hotfix and the others may not exist.

## Out of Scope
- Region **id** collisions (settled by #335) and region **bounds** overlap
  (`TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`).
- The latent set — `TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS`.
- Adding a `WorldValidator` call to the three paths. That is (b)'s follow-up and its blast radius is
  every world those paths load; it is not a probe's decision.
- `registries/mechanisms.yaml` content, owned by `world-rule-catalog-design`.

## Acceptance Criteria
- [ ] The probe runs over all 24 compositions and its output is stored under
      `agent-working/stored_artifacts/` as `.jsonl` (**not `.json`** — `.gitignore` drops
      `stored_artifacts/*.json`, so cited evidence in that extension never reaches the remote).
- [ ] All four checks report a count per world, including zeros.
- [ ] The probe is positive-controlled: for each of the four, show it detects a deliberately
      introduced instance. An unexercised detector reporting zero is not evidence of absence.
- [ ] Scope 3's world-truth-vs-untidy judgement is recorded per firing check.
- [ ] The stale `compiler.py` comment is corrected and the correction cites what made it stale.
- [ ] A follow-up ticket exists for each confirmed defect, or the investigation records explicitly
      that a check fired zero times and why no follow-up is needed.
- [ ] No behaviour change lands in this ticket. It is a measurement.

## Related Tickets
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (#335) — established region namespacing;
  (c) is the scope it did **not** cover.
- `TCK-20260902-WORLDCOMPILER-PLACE-WIRING` — wrote the comment that is now stale.
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — sibling; same "declared invariant,
  absent enforcement" family.
- `TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS` — the latent half of the same survey.
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` — in flight with Lane B;
  (b) is the same silent-fallthrough family seen from the compile side. **Check its outcome first**;
  it may already cover part of (b).
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — in flight with Lane B; depends on
  `generated_frontier_3_42`'s `moon_cave` place, so (a) and (f) touch its evidence.

## Related Docs
- `docs/world/assembly_contract.md`, `docs/architecture/world_repository_layout.md`
- `docs/mechanics/06_worldbuilding_foundation.md` — integrity validation
- `docs/parity_ledger/substrate.yaml`

## Related Stored Artifacts
_(the probe output will be the first)_

## Related Code Areas
- `src/worldbuilding/compiler.py:409-410` (a), `:406-409` (the stale comment), `:498-499`, `:537-538`,
  `:575-576` (b's silent skips)
- `src/worldbuilding/resolver.py:382` (c), `:366-367` (f)
- `src/lab/orchestrator.py:733`, `src/cli/entry.py:228`, `src/api/engine_manager.py:136` — the three
  unvalidated compile paths. **`src/cli/` and `src/api/` are assigned to neither implementer lane**
  (lane-split §2); read them freely, but a fix there needs a planner ruling.

## Assumptions / Open Questions
- Two of the four may already be covered by Lane B's in-flight batch. Confirm before building the
  probe rather than duplicating it.
- `generated_frontier_3_42` is named for (f) by the survey, not measured. It may be the wrong world.
- (b)'s three paths compile without validating — but whether `WorldValidator` would actually *catch*
  an unknown-region reference is unchecked. If it would not, (b) is a different defect than it looks.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
