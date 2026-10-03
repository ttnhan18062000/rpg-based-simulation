---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION
artifact_type: investigation
tags: [simulation-quality, world, corpus, calibration]
---

# Investigation — TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION

## Docs Requiring Update

- `docs/simulation_quality/corpus_tier_taxonomy.md`: register the new world (done during Implement, ahead of this write-up)
- `docs/simulation_quality/current_state.md`: findings summary (Implement phase)

## Authoring tooling: two real code paths found, only one actually works

1. **`ProceduralCompositionGenerator`** (`src/worldbuilding/cli.py generate` → `src/worldgeneration/generator.py`):
   selects pre-authored content modules (`data/content/world_modules/*.yaml`, 20 available) and
   assembles a `WorldCompositionSpec` (`module_refs` list). This is the real mechanism behind
   `generated_frontier_3_42` (confirmed: its own composition file uses this exact `module_refs`
   shape). **Its own `--population-scale` CLI flag is a dead parameter** — grep confirms
   `population_scale` is never read anywhere in this class's own module-selection logic; only
   `src/worldgeneration/schema.py`'s dataclass field exists, unconsumed here.
2. **`WorldProceduralGenerator`** (`src/worldgeneration/generator.py`, a different class in the
   same file): builds a complete synthetic `WorldSpec` directly, with a REAL, uncapped population
   scale (`pop_count_citizen = max(5, int(15 * intent.population_scale))`) — the only code path in
   this codebase with genuinely unbounded entity-count scaling. **Confirmed dead code**: zero
   invocation sites anywhere in `src/`/`tools/` outside its own definition — not wired to any CLI
   command. **Confirmed broken, not just unused**: direct instantiation and a real `.generate()`
   call (population_scale=35) raises `InvalidWorldSpecError` — the function's own generated
   `PopulationSpec` entries reference faction IDs (`town_council`, `goblin_warband`) it never
   defines in its own generated `factions` dict. A real, pre-existing bug, not something this
   ticket introduced. Fixing it is a `src/` engine-code change — explicitly out of this ticket's
   own scope (per its own Out of Scope: no engine-level content-generation fixes, only "author and
   calibrate," and even if in scope, debugging unowned generator logic is a different-sized task
   than this ticket's own budget).

## Real, measured scale ceiling via the working path

Combining `ProceduralCompositionGenerator`'s module system by hand (the CLI's own automatic
settlement-style module selection repeatedly picked colliding module combinations — 2 real
collisions hit: `healer_hut_0` building-ID collision between `frontier_village_core` and
`survivor_camp_shelter`/`settled_quarter`; `haunted_battlefield` region-ID collision between
`undead_battlefield` and `ruins_mystery_quest`), the maximum non-colliding combination found is 12
of the 20 available modules, producing **68 entities, 13 regions, 18 resource nodes, 7 buildings,
27 quests, 11 distinct populated factions** — confirmed via real `WorldCompiler.compile()`, not
estimated.

**500-1000 entities is not achievable via any currently-working tool in this codebase.** The only
code path capable of that scale (`WorldProceduralGenerator`) is broken. Reaching 500-1000 would
require either fixing that generator's own faction-reference bug (a real `src/` engine fix, out of
scope) or authoring many new bulk-population content modules (a much larger content-authoring
investment than "author and calibrate one world"). Disclosed honestly rather than forced — the
ticket's own Assumptions section explicitly anticipated this outcome ("not assumed; Investigate
should measure before committing to a specific scale target").

## Real findings at the achieved scale (68 entities, ~1.1x the prior corpus max of 62)

- **Watchdog/throttle activity**: 9 `Tick X exceeded budget` warnings in a single 200-tick run,
  first trip at tick 100 — notably earlier than F6's own documented ~tick 300-320 onset
  (`docs/audits/D06_longrun_health.md`), consistent with this session's own earlier finding
  (`TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION`) that this environment's
  watchdog fires earlier than documented — this run adds one more data point, at a genuinely
  larger entity count than that investigation's own worlds, though a single run is not itself
  proof of an entity-count correlation (would need a controlled multi-scale sweep to establish
  causation, out of this ticket's own budget — flagged as a real open question, not concluded).
- **Pillar signal without hand-authored content**: a first compile with `faction_tension_overrides: {}`
  produced 8 of 10 pillars at zero events (only WORLD and a single PROGRESSION event fired) —
  scale alone (more entities/regions) does not automatically produce richer SimQ signal without
  the same kind of hand-authored FACTION/INFORMATION overlay other archetype worlds already carry.
  Added `faction_tension_overrides` for 6 factions (mirroring `frontier_marches`'s own precedent
  format) — FACTION jumped to grade S, 65 events. The remaining 7 zero-signal pillars
  (AGENCY/COGNITION/COMBAT/ECONOMY/INFORMATION/NARRATIVE/SOCIAL) match the corpus's own
  established "structural, feature-gate blocked" pattern (no flags enabled, no
  quest-completion/combat content seeded) — not a defect, consistent with e.g.
  `wilderness_survival`'s own documented FACTION-only signal.
