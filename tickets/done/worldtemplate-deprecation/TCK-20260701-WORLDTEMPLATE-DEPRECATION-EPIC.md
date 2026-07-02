---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC
phase: done
date: 2026-07-01
tags: [world, architecture, schema, worldtemplate, worldcomposition, refactor]
---

# TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC

## Title
Deprecate the worldtemplate.v1 authoring schema; migrate sandbox_world to worldcomposition.v1

## Status
DONE

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
Investigating `TCK-20260701-SANDBOX-MONSTER-BALANCE` (SimQ D20 audit follow-up: 5 monster
entities in `sandbox_world` die within the first 10 ticks) surfaced a deeper architecture
issue: `sandbox_world` is compiled via the `worldtemplate.v1` authoring schema, whose compile
path (`WorldCompiler.compile()` called with `context=None`) never resolves entity stats from
the catalog — every entity, monster or citizen, gets identical flat defaults
(`hp=100/atk=10/def=0`). This is not a `sandbox_world`-specific content bug; it's a gap in an
entire legacy schema pipeline.

Checking every compiled world in `data/worlds/` confirms `sandbox_world` is the **only** world
still on `worldtemplate.v1` — all 9 others already use `worldcomposition.v1` (the module-based
composition system). `worldtemplate.v1` was a stopgap (population "recipes" instead of fully
enumerated entities) that predates `worldcomposition.v1`'s real catalog-driven stat resolution
via `WorldAssemblyResolver` → `CompileProfileResolver` → `RoleSemanticsService`, and it was
never retrofitted once the newer system existed. `worldcomposition.v1` already fully
supersedes its use case (module-based composition avoids the "huge data file for a complex
world" problem `worldtemplate.v1` also existed to solve) and is confirmed as the standing
primary approach going forward.

**Decision (confirmed with user 2026-07-01):** migrate `sandbox_world` off `worldtemplate.v1`,
then remove `worldtemplate.v1` support entirely (CLI branches, template-expansion code,
`create-template` bootstrap) rather than patch the legacy pipeline's stat-resolution gap.

**Important distinction — do NOT remove `worldspec.v1`.** `worldspec.v1` is not a competing
legacy authoring format: it is the compiler's canonical internal spec shape.
`WorldCompiler.compile(spec: WorldSpec, ...)` only ever accepts a `WorldSpec` object, and every
resolved `worldcomposition.v1` world's `resolved/world.resolved.yaml` is itself tagged
`schema_version: worldspec.v1` (verified: `data/worlds/urban_political/resolved/
world.resolved.yaml` and others). Zero `data/worlds/*/world.yaml` source files author
`worldspec.v1` directly — it exists purely as `WorldAssemblyResolver`'s output target and
`WorldCompiler`'s required input type. Removing it would break compilation for all 9
`worldcomposition.v1` worlds. `worldspec.v1` stays; only `worldtemplate.v1` (the standalone
recipe-authoring schema) is deprecated.

A related, separately-scoped finding from the same investigation: `EnvironmentService.
calculate_hazard_drain(region, entity)` (`src/world/environment.py`) already takes `entity` as
a parameter but never uses it — hazard damage is currently universal regardless of whether the
entity is native to that region's habitat or an intruding hostile. This is the actual
root cause of the `sandbox_world` monster deaths (their own `woods` region's `hazard_level:
1.5` kills them in ~7 ticks, independent of distance to town or their stats) and is tracked as
a child ticket here since it's an independent engine change.

## Scope
This epic tracks child tickets only — no direct implementation. Child tickets:

1. `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` — author a `worldcomposition.v1` replacement for
   `sandbox_world` (reusing existing modules, e.g. `frontier_village_core` for the town
   population and `wolf_den_near_forest` or a similar ecology module for the monster
   population), replacing the current `worldtemplate.v1` `world.yaml`.
2. `TCK-20260701-WORLDTEMPLATE-REMOVE` — remove `worldtemplate.v1` CLI support, the template-
   expansion code path, and the `create-template` bootstrap; update all affected docs. Depends
   on (1) — cannot remove the only schema `sandbox_world` still uses until it's migrated.
3. `TCK-20260701-HAZARD-NATIVE-IMMUNITY` — extend `EnvironmentService.calculate_hazard_drain`
   to exempt region-native entities from their own habitat's environmental hazard; hostile/
   visiting factions remain affected. Independent of (1)/(2).
4. `TCK-20260701-SANDBOX-MONSTER-BALANCE` (already exists, currently `BLOCKED` in
   `tickets/inprogress/`) — re-verify and close once (1) and (3) land. Not re-created here;
   linked as a dependent consumer of this epic's work.

## Out of Scope
- Removing or restructuring `worldspec.v1` (the compiler's internal canonical format — must
  stay; see Request Summary)
- Migrating any world other than `sandbox_world` (all others are already on
  `worldcomposition.v1`)
- Any change to `worldcomposition.v1`'s own resolution/assembly logic beyond what's needed to
  author `sandbox_world`'s replacement composition
- Broader hazard/combat rebalancing beyond the native-immunity mechanism

## Acceptance Criteria
- [ ] `sandbox_world` compiles via `worldcomposition.v1` with no `worldtemplate.v1` source
      file remaining
- [ ] `worldtemplate.v1` schema support is fully removed from `src/worldbuilding/cli.py` and
      any expansion code solely used for it
- [ ] `worldspec.v1` is untouched and still functions as the compiler's internal format
- [ ] Hazard drain exempts region-native entities; hostile/visiting entities remain affected
- [ ] `TCK-20260701-SANDBOX-MONSTER-BALANCE` is unblocked and closed
- [ ] All affected docs updated (see Related Docs) and, if this counts as an intentional
      behavior divergence, an entry added to `docs/guidelines/intentional_divergences.md`
      (confirmed correct path — not `v2_intentional_divergences.md` as CLAUDE.md's table
      names it; that filename does not exist on disk)

## Related Tickets
- TCK-20260701-SANDBOX-MONSTER-BALANCE (`tickets/inprogress/`, `BLOCKED`) — the ticket whose
  two failed fix attempts led to this investigation; blocked on this epic's children
- TCK-20260628-SIMQ-EPIC — grandparent context; SimQ calibration surfaced the original symptom
- TCK-20260614-WORLDMOD-UNIFY, TCK-20260614-WORLDDAT-MIGRATE — prior precedent for schema
  unification/migration in this same subsystem (WorldModuleSpec v1/v2 merge)

## Related Docs
- `docs/architecture/world_repository_layout.md` — documents all three schema versions;
  needs updating to reflect `worldtemplate.v1` removal
- `docs/guides/simulation.md` — world authoring guide; references `create-template` (line 37)
  which bootstraps a `worldtemplate.v1` file
- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology / world generation
  law; check for any `worldtemplate.v1`-specific references
- `docs/mechanics/05_world_evolution.md` §2 (Regional Trauma & Hazards) — needs a native-
  immunity clause once child ticket 3 lands
- `docs/parity_ledger/world_dynamics.yaml`, `docs/parity_ledger/substrate.yaml` — check for
  entries referencing schema versions or hazard drain formula
- `docs/guidelines/intentional_divergences.md` — add entries for both changes if warranted
- `docs/audits/D20_simq_integration.md` P2 row — resolves once child tickets land

## Related Stored Artifacts
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/` — contains full evidence of both
  rejected fix attempts (stat differentiation via role, spawn-placement distance), including
  the `WorldCompiler.compile()` context-gap trace and the hazard_drain_applied discovery

## Related Code Areas
- `data/worlds/sandbox_world/world.yaml` — current `worldtemplate.v1` source
- `data/content/world_modules/frontier_village_core.yaml`, `wolf_den_near_forest.yaml` —
  candidate reusable modules for the replacement composition
- `src/worldbuilding/cli.py` (~L101-102, ~L247-250, ~L336-337, ~L398 `create-template`) —
  `worldtemplate.v1` CLI branches
- `src/worldbuilding/recipe.py` — `WorldTemplateExpander` (template expansion, likely
  removable if solely used by `worldtemplate.v1`)
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()` (unchanged; already
  schema-agnostic, takes `WorldSpec` regardless of source)
- `src/worldbuilding/schema.py:123-158` — `WorldSpec` (`worldspec.v1`, keep unchanged)
- `src/world/environment.py` — `EnvironmentService.calculate_hazard_drain()`
- `src/engine/world_dynamics.py` (~L20-40) — where hazard drain is applied per-entity per-tick

## Assumptions / Open Questions
- Assumes the replacement `sandbox_world` composition should approximate the current
  population (roughly 15 citizens + 3 heroes in a town, 5 monsters in a nearby wilderness
  region) rather than match it exactly — module reuse won't produce identical entity counts,
  and that's expected/acceptable. Child ticket 1 should confirm this reading is correct.
  A different entity_count / new state_hash is expected and not a determinism regression.
  Does not need docs/guidelines/intentional_divergences.md entry as an entity-count difference
- "Native to a region" (for hazard immunity) needs a concrete definition during child ticket 3
  — candidates: entity's `kind` (e.g. `"monster"`), entity's `Faction` matching the region's
  associated wild/hostile faction, or a module-level tag. `wolf_den_near_forest.yaml`'s
  description ("proving contextual hostility instead of enemy-by-type") suggests a
  faction/context-based pattern may already partially exist there — investigate before
  designing a new mechanism.

## Implementation Notes
(epic — no direct implementation)

## Test Summary
(epic — see child tickets)

## Files Changed
(epic — see child tickets)

## Completion Summary
All three child tickets done:
- `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` — `sandbox_world` migrated to `worldcomposition.v1`
  (reusing `frontier_village_core` + `wolf_den_near_forest`); monster entities now resolve real
  catalog stats. Calibration anchors regenerated, 176 tests pass. Empirically confirmed the
  extinction symptom persists post-migration (real stats, still dies) — correctly isolating
  the hazard drain as the true root cause rather than a stats artifact.
- `TCK-20260701-HAZARD-NATIVE-IMMUNITY` — shipped in two passes. First pass (Faction.MONSTER_HORDE
  + region.kind=="WILDERNESS") was reviewed, tested, and shipped, then superseded by a
  user-directed redesign to a proper data-driven model: `RegionState.hazard_kind` +
  `FactionDefinition.hazard_immunities`, faction-specific and hostility-independent (a shared
  unendured hazard hurts mutually hostile factions equally). Second pass: 78+304 tests pass,
  docs/parity ledger/divergence log all in parity.
- `TCK-20260701-WORLDTEMPLATE-REMOVE` — `worldtemplate.v1` schema fully removed (CLI branches,
  `WorldTemplateExpander`, two production call sites the ticket's own scope missed);
  `create-template` repointed to scaffold `worldcomposition.v1`; `worldspec.v1`/`WorldSpec`
  confirmed untouched throughout. 247 tests pass.

`TCK-20260701-SANDBOX-MONSTER-BALANCE` (external, `tickets/inprogress/`, still `BLOCKED` after
two prior failed attempts) is now ready for a fresh attempt: `sandbox_world` has real stats
(fix #1) and the hazard mechanism now supports native exemption (fix #2), but `sandbox_world`
has not yet been recompiled to pick up the new `hazard_kind`/`hazard_immunities` content, and
no empirical re-run has confirmed the combination actually resolves the tick-8 extinction —
that verification is that ticket's job, not assumed here.
