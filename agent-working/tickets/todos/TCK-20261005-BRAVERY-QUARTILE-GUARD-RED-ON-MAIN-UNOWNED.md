---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED
phase: open
date: 2026-10-05
tags: [combat, testing, investigation]
---

# TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED

## Title

`test_bravery_quartile_combat_rate_2x` has been failing on `main` with no ticket owning it — the
quartile size collapses to 1, so the guard's own precondition is unmet

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

`tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x` fails
on `main` and has no ticket. It is a guard created by the now-closed
`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`, so closed work's assertion is red and
unowned — it shows up as "a known base failure" in every session that runs the scenarios suite, which is
exactly how a real regression would be waved through.

**Three independent confirmations, on three different commits, by three sessions:**

| who | commit | result |
|---|---|---|
| `rpg-feature-planning` | `foundation-scope-and-retreat-ruling` (#328 branch) | failing; enumerated in #328's pre-existing set |
| `rpg-implementer` | clean checkout of `246ee09f7` (pre-#328) | fails identically |
| `rpg-implementer-2` | clean `origin/main` `1c59e01f4` (post-#328), throwaway worktree | fails identically |

So it is **not** caused by #328, and not caused by the `dungeon_crawl` 32→12 entity correction — it fails
on both sides of that change.

**Symptom:** `quartile size collapsed to 1`. That is the test's *precondition* failing, not its
hypothesis: with one entity per quartile there is no distribution left to compare, so a "2x combat rate
between bravery quartiles" assertion cannot be evaluated either way. Two candidate explanations, and the
ticket must distinguish them rather than pick one:

1. **The population it samples has shrunk** — a corpus/world content change reduced the entity count so
   quartiles no longer have members. Then the guard needs to sample a world that can populate quartiles,
   or state a minimum population as an explicit precondition with a clear skip.
2. **Differentiation genuinely stopped happening** — entities no longer spread across bravery values, so
   the quartiles degenerate. That is a real behavioural defect and the guard is correctly red.

One measured detail from #328's investigation, relevant to (1): this test **builds its own spec and never
constructs a `ScenarioSetupResolver`**, so it does not go through the production world-loading path. Its
population therefore may not match any world the simulation actually runs — establish what it samples
before concluding anything about differentiation.

## Scope

- Determine which of the two explanations above holds, with the entity count and bravery distribution
  measured, not inferred.
- If (1): give the guard a population it can actually quartile, or an explicit minimum-population
  precondition that **skips loudly** rather than failing obscurely. Do not lower the 2x threshold to go
  green — the threshold is the hypothesis.
- If (2): file the behavioural defect, and keep this guard red (or `xfail(strict=True)`) pointing at it.
- Either way: the test must stop being an un-owned "known base failure".

## Out of Scope

- `test_long_run_stability`, the other failure in that known-base pair (a conftest timeout, seed-4
  population guard) — related only by both being tolerated-red.
- Re-opening `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`. Its conclusion stands; this
  is about its guard's current state.
- Any change to the 2x coefficient itself. See
  `TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL` (open, in the `embedding-latent-cognition` folder).

## Acceptance Criteria

1. The entity count and bravery distribution the test actually samples are measured and recorded, with
   the world/spec named.
2. The explanation is stated as (1), (2) or something else, with evidence — not left ambiguous.
3. The test is either green for a stated reason, or `xfail(strict=True)` against a named filed defect.
   **"Known base failure" is not an acceptable end state.**
4. If a minimum-population precondition is added, an under-populated run **skips with a message naming
   the shortfall**, and a green run proves quartiles had members.
5. The 2x threshold is unchanged, or its change is justified separately and recorded in the parity
   ledger / `intentional_divergences.md` as appropriate.

## Related Tickets

- `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` — **done**; created this guard
- `TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL` — open, owns the coefficient itself
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — done (#328); enumerated this as pre-existing
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — done (#333); halted its Test gate on this
  failure and confirmed it at a clean pre-#328 commit
- `TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION` — P1; the "builds its own spec,
  never constructs a resolver" detail is the same measurement-path concern

## Related Docs

- `docs/mechanics/02_combat_laws.md` — bravery's role in engagement
- `docs/mechanics/01_entity_anatomy.md` — attribute distribution at spawn
- `docs/testing/test_taxonomy.md` — where an integration-tier population guard belongs
- `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` — combat/cognition is **Lane A**

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/` — the
  pre-existing-failure enumeration

## Related Code Areas

- `tests/integration/scenarios/test_entity_differentiation.py` — the guard, and the spec it builds itself
- `src/entities/` — attribute spread at spawn
- `src/domains/combat_engagement/` — the engagement rate being compared

## Assumptions / Open Questions

- **UQ-1:** which world/spec does the test sample, and what was its entity count when the guard was
  written? Without the original number there is no way to say whether the population shrank or never
  sufficed. Check `TCK-20260810`'s artifacts for the figure it was calibrated against.
- **UQ-2:** has this ever passed in CI? If it was red from the day it landed, that reframes it from
  regression to a guard that never held — a different and more embarrassing finding worth stating.
- The three confirmations above were reported by the named sessions; the `246ee09f7` and `1c59e01f4`
  measurements were **not** re-taken by this ticket's author. Re-derive before relying on them.

## Implementation Notes

_(to be filled during implementation)_

## Test Summary

_(to be filled during implementation)_

## Files Changed

_(to be filled during implementation)_

## Completion Summary

_(to be filled during implementation)_
