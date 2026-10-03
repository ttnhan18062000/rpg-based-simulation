---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION

## Title
Batch 2 of the unbound-claims program: world (12), faction (5), region (4), group (2) —
23 mechanisms claiming a working state with no code binding

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Batch 2 of the 4-batch unbound-claims program (batch 1: entity layer, done, PR #229). Same governing
constraint: resolve the claim, not the count — a real binding, a corrected `state`, or an honest
"left unbound, here's why" are equally good outcomes.

## Scope
Resolve all 23 world/faction/region/group mechanisms with `state` in `done`/`partial`/`gated` and no
`implemented_by`: `campaigns`, `chronicle`, `opportunity_rumor_seeds`, `calamity_intensity`,
`world_boss_spawn`, `world_generation`, `equipment_scoring`, `inventory_trade_conservation`,
`crafting`, `buildings`, `town_services`, `building_sabotage`, `betrayal_siege_war`,
`social_contracts`, `reputation`, `cross_episode_grief_nemesis`, `country_lifecycle`,
`regional_trauma`, `city`, `camp`, `ruins_mines_battlefields`, `party_formation`, `guilds`.

## Out of Scope
- Registry schema, system membership, re-verifying already-verified entries (except where new
  evidence surfaced during this batch's own investigation directly contradicted one — see
  `calamity_intensity`).
- Fixing any code, including the two real defects surfaced (an unused `EquipmentService`, a dead
  `Betrayal` faction directive) and the `InnAction`/prior-note discrepancy on `town_services`.
- Performing the `betrayal_siege_war` Split candidate this batch's own investigation surfaced —
  flagged, not executed, same restraint as batch 1's `commitment_betrayal` merge non-execution.
- Batches 3/4 and the `xp_leveling`/`evolution` identity investigation — separate pieces of the
  same program, tracked in their own tickets, landing in the same PR per the user's own call.

## Acceptance Criteria
1. All 23 mechanisms resolved with a real binding, a corrected state, or a stated reason to leave
   unbound.
2. The outcome split reported explicitly, not just a bound-count.
3. Judgement-call bindings (not certainties) say so in the entry.
4. Any binding proposed on the strength of a pre-existing `verified` note's own claim is
   independently re-checked, not trusted — and if the re-check contradicts the note, the
   contradiction is surfaced rather than silently forced into a binding.
5. `registry.py::validate()` clean; all consumer artifacts regenerated and drift-checked clean.

## Related Tickets
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION` — batch 1, same program.
- `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` — independently
  corroborates this batch's own `chronicle` orphan finding.
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — still open; this batch's own finding
  (the producer has zero callers at all, not merely a data-starved trigger) needs reconciling
  against that ticket's own framing, flagged for the roadmap session.
- `TCK-20260907-CHURCH-CONTENT-AUTHORING` — cited by `town_services`'s own pre-existing note,
  cross-checked during this batch.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §3.1 — 6th search-failure shape, added
  earlier in this same session from batch 1's own `commitment_betrayal` finding; applied throughout
  this batch (`world_generation`'s `WorldCompiler.compile()` static-method call missed by an
  instantiation-pattern grep; `campaigns`'/`chronicle`'s docstring-only usage examples).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION/`.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tests/unit/tools/test_mechanism_state_caller_check.py`,
  `test_mechanism_registry_completeness_check.py` (pinned-baseline updates)
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html`,
  `mechanism_registry.html`, and the 3 markdown views — regenerated.

## Assumptions / Open Questions
Findings flagged for the roadmap session, not resolved here:
1. **`calamity_intensity`**: a real, registry-changing finding, not a checker false positive.
   `CalamityService.apply_calamity_consequences()` has zero real callers anywhere (confirmed by
   direct re-check after the state-caller checker flagged it) — stronger than the mechanism's own
   pre-existing (2026-09-17) `verified` note describes ("correct, wired code, defeated by real-world
   data never meeting its trigger precondition," implying reachability). Left unbound; the
   pre-existing note was not overwritten (it predates this batch), but the contradiction is recorded
   on the entry for `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` to reconcile.
2. **`betrayal_siege_war`** looks like a real Split candidate: siege/war is real and live
   (`MilitaryConflictPhase`), betrayal is not (`Betrayal(FactionDirective)` has zero real
   constructors). Flagged on the entry, not split here.
3. **`town_services`**'s own pre-existing note claims "Inn... services are live"; direct re-check
   found `InnAction.rest()` has zero references anywhere outside its own file — a real discrepancy
   with that prior claim, flagged but not resolved (state stays `done`, justified by Shop/Blacksmith
   alone).
4. **`EquipmentService`** (`equipment_scoring`'s new binding) and `BuildingRegistry`
   (`buildings`'s originally-considered, ultimately-unused candidate) are both real, well-built,
   entirely-uncalled code — worth a broader look at whether either should be wired in or retired.

## Implementation Notes

### Outcome split
**21 bound** (2 of them judgement calls, flagged in-entry: `crafting` shares `inventory_trade_
conservation`'s own `ResourceTransactionResolver` class since the mechanism's own logic is one
branch inside a single method, below this registry's current binding granularity; `town_services`
bound to Shop+Blacksmith only, Inn's own discrepancy flagged separately).
**4 state corrections**: `chronicle` (done→orphan, corroborated by an independently-found,
already-filed ticket), `equipment_scoring` (done→orphan, real code with zero external callers
anywhere), `betrayal_siege_war` (done→partial, siege/war real, betrayal half dead — Split candidate
flagged), `ruins_mines_battlefields` (partial→gap, applying this entry's own already-stated
conclusion, no fresh investigation).
**2 left unbound**: `calamity_intensity` (a real contradiction with a pre-existing verified note,
flagged rather than resolved unilaterally — see Assumptions #1), `ruins_mines_battlefields` (no real
implementing code exists, consistent with its own state correction above).

### A real self-correction during this batch, caught by the state-caller checker
Attempted to bind `calamity_intensity` on the strength of its own pre-existing verified note's
confident claim. The checker immediately flagged zero real callers. Independently re-checked rather
than trusted (same discipline established in batch 1 for `breakthrough_bonuses`'s own
self-correction) — the checker was right; the binding was reverted, not forced. This is the second
time this batch's own tooling has caught this session's own mistake before it landed, not after.

### Concurrent-fork process note
No forks were dispatched for this batch — all 23 mechanisms investigated directly, avoiding a
repeat of batch 1's read-only-instruction violation and the concurrent-write race it caused.

## Test Summary
`tests/unit/tools/test_mechanism_state_caller_check.py`: pinned finding set expanded from 6 to 9,
each new finding independently investigated (3 understood checker limitations documented, 1 real
finding that changed the registry rather than the pin). `tests/unit/tools/test_mechanism_registry_
completeness_check.py`: pinned counts updated (`bound` 29→33, `unbound` 32→28) with per-target
attribution. Full `tests/unit/tools/` suite: 260 passed. `registry.py::validate()`: clean, 93
mechanisms. All 5 blocking mechanism-registry checks: clean.

## Files Changed
- `registries/mechanisms.yaml` — 21 mechanisms bound, 4 state corrections (3 also bound).
- `tests/unit/tools/test_mechanism_state_caller_check.py`,
  `test_mechanism_registry_completeness_check.py` — pinned updates.
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html`,
  `mechanism_registry.html`, and the 3 markdown views — regenerated.

## Completion Summary
**Done.** 21 of 23 mechanisms bound (2 disclosed as judgement calls), 4 real state corrections (one
of them, `ruins_mines_battlefields`, applying an already-documented conclusion rather than fresh
investigation), 2 left unbound — one of them (`calamity_intensity`) because this batch's own
investigation genuinely contradicted a pre-existing verified conclusion, caught by the same
state-caller checker tool batch 1 fixed, and correctly NOT forced into a binding. A real Split
candidate (`betrayal_siege_war`) and a real prior-note discrepancy (`town_services`'s own Inn claim)
were both found and flagged rather than acted on. Batches 3/4 and the `xp_leveling`/`evolution`
identity investigation remain, landing in the same PR per the user's own call.
