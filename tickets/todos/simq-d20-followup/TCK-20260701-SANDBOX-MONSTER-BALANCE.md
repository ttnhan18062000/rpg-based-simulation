---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: open
date: 2026-07-01
tags: [world, combat, balance, sandbox_world, simq]
---

# TCK-20260701-SANDBOX-MONSTER-BALANCE

## Title
sandbox_world monsters spawn with no stat differentiation from citizens — extinct by tick 8

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
D20 audit (Actionable Next Steps, P2 row) flagged that SimQ's `early_extinction` COMBAT
penalty (-10) fires at tick 8 in `sandbox_world` because 5 monster-type entities (16-20) die
within the first 10 ticks, asking whether this is intentional world design or a spawn/balance
bug.

Investigation confirms this is a **world-data balance bug, not a SimQ scorer defect**:
- `CombatScorer.early_extinction` (`src/simulation_quality/scorers/combat.py` ~L82-90) fires
  once when any entity dies at `tick < early_extinction_before_tick` (10, from
  `config/simulation_quality/detection_params.yaml:16`). The threshold and single-fire gate
  are reasonable and match the audit's stated intent — this scorer needs no change.
- `data/worlds/sandbox_world/world.yaml` spawns 5 monsters in the `woods` region via
  region_random distribution, alongside 15 citizens + 3 heroes in `town_center`.
- All entities — monsters included — resolve to the same default stat block (HP=100, ATK=10,
  DEF=0) from `src/content_semantics/defaults.py`; there is no monster-specific stat profile
  overriding these defaults for sandbox_world's monster population.
- With no defensive differentiation and 18 potential hostile entities in reach, the 5
  monsters are killed almost immediately — this reads as a missing stat-authoring step for
  sandbox_world's monster population, not deliberate design. It's consistent with
  `docs/audits/D04_balance_tuning.md` §2 ("world content parameters are the primary balance
  lever, not per-combat constants... the authoring layer is uncalibrated").

## Scope
1. Confirm current monster stat resolution path for `sandbox_world`'s monster population
   (which catalog entry / archetype resolver produces entities 16-20's stats) —
   `src/content/resolver.py` `EntityArchetypeResolver` is the likely site.
2. Decide the fix: either (a) give sandbox_world monsters a distinct stat profile (higher
   HP/ATK/DEF appropriate to a "monster" role) via the catalog, or (b) adjust spawn placement/
   distance so monsters aren't immediately adjacent to 18 hostile entities at tick 0-8.
   Prefer (a) if a monster archetype concept already exists elsewhere in the catalog for
   other worlds (e.g. dungeon_crawl) — reuse rather than invent a new one.
3. Re-run the D20 audit's 200-tick seed 42/137 sandbox_world scenario after the fix; confirm
   final state hash changes (expected, since this changes tick-8 behavior) and that
   `early_extinction` no longer fires from an immediate wipe (some early combat death is fine;
   a full 5-entity monster wipe by tick 8 should not recur).
4. Update `docs/audits/D20_simq_integration.md` P2 row with the resolution.

## Out of Scope
- Changing the `early_extinction` scorer threshold or logic (confirmed correct)
- Rebalancing combat for any world other than sandbox_world
- Full combat formula changes (`docs/mechanics/02_combat_laws.md` — out of scope; this is
  content-layer, not engine-layer)

## Acceptance Criteria
- [ ] Root cause confirmed: which resolver/catalog path assigns sandbox_world monster stats
- [ ] Monsters no longer die as an entire cohort within the first 10 ticks in a fresh 200-tick
      seed 42 run (some attrition is acceptable; total wipe is not)
- [ ] Final state hash changes are expected and documented (this is an intentional behavior
      change, not a determinism break — same seed must still be reproducible)
- [ ] `docs/guidelines/v2_intentional_divergences.md` updated if this counts as a divergence
      from any documented legacy sandbox_world behavior
- [ ] D20 audit P2 row updated to resolved
- [ ] No regression in existing sandbox_world / world-compile tests

## Related Tickets
- TCK-20260628-SIMQ-EPIC — parent epic that surfaced this via calibration (done)
- D04 audit findings (docs/audits/D04_balance_tuning.md §2, §6.5) — related combat attrition
  observations across worlds; no ticket ID assigned there, doc-only
- TCK-20260627-P1I-WORLD-BALANCE-FIX — prior precedent for dungeon_crawl/wilderness_survival
  entity-count balancing; same category of fix, different world

## Related Docs
- `docs/audits/D20_simq_integration.md` — Actionable Next Steps, P2 row; "Notable worst
  events — Seed 42" table (entities 16-20 killed at tick 8)
- `docs/audits/D04_balance_tuning.md` §2 (Combat Balance), §6.5 (Combat Attrition Finding)
- `docs/mechanics/02_combat_laws.md` — combat resolution reference (context only)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260627-P1I-WORLD-BALANCE-FIX/` — prior world-balance investigation
  pattern to follow

## Related Code Areas
- `data/worlds/sandbox_world/world.yaml` — monster population spawn config
- `src/content/resolver.py` — `EntityArchetypeResolver` (stat resolution)
- `src/content_semantics/defaults.py` — default stat fallback (HP=100/ATK=10/DEF=0)
- `src/simulation_quality/scorers/combat.py` ~L82-90 — `early_extinction` (reference only,
  confirmed correct, not to be changed)

## Assumptions / Open Questions
- Assumes monster/citizen role should have distinct stats somewhere in the catalog system
  already (used by other worlds); needs confirmation at implementation time whether
  sandbox_world simply omits a `monster` archetype reference that exists elsewhere, or
  whether no such archetype exists anywhere yet.
- If no monster archetype exists in the catalog at all, this ticket's scope may need to
  expand to authoring one — flag back to standard/epic tier if so during implementation.

## Implementation Notes
(to be filled at implementation)

## Test Summary
(to be filled at implementation)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
