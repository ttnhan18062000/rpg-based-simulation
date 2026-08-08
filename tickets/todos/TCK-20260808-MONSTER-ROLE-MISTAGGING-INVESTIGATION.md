---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
phase: open
date: 2026-08-08
tags: [content, world]
---

# TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION

## Title
Investigate why monster-kind entities are frequently tagged `entity.identity.role = CITIZEN`
corpus-wide instead of `MONSTER` — real lead found, root cause not yet confirmed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

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
- [ ] investigation.md traces the real construction path for a real monster population and
      confirms the exact root cause (not assumed)
- [ ] Real fix lands and is re-verified against a live compiled world's actual
      `entity.identity.role` values, not just static code reading
- [ ] Known downstream consumers (`SpawnService`, `CombatResolutionSystem`) checked for any
      behavior change resulting from the fix — disclosed if any anchor/behavior shift results
- [ ] Scoped pytest passes

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
None yet.

## Related Code Areas
- `src/content_semantics/role.py` (`RoleSemanticsService.get_legacy_entity_role`)
- `data/content/social/roles.yaml` (role catalog — confirmed correct for monster archetypes)
- `data/content/entities/entity_archetypes.yaml` (archetype-native `role:` field values)
- `src/entities/contract_builder.py` (`resolved_archetype_to_contract` — path 1)
- `src/worldassembly/resolver.py` (population expansion — path 2, real call sites at lines
  ~949/994/1022 as of this ticket's filing)
- `src/world/spawn.py` (`SpawnService.process_spawns()` — real downstream consumer)
- `src/engine/combat.py` (`EntityRole.HERO`/`EntityRole.MONSTER` checks — real downstream consumer)

## Assumptions / Open Questions
- Whether `pop_spec.role`'s real value for monster populations matches the roles.yaml catalog —
  not assumed; this is the investigation's own first real question to answer.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
