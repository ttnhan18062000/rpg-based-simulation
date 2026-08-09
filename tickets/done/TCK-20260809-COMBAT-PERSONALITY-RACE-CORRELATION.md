---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION

## Title
Real per-entity personality (bravery etc.) has zero race/faction correlation despite genuine RNG
variance — a wolf and a citizen draw from the identical distribution; foundation fix for diverse
combat outcomes requested by the user after `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Direct follow-up requested by the user after this session's combat-legality and flee-personality
tickets: "make sure after simulation, we have a diverse combat result and outcome." Investigation
confirmed the foundation blocking this: `bravery` (and other personality traits) are real,
per-entity RNG values (`src/worldbuilding/compiler.py`) — genuine individual variance exists and
is already calibrated to matter for strategic route selection (`STRAT-226`, this session's own
Finding 2 in the sibling flee-vs-fight ticket) — but are entirely uncorrelated with race, faction,
or archetype. A wolf archetype and a town citizen draw bravery from the exact same distribution.

Also found, while tracing the real entity-construction architecture: a **second, separate** entity
spawner (`WorldEntitySpawner`/`ArchetypeEntityFactory`, `src/worldassembly/`) never sets
personality at all — the same class of bug already fixed once for the main compiler path
(`TCK-20260619-P0-ENTITY-INIT`), but for a code path that path's own fix never covered. Real live
corpus impact not yet confirmed (only 1 known caller, `src/scenarios/catalog_state_builder.py`) —
disclosed and filed as its own separate follow-up rather than fixed here.

## Scope
1. **Investigate**: confirm real personality-seeding architecture (how many distinct entity
   construction paths exist, which are live in real corpus worlds), confirm zero race correlation
   with real corpus data, identify a real, minimal fix approach.
2. **Plan/Decision**: `AskUserQuestion` — resolved: derive bravery bias from the real, existing
   `alignment_bucket` faction content field via a small code lookup table, not a new content
   schema, not a reinterpretation of `cognition_profile`'s qualitative fields.
3. **Implement**: wire the chosen approach into the confirmed-live entity-construction path.

## Out of Scope
- `WorldEntitySpawner`'s own zero-personality bug — real, confirmed, filed separately
  (requires threading a world seed through 3 function signatures across 2 files; live blast
  radius not yet confirmed).
- `ActionStyle` wiring (the mechanism that would let this personality variance actually change
  escape/fight outcomes at the tactical level) — the direct next ticket,
  `TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`.
- Personality traits other than `bravery` (greed/sociability/industry) — the user's own request
  was specifically about combat outcome diversity; those traits are out of this ticket's scope.

## Acceptance Criteria
- [x] investigation.md confirms real personality-seeding architecture with real data (not assumed)
- [x] Real design decision resolved with the user (`AskUserQuestion`) before implementation
- [x] Fix re-verified against real corpus data (dungeon_crawl, urban_political) showing real,
      measurable, ordered per-faction bravery skew while individual variance is preserved
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (DONE — this session, the ticket whose
  own Finding 4 first confirmed the zero-race-correlation gap)
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (next — consumes this ticket's own bravery-bias output)
- TCK-20260619-P0-ENTITY-INIT (DONE — the earlier, different all-zero-personality bug this
  ticket's own Finding 2 found a second, unfixed instance of)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (updated — cross-referenced from the existing
  bravery/Risk Multiplier section)
- `docs/audits/D05_entity_differentiation.md` (prior personality-differentiation audit history)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, the real, live personality-seeding
  path fixed here)
- `src/worldassembly/entity_spawner.py`, `src/entities/archetype_factory.py` (the separate,
  confirmed-broken path, disclosed but not fixed here)
- `src/content_semantics/faction.py` (`FactionSemanticsService.get_alignment_bucket`, the real
  content signal the fix derives from)

## Assumptions / Open Questions
- Whether `WorldEntitySpawner`'s path is live in any currently-scored real corpus world — not
  confirmed either way; disclosed honestly as unconfirmed rather than assumed safe to ignore.

## Implementation Notes
Added `get_bravery_bias(faction_str: str) -> float` (`src/worldbuilding/compiler.py`): looks up
the entity's real faction `alignment_bucket` via `FactionSemanticsService.get_alignment_bucket()`
and maps it through a small table (`wild` +0.35, `invader` +0.25, `rival` +0.15, `defender`
+0.05, `neutral` +0.0), defaulting to `0.0` on any resolution failure. Wired into the existing
personality-seeding call site: `bravery = min(1.0, max(0.0, rng_draw + bias))` — additive and
clamped, preserving per-entity RNG variance within each faction.

Real re-verification (live compiled worlds, not assumed): `dungeon_crawl`'s `wild_beast_pack`
population now averages bravery ≈0.89 vs. `goblin_warband`/`bandit_company`/`undead_remnants`
(invader) ≈0.73-0.83; `urban_political`'s `bandit_company` (invader) ≈0.85 > `hero_guild`/
`town_council` (defender) ≈0.61-0.72 > `merchant_league` (neutral) ≈0.49 — a real, ordered,
measurable population skew matching the intended `alignment_bucket` ranking, with individual
entity variance still present within each faction.

**Real, separate finding, disclosed not fixed**: `WorldEntitySpawner`'s own two branches
(`_spawn_archetype_native`, `_spawn_legacy_guard`, `src/worldassembly/entity_spawner.py`) never
set personality at all — confirmed via direct source read. Filed as its own follow-up ticket
rather than force-fit here (requires threading a world seed through 3 function signatures across
2 files, and its live corpus blast radius isn't yet confirmed — only 1 known caller found).

**Real, separate pre-existing test-infrastructure finding, disclosed not fixed**: running
`tests/unit/worldgeneration/` together with `tests/unit/strategic/test_opportunities.py` in the
same pytest process produces 13 failures in the latter — confirmed via `git stash` bisection to
reproduce identically with this ticket's own changes fully reverted. A pre-existing test-isolation
gap, unrelated to this ticket's own scope.

## Test Summary
New tests in `tests/unit/worldbuilding/test_world_compiler.py`:
`test_get_bravery_bias_by_real_alignment_bucket` (real content faction IDs across all 5 real
`alignment_bucket` values plus an unrecognized-faction no-crash case) and
`test_compiler_faction_bravery_bias_produces_real_population_skew` (30 predator + 30 merchant
synthetic-world compile, asserts >0.2 real average bravery separation with individual variance
preserved). Scoped pytest (`tests/unit/worldbuilding/`, `tests/unit/worldassembly/`,
`tests/unit/combat/`, `tests/unit/strategic/`, `tests/unit/entities/`, `tests/unit/content/`,
`tests/unit/core/`): 998 passed, 1 pre-existing unrelated failure (missing world data directory,
confirmed via bisection to predate this ticket).

## Files Changed
- `src/worldbuilding/compiler.py` — added `get_bravery_bias()` and wired it into personality
  seeding.
- `tests/unit/worldbuilding/test_world_compiler.py` — 2 new tests.
- `docs/mechanics/04_strategic_cognition.md` — cross-referenced the new mechanism.

## Completion Summary
Closed the confirmed-live half of the "personality has zero race correlation" gap the user's own
combat-diversity request depends on: bravery now measurably differs by faction in real, compiled
corpus worlds (verified with live data, not assumed), using the user's own explicitly chosen
approach (a code lookup table derived from real, existing content rather than new schema
authoring). A second, separate entity-construction path with the same class of bug, and a
pre-existing, unrelated test-isolation issue found along the way, are both disclosed and filed/
noted rather than silently absorbed into this ticket's own scope.
