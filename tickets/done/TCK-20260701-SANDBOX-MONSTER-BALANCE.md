---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: done
date: 2026-07-01
tags: [world, combat, balance, sandbox_world, simq]
---

# TCK-20260701-SANDBOX-MONSTER-BALANCE

## Title
sandbox_world monsters spawn with no stat differentiation from citizens — extinct by tick 8

## Status
DONE

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

## Scope — REVISED 2026-07-01 (option (a) proved unworkable, see Implementation Notes)

Option (a) — stat differentiation via `role:` reassignment — was implemented, empirically
tested, and reverted: `sandbox_world` is `schema_version: worldtemplate.v1`, whose compile
path (`WorldCompiler.compile()`, `src/worldbuilding/compiler.py:264-283`) hardcodes flat
stats (`hp=100/atk=10/def=0`) for every entity regardless of `role` whenever `context=None`
— which the CLI always passes for this schema. No registered role changes this. All four
candidate roles also broke `EntityRole.MONSTER` bucketing as a side effect. See
Implementation Notes for full evidence (already recorded, do not re-investigate this path).

**New scope: option (b) — spawn placement/distance.**
1. Investigate how `sandbox_world/world.yaml`'s `region_random` distribution places the 5
   monsters within the `woods` region relative to `town_center` (where the 15 citizens + 3
   heroes spawn) — find the actual spawn-position resolution code for `worldtemplate.v1`
   worlds (likely in `src/worldbuilding/compiler.py` or `src/systems/world_systems/
   generator.py`).
2. Investigate what makes an entity "in reach" of combat at tick 0-8 — movement speed per
   tick, aggro/engagement radius, whether `woods` and `town_center` are adjacent regions or
   separated by other regions/distance in the topology. Determine why 18 hostile entities
   reach the 5 monsters by tick 8 specifically.
3. Identify a content-only lever to increase separation: options may include increasing
   region distance/topology separation between `woods` and `town_center`, changing the
   monster spawn distribution pattern (e.g. spawn further from the region's town-facing
   edge), or reducing citizen/hero wander radius early-game — prefer whichever is a minimal,
   existing-mechanism change (no new engine code) consistent with the Out of Scope section.
4. Re-run the D20 audit's 200-tick seed 42/137 sandbox_world scenario after the fix; confirm
   final state hash changes (expected) and that `early_extinction` no longer fires from an
   immediate full-cohort wipe (some early combat death is fine; a total 5-entity wipe by
   tick 8 should not recur).
5. Update `docs/audits/D20_simq_integration.md` P2 row with the resolution.

If investigation finds that NO content-only spawn/distance lever exists either (e.g.
region topology has no distance concept for worldtemplate.v1, or movement mechanics make any
achievable separation insufficient), stop and report back rather than reaching for an
engine-layer change — that would be a scope expansion requiring a fresh decision, not an
implementation detail to route around silently.

## Scope — REVISED AGAIN 2026-07-01 (attempt 3, both prerequisite fixes now landed)

Options (a) and (b) above are historical — both falsified, see Implementation Notes. The
`TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC` (done) delivered the two actual prerequisites:
`TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` (sandbox_world now `worldcomposition.v1`, real
catalog stats) and `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (`RegionState.hazard_kind` +
`FactionDefinition.hazard_immunities` mechanism; `wolf_den`/`near_forest` already authored
`hazard_kind: NATURAL_TERRAIN`, `wild_beast_pack` faction already authored
`hazard_immunities: [NATURAL_TERRAIN]` — both landed as part of that ticket's content changes
to `data/content/world_modules/wolf_den_near_forest.yaml` and
`data/content/social/factions.yaml`).

**What's actually left:** `sandbox_world`'s compiled artifacts
(`data/worlds/sandbox_world/resolved/world.resolved.yaml`,
`world_compile_report.json`) were generated by `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`
*before* the hazard mechanism's content changes landed — they are stale and don't reflect
`hazard_kind`/`hazard_immunities`. This attempt is a recompile + empirical verification, not
a design decision:
1. Recompile `sandbox_world` (re-run `WorldAssemblyResolver` + `WorldCompiler` against current
   module content) to pick up `hazard_kind`/`hazard_immunities`.
2. Confirm via direct state inspection that `wolf_pack_small` entities' faction
   (`wild_beast_pack`) resolves `hazard_immunities` including `NATURAL_TERRAIN`, and that
   `wolf_den`/`near_forest` regions resolve `hazard_kind: NATURAL_TERRAIN`.
3. Empirically re-run the D20 200-tick scenario, seed 42 and 137. Confirm monsters no longer
   die from environmental hazard drain in their own den — some combat attrition from other
   causes is still acceptable per the original AC, but the specific `hazard_drain_applied`
   self-kill mechanism (15 dmg/tick from `woods`/`wolf_den`'s own hazard_level) should no
   longer apply to `wild_beast_pack`-faction entities.
4. If monsters STILL die (from combat, or any other cause) — that is fine per the original
   acceptance criteria ("some early combat death is fine; a total wipe is not"); the fix here
   specifically targets the self-inflicted-hazard death mechanism, not general survivability.
   Only escalate/report back if the hazard-immunity mechanism itself doesn't appear to be
   taking effect (e.g. compiled `RegionState.hazard_kind` doesn't match content, or
   `hazard_drain_applied` events still fire against `wild_beast_pack` entities in
   `NATURAL_TERRAIN` regions) — that would indicate a real defect in the sibling ticket's
   implementation, not something to route around here.
5. Regenerate the 4 `sandbox_world_*` calibration anchors again (they were already regenerated
   once by the migration ticket using pre-hazard-fix content; they need a second regeneration
   now that the hazard content has also changed).
6. Update `docs/audits/D20_simq_integration.md` P2 row to fully resolved, with the actual
   final outcome (tick-of-death distribution, if any deaths still occur and why).
7. Close this ticket — this closes out the whole investigation chain that started with the
   D20 audit's P2 finding.

## Out of Scope
- Changing the `early_extinction` scorer threshold or logic (confirmed correct)
- Rebalancing combat for any world other than sandbox_world
- Full combat formula changes (`docs/mechanics/02_combat_laws.md` — out of scope; this is
  content-layer, not engine-layer)

## Acceptance Criteria
- [x] Root cause confirmed: which resolver/catalog path assigns sandbox_world monster stats
- [x] Monsters no longer die as an entire cohort within the first 10 ticks in a fresh 200-tick
      seed 42 run (some attrition is acceptable; total wipe is not) — exceeded: 0/5 dead across
      a full 200 ticks, both seed 42 and seed 137
- [x] Final state hash changes are expected and documented (this is an intentional behavior
      change, not a determinism break — same seed must still be reproducible) — seed 42
      `836b45e8913b46862240c6ba80f177f6`, seed 137 `7e8ae05dbeffccb8edd65fd9754787aa`, both
      reproducible on repeat compiles
- [x] `docs/guidelines/v2_intentional_divergences.md` (actual file: `docs/guidelines/
      intentional_divergences.md`) updated if this counts as a divergence from any documented
      legacy sandbox_world behavior — the divergence itself was already documented by entry
      2.20 (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`); this ticket updated its staleness note
      to reflect the recompile
- [x] D20 audit P2 row updated to resolved
- [x] No regression in existing sandbox_world / world-compile tests — 184/184 passed across
      `tests/integration/worldassembly/`, `tests/unit/worldbuilding/`, `tests/unit/
      worldassembly/`; 9/9 `test_grade_regression.py` passed

## Related Tickets
- **TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC — blocks this ticket (see its SEQUENCE.md).**
  Both failed fix attempts here led to this epic: attempt 1 (stat differentiation) surfaced
  that `worldtemplate.v1` never resolves catalog stats; attempt 2 (spawn placement) surfaced
  that the actual killer is `woods.hazard_level` environmental drain, independent of stats or
  distance. This ticket should be re-verified (not assumed fixed) once
  `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` and `TCK-20260701-HAZARD-NATIVE-IMMUNITY` both land.
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
- SUPERSEDED: the original assumption (monster/citizen stats differ via a catalog role
  lookup) was disproven — `worldtemplate.v1`'s compile path never consults the catalog for
  stats. See Implementation Notes.
- New assumption: `worldtemplate.v1` world topology/spawn distribution has *some* content-
  level distance or placement control reachable without engine changes. This needs
  confirmation during re-investigation — if false, escalate rather than force a fix.

## Implementation Notes

**BLOCKED — plan.md's approved fix mechanism does not work for this world's schema.**
Full trace and evidence recorded in
`staging_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/plan.md` ("Deviations" section).

Summary: `sandbox_world/world.yaml` is `schema_version: worldtemplate.v1`. The CLI compile
path (`src/worldbuilding/cli.py`, `"worldtemplate" in schema_version` branch) always calls
`WorldCompiler.compile(spec, seed=seed, context=None)`. `WorldCompiler.compile()`
(`src/worldbuilding/compiler.py:264-283`) hardcodes combat stats
(`hp=100, atk=10, def=0`) for every entity when `context is None`, and only reads
`context.entities[...]` (catalog-resolved stats) when a `CompileContext` is supplied — which
never happens for `worldtemplate.v1` worlds. `data/content/social/roles.yaml`'s
`default_stats_profile` field (the mechanism investigation.md traced through
`CompileProfileResolver`/`RoleSemanticsService`) is only consulted by
`WorldAssemblyResolver.resolve()`, used for `worldcomposition.v1` module worlds
(e.g. `dungeon_crawl`) and the procedural generator — not sandbox_world's compile path.

Empirically verified (via `WorldTemplateExpander.expand()` + `WorldCompiler.compile()`,
matching the CLI's exact calls): changing `role:` to `predator_hunter`, `alpha`, `leader`, or
`brute` (the plan's full fallback sequence) all resolve to the identical flat default
`(100, 10, 0)` — zero stat differentiation in every case. Additionally, all four regress
`EntityRole` bucketing from `MONSTER` to `CITIZEN` (via `get_role_enum()`'s crude
`"MONSTER" in role_str.upper()` substring heuristic, which only the literal string
`"monster"` satisfies among catalog role IDs), which would silently break
`EntityRole.MONSTER`-keyed logic in `src/engine/legality.py`, `src/engine/combat_rewards.py`,
`src/engine/occupancy_snapshot.py`, `src/world/camp.py`, `src/world/spawn.py` — a regression
independent of, and in addition to, the fix not working.

The `role:` edit was applied, empirically tested, and reverted
(`data/worlds/sandbox_world/world.yaml` and `world_compile_report.json` are unchanged from
their pre-ticket state). The new regression test
(`tests/unit/worldbuilding/test_sandbox_world_monster_stats.py`) was written, used to prove
the negative result, then deleted — it would otherwise assert a property this fix cannot
deliver. No `src/` files were modified.

Ticket's own Scope section names an untried, still-viable, content-only alternative: option
(b), "adjust spawn placement/distance so monsters aren't immediately adjacent to 18 hostile
entities at tick 0-8." This requires new investigation (engagement radius, movement speed,
region-distance dynamics) not covered by the current investigation.md/plan.md, which focused
exclusively on option (a). Re-scoping to option (b) — or accepting an engine-layer change to
`WorldCompiler.compile()`/`WorldTemplateExpander` to make `worldtemplate.v1` worlds
catalog-aware (a change affecting every template-schema world, well beyond this ticket's
single-world scope) — is a decision for the next planning pass.

---

### ATTEMPT 2 — option (b), spawn placement/distance — 2026-07-01 — ALSO BLOCKED

Architecture review approved option (b) (spawn placement/distance) as the second approach.
`staging_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/plan.md` (current version) laid out
an 8-step plan: widen the `woods` region's `grid_bounds` from `[50,50,110,110]` to
`[90,90,125,125]` in `data/worlds/sandbox_world/world.yaml`, increasing minimum town_center↔woods
separation from ~14.14 tiles to ~70.7 tiles (well above the 10.0-unit perception radius), on
the theory that the 5 monsters were being reached and killed by the 18 town-faction entities
via proximity/pursuit before tick 10.

**Steps executed:**
1. Edited `woods` `grid_bounds` to `[90, 90, 125, 125]` in `data/worlds/sandbox_world/world.yaml`.
2. Recompiled via `python3 -m src.worldbuilding.cli compile sandbox_world --seed 42`: clean
   compile, no containment errors, `entity_count=23`, new `state_hash=c076a8393b5fd3424407f7804510f1fa`
   (vs. pre-fix `2f94f10135bc2aff1a68fc2c54b2c415` — recorded in `world_compile_report.json`
   before revert).
3. Added `tests/unit/worldbuilding/test_sandbox_world_region_separation.py` (geometry-only,
   `>= 40` tile separation assertion) — passed against the new bounds. Later deleted (see
   below).
4. **Empirical re-run — this is where the fix was falsified.** Wrote a scratchpad script
   replicating the CLI's exact compile path (`WorldTemplateSpec.model_validate` →
   `WorldTemplateExpander.expand(seed)` → `WorldCompiler.compile(spec, seed)`) feeding the
   resulting `AuthoritativeState` into a real `Kernel` for 200 ticks (this was necessary
   because `tools/calibrate_simq.py`'s `_load_world_state()` only loads
   `data/worlds/{name}/resolved/world.resolved.yaml`, which does not exist for `worldtemplate.v1`
   worlds like `sandbox_world` — confirmed empirically: running
   `calibrate_simq.py --name sandbox_world` silently falls back to the generic 10-entity
   hero+goblins scenario, not real sandbox_world content; this also means the prior
   `TCK-20260630-SIMQ-RECALIBRATE` ticket's "sandbox_world (10 entities)" completion note was
   actually the generic fallback too, not real sandbox_world — noted here as a related but
   out-of-scope tooling gap, not fixed by this ticket).
   - Seed 42 (new bounds): all 5 monsters (ids 16-20) died at **tick 7**, 0/5 alive at tick 10.
     **Full cohort wipe still occurred.**
   - Seed 137 (new bounds): identical outcome — all 5 died at tick 7.
   - Cross-check: re-ran the identical script with the **original** `[50,50,110,110]` bounds
     (in-memory only, no file changes) — **same result, same tick (7), same entities.**
     Region separation had **zero measurable effect** on the outcome.
   - Root cause found via `simulation_events.jsonl` inspection of the run: each monster
     receives a `hazard_drain_applied` event of **15 damage every tick** starting at tick 1
     (`near_death_survival` fires at tick 6 with `hp=10, max_hp=105`; `combat_kill` fires at
     tick 8 for all 5). 7 ticks × 15 dmg = 105 = exactly `max_hp`. **The monsters are being
     killed by the `woods` region's own `hazard_level: 1.5` environmental drain — not by
     combat with town-faction entities reaching them.** This is completely independent of
     distance from `town_center`; the monsters die standing in their own spawn region.
   - This means both the original ticket's diagnosis ("18 hostile entities reach the 5
     monsters") and option (b)'s theory (spawn-placement/distance as the lever) were
     **incorrect**. The `early_extinction` trigger is a self-inflicted environmental-hazard
     death, not a proximity/combat-reach problem. No amount of region separation from
     `town_center` can fix this, because `town_center` was never the cause.
5. Per the workflow's explicit instruction ("if the 200-tick re-run STILL shows a full
   5-entity wipe by tick 10 even with the widened separation, treat this as a test failure:
   STOP, do not finalize"), implementation was halted here. Steps 5-8 (grade anchors, D20 doc
   update, divergence-log determination, full regression pass) were **not executed** —
   finalizing on a fix that empirically does not work would misrepresent the ticket as
   resolved.
6. **Reverted**, matching the option (a) precedent: `data/worlds/sandbox_world/world.yaml`
   and `world_compile_report.json` restored to their original committed state (`git checkout`
   — confirmed clean diff afterward). `tests/unit/worldbuilding/test_sandbox_world_region_separation.py`
   deleted (it asserted a geometric precondition for a fix that does not address the actual
   root cause; keeping it would misleadingly suggest the separation threshold matters).
   Scratchpad run directories under `data/runs/` from this session's verification runs were
   removed. No `src/` files were touched at any point.

**Corrected root cause (for the next planning pass):** `data/worlds/sandbox_world/world.yaml`'s
`woods` region has `hazard_level: 1.5`. Whatever world-evolution/hazard system applies
`hazard_drain_applied` (see `docs/mechanics/05_world_evolution.md`, region hazard mechanics)
drains 15 HP/tick from entities standing in a hazardous region with no apparent mitigation for
the monster population itself (irony: the monster faction dies to environmental hazard in its
own designated habitat). A viable third option would be **lowering `woods.hazard_level`** (or
giving monsters hazard resistance/immunity if such a mechanism exists) — this is untried and
would need its own investigation into the hazard-drain formula and whether other worlds rely on
`woods`-style hazard_level values for balance elsewhere before changing it. This is a decision
for the next planning pass; not attempted in this session per the workflow's stop-on-failure
instruction.

## Test Summary
**Attempt 1** (option a): No tests were kept. A regression test
(`tests/unit/worldbuilding/test_sandbox_world_monster_stats.py`) was written and run to
empirically disprove the plan's fix mechanism, then deleted.

**Attempt 2** (option b): `tests/unit/worldbuilding/test_sandbox_world_region_separation.py`
was written, ran green (3/3 passed) against the widened bounds — but this only validated the
geometric precondition, not the actual behavioral outcome. The empirical 200-tick kernel
re-run (both seed 42 and seed 137) showed the full 5-monster cohort still dying by tick 8,
proving the fix ineffective. Per workflow instruction, this counts as an empirical test
failure. The test file was deleted along with the reverted world-data change since it no
longer validates anything relevant to the actual bug. No `pytest` regression suite run was
needed since no net change was left in place to regress.

**Attempt 3** (recompile + verify): `tests/integration/worldassembly/test_real_content_world_
modules.py` 6/6 passed (the suite whose 5/5 ERROR originally proved the resolver-gap blocker).
Empirical 200-tick Kernel re-run (not a pytest test — direct engine run against the real
compiled state), seed 42 and seed 137: 0/5 monster deaths, 0 `hazard_drain_applied` events
against `wild_beast_pack` entities, both seeds. `tools/calibrate_simq.py` re-run for all 4
`sandbox_world_*` anchors; `tests/simulation_quality/fixtures/grade_anchors.json` updated to
match. `tests/simulation_quality/test_grade_regression.py -k sandbox_world`: 4/4 passed; full
file: 9/9 passed. Full regression pass: `tests/integration/worldassembly/` (44) +
`tests/unit/worldbuilding/` (92) + `tests/unit/worldassembly/` (48) = 184/184 passed, no
regressions. Sanity re-run of pre-existing hazard-immunity unit coverage
(`test_regional_consequences.py`, `test_semantics.py::test_get_hazard_immunities`,
`test_catalog.py` hazard-immunity tests): 11/11 passed, unmodified.

## Files Changed
**Attempts 1-2**: None (net) — see notes above, both edited-then-reverted.

**Attempt 3**:
- `data/worlds/sandbox_world/resolved/world.resolved.yaml`,
  `data/worlds/sandbox_world/resolved/{compile_context,provenance_manifest,assembly_report,
  validation_report}.json` — recompiled (resolve + compile), reflecting `hazard_kind`/
  `hazard_immunities`
- `data/worlds/sandbox_world/world_compile_report.json` — recompiled, seed 42, state hash
  `836b45e8913b46862240c6ba80f177f6`
- `data/calibration/sandbox_world_seed42_200t/quality_report.json`,
  `data/calibration/sandbox_world_seed137_200t/quality_report.json`,
  `data/calibration/sandbox_world_seed999_200t/quality_report.json`,
  `data/calibration/sandbox_world_seed42_1000t/quality_report.json` (and each directory's
  `quality_scores.jsonl`) — regenerated calibration anchors
- `tests/simulation_quality/fixtures/grade_anchors.json` — updated `sandbox_world_*` grades to
  match the regenerated anchors
- `docs/audits/D20_simq_integration.md` — P2 `early_extinction` row updated to resolved
- `docs/guidelines/intentional_divergences.md` — entry 2.20 staleness note updated (one line)
- `tickets/inprogress/TCK-20260701-SANDBOX-MONSTER-BALANCE.md` → moved to `tickets/done/`
- No `src/` files touched.

## Completion Summary
**DONE — resolved on the third implementation attempt.**

- **Attempt 1 (option a, stat differentiation via `role:`)**: falsified. `worldtemplate.v1`'s
  compile path never consulted the catalog for stats regardless of `role`; all 4 candidate
  roles also broke `EntityRole.MONSTER` bucketing. See
  `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/investigation_v1_option_a_rejected.md`
  / `plan_v1_option_a_rejected.md`.
- **Attempt 2 (option b, spawn placement/distance)**: architecture-approved, implemented,
  empirically tested, and also falsified. Widening `town_center`↔`woods` separation from ~14 to
  ~71 tiles had zero effect on the outcome. Direct event-log inspection found the real root
  cause: the `woods`/`wolf_den` region's own `hazard_level` environmental drain
  (`hazard_drain_applied`) self-killed the monster population in its own habitat, entirely
  independent of proximity to `town_center` or combat with any other faction.
- **Attempt 3 (recompile + verify, this pass)**: succeeded once both real prerequisite fixes
  landed — `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` (real catalog stats, closing the attempt-1
  gap) and `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (typed `hazard_kind`/`hazard_immunities`
  exemption mechanism, closing the attempt-2 gap), plus a resolver-plumbing hotfix
  (`TCK-20260701-HAZARD-KIND-RESOLVER-GAP`) that this pass's own re-verification surfaced as
  blocking `sandbox_world`'s specific resolve path. With all three in place, `sandbox_world` was
  recompiled (seed 42 hash `836b45e8913b46862240c6ba80f177f6`, seed 137 hash
  `7e8ae05dbeffccb8edd65fd9754787aa`) and empirically re-verified: **0/5 monster deaths across a
  full 200-tick run at both seeds, zero `hazard_drain_applied` events against `wild_beast_pack`
  entities** — exceeding the AC's minimum bar. Calibration anchors regenerated, D20 audit P2
  row resolved, divergence-log staleness note updated, full regression pass clean (184/184 +
  9/9 grade regression), parity ledger confirmed already correct (no re-touch needed). No `src/`
  changes at any point across all three attempts — this was a content/data/doc-only
  investigation-and-recompile chain throughout. This closes out the full investigation chain
  that started with the D20 SimQ audit's `early_extinction` P2 finding.

---

### ATTEMPT 3 — recompile + verify — 2026-07-02 — RESOLVED

The "third planning pass" called for above happened as `TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC`
(done), which delivered the two actual prerequisites external to this ticket:
`TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` (migrated `sandbox_world` off `worldtemplate.v1` onto
`worldcomposition.v1`, giving monsters real catalog stats instead of the flat 100/10/0 default —
closing the attempt-1 gap) and `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (added the typed
`RegionState.hazard_kind` / `FactionDefinition.hazard_immunities` exemption mechanism, authored
`hazard_kind: NATURAL_TERRAIN` on `wolf_den`/`near_forest` and `hazard_immunities:
[NATURAL_TERRAIN]` on `wild_beast_pack` — directly targeting the attempt-2 root cause, the
self-inflicted `hazard_drain_applied` environmental kill).

This attempt's first pass (recorded in this session's earlier `plan.md`/`investigation.md`
versions, superseded by the current ones) found a further blocker: `sandbox_world resolve`
failed outright because `RegionRecipeSpec` (`src/worldbuilding/recipe.py`) and
`WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py`) didn't
forward the new `hazard_kind` field — a Pydantic `extra_forbidden` error blocked all
`worldcomposition.v1` module loading. That gap was filed and fixed as a hotfix,
`TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (done).

With all three prerequisites landed, this final pass re-verified the whole chain from scratch
(not assuming any prior ticket's working-log claim) and executed the recompile:
- Re-ran `python3 -m src.worldbuilding.cli resolve sandbox_world` then
  `compile sandbox_world --seed 42 --from-resolved` (and `--seed 137`): both compile cleanly,
  zero validation errors, deterministic hashes reproduced on repeat runs — seed 42
  `836b45e8913b46862240c6ba80f177f6`, seed 137 `7e8ae05dbeffccb8edd65fd9754787aa`. Canonical
  seed-42 state left on disk in `data/worlds/sandbox_world/resolved/*` and
  `world_compile_report.json`.
- Confirmed `hazard_kind: NATURAL_TERRAIN` resolves on both `wolf_den`/`near_forest` (via the
  resolved YAML and the compiled `RegionState` objects), and traced `wild_beast_pack`'s
  `hazard_immunities` through the real `FactionSemanticsService` →
  `EnvironmentService.calculate_hazard_drain` path (not just YAML inspection): a `wild_beast_pack`
  entity standing in `wolf_den` takes `0` drain; a non-immune control entity (`hero_guild`) in the
  same region takes the expected `20`.
- Ran a full 200-tick Kernel re-run against the real compiled state (not the generic 10-entity
  fallback — confirmed `entity_count == 18` was loaded both via direct inspection and via
  `tools/calibrate_simq.py`, which loads `resolved/world.resolved.yaml` when present) for both
  seed 42 and seed 137: **all 5 `wild_beast_pack` monster entities (14-18) survive the full 200
  ticks at both seeds — 0 deaths, 0 `hazard_drain_applied` events against them.** This exceeds
  the AC's minimum bar. The `ENABLE_COMBAT_ENGAGEMENT` flag defaults off in this harness (same
  as documented for `TCK-20260701-SIMQ-AGENCY-ROUTING-DOC`'s AGENCY finding), so COMBAT-pillar
  `event_count=0` in the regenerated calibration anchors is expected and does not mask anything —
  the hazard-drain death mechanism that caused the original wipe is not gated by that flag and is
  independently confirmed absent via direct event-log inspection.
- Regenerated all 4 `sandbox_world_*` calibration anchors via `tools/calibrate_simq.py`
  (`--name sandbox_world --seed {42,137,999} --ticks 200` and `--seed 42 --ticks 1000`) and
  updated `tests/simulation_quality/fixtures/grade_anchors.json` to match the new empirical
  grades. Net grade shifts vs. the prior (pre-hazard-fix) anchors: `seed42_200t` and
  `seed137_200t` COMBAT B→C and PROGRESSION B→C (both consistent with the reduced/changed event
  mix once monsters stop dying); `seed999_200t` PROGRESSION B→C; `seed42_1000t` NARRATIVE B→A.
  `WORLD` stayed B across all four. `test_grade_regression.py -k sandbox_world` (4/4) and the
  full suite (9/9) pass against the new anchors.
- Full regression pass: `tests/integration/worldassembly/` + `tests/unit/worldbuilding/` +
  `tests/unit/worldassembly/` — **184/184 passed**, no regressions. Sanity re-run of the
  hazard-immunity mechanism's own unit coverage
  (`tests/unit/world/test_regional_consequences.py`, `test_semantics.py::test_get_hazard_
  immunities`, `test_catalog.py` hazard-immunity tests) — 11/11 passed, unmodified.
- Updated `docs/audits/D20_simq_integration.md`'s P2 `early_extinction` row to resolved, with
  the full three-part root-cause chain and final outcome. Updated
  `docs/guidelines/intentional_divergences.md` entry 2.20's staleness note (one line) to reflect
  the recompile having happened, rather than adding a new divergence entry (the divergence
  itself was already documented by `TCK-20260701-HAZARD-NATIVE-IMMUNITY`).
- Parity ledger (`docs/parity_ledger/world_dynamics.yaml` WORLD-029/WORLD-060): confirmed
  already correctly updated by `TCK-20260701-HAZARD-NATIVE-IMMUNITY`; no re-touch needed, per
  architecture review.
- No `src/` files touched (scope guard respected: `src/world/environment.py`,
  `src/worldbuilding/compiler.py`, `src/worldbuilding/recipe.py`,
  `src/worldassembly/resolver.py` all untouched — already correct and shipped by sibling
  tickets).

**This closes out the full investigation chain started by the D20 SimQ audit's `early_extinction`
P2 finding.**
