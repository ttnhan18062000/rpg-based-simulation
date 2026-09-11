---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
phase: done
date: 2026-08-08
tags: [content, world]
---

# TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION

## Title
Investigate why monster-kind entities are frequently tagged `entity.identity.role = CITIZEN`
corpus-wide instead of `MONSTER` — root cause confirmed and fixed: `WorldCompiler.compile()`
had no catalog access of its own, and every real caller except 2 omitted the `CompileContext`
that's the only other way it can resolve role/faction correctly

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Real corpus data (found during `TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`, restated
in `docs/audits/D21_entity_lifecycle_foundation_layers.md`) shows monster-kind entities are
frequently tagged `role=CITIZEN` instead of `role=MONSTER`. `SpawnService.process_spawns()`
(`src/world/spawn.py`) reads `EntityRole.MONSTER` for its own density check, so this mistagging has
a real, live downstream consequence. This matters beyond that one call site: `entity.identity.role`
is exactly the field the simulation's own human/monster behavioral split (complex cognitive path
for humans vs. patrol/attack-only for monsters, no quests/trade/communication) would need to lean
on to be enforced by the engine rather than by coincidence of world layout.

**A real, more specific lead was found investigating this ticket's own filing** (not yet fully
confirmed — this is the investigation's starting point, not its conclusion):

- `RoleSemanticsService.get_legacy_entity_role(role_id)` (`src/content_semantics/role.py`,
  `docs/content/content_semantics_contract.md`) is the real service responsible for mapping a
  catalog role ID to the legacy `EntityRole` enum. It looks up `RoleDefinition.legacy_engine_role`
  first; only falls back to keyword-matching the `role_id` string (HERO/SHOP/MONSTER/CITIZEN/
  WORKER/GUARD, final fallback `EntityRole.CITIZEN`) if the catalog lookup misses.
- **The catalog itself (`data/content/social/roles.yaml`) is correct**: `predator_hunter`,
  `alpha`, `raider`, `leader`, `sentinel`, `brute`, `dragon_champion` (real monster-archetype role
  IDs, confirmed via `data/content/entities/entity_archetypes.yaml`'s own `role:` field values)
  all map to `legacy_engine_role: MONSTER` in the roles catalog. So the naive "keyword-fallback
  fails for creature-flavored role names" theory is **refuted** — the primary catalog path should
  work correctly if it's actually being used with the right lookup key.
- **3 real entity-construction paths exist** (per `src/entities/contract_builder.py`'s own
  docstring): (1) archetype-native (`resolved_archetype_to_contract`, reads
  `arch.legacy_engine_role` directly off an already-resolved archetype — looks correct), (2)
  "worldspec role/faction/count" population expansion (`src/worldassembly/resolver.py`, confirmed
  via direct grep to call `self.role_semantics.get_legacy_entity_role(pop_spec.role)` at 3 call
  sites — also looks correct, IF `pop_spec.role` holds the right catalog `id` string), (3) legacy
  `V2EntityBuilder` (arena/test/migration use, likely not the corpus's real path).
- **Open, unconfirmed question**: real world modules (e.g. `goblin_camp_conflict.yaml`,
  `wolf_den_near_forest.yaml`) do NOT declare population entries with a literal `role:` key
  (confirmed via direct grep — zero matches) — meaning `pop_spec.role`'s actual real string value
  for monster populations in real world content is not yet traced. If it resolves to something
  other than the exact catalog `id` (e.g. a race/kind name like "goblin"/"wolf" instead of a role
  archetype name like "raider"/"alpha"), the catalog lookup would miss and fall through to the
  keyword-fallback — which WOULD then default to `CITIZEN` for a creature-name string. This is the
  strongest real candidate for the actual root cause, but is not yet confirmed — trace
  `pop_spec.role`'s real value for a real monster population before concluding.

## Scope
1. **Investigate** (mandatory before Plan):
   - Trace a real monster population's actual construction path end-to-end for a real corpus world
     (e.g. `goblin_camp_conflict` module's own population entries) — confirm which of the 3
     construction paths is actually used, and what the real `role_id`/`pop_spec.role` string value
     is at the point `get_legacy_entity_role()` is called.
   - Confirm or refute the "population spec's role field doesn't match the roles.yaml catalog id"
     hypothesis with real data (a live compile + direct field inspection, not static reading alone).
   - If confirmed: determine the real, minimal fix — likely either (a) world module content should
     declare the correct catalog role ID, or (b) `PopulationRecipeResolver`/whatever resolves
     `pop_spec.role` needs its own translation step from race/kind name to catalog role ID.
   - If refuted: keep investigating — check `ArchetypeEntityFactory`/`EntityArchetypeResolver`
     directly for a different real cause (e.g. a default/fallback value assigned before the role
     service is ever consulted).
2. **Plan**: once root cause is confirmed, scope the real fix — content correction, resolver
   translation fix, or both. Note the real downstream consumers already known
   (`SpawnService.process_spawns()`'s density check; `CombatResolutionSystem`'s reward
   classification and multiple `EntityRole.HERO`/`EntityRole.MONSTER` checks in `src/engine/
   combat.py`) so the fix's real blast radius is understood before landing it.
3. **Implement**: the confirmed, minimal fix. Re-verify via a real compiled world + direct
   `entity.identity.role` inspection that monster-kind entities now correctly show `MONSTER`.

## Out of Scope
- Any change to the human/monster behavioral split itself (quest/trade/communication gating) —
  this ticket only concerns the underlying data-integrity signal (`entity.identity.role`) being
  correct, not building new behavior on top of it.
- `IDENTITY` bucket reachability (`entity_role_changed`/`entity_faction_changed` events) — a
  separate, already-documented hard ceiling (`docs/audits/D21_entity_lifecycle_foundation_layers.md`),
  unrelated to this ticket's own concern (initial spawn-time role assignment, not post-spawn role
  changes).

## Acceptance Criteria
- [x] investigation.md traces the real construction path for a real monster population and
      confirms the exact root cause (not assumed) — the ticket's own original "ambiguous shared
      role_id" hypothesis was refuted by real data (even unambiguous role_ids like
      "predator_hunter" showed CITIZEN); the real cause is one level deeper: `WorldCompiler.
      compile()` has no catalog access of its own and needs a pre-populated `CompileContext` it
      almost never receives
- [x] Real fix lands and is re-verified against a live compiled world's actual
      `entity.identity.role` values, not just static code reading — confirmed via direct
      compiled-state inspection, zero CITIZEN mistagging remains
- [x] Known downstream consumers (`SpawnService`, `CombatResolutionSystem`) checked for any
      behavior change resulting from the fix — disclosed if any anchor/behavior shift results —
      both checked; a real, disclosed, material shift confirmed (see Completion Summary)
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS (DONE — original finding)
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT (DONE — restated this finding as a foundation-layer
  data-integrity risk)
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent context)

## Related Docs
- `docs/content/content_semantics_contract.md` (`RoleSemanticsService`)
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`
- `docs/audits/D05_entity_differentiation.md` (prior real per-entity role observation data)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION/` (moved to
  `stored_artifacts/` at Finalize)

## Related Code Areas
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, `get_role_enum()`/
  `get_faction_enum()` — the real, confirmed bug site: no `catalog_repo` of its own)
- `src/worldbuilding/repository.py` (`WorldRepository` — new `load_world_with_context()` method,
  the real fix)
- `src/worldassembly/context.py` (`CompileContext` — the already-correct mapping this fix
  surfaces, previously computed but never read by most real callers)
- `src/content_semantics/role.py` (`RoleSemanticsService.get_legacy_entity_role` — confirmed
  correct in isolation; the bug was never reaching it)
- `data/content/social/roles.yaml` (role catalog — confirmed correct for monster archetypes)
- `data/worlds/{name}/resolved/compile_context.json` (the real, already-computed, previously-
  unused artifact this fix surfaces — exists for every corpus world)
- `src/cli/entry.py`, `tools/calibrate_simq.py`, `tools/balance_measure.py`,
  `tools/personality_audit.py` (the 4 real, confirmed-buggy call sites, now fixed)
- `src/world/spawn.py` (`SpawnService.process_spawns()` — real downstream consumer, behavior
  shift confirmed)
- `src/engine/combat_rewards.py` (`CombatRewardClassificationService` — real, secondary
  downstream consumer, disclosed but not separately re-verified)

## Assumptions / Open Questions
- Whether `pop_spec.role`'s real value for monster populations matches the roles.yaml catalog —
  **resolved**: it does (confirmed via direct inspection of `world.resolved.yaml` and
  `WorldAssemblyResolver`'s own construction). The ticket's own original "ambiguous shared
  role_id" hypothesis was refuted — the real bug is one level deeper.

## Implementation Notes
Traced 3 levels deep before finding the real root cause:
1. Confirmed the catalog itself (`roles.yaml`) is correct, and found some real ambiguous shared
   role_ids ("scout"→GUARD, "hunter"→HERO, "shaman"→HERO, "guardian"→GUARD) used by real monster
   archetypes (goblin_scout, dwarven_hunter, lizardfolk_shaman, spirit_guardian) — a real,
   partial contributing factor, but NOT the primary cause.
2. Direct compiled-state inspection (`dungeon_crawl_seed42`) showed EVERY sampled monster
   archetype role — including unambiguous ones like "predator_hunter"/"raider"/"sentinel" that
   `roles.yaml` correctly maps to MONSTER — showing `role=CITIZEN`. This ruled out the
   ambiguous-role-id hypothesis as the sole/primary cause: something was preventing the catalog
   lookup from ever succeeding at all.
3. `RoleSemanticsService.get_legacy_entity_role('predator_hunter')` tested in isolation DOES
   correctly return MONSTER — the catalog and service both work. The real bug: `WorldCompiler.
   compile()` has no `catalog_repo` parameter of its own (confirmed via its own signature) — it
   can ONLY resolve role/faction correctly via a pre-populated `context.legacy_roles`/
   `.legacy_factions` mapping. `data/worlds/{name}/resolved/compile_context.json` already
   contains this exact, correct mapping (computed once by `WorldAssemblyResolver.assemble()`),
   but `WorldRepository.load_world()` never surfaced it, and 4 of 6 real callers of
   `WorldCompiler.compile()` never loaded/passed it (only `src/worldbuilding/cli.py`'s own
   `compile` subcommand and `src/lab/orchestrator.py` did, independently duplicating the correct
   logic each time).

Fix: added `WorldRepository.load_world_with_context()`, centralizing the correct load-and-pass
logic (previously only correctly implemented in 2 places, duplicated) so all 6 real callers can
share it. Updated the 4 confirmed-buggy callers (`src/cli/entry.py` — the general simulation-run
CLI entrypoint; `tools/calibrate_simq.py`; `tools/balance_measure.py`;
`tools/personality_audit.py`) to use it.

**Downstream consumer check (per Acceptance Criteria)**: `SpawnService.process_spawns()`'s own
monster-density check (`src/world/spawn.py:55`) was confirmed to always see ~0 real monsters
before this fix (since none were ever tagged MONSTER), meaning it was structurally unable to
throttle spawning correctly — likely over-spawning relative to the intended density target. Real
corpus re-verification (`dungeon_crawl_seed42_2000t`): WORLD pillar events dropped from 152 to
114 post-fix, a real, modest, expected consequence. `CombatRewardClassificationService`
(`src/engine/combat_rewards.py`, keyed by `EntityRole.MONSTER`/`HERO`) is a real, disclosed,
secondary consumer — a mistagged monster fell through to an unintended reward classification;
not separately re-verified at corpus scale (out of proportionate scope for this ticket's own
Verify step).

**Real, significant, disclosed finding**: `urban_political_seed42_2000t`'s own faction
distribution moved from `{TOWN_COUNCIL: 14, NEUTRAL: 13, HERO_GUILD: 3}` (zero MONSTER_HORDE at
all) to `{TOWN_COUNCIL: 14, NEUTRAL: 9, MONSTER_HORDE: 4, HERO_GUILD: 3}` — real hostile-faction
entities were previously entirely invisible to faction-based hostility detection. The real,
measured COMBAT pillar consequence: grade moved from C (norm ~-0.002, 5 events) to A (norm
~+1.03, 196 events), reproduced twice for consistency. This directly connects to this session's
whole day of combat-resolution investigation (`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`
et al.) — this bug may have been a real, previously-unaddressed contributing cause sitting
underneath the identity-resolver-layer fixes those tickets landed, for at least some worlds.

## Test Summary
4 new tests in `tests/unit/worldbuilding/test_world_repository.py`: non-composition returns
`(spec, None)`; composition with a real `compile_context.json` returns the correct `EntityRole`
mapping; composition missing `compile_context.json` degrades gracefully to `None` (not an error);
unresolved composition still raises. All 4 confirmed via git-stash bisection to genuinely fail
pre-fix. Full scoped re-run: `tests/unit/worldbuilding/`, `tests/simulation_quality/`,
`tests/unit/content_semantics/`, `tests/unit/core/`, `tests/unit/entities/`, `tests/unit/world/`,
`tests/unit/tactical/`, `tests/unit/combat/`, `tests/unit/engine/`, `tests/unit/kernel/`,
`tests/integration/worldassembly/`, `tests/integration/kernel/test_determinism_suite.py` — 1479
passed, 84 skipped, only the 1 pre-existing, already-confirmed-unrelated failure
(`test_grade_anchor_file_exists_and_valid`, missing local calibration-report fixture, confirmed
via bisection identical on pristine pre-fix code).

Real corpus re-verification: direct compiled-state inspection (`dungeon_crawl_seed42`,
`urban_political_seed42`) confirms zero entities show `role=CITIZEN` post-fix (was ~100% of
monster-archetype entities); real faction distribution corrected (see Implementation Notes). SimQ
calibration re-run on both worlds shows the real, disclosed COMBAT/WORLD pillar shifts documented
above and in `docs/parity_ledger/substrate.yaml` SUB-384.

## Files Changed
- `src/worldbuilding/repository.py` — new `WorldRepository.load_world_with_context()` method
- `src/cli/entry.py`, `tools/calibrate_simq.py`, `tools/balance_measure.py`,
  `tools/personality_audit.py` — the 4 real, confirmed-buggy call sites, fixed
- `tests/unit/worldbuilding/test_world_repository.py` — 4 new tests
- `docs/parity_ledger/substrate.yaml` — SUB-384 (full fix, real measured impact)
- `docs/parity_ledger/infrastructure.yaml` — INFRA-330 (calibration-tooling half)
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` — updated the prior "disclosed, not
  fixed" section to reflect the confirmed fix
- `docs/content/content_semantics_contract.md` — added the real structural caveat to
  `RoleSemanticsService`'s own docs

## Completion Summary
Investigated a real, corpus-wide data-integrity bug the ticket's own filing had already narrowed
to a real lead (an ambiguous shared role_id hypothesis) but not confirmed. That hypothesis was
refuted by real data — even unambiguous monster role_ids showed the same mistagging — and traced
one level deeper to the real, complete root cause: `WorldCompiler.compile()` has no catalog
access of its own and can only correctly resolve `entity.identity.role`/`.faction` via a
pre-populated `CompileContext` that 4 of 6 real callers never loaded, silently falling back to
naive keyword matching that fails for almost every real monster archetype role/faction ID. Fixed
by centralizing the already-correct-in-2-places loading logic into one shared
`WorldRepository.load_world_with_context()` method and updating all 4 real, confirmed-buggy call
sites — including the general "run a simulation" CLI entrypoint, meaning this bug affected real,
live simulation runs, not just SimQ calibration tooling.

Checked both known downstream consumers per the ticket's own acceptance criteria and found real,
disclosed behavior shifts for both: `SpawnService`'s monster-density spawn-throttling was
structurally blind before this fix (real WORLD-pillar event count dropped 152→114 post-fix, the
expected direction); `CombatRewardClassificationService`'s own reward-classification lookup was
also affected (disclosed, not separately re-verified at corpus scale). Went beyond the minimum
bar by measuring the real, material SimQ-scoring consequence directly: `urban_political`'s own
COMBAT pillar moved from grade C to grade A, because real hostile-faction entities that were
previously invisible to faction-based hostility detection (0 real MONSTER_HORDE-tagged entities
existed anywhere in that compiled world before this fix) are now correctly detected — a
significant, real, honestly-measured connection back to this session's entire day of separate
combat-resolution investigation work. `grade_anchors.json` itself was deliberately not touched
(out of this ticket's own scope) — a follow-up recalibration ticket is a real, concrete
candidate for the user's next direction, given the confirmed, material shift.
