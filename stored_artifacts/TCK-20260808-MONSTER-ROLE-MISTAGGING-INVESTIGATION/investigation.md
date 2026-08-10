---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
artifact_type: investigation
tags: [content, world]
---

# Investigation: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION

## Question
Why are monster-kind entities frequently tagged `entity.identity.role = CITIZEN` corpus-wide
instead of `MONSTER`?

## Method
Direct, layered tracing: catalog inspection, direct construction-path source reads, and live
compiled-state inspection at each layer to confirm/refute hypotheses with real data rather than
static reasoning alone.

## Hypothesis 1 (refuted): Ambiguous shared role_id
`roles.yaml` was checked for every role_id used by real monster archetypes. Most are unambiguous
and correct (predator_hunter/alpha/raider/leader/sentinel/brute → MONSTER). But some are
genuinely ambiguous and shared with non-monster archetypes: `scout`→GUARD, `guardian`→GUARD,
`hunter`→HERO, `shaman`→HERO — used by real monster archetypes (goblin_scout, spirit_guardian,
dwarven_hunter, lizardfolk_shaman). This is a real, partial contributing factor.

**Refuted as the primary cause**: direct compiled-state inspection (`dungeon_crawl_seed42`)
showed EVERY sampled monster archetype — including unambiguous ones like "predator_hunter" and
"raider" that `roles.yaml` correctly maps to MONSTER — showing `role=CITIZEN`. If the catalog
lookup were succeeding, these should have shown MONSTER correctly. Something was preventing the
catalog lookup from ever succeeding at all.

## Hypothesis 2 (confirmed): `WorldCompiler.compile()` has no catalog access

`RoleSemanticsService.get_legacy_entity_role('predator_hunter')` tested in complete isolation
correctly returns `EntityRole.MONSTER` — the catalog and the service both work correctly.

`WorldCompiler.compile()`'s own signature: `compile(spec, seed, output_report_path=None,
context=None)` — no `catalog_repo` parameter at all. Its local `get_role_enum()`/
`get_faction_enum()` helpers (`src/worldbuilding/compiler.py`) can ONLY reach the real, correct
`RoleSemanticsService` path when a `context` (a `CompileContext`) with a pre-populated
`legacy_roles`/`legacy_factions` dict is passed in. Without it, they fall through to a local,
naive keyword-matching fallback that checks for the literal substrings HERO/SHOP/STORE/MONSTER/
CITIZEN/CIVILIAN/WORKER/PEASANT/GUARD — none of which appear in real archetype role_ids like
"predator_hunter"/"raider"/"sentinel"/"scout"/"leader", defaulting all of them to
`EntityRole.CITIZEN`.

Real corpus worlds already have the correct mapping computed and persisted: `data/worlds/
{name}/resolved/compile_context.json` (generated once by `WorldAssemblyResolver.assemble()`
during the original module→worldspec resolution) contains exactly the right `legacy_roles`
mapping (confirmed: `{"scout": 5, "raider": 2, "leader": 2, "predator_hunter": 2, "sentinel": 2}`
— matching `EntityRole` int values exactly). `CompileContext.from_dict()` correctly reconstructs
proper `EntityRole` enum instances from this data.

**The real gap**: `WorldRepository.load_world()` never surfaced this file. Of the 6 real callers
of `WorldCompiler.compile()` found via `grep -rln "WorldCompiler.compile(" src/ tools/`:
- `src/worldbuilding/cli.py`'s own `compile` subcommand — correctly loads and passes
  `compile_context.json` (independently implemented).
- `src/lab/orchestrator.py` — also correctly loads it (independently implemented, separately).
- `src/cli/entry.py` (the general "run a simulation" CLI entrypoint), `tools/calibrate_simq.py`,
  `tools/balance_measure.py`, `tools/personality_audit.py` — all 4 call
  `WorldCompiler.compile(spec, seed)` with NO context, confirmed via direct source read.

This confirms the bug affects real, live simulation runs through the standard CLI (not just
SimQ calibration tooling), and that the correct fix already existed independently in 2 places —
never centralized, so 4 other real callers missed it.

## Fix
Added `WorldRepository.load_world_with_context(world_id) -> (WorldSpec, Optional[CompileContext])`
— centralizes the correct loading logic (mirrors `load_world()`'s own composition-detection,
additionally loading `resolved/compile_context.json` via `CompileContext.from_dict()` when
present). Updated the 4 confirmed-buggy call sites.

## Verification
Direct compiled-state inspection, both before and after the fix, on both `dungeon_crawl` and
`urban_political`. Zero `CITIZEN` mistagging remains post-fix. `urban_political`'s own faction
distribution moved from zero `MONSTER_HORDE`-tagged entities anywhere in the compiled world to 4
correctly-tagged entities — real hostile factions were previously entirely invisible to
faction-based hostility detection.

## Real, Measured, Disclosed Impact
- `SpawnService.process_spawns()`'s own monster-density check was structurally blind before this
  fix (always saw ~0 real monsters). Real corpus effect: WORLD-pillar event count dropped 152→114
  post-fix (`dungeon_crawl_seed42_2000t`) — the expected direction (correctly-throttled spawning).
- `urban_political_seed42_2000t`'s COMBAT pillar moved from grade C (norm ~-0.002, 5 events) to
  grade A (norm ~+1.03, 196 events), reproduced twice for consistency — a large, real, positive
  shift from previously-invisible hostile pairs now correctly engaging.
- `CombatRewardClassificationService` (keyed by `EntityRole.MONSTER`/`HERO`) is a real, disclosed,
  secondary consumer — not separately re-verified at corpus scale (out of proportionate scope).
- `grade_anchors.json` deliberately not updated (out of this ticket's own scope) — a real,
  material shift is now disclosed; a follow-up recalibration ticket is a concrete candidate.
